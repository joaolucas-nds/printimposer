---
name: smoke
description: Roda o smoke test da GUI do PrintImposer (os 9 itens do CLAUDE.md) e relata PASSOU/FALHOU por item. Use quando o usuario pedir /smoke ou depois de mudanca de interface.
disable-model-invocation: true
---
Rode o smoke test completo da GUI, na ordem da secao "Smoke test da GUI" do CLAUDE.md.

Passos:
1. Rode `python tests/test_engine.py`. Se falhar, PARE e relate — nao adianta abrir a janela
   com o nucleo quebrado.
2. Abra `python print_imposer.py` e percorra os 9 itens do checklist.
3. Para cada item: diga PASSOU ou FALHOU. Em falha, inclua o traceback inteiro e o que
   estava na tela.
4. Feche o app e confirme que `~/.printimposer/settings.json` foi criado/atualizado.

Nao conserte nada nesta passada — primeiro relate o quadro completo. Correcao vem depois,
com o menor diff possivel. Se a falha for de arquitetura e a spec nao decidir, diga isso e
pare: essa decisao e do chat com o dono.

Item que so o olho humano confirma (nitidez em zoom 125%/150%, aparencia do tema): diga
o que voce viu e marque «confirmar com o dono» — nao declare PASSOU por inferencia.

Grave o relatorio tambem em `../AAMMDD-HHMM-code-printimposer-probe-smoke.txt` (o
`AAMMDD-HHMM` sai de `date +%y%m%d-%H%M`, rodado na hora).
