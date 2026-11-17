---
name: ship-pr
description: Liga o auto-merge (squash) de um PR na branch principal, preso ao SHA da head, e espera o resultado; quem decide é o ruleset. Só o usuário dispara, porque o merge é decisão humana.
disable-model-invocation: true
argument-hint: '[pr-number]'
---

<!-- LTeX: language=pt-BR -->

Integre à branch principal o PR $ARGUMENTS (sem número: o PR da branch atual, `gh pr view --json number`). Nomes em crases como `main-branch` e `gate` são **contratos**: o valor real está na tabela de contratos das regras do projeto (formato em `${CLAUDE_PLUGIN_ROOT}/README.md`). Contrato ausente da tabela: pare e pergunte, nunca adivinhe.

Quem decide se pode integrar é o **ruleset** da `main-branch` (check `gate` verde no SHA da head, branch atualizada, histórico linear). A skill não reimplementa essa decisão: liga o [auto-merge](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request), que só integra depois que todos os requisitos passam, e espera o resultado. Nunca `--admin`.

1. Se houver outro PR aberto (`gh pr list`), pare e pergunte: um PR aberto por vez.
2. Leia `gh pr view <n> --json state,headRefOid,mergeStateStatus`, uma leitura por comando.
   - `MERGED`: vá ao passo 5.
   - `UNKNOWN` (logo após um merge na `main-branch` ele ainda não foi calculado): leia de novo, no máximo 3 vezes; persistindo, pare e reporte.
   - `BEHIND` ou `DIRTY`: confirme numa segunda leitura, porque um merge em andamento mostra esses estados por um instante. `BEHIND` confirmado: `gh pr update-branch <n>` e leia de novo (o SHA da head mudou). `DIRTY` confirmado (conflito): pare; o conflito se resolve localmente, e o auto-merge nunca integraria.
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
   - `timeout`: reporte o último estado. Um check obrigatório além do `gate`, pendente ou falho, também segura o merge e termina aqui: nomeie-o com `gh pr checks <n>`.
5. Confirme `MERGED` (`gh pr view <n> --json state`) e só então `git switch <main-branch>`, `git pull --ff-only` e apague a branch local integrada.
6. Prazo esgotado ou falha, com o usuário possivelmente ausente: avise também com `PushNotification`, se a ferramenta existir.
7. Espera interrompida (notificada como parada, ou a sessão reaberta): leia primeiro o estado real (`gh pr view <n> --json state,autoMergeRequest,mergeStateStatus`), conte ao usuário e só então retome do passo adequado; nunca presuma que a espera continua.

**Limite:** tarefas em segundo plano morrem com a sessão, e nada acorda uma sessão fechada. O auto-merge segue no GitHub, mas ninguém reporta: a próxima mensagem ou chat começa pelo passo 7.
