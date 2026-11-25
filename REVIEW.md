<!-- LTeX: language=pt-BR -->

# Instruções de revisão

Verificações próprias deste repositório, lidas pelo `mission:reviewer` além da lista dele. Regras gerais ficam em `.claude/rules/core.md` e no `CLAUDE.md`, que o revisor já carrega.

## Sempre verifique

- **O núcleo não cita stack:** nada de ferramenta, linguagem ou tipo de alvo (`npm`, `pytest`, `playwright`, `BASE_URL`…) fora de um pack; o núcleo fala em contratos ([ADR 0003](docs/adr/0003-stack-agnostic-core-defines-contracts.md)).
- **O pack não traz abstração do domínio:** walking skeleton só com infraestrutura, pastas documentadas e um smoke; nada de `BasePage`, page objects, clientes de API ou autenticação.
- **O que entra tem evidência:** cada peça nova do template ou do plugin aparece em [`docs/INVENTORY.md`](docs/INVENTORY.md) ou num ADR em [`docs/adr/`](docs/adr/); sem isso, fica de fora (regra de três).
- **O plugin não cita stack nem branch fixa:** skills e agentes em `plugins/` nomeiam contratos (`check`, `test`, `smoke`, `main-branch`, `gate`, `session-summary`), nunca um comando, ferramenta, `main`/`master` ou `ci-passed`. O README do plugin pode citar um valor só como exemplo da tabela de contratos.
- **Mudança no plugin chega aos projetos:** se a mudança altera o que um projeto precisa fornecer (contrato, configuração do repositório, instalação), o README do plugin explica, com fonte.
- **Portão novo foi visto reprovando:** um job novo no CI entra no `needs` do `ci-passed`, e o registro da missão diz como ele foi visto falhando.

## Não reporte

- O que `validate-plugins` já impõe (manifesto, frontmatter, campos das skills e dos agentes).
