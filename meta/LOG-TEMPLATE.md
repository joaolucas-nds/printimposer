# LOG-TEMPLATE.md — Formato do Log do Dia

> **Referência fixa.** Este arquivo é o MOLDE — não é substituído.
> O log entra ao bater um gatilho de evento — cortar versão, registrar decisão ou erro grave, virar o dia —, e não «no fim», que numa conversa longa nunca chega. O assistente entrega um arquivo novo `logs/AAAA-MM-DD.md` preenchido neste formato.
> Os logs vivem em `logs/` no Git (NÃO no Projeto) e são lidos só sob demanda — quando você precisar recuperar o detalhe de um dia antigo.

---

# Log — AAAA-MM-DD

## Objetivo do dia
[O que se pretendia fazer ao começar.]

## Feito
- [Mudanças concretas: arquivos tocados, funções criadas, bugs resolvidos.]

## Decisões
- [Decisões tomadas → quais viraram DEC-N em DECISIONS.md.]

## Bugs
- [Bugs encontrados/resolvidos → quais viraram FIX-N.]

## Aprendizados / armadilhas
- [O que descobrimos que vale virar armadilha em CONTEXT.md.]

## Onde parei
[Estado exato ao encerrar + próximo passo óbvio. Isto alimenta o «Última conversa» do STATUS.]

## Próximos passos
- [Ações para o próximo turno.]
