# ANALISE — Ordem interna da F4 (Qualidade profissional)

> **Status:** Decidida (2026-11-03) — escada C; desfecho no fim e na DEC-014
> **Data:** 2026-11-03
> **Elos:** ROADMAP F4 · DEC-001, DEC-003, DEC-005, DEC-006 · HISTORY §1–§5 · IDEAS (entradas listadas abaixo)

## Problema

A F4 tem nove itens sem ordem («ordem interna não decidida»). Eles não são independentes: **marcas de canto, sangria e compressão mudam de forma conforme a saída seja raster (hoje) ou vetorial (o maior item da fase)**. Na ordem errada, as marcas e a sangria são feitas duas vezes — uma no Pillow, depois de novo no PDF vetorial —, ou a fase abre pelo item mais caro e arriscado (imposição vetorial, que reabre DEC-001/003/006) antes de entregar qualquer ganho.

Se nada for decidido, a próxima WO pega o item que parecer mais fácil, e a ordem vira acaso.

## Restricoes / o que foi medido

**Lido no repositório neste turno** (ROADMAP, IDEAS, HISTORY, DECISIONS, `print_imposer.py`):
- O motor é raster de ponta a ponta: `compose_page` monta uma `PIL.Image` por folha; linhas de corte são desenhadas DEPOIS, por cima (DEC-001, DEC-005). O PDF sai por `Image.save(..., "PDF", resolution=dpi)` (DEC-006).
- O rodapé fixo da F3 **já mostra** o selo de qualidade e o tamanho da célula em mm/px. Do item «Barra de estado com px, MB estimados e selo», falta só **MB estimados** (e o px da folha inteira).
- A entrada SVG já existe e rasteriza **no tamanho da célula** (zero upscale). PDF de entrada é da mesma família (HISTORY §5, IDEAS 2026-07-18).
- Marcas de canto precisam de espaço para existir: com «entre imagens = 0» só cabem na margem externa da folha (HISTORY §4: «gutter mínimo é necessário»). **Sangria e marcas são acopladas:** a marca indica o corte (trim), a sangria transborda além dele — a geometria das duas é uma só.
- IDEAS marca «Moldura de 3 fotos» e «.exe» como F4, mas o ROADMAP os põe na **F5** (layouts livres, distribuição). Divergência de registro; esta análise segue o ROADMAP.

