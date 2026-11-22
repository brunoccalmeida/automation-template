---
name: close-mission
description: Definition of Done da missão do chat. Use quando a implementação estiver pronta, antes do revisor e do PR, sem esperar o usuário pedir.
model: inherit
---

<!-- LTeX: language=pt-BR -->

Feche a missão; cada item é verificado, não presumido. Nomes em crases como `check`, `test` e `main-branch` são **contratos**: o comando ou valor real está na tabela de contratos das regras do projeto (formato em `${CLAUDE_PLUGIN_ROOT}/README.md`). Contrato ausente da tabela: pare e pergunte ao usuário, nunca adivinhe.

1. **Portões verdes:** `check`, `test` e, se o projeto tiver, `smoke` passam localmente, no estado final da branch. Portão vermelho se corrige antes do revisor, nunca se pula.
2. **Issues em dia:** as resolvidas citadas no PR (`Closes #N`); pendências descobertas viram issues novas com label `priority: P0/P1/P2`, seguindo os campos de `.github/ISSUE_TEMPLATE/`, se existir.
3. **Resumo de sessão** (`session-summary`), na branch da missão: só **estado**. Tabela com uma ideia por linha (a fila de PRs como ficará após o merge) e a próxima missão recomendada pela prioridade das regras, com links para issues e ADRs. Cite issues, não o número do PR (ele ainda não existe). Decisão duradoura vira regra ou ADR; armadilha que vai se repetir ganha uma linha no resumo. O histórico vai no PR (passo 6).
4. **README e documentação** acompanham o que mudou para quem usa o projeto.
5. **Revisor** (`mission:reviewer`): salve no scratchpad o texto da issue (`gh issue view <n>`) e, num segundo arquivo, as mensagens de commit da branch (`git log <main-branch>..HEAD`) seguidas do resumo e do diff completo (`git diff --stat <main-branch>...HEAD` e `git diff <main-branch>...HEAD`); passe os dois caminhos. As mensagens vão junto porque o revisor confere nelas o registro do RED e não roda `git`. Corrija os achados que procedem e rode os portões de novo.
6. **PR com o registro da missão:** commit, push e `gh pr create` com `Closes #N`. O corpo do PR **é** o registro: decisões, fontes consultadas, como o RED foi visto (ou a mutação) e os achados do revisor em três listas, cada uma com "nenhum" quando vazia, porque elas são a matéria-prima do gabarito do revisor:
   - **corrigidos:** achados que procediam;
   - **falsos positivos:** achados descartados, cada um com o porquê;
   - **falsos negativos:** defeito que o revisor deixou passar e que a lista dele ou o `REVIEW.md` cobria, achado depois dele nesta missão, ou vindo de uma missão anterior e corrigido por esta ou aberto como issue nova (passo 2). Quando vem de uma missão anterior, a issue que o corrige (ou o PR, sem issue) leva a label `reviewer-miss` e cita o PR da missão que entregou o defeito.

   Se existir `.github/pull_request_template.md`, siga as seções dele (`gh pr create --body` ignora o modelo). O squash grava o corpo na `main-branch` só se o repositório usar a descrição do PR como mensagem: confira que `gh api repos/{owner}/{repo} --jq .squash_merge_commit_message` imprime `PR_BODY` e, se não, avise o usuário antes do merge. Peça ao usuário `/clear` e, como **primeira mensagem do chat novo**, `/mission:ship-pr <n>`: a skill não precisa desta conversa (o PR e o resumo guardam tudo), e cada chamada da espera pelo merge reenviaria o contexto inteiro. O plugin bloqueia `ship-pr` num chat que já tem conversa.
7. **Com o PR integrado:** confirme as issues fechadas (`gh issue view <n> --json state`) e a `main-branch` local atualizada; avise que a missão terminou e que o próximo chat pode começar. Fato surgido no merge (ex.: check intermitente) vira issue e entra no resumo da próxima missão, não em PR novo.
