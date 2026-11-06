<!-- LTeX: language=pt-BR -->

# automation-template - Regras do projeto

Regras que valem em todo chat, compartilhadas entre Claude Code (`CLAUDE.md` importa este arquivo) e GitHub Copilot. Estado do projeto e próxima missão: [docs/PROJECT_SESSION_SUMMARY.md](../docs/PROJECT_SESSION_SUMMARY.md).

## O que é este projeto

Template [Copier](https://copier.readthedocs.io/) para projetos de automação de testes: um **núcleo** (regras, skills, revisor, CI, configuração do GitHub) que todo projeto herda, mais um **pack** por ferramenta (`ts-playwright`, `python-behave-selenium`). Fontes: `uat-automation-framework` e `playwright-qa-starter-kit`. As decisões de arquitetura estão em `docs/adr/`; a evidência do que entra, em `docs/INVENTORY.md`.

## Regras de arquitetura do template

- **O núcleo não cita stack** (ferramenta, linguagem, tipo de alvo): define contratos (`check`, `test`, `smoke`, configuração por variáveis de ambiente) que cada pack implementa via variáveis do Copier ([ADR 0003](../docs/adr/0003-stack-agnostic-core-defines-contracts.md)).
- **Pack por ferramenta, não por tipo de teste**; tipo de teste é opção dentro do pack ([ADR 0002](../docs/adr/0002-core-plus-packs-split-by-tool.md)).
- **Walking skeleton, sem abstração do domínio:** infraestrutura, convenções como pastas documentadas e um smoke; nada de `BasePage`, page objects, clientes de API ou autenticação.
- **Entra por evidência:** o que não estiver comprovado nos projetos de origem fica de fora (regra de três).
- **Separe o que é do template do que é do projeto gerado:** o projeto acrescenta arquivos próprios em vez de editar os do template, para o `copier update` não gerar conflito.

## Regra de ouro: todo teste foi visto falhando

Teste que nunca falhou não prova nada. Template não roda sozinho: ele é testado **gerando um projeto** e validando o resultado.

1. **Teste antes:** escreva o teste (do template ou do projeto gerado), rode e veja FALHAR pelo motivo esperado; implemente o mínimo para passar; refatore com tudo verde.
2. **Mutação:** se o teste já nasce verde, quebre de propósito o que ele protege e veja-o falhar com uma mensagem que aponta o problema; desfaça.

Registre no commit como o RED foi visto (comando e erro). Portões (lint, CI) seguem a mesma regra: prove com uma sonda que eles reprovam o que devem.

## Melhores práticas sempre

- Havendo mais de um caminho, recomende o indicado pelas melhores práticas e cite o princípio que o sustenta (ex.: YAGNI, fail fast, DRY).
- Antes de perguntar uma decisão ao usuário, **consulte** a documentação oficial (Copier, Git, GitHub, Claude Code), sem citar de memória; a pergunta traz as fontes e a recomendação.
- O padrão é aplicar a prática estabelecida. Investigação ou medição sob medida só quando a economia esperada supera claramente o custo; estimativa e suposição são rotuladas como tais.
- Sem atalhos por conveniência. Desvios só com justificativa explícita no commit, na documentação ou num ADR.
- Regra deste arquivo que não siga as melhores práticas deve ser substituída, não contornada.

## Ciclo de missão (uma missão por chat)

Contexto longo degrada a qualidade; cada chat cuida de **uma missão** (uma GitHub Issue) e **o estado mora no repositório, não na conversa**. O handoff nunca depende de o usuário pedir (só o merge depende).

**Início de cada chat** (automático):

1. Ler `docs/PROJECT_SESSION_SUMMARY.md`.
2. Listar issues e PRs abertos (`gh issue list`, `gh pr list`).
3. Propor a missão de maior prioridade e confirmar com o usuário. Prioridade: bloqueio → segurança → visibilidade → dívida técnica (labels `priority: P0/P1/P2`).

**Fechamento** (automático): skill `/close-mission`, a Definition of Done; o registro de sessão vai no PR da própria missão.

## Gasto de tokens (contexto)

- Regras sempre carregadas < 200 linhas; regra de uma parte do código vai para arquivo com escopo de caminho.
- Não repita o que lint/testes já impõem; regra sem exceção vira teste ou hook, não ênfase.
- Filtre saídas na origem (`grep`, `head`, `--jq`, `gh run view --log-failed`); documentação web por seção, nunca a página inteira.
- Subagente só com motivo: trabalho paralelo independente, saída volumosa ou revisor independente.
- Modelo e esforço fixos durante o chat (trocar invalida o cache).

## Espere o estado ficar pronto antes de agir

Toda leitura ou decisão após uma ação espera o **resultado** da ação, nunca um estado intermediário. Pergunte: _"isto vê o resultado, ou um estado que ainda está mudando?"_

- Checks de CI: logo após um push, os checks verdes ainda são do commit anterior; consulte pelo SHA da head atual. Check ausente é pendente.
- `mergeStateStatus` = `UNKNOWN` logo após um merge na `main`: espere sair de `UNKNOWN`.
- **"Ainda não sei" não é "sim".** Pendente, `UNKNOWN` ou resposta vazia significam _esperar_.
- Espere por condição, nunca por tempo fixo; em polling, o intervalo é só o ritmo, a saída é a condição.

## Diagnóstico de erros

Nunca "chute" soluções: **observe** (mensagem completa, log), **contextualize**, **investigue** o mesmo padrão em outros lugares, ache a **causa raiz**, **corrija** em todos os locais afetados e **valide** sem regressão. Ao reportar: erro observado, causa raiz, análise, solução proposta com justificativa e prevenção.

## Comunicação

- Conversa, regras e documentação interna em **português (Brasil)**; código, commits, issues, ADRs e README em inglês (portfólio público).
- Explicar o **porquê**, não só o quê; opiniões fundamentadas, não só concordância.

## Git e Pull Requests

- **Conventional Commits** (`feat`, `fix`, `refactor`, `test`, `docs`, `style`, `perf`, `build`, `ci`, `chore`; escopo opcional), commits atômicos.
- **Um PR aberto por vez:** a `main` exige branch atualizada, e cada merge desatualiza os outros PRs abertos. Trabalho pronto espera em commit local até a fila esvaziar.
- **Antes de abrir o PR da missão**, o subagente `reviewer` revisa o diff (salvo em arquivo no scratchpad) contra a issue; corrija os achados que procedem e registre os descartados com o porquê.
- **Merge só pelo usuário.** Squash, com os checks obrigatórios verdes no SHA da head. Nunca `--admin` para furar proteção de branch.
- Nunca commitar credenciais; `.env` fica fora do Git.

## Princípios

Explícito é melhor que implícito; simples é melhor que complexo; legibilidade conta; erros nunca passam em silêncio; diante da ambiguidade, recuse a tentação de adivinhar.
