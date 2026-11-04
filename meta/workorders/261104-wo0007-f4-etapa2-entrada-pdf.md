# WO 0007 — F4 etapa 2 (v1.4.0): entrada PDF via pypdfium2

## Cabecalho

> **Tipo:** mista — Parte A: WO de DOC (ancoras exatas). Parte B: WO de CODIGO que **delega a implementacao** a partir da spec. **Muda a interface → traz «Roteiro do dono» no fim.**
> **Config sugerida:** Opus · `/effort` alto (referencia de fonte atravessa motor e lista).
> **Pre-requisito:** HEAD `e18eccb` em `main`, empurrado. Suite verde (85 testes, 5 skips de SVG).
> **Base:** escada C (`meta/analises/261103-ANALISE-ordem-f4.md`, etapa 2); medicao de 03/11 (`pypdfium2-5.14.0-py3-none-win_amd64.whl` baixa sem compilar).
> **Arquivos que o chat gravou no disco e esta WO versiona** (`sha1sum` medido ao gravar):
> - `3152d8d2589e04ccde780372c6db91c9e92cefd7  meta/specs/261104-SPEC-F4-etapa2.md`
> - `3e4e8f29337eb54ca2867a14f0f319b888460f56  logs/2026-11-04.md`
> **Ancora semantica:** trecho que nao bater EXATAMENTE → **PARE e reporte**.
> **Idempotencia:** texto novo inteiro ja no arquivo e ancora ausente → PULE e diga.
> **Ancoras lidas em:** lidas pelo chat NESTE turno: `meta/STATUS.md` (sha1 `af92d5bfd53faa0dcf75c3a19b416a5de5ca5636`; linhas 37 e 43), `meta/IDEAS.md` (sha1 `0d8972f4be5891801480332d4b3dd2a6573b3510`; linha 70). Parte B: `print_imposer.py` lido em `_probe_svg_backend`/`rasterize_svg`/`open_source` (55–102, 336–390), `ImageEntry` (395–460), `quality_report` (715–730), `_filetypes`/`_add_folder` (1160–1200), `_expand` (693–705); o resto e leitura SUA.
> **Canal dos meta neste ciclo = CODE** para STATUS, IDEAS, CHANGELOG. O chat ja gravou a spec e a parte dele do log.
> **Proximo comando:** nenhum.

---

## 1. Por que

Etapa 2 da escada C. O Figma exporta PDF vetorial; entrada PDF da o mesmo ganho do SVG (arte desenhada no tamanho da celula) com instalacao de um `pip install`, enquanto o SVG nunca ligou na maquina do dono. Spec: `meta/specs/261104-SPEC-F4-etapa2.md`.

---

# PARTE A — registro (commit `docs`, antes do codigo)

## Edicao A1 — `meta/STATUS.md`

**A1a. Trocar** a linha inteira (o caminho perdeu um `\f` ao ser gravado — o certo esta no relatorio da wo0006):
~~~~
- [ ] **Dono:** apagar a pasta temporária da sonda `pypdfium2` (`rm -r` negado ao Code na wo0006): `%TEMP%\claude\C--Users-alexk-Tools-PrintImposer-printimposere86a394-080c-4ad1-b60b-c223bc59d98a\scratchpad\pdfium`.
~~~~
**por:**
~~~~
- [ ] **Dono:** apagar a pasta temporária da sonda `pypdfium2` (`rm -r` negado ao Code na wo0006). No CMD: `rmdir /s /q "%TEMP%\claude\C--Users-alexk-Tools-PrintImposer-printimposer\fe86a394-080c-4ad1-b60b-c223bc59d98a\scratchpad\pdfium"`.
~~~~
Grave com escrita que **nao interprete barra invertida** (arquivo lido/gravado como texto, sem `\f` virar caractere de controle). **Conferencia:** `grep -c 'printimposer\\fe86a394' meta/STATUS.md` → `1` e `grep -c 'printimposere86a394' meta/STATUS.md` → `0`.

