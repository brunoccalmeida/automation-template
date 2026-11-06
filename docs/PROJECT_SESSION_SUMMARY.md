<!-- LTeX: language=pt-BR -->

# Resumo das sessões

Estado do projeto entre chats. Lido no início de cada missão (ver `.github/copilot-instructions.md`). Histórico detalhado mora no Git (PRs, commits, issues); decisões duradouras, em `docs/adr/`. Este arquivo guarda só o **estado** e a **próxima missão**.

## Estado atual

| Item | Estado |
| --- | --- |
| Missão atual | 0 — Fundação (#1), concluída com o merge deste PR |
| Próxima missão | 1 — Walking skeleton do template (#2) |
| PRs abertos | nenhum após o merge |
| Portões | nenhum ainda: o CI do template nasce na Missão 1. Sem ruleset na `main` até lá |
| Decisões | [ADR 0001](adr/0001-use-copier.md) Copier · [ADR 0002](adr/0002-core-plus-packs-split-by-tool.md) núcleo + packs por ferramenta · [ADR 0003](adr/0003-stack-agnostic-core-defines-contracts.md) núcleo agnóstico com contratos |
| Evidência | [INVENTORY.md](INVENTORY.md): cada peça dos dois projetos de origem classificada (núcleo / pack / app), com o melhor lado e a fase |

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

**Pendente com o usuário:** abrir uma issue pública em cada repositório de origem apontando para as Missões 8a/8b (só com confirmação explícita).

## Próxima missão recomendada

**Missão 1 (#2), walking skeleton do template.** Instalar o Copier (`uv tool install copier` ou `pipx`; conferir a versão estável no PyPI), criar o `copier.yml` mínimo com uma pergunta e um arquivo renderizado, e um workflow que roda `copier copy` com respostas fixas e valida o projeto gerado. Ver o teste falhar antes (ex.: arquivo esperado ausente). Depois do CI verde: gate `ci-passed`, ruleset "Protect main" e skill `ship-pr`, como na Missão 1 do kit.