**Fontes externas, lidas neste turno:**
- **`pypdfium2`** — wheels prontas para Windows (x86-64, x86-32, ARM64) com o binário do PDFium embutido; licença Apache-2.0/BSD-3; `render_page(...)` devolve uma `PIL.Image`. Ou seja: a entrada PDF instala com um `pip install`, **mais fácil que o SVG**, que no Windows depende de cairo nativo. Fonte: [PyPI — pypdfium2](https://pypi.org/project/pypdfium2/0.12.0/) (página de versão antiga; o próprio PyPI aponta a 5.14.0 como atual).
- **AVIF no Pillow** — a 11.2 passou a ler/gravar AVIF, mas **só compilado do fonte**; a 11.2.1 saiu «without libavif included in the wheels». Se versões posteriores já trazem libavif na wheel, **não verifiquei**. Fonte: [Pillow 11.2.1 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/11.2.1.html). HEIC continua via `pillow-heif`.
- **Imposição vetorial com `pypdf`** — o guia oficial mostra exatamente um N-up 4×4 de cartões numa A4, com `merge_transformed_page` + `Transformation().translate()`. Fonte: [pypdf — cropping and transforming](https://github.com/py-pdf/pypdf/blob/3.13.0/docs/user/cropping-and-transforming.md). O guia **não diz** que o resultado é vetorial; pelo mecanismo (copia o conteúdo da página, não a rasteriza), deve ser — **deduzido, a confirmar por sonda**.

**Não medido — pedido ao Code (seção «Medição pedida», no fim):** versão do Pillow e se ele lê AVIF/WEBP; se `pypdfium2` e `pypdf` instalam no Python do dono; **se o PDF de saída de hoje é JPEG por dentro** (suspeita do chat: o Pillow grava imagem RGB em PDF com `DCTDecode`, isto é, compressão com perda — se confirmar, o «PDF para gráfica» atual já perde qualidade, e a compressão sobe de prioridade); tamanho real de uma folha A4 2×2 a 300 DPI em PNG e PDF.

## Opcoes consideradas

### A — Raster até o fim; vetorial sai da F4
Marcas, sangria e compressão no motor Pillow atual; a imposição vetorial vai para a F5 ou é descartada.
- **Ganha:** diffs pequenos, arquivo único preservado (DEC-003), nada de pipeline duplo.
- **Perde:** o teto de qualidade fica no DPI; arquivos grandes; se a vetorial voltar depois, marcas e sangria são refeitas no PDF.
- **Descartada como plano inteiro** porque fecha a porta da vetorial sem o dado que decide (você manda para gráfica?). Mas as etapas 1 e 2 dela sobrevivem na opção C.

### B — Vetorial primeiro
Abrir a F4 pela imposição vetorial (`pypdf` para posicionar páginas PDF; imagens raster embutidas como imagem), e então marcas e sangria nascem vetoriais.
- **Ganha:** qualidade máxima e arquivo mínimo para quem exporta PDF do Figma; marcas sem peso; sem retrabalho.
- **Perde:** é o item mais caro e de maior risco, logo no começo; vira **dois pipelines** (preview continua raster — precisaria do `pypdfium2` para mostrar o PDF); reabre DEC-001, DEC-006 e provavelmente DEC-003 (arquivo único). E entrada PNG — o seu fluxo de hoje — **não ganha nada** com isso.
- **Descartada** como primeiro passo: aposta o começo da fase numa premissa que não foi medida (seu uso real de gráfica) e não melhora o fluxo PNG atual.

### C — Escada: barato e certo primeiro, decisão vetorial com dado na mão *(recomendada)*

| Etapa | Itens | Versão | Por que nesta posição |
|---|---|---|---|
| **1. Ganhos baratos e independentes** | Compressão escolhível na saída (PNG/TIFF lossless × JPEG/PDF com qualidade) · margem por eixo (X/Y) · MB estimados no rodapé · HEIC/AVIF opcional | 1.3.0 | Valem com OU sem vetorial: compressão sempre importa para entrada raster, margem por eixo é geometria comum, o rodapé já existe. Nenhum é desfeito depois. |
| **2. Entrada PDF** (via `pypdfium2`, rasterizando na célula como o SVG) | 1 item | 1.4.0 | Mesmo ganho do SVG, instalação mais fácil. E não se perde se a vetorial vier: o `pypdfium2` vira o renderizador do preview do PDF vetorial. |
| **3. Portão: imposição vetorial — sim, F5, ou descartar** | decisão, não código | — | Decidida com os números da medição e o seu uso real (casa × gráfica). Se «sim», ganha análise própria (DEC-001/003/006). |
| **4. Marcas de canto + sangria**, juntas | 2 itens | 1.5.0 | Depois do portão, para nascerem no pipeline certo e uma vez só. A geometria (trim, sangria, gutter) entra no motor; o desenho segue o pipeline escolhido. |
| **Quando der** | Nitidez em zoom 125%/150% | — | Depende de monitor/escala, não de ordem. |

## Recomendacao

**Opção C.** Ela entrega ganho real cedo (1.3.0 com quatro melhorias pequenas, todas independentes da decisão vetorial), coloca a entrada PDF quando ela é barata, e adia o único item caro para um portão em que a decisão vem com número e com o seu uso real — em vez de apostar o começo da fase nele. O retrabalho que a ordem errada causaria (marcas e sangria feitas duas vezes) desaparece porque elas ficam **depois** do portão.

**Melhor argumento contra:** se você manda quase tudo para gráfica e exporta PDF do Figma, a vetorial é o ganho nº 1 (HISTORY §2) e a escada a atrasa em duas versões. Resposta: nesse caso, o portão da etapa 3 sobe para logo depois da etapa 2 (que é pré-requisito útil dela de qualquer jeito) — a escada só muda de altura, não de ordem.

## Riscos

- **A medição confirma que o PDF de hoje é JPEG por dentro.** Então a etapa 1 tem um item quase-bug: o PDF passa a ter a qualidade escolhida, e o padrão deve ser sem perda. Sinal: resultado do item 3 da medição.
- **`pypdfium2` ou `pypdf` sem wheel para o Python do dono** *(medido depois: Python 3.13.13 no PATH; as três wheels baixaram)*. A etapa 2 degrada como o SVG (formato some do seletor), e o portão vetorial fica caro. Sinal: item 2 da medição.
- **Margem por eixo mexe no `LayoutConfig` e no `settings.json`** — mesmo cuidado da `sections_open`: arquivo antigo cai no padrão (X = Y = valor atual).
- **Etapa 1 com quatro itens pode inchar.** Se a spec passar de uma WO tranquila, quebra em 1.3.0 (compressão + MB estimados) e 1.3.1 (margem por eixo + HEIC/AVIF).

## Ponto de decisao

1. **Aprova a escada C** (1.3.0 ganhos baratos → 1.4.0 entrada PDF → portão vetorial → 1.5.0 marcas + sangria)?
2. **Para onde vão as suas folhas:** impressora de casa, gráfica, ou as duas? — é o dado que posiciona o portão da etapa 3.

## Medição pedida *(para o Claude Code — não é WO: não edita, não commita)*

Rode e devolva **número cru + o comando que o produziu**, sem interpretar (se achar que um número indica problema, diga o número primeiro e a suspeita depois). Grave o relatório em `../AAMMDD-HHMM-code-printimposer-probe-f4.txt`. Ambiente isolado: crie uma pasta temporária e defina `USERPROFILE` **e** `HOME` para ela antes de importar o app (CONTEXT, armadilha 11); apague o que criar.

1. `python --version` e `python -c "import PIL, PIL.features as f; print(PIL.__version__, f.check('avif'), f.check('webp'))"`.
2. Instalabilidade, **sem instalar no Python do dono**: `pip download pypdfium2 pypdf pillow-heif --no-deps -d <pasta temporária>` — diga quais baixaram wheel e o nome do arquivo de cada uma (o nome traz a plataforma e a versão do Python).
3. O PDF de hoje é JPEG por dentro? Gere uma folha A4 2×2 a 300 DPI pelo `ImpositionEngine` com quatro imagens de teste RGB e saída PDF; abra o PDF gerado como bytes e conte as ocorrências de `/DCTDecode` e de `/FlateDecode` (`grep -c` sobre o binário, ou `bytes.count`). Diga também a linha do `PdfImagePlugin` do Pillow instalado que escolhe o filtro para modo `RGB` (caminho do arquivo + o trecho).
4. Tamanho em bytes da mesma folha salva em PNG, PDF e JPEG (`os.path.getsize`).

**O que esta medição NÃO responde:** se a qualidade do PDF é aceitável para gráfica (isso é olho, não número) e se o `pypdf` gera saída vetorial (pede uma sonda própria, se o portão da etapa 3 for aberto).

## Desfecho *(2026-11-03)*

**Decisão do dono:** escada C aprovada · folhas vão para **casa e gráfica** (portão vetorial fica na posição 3, com sonda própria) · PDF **sem perda** por padrão.

**Medição** (`261103-1852-code-printimposer-probe-f4`, arquivada em `zz_notas-arquivadas/`):
| Item | Resultado |
|---|---|
| Python / Pillow | 3.13.13 · Pillow 12.2.0 · AVIF `True` · WEBP `True` |
| Wheels | `pypdfium2-5.14.0-py3-none-win_amd64` · `pypdf-6.21.4-py3-none-any` · `pillow_heif-1.8.1-cp313-cp313-win_amd64` — as três baixaram |
| PDF de hoje | `/DCTDecode` = 1, `/FlateDecode` = 0 — **JPEG por dentro**, qualidade padrão do Pillow (o `save` não passa `quality`) |
| Tamanhos (folha sintética A4 2×2 300 DPI) | PDF 3.176.835 · PNG 11.327.669 · JPEG q95 7.304.693 bytes — ordem de grandeza, conteúdo sintético |

**Consequências:** a etapa 1 ganha um item de correção (PDF sem perda) e perde uma dependência (AVIF já é nativo). Spec: `meta/specs/261103-SPEC-F4-etapa1.md`. O caminho do PDF sem perda (escritor próprio embutindo o fluxo do PNG) virou DEC-014.

