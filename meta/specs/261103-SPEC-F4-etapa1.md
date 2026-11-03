# SPEC — F4 etapa 1: PDF sem perda, compressão escolhível, espaçamento X/Y, tamanho da folha, HEIC/AVIF (v1.3.0)

> Spec de feature. Escrita em 2026-11-03 a partir da `meta/analises/261103-ANALISE-ordem-f4.md` (escada C, aprovada pelo dono) e da medição `261103-1852-code-printimposer-probe-f4` (arquivada em `zz_notas-arquivadas/`).
> Alvo: v1.3.0. Estado: aprovada, a implementar — pelo Claude Code, via `meta/workorders/261103-wo0005-f4-etapa1.md`.

## Problema

1. **O PDF de hoje perde qualidade sem avisar.** Medido em 03/11: uma folha A4 2×2 a 300 DPI gerada em PDF tem `1 /DCTDecode` e `0 /FlateDecode`. O Pillow grava imagem RGB em PDF **sempre** como JPEG (`PdfImagePlugin.py` do Pillow 12.2.0, linhas 118–121; a documentação: «L, RGB and CMYK mode images use JPEG encoding»), e não tem opção de qualidade. O formato que o README recomenda «para gráfica» é o único que comprime com perda sem o usuário escolher.
2. **Não há como escolher compressão.** JPEG está fixo em qualidade 95; PDF no padrão interno do Pillow.
3. **O espaçamento entre imagens é um valor só** para colunas e linhas (IDEAS 2026-06, «Margem por eixo»).
4. **O rodapé não mostra o tamanho da folha** — só a célula.
5. **HEIC e AVIF não entram.** Medido: o Pillow instalado (12.2.0) já lê AVIF (`features.check('avif') = True`), mas `.avif` não está em `RASTER_EXT`. HEIC precisa do `pillow-heif` (wheel `cp313-win_amd64` disponível, medido).

## Critérios de aceite (verificáveis)

- [ ] PDF gerado com o padrão novo contém `/FlateDecode` em cada página e **zero** `/DCTDecode`.
- [ ] O PDF sem perda é **idêntico em pixels** à folha composta: renderizado de volta (sonda com `pypdfium2` instalado em pasta temporária, **não** no Python do dono) no DPI da folha, a diferença pixel a pixel contra a `Image` composta é zero.
- [ ] Com «PDF: JPEG» escolhido, o PDF tem `/DCTDecode` e a qualidade escolhida é a usada (JPEG embutido reabre com o mesmo tamanho em bytes que `page.save(buf, "JPEG", quality=q)`).
- [ ] Saída JPEG usa a qualidade escolhida (padrão 95, como hoje).
- [ ] Espaçamento X e Y independentes mudam a geometria certa: com X = 10 mm e Y = 0, só as colunas se afastam; linhas de corte acompanham.
- [ ] `settings.json` e `presets.json` da 1.2 (só `margin_between_mm`) carregam com X = Y = valor antigo.
- [ ] Rodapé mostra o tamanho da folha em px e o tamanho bruto em MB.
- [ ] `.avif` aparece no seletor quando o Pillow lê AVIF; `.heic/.heif` aparecem só quando o `pillow-heif` está instalado e registra o abridor; sem eles, o app abre igual.
- [ ] Suíte verde com os testes novos; `/smoke` sem FALHOU.

## Decisões de design

### 1. PDF sem perda por escritor próprio (stdlib), não pelo Pillow nem por `img2pdf`
- **Como:** para cada folha, `page.save(buf, "PNG")`; concatenar os dados dos blocos `IDAT` do PNG e embuti-los como imagem do PDF com `/Filter /FlateDecode` e `/DecodeParms << /Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns <largura> >>`. É o mesmo truque do `img2pdf`: o PDF aceita o fluxo comprimido do PNG sem recomprimir, então é **sem perda por construção**, e o tamanho fica o do PNG. PNG sem entrelaçamento (o padrão do Pillow).
- **Modo JPEG do PDF:** mesmo escritor, com os bytes de `page.save(buf, "JPEG", quality=q)` embutidos com `/Filter /DCTDecode`.
- **Estrutura mínima do PDF:** catálogo, árvore de páginas, uma página por folha com `/MediaBox` em pontos (`mm × 72 / 25.4`) e a imagem desenhada por `q <w_pt> 0 0 <h_pt> 0 0 cm /Im0 Do Q`; tabela `xref` com offsets corretos e `trailer`. Função pública com docstring; constante de versão do PDF `%PDF-1.4`.
- **Por que não o Pillow:** não tem caminho sem perda para RGB (problema 1).
- **Por que não `img2pdf`:** depende do `pikepdf` (C++) e é LGPL-3 — duas dependências novas para o formato **padrão**, e a regra do projeto é que o padrão nunca depende de extra opcional (CLAUDE.md, «degrada com elegância»). O escritor próprio cabe em ~100 linhas de stdlib (`zlib` não é nem preciso: os dados já vêm comprimidos do PNG).
- Registrar como **DEC-014**, que substitui a **DEC-006** (PDF por `Image.save`).