**A1b. Trocar** a linha inteira em «Quebrado / Com Problema»:
~~~~
- (nada conhecido.)
~~~~
**por:**
~~~~
- **Suspeita, por leitura de código (não medida):** SVG com Auto-Rotate pode sair **ampliado** — é rasterizado na caixa `(cw, ch)` e só depois girado, então arte deitada numa célula em pé é desenhada pequena e esticada. Não se manifesta hoje (SVG indisponível na máquina do dono). O PDF da 1.4.0 já rasteriza na orientação final; o SVG pede um teste com stub e o mesmo conserto. Ver SPEC-F4-etapa2 §3.
~~~~

## Edicao A2 — `meta/IDEAS.md`

**Trocar** a linha inteira:
~~~~
O Figma exporta PDF. PDF de entrada tem o mesmo ganho do SVG (rasterizar na resolução exata da célula, zero upscale) e é o degrau natural para a imposição vetorial. Tratar SVG e PDF como a mesma família de entrada.
~~~~
**por:**
~~~~
O Figma exporta PDF. PDF de entrada tem o mesmo ganho do SVG (rasterizar na resolução exata da célula, zero upscale) e é o degrau natural para a imposição vetorial. Tratar SVG e PDF como a mesma família de entrada. **Entra na 1.4.0 (F4 etapa 2), via `pypdfium2` opcional** — `meta/specs/261104-SPEC-F4-etapa2.md`.
~~~~

## Commit A — e push
```
git add -- meta/STATUS.md meta/IDEAS.md meta/specs/261104-SPEC-F4-etapa2.md meta/workorders/261104-wo0007-f4-etapa2-entrada-pdf.md logs/2026-11-04.md
git commit -m "docs: spec da F4 etapa 2 (entrada PDF) e suspeita do SVG com auto-rotate"
git push
```
Conferencia: `git diff --cached --stat` → exatamente esses 5 caminhos.

---

# PARTE B — implementar `meta/specs/261104-SPEC-F4-etapa2.md` (commit `feat`)

## Edicao B1 — implementar a spec
Leia a spec INTEIRA e siga os «Passos». `VERSION = "1.4.0"`; bloco «Novidades da 1.4» no docstring do topo. Limites: «Fora de escopo» da spec; decisao de arquitetura nao coberta → **PARE e relate**.

## Edicao B2 — testes headless
No minimo: sem `pypdfium2`, `.pdf` fora de `SUPPORTED_EXT` e do seletor; referencia de fonte nao muda raster nem SVG (testes antigos verdes); PDF de N paginas vira N itens com rotulo `· p. i/N`; confirmacao acima de 50 paginas (logica, sem dialogo real); PDF ilegivel vai para a lista de pulados; **caixa de render na orientacao final** (stub do renderizador registra `(w, h)` pedido: com Auto-Rotate e orientacao diferente → `(ch, cw)`); PDF fora da guarda de qualidade; cache de miniatura distingue paginas. **Fixture:** gere os PDFs de teste com o proprio `write_pdf` do app (DEC-014) — ele faz PDF de varias paginas sem dependencia.

## Edicao B3 — validacao
1. Suite verde; diga antes (85) e depois.
2. **Sonda com `pypdfium2` real**, instalado em pasta temporaria (`pip install --target <pasta> pypdfium2`, `PYTHONPATH` so no processo da sonda) — **nunca** no Python do dono: PDF de 3 paginas (feito com `write_pdf`) entra como 3 itens; folha 2×2 A4 300 DPI com essas paginas gera em PNG e em PDF sem perda; e uma pagina **paisagem** numa celula **retrato** com Auto-Rotate sai com a dimensao certa sem ampliacao (compare o tamanho do render pedido com a celula). Relate os numeros.
3. `/smoke` (9 itens do `CLAUDE.md` + 5 da SPEC-F3 §11) com `pypdfium2` disponivel so para o processo de teste. App isolado com `USERPROFILE` e `HOME` temporarios (armadilha 11).
4. A pasta temporaria da sonda: liste e **diga o caminho** no relatorio; nao tente apagar com `rm -r` (o classificador nega) — o dono apaga.

