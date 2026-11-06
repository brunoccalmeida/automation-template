<!-- LTeX: language=pt-BR -->

# Inventário dos projetos de origem

Levantamento da Missão 0 (06/11/2026): o que existe em [uat-automation-framework](https://github.com/brunoccalmeida/uat-automation-framework) (**UAT**, Python/Behave/Selenium, 130+ PRs) e em [playwright-qa-starter-kit](https://github.com/brunoccalmeida/playwright-qa-starter-kit) (**kit**, Playwright/TS, Missão 3 em andamento), qual lado faz melhor e para onde cada peça vai. É a evidência por trás de cada decisão de "entra ou não entra" no template ([ADR 0002](adr/0002-core-plus-packs-split-by-tool.md)).

## Como ler

**Categoria** (de onde a peça vai morar):

- **N — contrato do núcleo:** a mesma intenção nos dois projetos e independente de stack. Vai para o núcleo, sem citar ferramenta ([ADR 0003](adr/0003-stack-agnostic-core-defines-contracts.md)).
- **P — implementação do pack:** mesma forma, conteúdo da stack. Vai para o pack, como walking skeleton.
- **A — específico do app:** depende do Sauce Demo ou do Restful Booker. Fica de fora.

**Melhor:** qual lado serve de base (UAT, kit, os dois somados, ou nenhum = lacuna). **Fase:** onde entra no [plano](PROJECT_SESSION_SUMMARY.md#plano-de-missões).

Postura: com só dois projetos, **na dúvida, fica de fora** (regra de três). Sobe para o template quando um terceiro projeto repetir o padrão.

## 1. Regras sempre carregadas (`.github/copilot-instructions.md`, importado pelo `CLAUDE.md`)

| Seção | UAT | kit | Melhor | Cat. | Fase |
| --- | --- | --- | --- | --- | --- |
| `CLAUDE.md` com `@import` | Idêntico (resumo em `docs/ai-workflow/`) | Idêntico (resumo em `docs/`) | Empate | N | 2a |
| Regra de ouro (RED) | "TDD" + duplo ciclo Behave/pytest | "Todo teste foi visto falhando", com dois caminhos: teste antes do código de suporte, ou mutação; vale também para portões | **kit**: agnóstica e serve a SUT de terceiros | N (o duplo ciclo vai para o pack Python: P) | 2a / 6 |
| Melhores práticas sempre | Tem a regra extra "investigação sob medida só quando a economia supera o custo; estimativa é rotulada" | Versão curta | **Somados** | N | 2a |
| Ciclo de missão | Igual, e explicita que o handoff nunca depende do usuário | Igual | Somados; os passos de "início do chat" saem da regra para a skill `start-mission` e o hook `SessionStart` | N | 2b / 3 |
| Gasto de tokens | Mais completo: docs web por seção, modelo fixo no chat, medir antes/depois, `AGENT_TOKEN_SPEND.md` | Resumo | **UAT** | N | 2a |
| Seção de testes da stack | Duplo ciclo, hierarquia unit/integração/E2E | Hierarquia API/E2E, isolamento, localizadores, `test.fail` | Cada um na sua stack | P (isolamento e bug conhecido viram política: N) | 2a / 5 / 6 |
| Espere o estado final | Princípio + tabela; tem a regra extra "estado final igual ao inicial: altere o inicial antes de agir" | Princípio + tabela | **UAT** no princípio; linhas da tabela por stack | N (linhas de CI/GitHub) + P (linhas da ferramenta) | 2a |
| Diagnóstico de erros | Com exemplo concreto | Com as ferramentas do Playwright | Empate | N + exemplos no pack | 2a |
| Comunicação | "Sempre pt-BR; código em inglês" | Mais preciso: commits e README em inglês | **kit** | N | 2a |
| Dependências | Poetry; **duas fontes de vulnerabilidade** (Dependabot + `pip-audit`) | npm exato; `overrides` em vez de `audit fix --force`; conferir *peer dependencies* | Somados: princípios no núcleo (lock commitado, versão exata, major = decisão humana, duas fontes), comandos no pack | N + P | 2a |
| Git e PR | Explica **por que** um PR aberto por vez (branch atualizada exigida) | Mais curto | **UAT** | N | 2a |
| Princípios (Zen) | Idêntico | Idêntico | Empate | N | 2a |
| Regras por caminho (`.claude/rules/` = `.github/instructions/`) | Sim: Python, Selenium, workflows, Poetry | **Não tem** | **UAT** | Mecanismo N; conteúdo P, exceto `workflows.md` (N, menos a linha do `pip-audit`) | 2a |

## 2. Skills e agente

| Peça | UAT | kit | Melhor | Cat. | Fase |
| --- | --- | --- | --- | --- | --- |
| `close-mission` | Sem "Portões verdes"; tem "fato surgido no merge vira issue, não PR novo"; passo de traduções do README (A) | Tem o passo 1 "Portões verdes" e o `git diff main...HEAD` explícito | **kit** + a frase final do UAT | N (`{{ cmd_check }}`) | 2b |
| `ship-pr` | `merge_when_green.py` (187 linhas + testes, depende de Poetry) | **Auto-merge nativo** com `--match-head-commit` e laço de espera em shell; sem script | **kit**: menos código, nenhuma dependência de stack | N | 2b |
| `reviewer` | 5 itens | 6 itens: **+ isolamento no ambiente compartilhado** | **kit** | N, com a linha "ignore o que X já impõe" como ponto de extensão do pack | 2b |
| `start-mission` | Não tem | Não tem | Lacuna | N | 2b |

## 3. Configuração e testes do próprio harness

| Peça | UAT | kit | Melhor | Cat. | Fase |
| --- | --- | --- | --- | --- | --- |
| `test_agent_rules.py` | Limite de 200 linhas, cópias Claude/Copilot iguais, metadados das skills, revisor só leitura | Não tem: nada impede o kit de passar das 200 linhas | **UAT** | N (os testes de LTeX/cSpell/pyright são P ou saem) | 2b |
| `test_doc_links.py` | Barra link quebrado em `.md` | Não tem | **UAT** | N | 2b |
| Hook `PreToolUse` que compacta a saída de testes | `filter_test_output.py` (`pytest -q`, `behave -f progress2`) | Não tem | **UAT** | P (o runner muda por stack; o kit pode usar `--reporter=line`) | 5 / 6 |
| Plugin LSP | `pyright-lsp` | Não tem | **UAT** | P | 5 / 6 |
| Permissões `allow`/`deny` | Não tem | Não tem | Lacuna: "nunca `--admin`" ainda é só texto | N | 3 |
| Hook `SessionStart`, hook de segredos | Não tem | Não tem | Lacuna | N | 3 |
| `.vscode/` versionado | Sim (cSpell `en,pt_BR,es`, extensões) | Não versionado | UAT | P (extensões por stack); fora até haver evidência de valor no núcleo | 5 / 6 |

## 4. Documentação

| Peça | UAT | kit | Melhor | Cat. | Fase |
| --- | --- | --- | --- | --- | --- |
| `PROJECT_SESSION_SUMMARY.md` | 137 linhas; a tabela de estado **virou histórico**: células com mais de 1.200 caracteres | Curto, com tabela de estado e **plano de missões** | **kit** na forma; o problema do UAT justifica os ADRs (decisão duradoura sai do resumo) | N (modelo) | 2a |
| ADRs | Não tem | Não tem | Lacuna (este repositório já usa: `docs/adr/`) | N (modelo) | 2a |
| `KNOWN_ISSUES.md` | Não tem | `KI-n` com esperado/observado/impacto/teste, e o aviso "confirme que o teste falha pelo motivo do bug" | **kit** | N (modelo) | 2a |
| Relatório de spike | Não tem | Achados do spike dentro do resumo | kit (conteúdo); falta modelo próprio | N (modelo) | 2a |
| Política de testes instáveis (flaky) | Improvisada no #129 (instrumentar, sem retry, citando Fowler) | `retries: 2` no CI, flaky visível no relatório | **Nenhum** tem política escrita, e os dois divergem (ver §8) | N | 2a |
| `docs/ai-workflow/` (índice em inglês + `AGENT_TOKEN_SPEND.md`) | Sim | Não | **UAT** | N | 2a |
| README em 3 idiomas + validador de métricas (452 linhas) | Sim | Não | — | A/opcional: fora (YAGNI) | — |

## 5. CI e GitHub

| Peça | UAT | kit | Melhor | Cat. | Fase |
| --- | --- | --- | --- | --- | --- |
| Gate `ci-passed` (único check obrigatório, `always()`, lista de permissão) | `check_needs.py` + `test_ci_gate.py` (Python) | Inline em `yq`/`jq`, e **confere que o gate depende de todo job** | **kit**: sem dependência de stack | N | 1 / 2b |
| Actions fixadas por SHA | Sim, **cobrado** por `test_workflow_pinning.py` | Sim, mas nada cobra | **UAT** (cobrança); avaliar se o zizmor substitui o teste | N | 3 |
| Endurecimento do workflow | `permissions: contents: read`; **sem** `concurrency` no nível do workflow (só no job de deploy do Pages), `persist-credentials: false` e `timeout-minutes` | Os quatro | **kit** | N | 1 |
| Dependabot | Agrupado; ecossistema `docker-compose` | Agrupado + **`cooldown` de 7 dias** + `versioning-strategy` | **kit** (bloco `github-actions` no núcleo, bloco do ecossistema no pack) | N + P | 4 / 5 / 6 |
| Sentinela de `ignore` do Dependabot | Não tem | `check-dependency-ignores.ts` reprova o `check` quando o ignore caduca | **kit** | Padrão N, implementação P | 5 |
| Segunda fonte de vulnerabilidades, diária | `pip-audit --strict` (PR + diário) | **Não tem** | **UAT** | Padrão N, implementação P | 5 / 6 |
| Hooks locais antes do commit | `pre-commit` (rodado também no CI) | Não tem | **UAT**, com ressalva: `rev: v5.0.0` por tag (contradiz a regra de SHA) e o repositório `pre-commit-hooks` repetido | P | 6 |
| Checagem de encoding (UTF-8, sem NUL) | `check_text_encoding.py` (o `.gitignore` em UTF-16, gerado pelo PowerShell, não casava nada, #26) | Não tem | **UAT**; o problema é do Windows, não da stack | N | 3 |
| Ruleset | "Protect master" (`ci-passed` + `pip-audit`) | "Protect main" (`ci-passed`) | Empate; o núcleo usa `main` | N | Este repo: 1 · projeto gerado: 4 |
| Labels `priority: P0/P1/P2` | Iguais | Iguais | Empate | N | Este repo: 0 · projeto gerado: 4 |
| Config do repositório (só squash, auto-merge, título/corpo do PR) | Auto-merge desligado | Configurado | kit | N | Este repo: 0 · projeto gerado: 4 |
| Modelos de issue e PR | Não tem | Não tem | Lacuna | N | 4 |
| `.gitattributes` | `* text=auto` (rejeitou `eol=lf`) | `* text=auto eol=lf` (Prettier exige LF) | Divergem (ver §8) | N | 2a |
| Relatório publicado | Allure no Pages + Codecov via OIDC | Planejado (Missão 6 do kit) | UAT | P | 5 / 6 |
| Selenium Grid em `compose.yaml` por digest, mesma fonte local e CI | Sim (*dev/prod parity*) | — | UAT | P | 6 |

## 6. Código de teste

### Infraestrutura (vai para o pack)

| Peça | UAT | kit | Melhor | Cat. |
| --- | --- | --- | --- | --- |
| Configuração | `config.yaml` commitado com URL e senha; hierarquia CLI > env > YAML feita à mão (`config_resolver.py`, 172 linhas); sem validação: chave ausente estoura `KeyError` no uso | Variáveis de ambiente validadas com zod na inicialização (*fail fast*, mensagem cita a variável); `.env.example`; o shell vence o `.env` | **kit** (Twelve-Factor, fator III) | Contrato N, implementação P |
| Config do runner | — | `forbidOnly` no CI; trace desligado no CI porque gravaria a senha em texto puro (decisão documentada) | **kit** | P |
| Evidência de falha | Screenshot + URL no Allure; artefatos de integração no CI (#129) | `expectJson` falha com URL + corpo da resposta | Os dois; o contrato é "a falha traz evidência para diagnosticar sem reproduzir" | Contrato N, implementação P |
| Smoke | `smoke.feature` com `@smoke`, mas acoplado ao Sauce Demo | Não tem | Lacuna nos dois: smoke = "SUT alcançável" | Contrato N, implementação P |

### Convenções (só a forma vai para o pack)

| Peça | UAT | kit | Melhor | Cat. |
| --- | --- | --- | --- | --- |
| Pastas | `core/`, `pages/`, `features/steps/`, `tests/{unit,integration,helpers}` | `src/{api,config,data}`, `tests/{api}`, `tests/fixtures.ts` | Cada um na sua stack | P (pastas vazias com README) |
| Bug conhecido do app | Cenário **afirma o defeito** (`problem_user` vê o produto errado). Legítimo no Sauce Demo, onde o defeito é intencional, mas generalizado transforma bug em comportamento esperado | `test.fail()` **afirma o comportamento correto** e aponta para `KNOWN_ISSUES.md`; avisa quando o bug é corrigido | **kit** | Política N, marcação P |
| Isolamento de dados | Usuários fixos pré-cadastrados (o Sauce Demo não guarda estado entre sessões) | Fixture cria dados únicos por teste (ambiente compartilhado) | **kit** como regra geral | Política N |

### Abstrações do domínio (ficam de fora)

`BasePage` (249 linhas), page objects, steps e features do UAT; clientes de API, schemas zod, `factories.ts` e specs do kit. Dependem do app (**A**). As **ideias** reaproveitáveis delas já estão nas regras, não no código: esperar a página de destino após navegar em SPA, remover o erro antigo antes de reenviar um formulário, esperar o elemento parar de se mover (`wait_until_stable`, o *actionability check* "Stable" do Playwright).

### Qualidade dos testes (vai para o backlog da Fase 8)

- **UAT, testes que repetem o código.** Exemplo: `assert LoginPage.USERNAME_INPUT == (By.ID, "user-name")` em `tests/test_login_page.py`. Teste assim quebra em toda refatoração e não pega bug nenhum: é o *change-detector test* (Google Testing Blog, "Change-Detector Tests Considered Harmful"). Os unitários de page object com `Mock` conferem que `type()` foi chamado com o localizador, ou seja, testam a implementação, enquanto os 96 testes de integração com navegador real já cobrem o contrato com o DOM. Os 656 unitários estão inflados por esse padrão. Candidatos à remoção, avaliados um a um na Missão 8b.
- **UAT, configuração.** URL e senha no `config.yaml` funcionam para um demo público, mas o padrão não serve para um cliente real: migrar para variáveis de ambiente validadas, como no kit.
- **kit, segurança.** Sem segunda fonte de vulnerabilidades (`npm audit` ou equivalente) e sem portão local antes do commit.
- **kit, harness defasado.** Sem regras por caminho, sem testes do harness, sem hook de saída, sem LSP (§1 e §3; a adoção do template na Missão 8a resolve).

## 7. Lacunas nos dois projetos

Nenhum dos dois tem, e o template passa a ter:

| Lacuna | Fase |
| --- | --- |
| Permissões `allow`/`deny` no `.claude/settings.json` (`--admin`, `push --force`, push na `main`) | 3 |
| Hook `SessionStart` (resumo + issues abertas) e hook que bloqueia leitura/edição de `.env` | 3 |
| gitleaks e zizmor no CI; Scorecard | 3 / 7 |
| Modelos de issue (missão com critérios de aceite) e de PR | 4 |
| Skills `start-mission` e `/new-project` (labels, ruleset, issues do plano) | 2b / 4 |
| ADRs, política de flaky, modelo de relatório de spike | 2a |
| CI do próprio template, que gera um projeto por pack e o valida | 1 |

## 8. Decisões que ficam para a missão da fase

- **Fim de linha (2a).** O UAT rejeitou `eol=lf` porque força LF no disco do Windows; o kit precisa dele porque o Prettier exige LF. Este repositório usa `eol=lf` (os editores atuais lidam bem com LF no Windows). Confirmar com a documentação do Git antes de pôr no núcleo.
- **Retries no CI (2a, política de flaky).** O kit usa `retries: 2` e confia no relatório para mostrar o flaky; o UAT recusou retry no #129 citando Fowler ("rodar de novo até passar torna o teste inútil"). A política precisa decidir com fontes, e o que o núcleo exige é que a instabilidade fique **visível e rastreada** (issue), seja qual for o mecanismo.
- **O harness deste repositório (2a/2b).** Para trabalhar por missões desde já, este repositório tem uma cópia mínima do harness do kit (`CLAUDE.md`, regras, `close-mission`, `reviewer`). É a terceira cópia à mão, o próprio problema que o template resolve. A Fase 2 deve fazer este repositório usar o núcleo (*dogfooding*): gerado por ele, ou com um teste que compara as duas versões.
