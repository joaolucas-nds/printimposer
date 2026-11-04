# SPEC — F4 etapa 2: entrada PDF (v1.4.0)

> Spec de feature. Escrita em 2026-11-04 pela escada C da `meta/analises/261103-ANALISE-ordem-f4.md` (etapa 2).
> Alvo: v1.4.0. Estado: aprovada pelo plano da escada, a implementar — pelo Claude Code, via `meta/workorders/261104-wo0007-f4-etapa2-entrada-pdf.md`.

## Problema

O Figma exporta PDF vetorial, e hoje o PrintImposer não aceita PDF. O caminho vetorial que existe (SVG) depende de cairo nativo e **nunca ligou** na máquina do dono (`SVG: indisponível` desde 07/2026). Entrada PDF dá o mesmo ganho do SVG — a arte é desenhada já no tamanho da célula, sem ampliação — com instalação de um `pip install` só: medido em 03/11, `pypdfium2-5.14.0-py3-none-win_amd64.whl` traz o PDFium embutido (licença Apache-2.0/BSD-3) e baixou sem compilar.

## Critérios de aceite (verificáveis)

- [ ] Sem `pypdfium2`: o app abre igual à 1.3; `.pdf` não aparece no seletor nem entra por «+ Pasta»; o cabeçalho diz `PDF: indisponível`.
- [ ] Com `pypdfium2`: `.pdf` entra pelos dois caminhos; o cabeçalho diz `PDF: pypdfium2`; `Ajuda › Sobre` lista «PDF sim» em «Formatos extras».
- [ ] PDF de **N páginas** vira **N itens** na lista, na ordem das páginas, com nome `arquivo.pdf · p. 2/5`; cada item tem sua miniatura, quantidade, ▲ ▼ e ✕, como uma imagem.
- [ ] Arquivo com **mais de 50 páginas** pede confirmação antes de adicionar («Adicionar as 120 páginas de catalogo.pdf?»).
- [ ] PDF com senha, corrompido ou com 0 páginas **não entra** e não derruba nada: ao fim do lote, uma única mensagem lista os arquivos pulados e o motivo.
- [ ] A página é rasterizada **no tamanho que vai ocupar na célula, já na orientação final**: com Auto-Rotate ligado e orientação da página ≠ da célula, renderiza na caixa girada (`ch × cw`) e então gira — **nenhuma ampliação** depois do render (teste headless com o renderizador substituído por um stub que registra a caixa pedida).
- [ ] Item de PDF fica fora da guarda de qualidade (como o SVG).
- [ ] Preview e geração usam o mesmo caminho; uma folha 2×2 A4 300 DPI com quatro páginas de um PDF gera sem erro em PNG e em PDF sem perda.
- [ ] Suíte verde com os testes novos (os que dependem do `pypdfium2` são pulados sem ele, como os de SVG); `/smoke` sem FALHOU.

## Decisões de design

### 1. Back-end opcional, sondado por render real (FIX-002)
- `try: import pypdfium2` no carregamento; a sondagem cria um documento em memória (`PdfDocument.new()`, uma página pequena), **renderiza** e confere que saiu uma `Image`. Só então `PDF_OK = True` e `.pdf` entra em `SUPPORTED_EXT`.
- Guardar a referência do módulo (lição do segundo bug da FIX-002).
- Não instalar nada no Python do dono — a instalação é decisão dele (`pip install pypdfium2`, no README).

### 2. Uma página = um item da lista
- `ImageEntry` ganha `page_index: int = 0` e `page_count: int = 1`; o rótulo mostra `nome.pdf · p. {i+1}/{n}` quando `n > 1`.
- O motor passa a lidar com **referência de fonte** (caminho + página), não só caminho: `_expand`, `compose_page`, `open_source` e o que mais consumir a lista. Formato da referência é decisão de código (NamedTuple, tupla, etc.); o requisito é que raster e SVG continuem funcionando sem mudança visível e que os testes antigos passem.
- O cache de miniatura chaveia também pela página.
- **Por que não «só a primeira página»:** o Figma exporta vários frames num PDF de várias páginas; pegar só a primeira perderia o resto em silêncio.

### 3. Rasterizar na orientação final
- Para PDF, o tamanho da página em pontos é conhecido antes do render (`page.get_size()`). Com Auto-Rotate ligado e orientação diferente da célula, a caixa de render é `(ch, cw)`; senão `(cw, ch)`. Escala = `min(caixa_w / w_pt, caixa_h / h_pt)`, respeitando o modo de ajuste (fit: `min`; fill: `max`, e o `_place_image` recorta; stretch: render em `(caixa_w, caixa_h)` direto).
- Fundo da página: renderizar com fundo branco opaco (PDF sem fundo vira preto/transparente conforme o renderizador) — a cor de fundo da folha continua valendo para a área fora da página.
- **Suspeita sobre o SVG, por leitura de código, NÃO medida:** hoje o SVG é rasterizado na caixa `(cw, ch)` e só depois o Auto-Rotate gira — arte deitada em célula em pé seria desenhada pequena e então **ampliada**. O SVG não liga na máquina do dono e o conserto dele está **fora desta spec**; a WO registra a suspeita para tratar depois com teste próprio.

### 4. Guarda de qualidade e o que ela não vê
- Item de PDF é ignorado pela guarda (vetor não amplia). **Limite honesto:** um PDF que só embrulha uma imagem raster pequena continua pequeno — a guarda não abre o conteúdo da página. Vai no README.

### 5. Interface
- Seletor de arquivos ganha o tipo `PDF (*.pdf)` quando `PDF_OK`.
- Cabeçalho: `v1.4.0 · SVG: … · PDF: …`.
- `Ajuda › Sobre`: «Formatos extras: AVIF … · HEIC … · PDF …».

## Fora de escopo
- Saída vetorial / imposição vetorial (portão da etapa 3). A folha continua rasterizada no DPI e escrita pelo escritor de PDF da DEC-014.
- Consertar o SVG (só registrar a suspeita).
- Escolher um intervalo de páginas no diálogo (todas entram; remove-se o que não quer com ✕).
- PDF com senha: não pede senha, só pula.
- Instalar `pypdfium2` no Python do dono.

## Passos
1. Sondagem `PDF_OK` + módulo guardado; extensão e tipo no seletor; cabeçalho e Sobre.
2. Referência de fonte (caminho + página) no motor e na lista; testes antigos verdes.
3. Ingestão: expandir páginas, confirmação acima de 50, lista de pulados.
4. Render na orientação final + miniatura por página.
5. Testes headless (com stub de renderizador onde o `pypdfium2` faltar) + sonda com `pypdfium2` em pasta temporária.
6. `/smoke` + roteiro do dono da WO.
