<!-- LTeX: language=pt-BR -->

# Resumo das sessões

Estado do projeto entre chats. Lido no início de cada missão (ver `.github/copilot-instructions.md`). Histórico detalhado mora no Git: o registro de cada missão (decisões, fontes, como o RED foi visto, achados) vai no **corpo do PR**, que o squash grava na `main`; decisões duradouras, em `docs/adr/`. Este arquivo guarda só o **estado** e a **próxima missão** ([ADR 0004](adr/0004-partial-resumption-with-a-plugin.md), item 8). A seção "Missão 0" abaixo é anterior a essa regra e fica como histórico.

## Estado atual

| Item | Estado |
| --- | --- |
| Situação | **Retomada parcial: plugin** (17/11/2026, [ADR 0004](adr/0004-partial-resumption-with-a-plugin.md)). O Copier continua pausado ([Pausa](#pausa)). Missões 0 (#1), A (#14), B (#15, piloto no kit) e A.1 (#19, #20, #21, correções do piloto) concluídas |
| Entregue | Marketplace `brunoccalmeida-plugins` com o plugin [`mission`](../plugins/mission/README.md): `/mission:close-mission`, `/mission:ship-pr`, `mission:reviewer`. Contrato dos projetos (tabela de contratos, configuração do repositório, `REVIEW.md`) no README do plugin |
| Próxima missão | C1 — plugin no playwright-nextjs-e2e-ci (#22) |
| Fila | C2 — plugin no UAT (#23) · D — este repositório usa o próprio plugin (#17) · Copier: #2 a #11, pausados |
| Pendência no kit | Atualizar o plugin e apagar a regra local de contorno do `DIRTY` (issue aberta no kit após o merge da A.1) |
| PRs abertos | nenhum após o merge |
| Portões | CI `validate-plugins`: valida o marketplace e cada plugin; reprova qualquer erro ou *warning*, menos o `version` omitido de propósito. **Ainda não é obrigatório**: a `main` não tem ruleset (previsto na Missão 1, #2) |
| Ferramenta de CI | Claude Code CLI 2.1.326 fixado com lockfile em `.github/tools/claude-cli/`; subir de versão exige aprovar de novo o `postinstall` (`allowScripts` preso à versão) |
| Decisões | [ADR 0001](adr/0001-use-copier.md) Copier · [ADR 0002](adr/0002-core-plus-packs-split-by-tool.md) núcleo + packs por ferramenta · [ADR 0003](adr/0003-stack-agnostic-core-defines-contracts.md) núcleo agnóstico com contratos · [ADR 0004](adr/0004-partial-resumption-with-a-plugin.md) retomada parcial com plugin |
| Evidência | [INVENTORY.md](INVENTORY.md): peças dos projetos de origem classificadas (núcleo / pack / app); nextjs como terceira fonte e a comparação das quatro versões das peças do plugin |
| Armadilhas | Este repositório ainda roda as cópias à mão de `close-mission` e `reviewer` em `.claude/` até a Missão D. O UAT grava o squash com `COMMIT_MESSAGES`, então o registro no corpo do PR não chega ao Git lá (Missão C2). PR de outro repositório só fecha issue daqui com `Closes brunoccalmeida/automation-template#N` (a #15 ficou aberta por isso). Para rodar o portão no Windows, passe ao script o caminho absoluto de `.github\tools\claude-cli\node_modules\.bin\claude.cmd` |

## Plano de missões

| Fase | # | Issue | Missão | Entrega |
| --- | --- | --- | --- | --- |
| 0. Fundação | 0 | #1 | Fundação | Repositório, 3 ADRs, inventário, harness mínimo deste repositório, issues |
| 1. Esqueleto do template | 1 | #2 | Walking skeleton | `copier.yml` mínimo, um arquivo gerado, CI que roda `copier copy` e valida o resultado; gate `ci-passed`, ruleset, `ship-pr`. Primeiro teste visto falhando |
| 2. Núcleo agnóstico | 2a | #3 | Regras e docs | Regras do núcleo, `CLAUDE.md`, regras por caminho; modelos: resumo de sessão, KNOWN_ISSUES, ADR, política de flaky, relatório de spike |
| | 2b | #4 | Skills, revisor e testes do harness | `start-mission`, `close-mission`, `ship-pr` (auto-merge nativo), `reviewer` com pontos de extensão; comandos como variáveis do Copier; testes: limite de linhas, cópias Claude/Copilot iguais, links, **nenhum termo de stack no núcleo** |
| 3. Fazer cumprir | 3 | #5 | Permissões, hooks e segurança | `allow`/`deny`, hook `SessionStart`, hook de segredos, checagem de encoding, gitleaks, zizmor |
| 4. GitHub | 4 | #6 | Bootstrap do GitHub | Labels, ruleset, config de merge, modelos de issue/PR, Dependabot do núcleo, skill `/new-project` |
| 5. Pack TS | 5 | #7 | Pack `ts-playwright` | Walking skeleton com opções e2e/api, extraído do kit |
| 6. Pack Python | 6 | #8 | Pack `python-behave-selenium` | Walking skeleton extraído do UAT; prova que o núcleo é agnóstico |
| 7. Release | 7 | #9 | v1.0 | Tag, README de portfólio com diagrama e "como usar", Scorecard |
| 8. Backlog | 8a | #10 | Adotar no kit | `copier` no playwright-qa-starter-kit + correções que o template não cobre |
| | 8b | #11 | Adotar no UAT | O mesmo no uat-automation-framework; prova o `copier update` em projeto real |
| Plugin | A | #14 | Plugin do harness | Marketplace + plugin `mission`, contrato dos projetos, portão de validação no CI (concluída) |
| | B | #15 | Piloto no kit | Tabela de contratos, `REVIEW.md`, plugin no escopo do projeto, uma missão real de ponta a ponta (concluída, kit#51) |
| | A.1 | #19, #20, #21 | Correções do piloto | `DIRTY` por merge no `ship-pr`; instalação sem CLI no PATH e `autoUpdate` explícito no README (concluída) |
| | C1 | #22 | nextjs | O mesmo no playwright-nextjs-e2e-ci (substitui metade da #16) |
| | C2 | #23 | UAT | O mesmo no UAT; squash com a descrição do PR, script de espera, `pip-audit` (substitui metade da #16) |
| | D | #17 | Dogfooding | Este repositório usa o próprio plugin |

A Missão 2b (#4) encolhe: as skills e o revisor já vivem no plugin; o Copier passa a renderizar só a tabela de contratos e o registro do marketplace ([ADR 0004](adr/0004-partial-resumption-with-a-plugin.md), consequências).

Princípio: cada peça entra na missão que a usa (YAGNI), e cada fase já nasce testada pelo CI da Fase 1.

## Missão 0 (#1)

**Decisões** (conversas de 06/11/2026, registradas nos ADRs): Copier pelo `copier update` (3-way merge), não *template repository* (cópia sem vínculo) nem plugin (só cobre o que o Claude Code lê); um repositório com núcleo + packs divididos por **ferramenta**, não por tipo de teste; núcleo agnóstico que define contratos (`check`, `test`, `smoke`, configuração por ambiente) ligados aos comandos por variáveis do Copier; esqueleto de pack como walking skeleton, sem abstração do domínio. README, ADRs, issues e commits em inglês; regras e docs internos em pt-BR.

**Fontes consultadas:** Copier, [Updating a project](https://copier.readthedocs.io/en/stable/updating/) (regenera a versão antiga, calcula o diff do projeto e o reaplica sobre a nova; exige tags no template e projeto limpo; nunca editar `.copier-answers.yml` à mão); Nygard, *Documenting Architecture Decisions*; Twelve-Factor App, fator III.

**RED:** não se aplica nesta missão, que só entrega documentação; não há portão para provar. O primeiro teste do template, visto falhando, é critério de aceite da Missão 1.

**Achados do inventário** (detalhes em [INVENTORY.md](INVENTORY.md)):

- O kit é a melhor base para `ship-pr`, `close-mission`, `reviewer`, gate `ci-passed` sem script, endurecimento dos workflows, Dependabot com `cooldown` e configuração validada por ambiente; o UAT, para regras por caminho, testes do harness, hook de saída, cobrança de SHA, segunda fonte de vulnerabilidades e checagem de encoding.
- Código de teste do UAT: testes que repetem o código (localizador igual a ele mesmo) e unitários de page object que só conferem chamadas de mock; vão para a Missão 8b.
- Nenhum dos dois tem política de flaky, e eles divergem (retry no kit, sem retry no UAT); `.gitattributes` também diverge. Decidir na Missão 2a.
- Este repositório tem a terceira cópia à mão do harness, só para trabalhar por missões até a Fase 2, que deve fazê-lo usar o próprio núcleo.

**Backlog nos repositórios de origem** (aberto com a confirmação do usuário): playwright-qa-starter-kit#15 e uat-automation-framework#134, ligados às Missões 8a (#10) e 8b (#11).

## Pausa

**Decisão (06/11/2026):** o template fica pausado até o primeiro trabalho pago de automação.

**Por quê:**

- **Regra de três.** O template é extraído de dois projetos, e a regra "entra por evidência" pede três. O inventário já mostra divergências sem desempate (política de flaky, `.gitattributes`); o primeiro projeto de cliente é o terceiro caso que separa o que é comum de verdade do que é coincidência. Extrair antes é abstração prematura.
- **Prioridade.** Portfólio e trabalho pago vêm antes: o cliente compra testes rodando no CI dele, não o fluxo de trabalho. O custo de não ter o template (portar melhorias à mão entre os repositórios) é baixo e linear; o template ainda tem 10 missões.

**Consequências:**

- Inverte a decisão anterior de só corrigir os projetos de origem depois do template: até a retomada, as melhorias entram neles à mão.
- playwright-qa-starter-kit#15 e uat-automation-framework#134 ficam com a label `blocked`.
- Nada se perde: ADRs, [INVENTORY.md](INVENTORY.md) e as issues #2 a #11 continuam válidos. Na retomada, revisar o inventário com o que o projeto do cliente mostrou ser repetível.

**Gatilho para retomar:** o primeiro trabalho pago de automação concluído (ou um terceiro projeto que precise do mesmo harness).

**17/11/2026:** o segundo gatilho disparou (playwright-nextjs-e2e-ci). Retomado só o plugin ([ADR 0004](adr/0004-partial-resumption-with-a-plugin.md)); o Copier segue pausado pelos mesmos motivos.

## Próxima missão recomendada

**Missão C1 (#22), plugin no playwright-nextjs-e2e-ci.** Seguir o [README do plugin](../plugins/mission/README.md), já com as correções do piloto: tabela de contratos nas regras, `REVIEW.md` (app congelado, banco novo por job), marketplace e plugin no escopo do projeto com `"autoUpdate": false` declarado, cópias locais removidas, uma missão real fechada com `/mission:close-mission` e integrada com `/mission:ship-pr`. O PR de lá fecha a issue daqui com `Closes brunoccalmeida/automation-template#22`. Depois, C2 (#23) no UAT.