## Edicao B4 — registro
- `meta/CHANGELOG.md`: `## [1.4.0] — <data>`, movendo para dentro dela o que estiver em `[Não lançado]` (a «Documentação» do README da 1.3); `[Não lançado]` fica `- (nada pendente.)`.
- `meta/STATUS.md`: Versão 1.4.0; etapa 2 feita, aguardando o roteiro do dono; Funcionando com a entrada PDF; Backlog sem «Chat: etapa 2 (1.4.0)» e com «Chat: README para a 1.4» e «Chat + dono: portão da imposição vetorial (etapa 3)»; «Última conversa». Procure `1.3.0` e `85 testes` no arquivo inteiro.
- `logs/2026-11-04.md`: sua secao no FIM.

## Commit B — e push
```
git add -- print_imposer.py tests/test_engine.py meta/CHANGELOG.md meta/STATUS.md logs/2026-11-04.md
git commit -m "feat: F4 etapa 2 - entrada PDF via pypdfium2 (v1.4.0)" -m "PDF entra como fonte opcional, sondada por render real; cada pagina vira um item da lista; rasteriza na celula ja na orientacao final (sem ampliacao); PDF ilegivel e pulado com aviso. SPEC-F4-etapa2."
git push
```

---

## Armadilhas desta WO
- **Commit A antes do codigo.**
- **Nao instale `pypdfium2` no Python do dono.** Sonda e smoke usam pasta temporaria. O dono instala no roteiro, se quiser.
- **Referencia de fonte atravessa o motor:** `_expand`, `compose_page`, `open_source`, miniatura e guarda. Raster e SVG nao podem mudar de comportamento — os 85 testes atuais sao a rede.
- **Fundo da pagina PDF:** renderize com fundo branco opaco; transparencia vira preto em alguns caminhos.
- **Barra invertida em caminho Windows** dentro de texto gravado por script: use string crua ou leia/grave sem interpretar escapes (foi assim que o STATUS perdeu um `\f`).
- **Isolamento:** `USERPROFILE` e `HOME` temporarios.

## Relatorio de aplicacao
Formato `/apply-wo`, em `../AAMMDD-HHMM-code-printimposer-apply-wo0007.txt`. Se so a Parte A fechar verde, empurre o commit A e relate a Parte B como vermelha, com o menu.

---

## Roteiro do dono *(depois do relatorio verde; leva ~10 min)*

**0. Instale o leitor de PDF do app** (é opcional; sem ele o app só não aceita PDF). No CMD:
```
python -m pip install pypdfium2
```
Certo: termina com `Successfully installed pypdfium2-…`.

1. **Abra pelo `printimposer.bat`.** Certo: cabeçalho `v1.4.0 · SVG: indisponível · PDF: pypdfium2`; `Ajuda › Sobre` lista «PDF sim».
2. **Exporte do Figma um PDF com 3 ou 4 frames** (ou use qualquer PDF de várias páginas) e adicione por **+ Arquivos**. Certo: entram **um item por página**, na ordem, com nome `arquivo.pdf · p. 1/4`, `p. 2/4`…, cada um com miniatura.
3. **Grade 2×2, A4, 300 DPI**, com os itens do PDF. Certo: o preview mostra as páginas nas células; o selo de qualidade não reclama delas.
4. **Página deitada em célula em pé:** se o PDF tiver um frame paisagem, ligue o Auto-Rotate. Certo: a arte gira e sai **nítida**, sem cara de ampliada (compare com o mesmo frame exportado em PNG pequeno, se quiser ver a diferença).
5. **Gere em PDF (sem perda)** e abra no seu leitor. Certo: abre, texto e traços do Figma nítidos ao dar zoom.
6. **Um PDF com senha ou um arquivo `.pdf` corrompido** (renomeie um `.txt` para `.pdf`), adicionado junto com outros. Certo: os bons entram; aparece **uma** mensagem dizendo qual foi pulado e por quê; o app segue.
7. **+ Pasta** numa pasta com PNGs e PDFs misturados. Certo: entram os dois tipos; os PDFs expandidos em páginas.

Devolva: «wo0007 aplicada e roteiro feito: tudo certo, menos os itens que eu listar abaixo».
