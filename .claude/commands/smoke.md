Rode o smoke test completo da GUI, na ordem da secao "Smoke test da GUI" do CLAUDE.md.

Passos:
1. Rode `python tests/test_engine.py`. Se falhar, PARE e relate — nao adianta abrir a janela
   com o nucleo quebrado.
2. Abra `python print_imposer.py` e percorra os 9 itens do checklist.
3. Para cada item: diga PASSOU ou FALHOU. Em falha, inclua o traceback inteiro e o que
   estava na tela.
4. Feche o app e confirme que `~/.printimposer/settings.json` foi criado/atualizado.

Nao conserte nada nesta passada — primeiro relate o quadro completo. Correcao vem depois,
com o menor diff possivel, e so no que for de execucao. Se a falha for de arquitetura,
diga isso e pare: essa decisao e do chat.
