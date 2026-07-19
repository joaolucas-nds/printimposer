Encerre a tarefa atual e deixe o projeto pronto para a proxima sessao.

1. Rode `python tests/test_engine.py` — tem de estar verde.
2. Confira `git diff` inteiro. Diff menor que resolve; nada de refactor nao pedido.
3. Atualize `meta/STATUS.md` em modo APPEND: o que passou a funcionar sai da secao
   "Quebrado", o que quebrou entra. Nao reescreva o arquivo.
4. Se corrigiu bug grave, acrescente um `FIX-N` em `meta/DECISIONS.md` com
   sintoma / causa raiz / solucao / licao. Nunca reescreva entrada existente.
5. Se topou com uma ideia pelo caminho, registre em `meta/IDEAS.md` sem decidir por ela.
6. Commit em PT-BR, imperativo curto, SEM ACENTO. Nao faca push.
7. Feche relatando: o que mudou, o que testou, o que ficou aberto para o chat decidir.