### 2. Compressão escolhível — onde e quais valores
Na seção **Saída**, logo abaixo de «Formato», um controle que muda conforme o formato:

| Formato | Controle | Valores | Padrão |
|---|---|---|---|
| PDF | «Compressão» | **Sem perda** · JPEG | **Sem perda** |
| PDF com JPEG | «Qualidade» | 50–100 | 90 |
| JPEG | «Qualidade» | 50–100 | 95 (como hoje) |
| PNG, TIFF | nenhum (já são sem perda: PNG Deflate, TIFF LZW) | — | — |

Campos novos no `LayoutConfig` e em `PRESET_FIELDS`: `pdf_compression` (`"lossless"`/`"jpeg"`) e `jpeg_quality` (int). O mesmo `jpeg_quality` serve aos dois usos; quando o usuário troca de PDF-JPEG para JPEG, o campo mostra o valor atual, sem «padrão por formato» escondido — **um valor só, visível**. Valor fora de 50–100 é ajustado para o limite (mesmo padrão do DPI hoje).

### 3. Espaçamento por eixo
- `margin_between_mm` vira **dois** campos: `margin_between_x_mm` (entre colunas) e `margin_between_y_mm` (entre linhas). Atualizar `PRESET_FIELDS`, o motor (geometria de `cell_px`, `compose_page`, posições e `_draw_cuts`) e a UI («Entre colunas (mm)» e «Entre linhas (mm)» na seção Margens).
- **Compatibilidade:** `from_dict` que receba `margin_between_mm` e **não** receba os campos novos preenche X = Y = esse valor. Nada se perde de presets e configurações da 1.2.
- A margem externa continua um valor só (fora do escopo).

### 4. Tamanho da folha no rodapé
Linha nova no resumo fixo, abaixo da célula: `Folha: 2480 × 3508 px · 24,9 MB bruto`. «Bruto» = `largura × altura × 3` bytes (RGB sem compressão), em MB de 1024². É exato e honesto; **não** estimar o tamanho comprimido (depende do conteúdo — a medição de 03/11 mostrou PNG 3,6× maior que o PDF JPEG na mesma folha sintética). O rodapé tem altura fixa ≤ 84 px (SPEC-F3 §11): se a linha nova não couber, juntar com a linha da célula numa só.

### 5. HEIC/AVIF
- **AVIF:** acrescentar `.avif` a `RASTER_EXT` **só se** `PIL.features.check("avif")` for verdadeiro (sondar a capacidade, FIX-002).
- **HEIC:** `try: import pillow_heif; pillow_heif.register_heif_opener()` no carregamento do módulo; se registrar, `.heic` e `.heif` entram. Sem o pacote, nada muda. Não instalar nada no Python do dono.
- `Ajuda › Sobre` mostra uma linha `Formatos extras: AVIF sim/não · HEIC sim/não`.

## Fora de escopo
- Marcas de canto e sangria (etapa 4, depois do portão vetorial).
- Entrada PDF (etapa 2, v1.4.0).
- Imposição vetorial (portão da etapa 3).
- Margem externa por eixo; controle de proporção X/Y da imagem (IDEAS, outra coisa).
- Estimar tamanho comprimido.
- Instalar `pillow-heif` ou qualquer pacote no Python do dono.

## Passos
1. Escritor de PDF (`write_pdf(pages, path, dpi, mode, quality)`) + testes headless de estrutura (contagem de filtros, `xref` coerente, `IDAT` embutido byte a byte igual ao do PNG da folha).
2. `save()` usa o escritor para PDF; JPEG usa `jpeg_quality`.
3. Campos `pdf_compression` e `jpeg_quality` + UI na seção Saída.
4. Espaçamento X/Y no `LayoutConfig`, motor, linhas de corte, UI; compatibilidade de `from_dict`; testes.
5. Linha da folha no rodapé.
6. AVIF/HEIC com sondagem; linha no Sobre; testes do caso sem extra.
7. Sonda de ida e volta do PDF com `pypdfium2` em pasta temporária (critério 2).
8. `/smoke` (9 + 5 itens) + os itens novos da WO.
