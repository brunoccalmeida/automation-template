<!-- LTeX: language=pt-BR -->

# automation-template - Regras do projeto

Regras só deste repositório. As que valem em todo projeto ficam em [`.claude/rules/core.md`](.claude/rules/core.md), que vem do template e não se edita aqui.

## Contratos

Valores que o núcleo e o plugin [`mission`](plugins/mission/README.md) usam neste repositório. O artefato publicado hoje é o próprio plugin, então `check` é a validação dele e `test`, os testes dos seus hooks, até a Missão 1 (#2) trazer os testes do template.

| Contrato | Valor |
| --- | --- |
| `check` | `npm ci --prefix .github/tools/claude-cli` uma vez, depois `python3 .github/scripts/validate_plugins.py` (no Windows, passe ao script o caminho absoluto de `.github\tools\claude-cli\node_modules\.bin\claude.cmd`) |
| `test` | `python3 -m unittest discover -s tests` (testes dos hooks do plugin; precisam de `sh` e `git` no `PATH` e falham sem eles; no Windows, `python` ou `py -3`, com o Git Bash no `PATH`) |
| `smoke` | Nenhum: ainda não há template para gerar um projeto (Missão 1, #2) |
| `main-branch` | `main` |
| `gate` | `ci-passed` |
| `session-summary` | `docs/PROJECT_SESSION_SUMMARY.md` |

## Exceções ao núcleo

- **"Everything written to the repository is in English":** regras e documentos internos (`CLAUDE.md`, `REVIEW.md`, `docs/PROJECT_SESSION_SUMMARY.md`, `docs/INVENTORY.md`) continuam em português (Brasil) até a #46 traduzi-los. Por quê: traduzir é uma missão própria; misturar idiomas no mesmo documento seria pior que esperar.

## Regras de arquitetura do template

Este repositório é um template [Copier](https://copier.readthedocs.io/) para projetos de automação de testes: um **núcleo** que todo projeto herda e um **pack** por ferramenta (`ts-playwright`, `python-behave-selenium`). As decisões estão em `docs/adr/`; a evidência do que entra, em `docs/INVENTORY.md`.

- **O núcleo não cita stack** (ferramenta, linguagem, tipo de alvo): define contratos que cada pack implementa via variáveis do Copier ([ADR 0003](docs/adr/0003-stack-agnostic-core-defines-contracts.md)).
- **Pack por ferramenta, não por tipo de teste**; tipo de teste é opção dentro do pack ([ADR 0002](docs/adr/0002-core-plus-packs-split-by-tool.md)).
- **Walking skeleton, sem abstração do domínio:** infraestrutura, convenções como pastas documentadas e um smoke; nada de `BasePage`, page objects, clientes de API ou autenticação.
- **Entra por evidência:** o que não estiver comprovado nos projetos de origem fica de fora (regra de três).
- **Separe o que é do template do que é do projeto gerado:** o projeto acrescenta arquivos próprios em vez de editar os do template, para o `copier update` não gerar conflito.
- **O template se testa gerando um projeto:** ele não roda sozinho; o teste gera um projeto e valida o resultado.

## Ruleset como código

[`.github/rulesets/protect-main.json`](.github/rulesets/protect-main.json) descreve o ruleset ativo (id 27584439), mas editar o arquivo não muda o GitHub. Mudou o arquivo: aplique com `gh api -X PUT repos/{owner}/{repo}/rulesets/27584439 --input .github/rulesets/protect-main.json` e confira com `gh api repos/{owner}/{repo}/rulesets/27584439`; mudou na interface: traga a mudança para o arquivo. A checagem automática de divergência fica para a Missão 4 (#6).

## Mudança no próprio plugin

A missão é fechada pela versão publicada (instalada do GitHub, `autoUpdate: false`), não pela da branch. Para experimentar a da branch, abra uma sessão com `claude --plugin-dir ./plugins/mission`, que sobrepõe a instalada só nessa sessão ([Plugin loading reference](https://code.claude.com/docs/en/plugins/loading.md#name-conflicts)). Depois do merge, `claude plugin update mission@brunoccalmeida-plugins`.
