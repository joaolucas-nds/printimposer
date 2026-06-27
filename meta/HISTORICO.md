# HISTORICO.md — Conhecimento Consolidado

> **Opcional.** Arquivo-baú para conhecimento denso que já foi aprendido e não muda mais — guias técnicos, análises de viabilidade, notas de migração — que tornariam o CONTEXT pesado demais.
> Não é lido no início da sessão; o assistente consulta sob demanda quando o assunto aparece.

---

## 1. Qualidade de impressão e DPI (guia de fonte → folha)

A folha é rasterizada no DPI configurado. Tamanho em pixels: `px = mm × DPI / 25.4`.

Tamanhos-alvo (a 300 DPI):
| Papel | px (L × A) |
|---|---|
| A3 | 3508 × 4961 |
| A4 | 2480 × 3508 |
| A5 | 1748 × 2480 |
| A6 | 1240 × 1748 |
| Letter | 2550 × 3300 |

**Regra prática:** para um card A6 imprimir a 300 DPI, a imagem-fonte deve ter **≥ 1240×1748 px**. Se tiver menos, a ferramenta faz *upscale* e a impressão perde nitidez — daí a "guarda de qualidade" planejada (avisar quando fonte < célula).

**Sobre "exportar 4× no Figma = 300 DPI":** só é verdade se o frame-base tiver os pixels certos. Exportar a 4× multiplica os pixels por 4; o resultado só atinge 1240×1748 se o frame a 1× for ~310×437 px. **Mire o alvo em pixels, não a escala** — ou use exportação por tamanho fixo em px no Figma. Quando em dúvida, exporte maior; reduzir preserva qualidade, ampliar não.

## 2. O que é "compressão" aqui (respondendo a dúvida do usuário)

Sim, "compressão" é o termo correto. Há duas perdas distintas envolvidas:

1. **Reamostragem (resampling):** encaixar a imagem na célula muda sua contagem de pixels. Reduzir para caber é seguro; ampliar (upscale) inventa pixels e borra. Isso é independente do formato.
2. **Compressão do arquivo:**
   - *Lossless* (PNG, TIFF/LZW, Flate no PDF) — preserva todos os pixels; arquivo maior. Linhas finas e bordas nítidas incham o arquivo (detalhe de alta frequência).
   - *Lossy* (JPEG) — descarta informação para reduzir tamanho; cria artefatos em bordas e texto. Bom para foto, ruim para linhas nítidas.

**O que o Windows faz no "4 imagens por folha":** o driver reamostra cada imagem para o tamanho do slot e rasteriza a folha, normalmente recomprimindo no caminho — é dessa reamostragem + recompressão que vem a perda que o usuário notou. A ferramenta resolve isso controlando o DPI explicitamente e (planejado) expondo a escolha de compressão, para o usuário decidir o trade-off tamanho × qualidade conscientemente.

**Maior salto possível:** não rasterizar. Se a entrada for PDF vetorial (export do Figma), dá para posicionar as páginas vetorialmente — qualidade perfeita, arquivo minúsculo, marcas sem peso. É a F3 do ROADMAP.

## 3. SVG como entrada — por que não é direto e qual o caminho

Pillow **não rasteriza SVG** (não tem renderizador de vetor). Para aceitar SVG seria preciso um conversor:
- **cairosvg** (puro Python + cairo) — `cairosvg.svg2png(...)` para um buffer e então abrir no Pillow. Dependência adicional.
- **Inkscape** por linha de comando — robusto, mas exige Inkscape instalado (dependência externa pesada).

Decisão atual: exportar PNG do Figma (caminho mais simples e confiável). SVG de **entrada** segue como ideia ativa com ressalva de dependência. SVG de **saída** foi descartado: com arte raster, o SVG só embutiria os bitmaps — nenhum ganho.

## 4. Pesquisa de imposição/prepress profissional (2026) — o que mirar

Levantamento de ferramentas de referência (Kodak Preps, Ultimate Impostrip, Montax Imposer, Metrix, PDF Press, DevaliPI Imposition Studio) e do que elas oferecem, filtrado pelo escopo deste projeto (N-up plano para corte, uso pessoal/semi-profissional):

**Recursos que fazem sentido adotar (viraram IDEAS/ROADMAP):**
- **Entrada/saída em PDF vetorial** — preserva qualidade e reduz drasticamente o tamanho. O diferencial de qualidade nº1.
- **Marcas de corte de canto** (ticks no gutter) em vez de linhas atravessando a folha — padrão de indústria, quase sem peso no arquivo.
- **Sangria (bleed)** ~3 mm (1/8") — evita borda branca no corte de artes sem margem.
- **Templates / hot folders** — salvar uma configuração e só jogar os arquivos para processar. Mapeia direto no desejo de "esforço mínimo" → presets (.json) + (futuro) pasta observada.
- **Preview em tempo real** — destacado até por ferramentas pagas como diferencial; o PrintImposer **já tem**.
- **Step-and-repeat** — duplicar uma arte N vezes; versão básica já existe via "quantidade".

**Recursos deliberadamente fora do escopo:**
- Imposição de cadernos/booklet (saddle stitch, perfect binding) e *cut & stack* com ordenação de pilha.
- Registro multi-plate / separação de cores / trapping / overprint (offset).
- Nesting de formas irregulares e imposição de embalagem (die-line, step-and-repeat de formas).
- Variable Data Printing (VDP), JDF/JMF, integração com RIP/MIS.

**Terminologia de marcas (para implementar marcas de canto corretamente, F3):**
- *Crop/trim marks*: indicam onde cortar (tamanho final). Ficam nos cantos, fora da arte, no gutter.
- *Bleed marks*: como as de corte, mas no limite da sangria.
- *Registration marks*: alinhamento entre cores; fora do escopo.
- Gutter mínimo é necessário para haver espaço onde desenhar as marcas de canto sem invadir a arte.

## 5. Nota técnica — CustomTkinter + Tkinter nativo

- **Aninhar CTk em geometria nativa:** widgets CustomTkinter com canvas interno (ex.: `CTkScrollableFrame`) não podem ser adicionados diretamente a `tk.PanedWindow`; interponha um `tk.Frame` neutro. Causa raiz e correção em FIX-001.
- **Drag-and-drop de arquivos:** não há suporte nativo; usa-se `tkinterdnd2` com um wrapper de classe sobre `CTk` (padrão confirmado na comunidade). É dependência opcional — degradar com elegância se ausente. Tem hook próprio para PyInstaller, útil na F4.
- **PDF a partir de imagem:** `PIL.Image.save(..., "PDF", resolution=dpi, save_all=True, append_images=[...])` gera multipágina. Para escolher compressão/embutir sem recomprimir, avaliar `img2pdf`. Para imposição vetorial (F3), `pypdf`/`reportlab` posicionam páginas PDF.
