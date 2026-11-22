---
name: ship-pr
description: Liga o auto-merge (squash) de um PR na branch principal, preso ao SHA da head, e espera o resultado; quem decide é o ruleset. Só o usuário dispara, porque o merge é decisão humana.
disable-model-invocation: true
argument-hint: '[pr-number]'
model: opus
---

<!-- LTeX: language=pt-BR -->

Integre à branch principal o PR $ARGUMENTS (sem número: o PR da branch atual, `gh pr view --json number`). Nomes em crases como `main-branch`, `gate`, `check` e `test` são **contratos**: o valor real está na tabela de contratos das regras do projeto (formato em `${CLAUDE_PLUGIN_ROOT}/README.md`). Contrato ausente da tabela: pare e pergunte, nunca adivinhe.

Quem decide se pode integrar é o **ruleset** da `main-branch` (check `gate` verde no SHA da head, branch atualizada, histórico linear). A skill não reimplementa essa decisão: liga o [auto-merge](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request), que só integra depois que todos os requisitos passam, e espera o resultado. Nunca `--admin`.

1. Se houver outro PR aberto (`gh pr list`), pare e pergunte: um PR aberto por vez.
2. Leia `gh pr view <n> --json state,headRefOid,mergeStateStatus`, uma leitura por comando.
   - `MERGED`: vá ao passo 5.
   - `UNKNOWN` (logo após um merge na `main-branch` ele ainda não foi calculado): leia de novo, no máximo 3 vezes; persistindo, pare e reporte.
   - `BEHIND` ou `DIRTY`: confirme numa segunda leitura, porque um merge em andamento mostra esses estados por um instante. `BEHIND` confirmado: `gh pr update-branch <n>` e leia de novo (o SHA da head mudou). `DIRTY` confirmado (conflito; o auto-merge nunca integraria): resolva com **merge** da `main-branch` na branch do PR, nunca com rebase. `git fetch origin`, `git merge origin/<main-branch>` na branch do PR, resolva o conflito, rode `check` e `test`, commit e **push normal**; leia de novo (o SHA da head mudou). Conflito que pede decisão de conteúdo (as duas versões trazem mudanças que se excluem): pare e pergunte. Por que merge: o rebase reescreve os commits já publicados e só sobe com force push, que as travas de push do projeto costumam negar; o merge só acrescenta um commit. É o que o `gh pr update-branch` faz por padrão, e o squash leva um único commit à `main-branch`, que segue linear do mesmo jeito.
3. `gh pr merge <n> --auto --squash --match-head-commit <sha>`, sozinho no comando. O `--match-head-commit` faz o GitHub recusar o merge se a head mudar depois da leitura. Com o PR já pronto, o `gh` integra direto em vez de ligar o auto-merge; o passo 4 cobre os dois casos. Saída diferente de 0: leia o stderr e pare. Título e corpo do squash vêm do PR, então revise-os antes.
4. Espere o **resultado**, não um estado intermediário: os checks são lidos pelo SHA da head (logo após um push, `gh pr checks` ainda mostra os do commit anterior, ou nenhum) e o merge acontece depois deles, de forma assíncrona. Rode em segundo plano, aguardando a notificação, este laço (Bash), que só sai num estado final:

   ```sh
   n=<n>; sha=<sha>; gate=<gate>; : "${n:?}" "${sha:?}" "${gate:?}"; deadline=$((SECONDS + 1800))
   until out=$(gh pr view "$n" --json state,autoMergeRequest --jq '"\(.state) \(.autoMergeRequest != null)"') \
     && result=$(gh api "repos/{owner}/{repo}/commits/$sha/check-runs?check_name=$gate" --jq '[.check_runs[] | select(.status == "completed")][0].conclusion // "pending"') \
     && { [ "${out%% *}" != OPEN ] || [ "${out#* }" = false ] || ! printf '%s\n' "$result" | grep -qxE 'pending|success|skipped|neutral'; }
   do [ "$SECONDS" -lt "$deadline" ] || { echo "timeout: $out $gate=$result" >&2; exit 1; }; sleep 30; done
   echo "$out $gate=$result"
   ```

   Erro de rede ou da API conta como "ainda não sei" e o laço tenta de novo; persistindo, o prazo de 30 min encerra com `timeout` e o último estado lido. `success`, `skipped` e `neutral` são as conclusões que o GitHub aceita num check obrigatório.

   - `MERGED`: vá ao passo 5.
   - `gate` com falha: o PR não integra. Diagnostique pelo log (`gh run view <run-id> --log-failed`) e, depois do push da correção, volte ao passo 2 (o SHA preso no passo 3 era o antigo). O auto-merge **continua ligado**: um re-run verde integra sozinho; para impedir, `gh pr merge <n> --disable-auto`.
   - `OPEN false` (auto-merge desligado, por exemplo por head nova ou `BEHIND`): volte ao passo 2.
   - `CLOSED` (PR fechado sem merge): pare e reporte; não reabra nem tente integrar.
   - `timeout`: reporte o último estado. Um check obrigatório além do `gate`, pendente ou falho, também segura o merge e termina aqui: nomeie-o com `gh pr checks <n>`.
5. Confirme `MERGED` (`gh pr view <n> --json state`) e só então `git switch <main-branch>`, `git pull --ff-only` e apague a branch local integrada. Este chat é o único que vê o merge, então feche a missão aqui:
   - **Issues fechadas:** liste as que o PR fecha com `gh pr view <n> --json closingIssuesReferences --jq '.closingIssuesReferences[].url'` (inclui as de outro repositório) e confira cada uma com `gh issue view <url> --json state`. O GitHub fecha as issues depois do merge, de forma assíncrona: issue ainda `OPEN`, leia de novo a cada 10 s até fechar, por no máximo 2 min; persistindo, reporte ao usuário, sem fechar à mão.
   - **Issues citadas sem fechar:** leia o corpo (`gh pr view <n> --json body`) e confira o estado de cada issue que ele cita fora daquela lista. Lista vazia, ou issue citada ainda `OPEN`, é aviso ao usuário, que decide se o PR devia tê-la fechado: nenhuma palavra de fechamento chegou a ela (em outro repositório, só `Closes owner/repo#N` fecha). Foi o caso do kit#51, que fechou só kit#50 e citava automation-template#15 apenas como link.
   - **Fato surgido no merge** (ex.: check intermitente, `BEHIND` repetido) vira issue e entra no resumo da próxima missão, não em PR novo.
   - Avise que a missão terminou e que o próximo chat pode começar.
6. Prazo esgotado ou falha, com o usuário possivelmente ausente: avise também com `PushNotification`, se a ferramenta existir.
7. Espera interrompida (notificada como parada, ou a sessão reaberta): leia primeiro o estado real (`gh pr view <n> --json state,autoMergeRequest,mergeStateStatus`), conte ao usuário e só então retome do passo adequado; nunca presuma que a espera continua.

**Limite:** tarefas em segundo plano morrem com a sessão, e nada acorda uma sessão fechada. O auto-merge segue no GitHub, mas ninguém reporta. Para retomar pelo passo 7, mande uma mensagem comum neste chat, ou `/clear` e `/mission:ship-pr <n>` como primeira mensagem do chat novo: digitado de novo num chat que já tem conversa, o comando é bloqueado pelo plugin.
