# ANALISE — Portão da imposição vetorial (F4, etapa 3)

> **Status:** Em discussao — sonda 1 feita (04/11); falta a sonda 2, com os PDFs do Figma do dono (seção «Medição pedida 2»)
> **Data:** 2026-11-04
> **Elos:** ROADMAP F4 (escada C, etapa 3) · `meta/analises/261103-ANALISE-ordem-f4.md` · DEC-001, DEC-003, DEC-005, DEC-014 · IDEAS «Entrada vetorial → imposição vetorial»

## Problema

Hoje toda folha é **rasterizada**: o PDF de saída é uma imagem por página, no DPI escolhido (DEC-001; sem perda desde a DEC-014). Para entrada PDF isso significa: o texto e os traços vetoriais da arte viram pixels, e imagens que já estavam dentro do PDF são **reamostradas e regravadas**. A imposição vetorial colocaria cada página de entrada na folha **como está** (transformação de posição/escala/giro), sem rasterizar.

A pergunta do portão: **fazer isso agora (antes das marcas e da sangria), adiar para a F5, ou descartar?** Decidir errado custa caro nos dois sentidos — fazer cedo abre um segundo pipeline de saída num arquivo único de 2.867 linhas; adiar sem critério deixa a etapa 4 desenhada para um pipeline só.

## Restricoes / o que foi medido

**Lido no repositório e nos relatórios, neste turno:**
- `print_imposer.py` tem **2.867 linhas** e `tests/test_engine.py` **1.215** (`wc -l`). DEC-003 (arquivo único) foi escrita para ~1.200.
- O escritor de PDF próprio (DEC-014) já monta catálogo, páginas e `xref`; o `pypdfium2` 5.14.0 já está no Python do dono (relatório da wo0007).
- **Os PDFs reais do dono** (cartazes gerados por jsPDF, `zz_notas-arquivadas/cartazes-acessorios-2026-11-04-a4.pdf`, 790.196 bytes, 4 páginas) têm `/DCTDecode` = 4 e `/FlateDecode` = 4 (contado por `bytes.count` neste turno). Ou seja: **há imagem JPEG dentro**; se o texto também é vetorial (fontes) **não foi medido**. A saída raster sem perda do app, a 150 DPI, deu 730.153 bytes para 2 folhas.
- **Fato de desenho que muda o argumento da análise anterior:** PNG, JPEG, TIFF e WebP continuam **raster** de qualquer jeito. Então marcas de canto e sangria **precisam existir no motor raster** mesmo que o PDF fique vetorial. A vetorial não evita fazer as marcas duas vezes — ela **acrescenta** um segundo desenhista. O jeito de não duplicar é uma **camada de geometria** comum (retângulos de corte, sangria e segmentos de marca em mm) com dois desenhistas (Pillow e operadores PDF).

**Fonte externa, lida em 03/11:** o `pypdf` monta N-up por `merge_transformed_page` (exemplo oficial de 16 cartões numa A4). **Não verificado:** se o resultado é vetorial (deduzido pelo mecanismo). O PDFium — que já temos pelo `pypdfium2` — tem funções para transformar uma página em objeto de formulário e posicioná-lo com matriz (`FPDF_NewXObjectFromPage`, `FPDF_NewFormObjectFromXObject`); **se o `pypdfium2` 5.14 as expõe, não verifiquei** — é o item 2 da sonda.

**Não medido (pedido na sonda):** se o texto dos PDFs reais é vetorial; se os protótipos geram N-up correto; tamanho e nitidez vetorial × raster a 300 DPI; tempo.

## Opcoes consideradas

### A — Descartar
O PDF continua raster sem perda. **Ganha:** um pipeline só, nada novo para manter. **Perde:** texto vetorial vira pixel; imagens embutidas são reamostradas; arquivo a 300 DPI fica grande. **Descartada como plano** só se a sonda mostrar que o ganho é imperceptível no uso do dono.

### B — F5, com a geometria preparada agora
Etapa 4 (marcas + sangria) vem primeiro, no motor raster, **mas** já com a camada de geometria separada do desenho. A vetorial entra depois como segundo desenhista sobre a mesma geometria. **Ganha:** entrega as marcas logo, sem retrabalho futuro; nenhum pipeline novo agora. **Perde:** quem manda PDF para gráfica espera mais pelo PDF vetorial.

### C — Agora, como modo de saída opcional
Na seção Saída, `PDF › Compressão` ganha **«Vetorial»** ao lado de «Sem perda» e «JPEG». Entradas PDF entram como objeto de formulário (sem rasterizar); entradas raster entram como imagem original embutida, só escalada (sem reamostrar). Fundo, linhas de corte e, depois, marcas como operadores PDF. **Ganha:** qualidade máxima e arquivo pequeno para PDF; caminho natural para gráfica. **Perde:** segundo pipeline; o preview (raster) deixa de ser idêntico à saída vetorial — diferença pequena, mas existe; provavelmente força revisar a DEC-003 (modularizar).

## Recomendacao

**Decidir pelo resultado da sonda, com critério fixado ANTES de medir:**
- **C** se as três condições valerem: (1) um protótipo (via `pypdfium2` ou `pypdf`) gera o N-up correto dos PDFs reais do dono — posição, escala, giro, recorte do modo Preencher; (2) o render do protótipo a 300 DPI difere do raster do app só por arredondamento (média de diferença por pixel ≤ 2 de 255) **e** os recortes ampliados mostram ganho visível de nitidez no texto, no seu olho; (3) o PDF vetorial fica **≤ 1/3** do tamanho do raster sem perda a 300 DPI.
- **B** em qualquer outro caso — e B **sempre** com a camada de geometria comum, porque ela é necessária para as marcas existirem nos formatos raster.
- **A** só se o protótipo falhar nas duas bibliotecas.

**Por quê critério e não palpite:** a análise de 03/11 adiou esta decisão para quando houvesse dado; o dado decisivo (o texto dos PDFs do dono é vetorial? quanto se ganha?) cabe numa sonda de uma rodada. **Melhor argumento contra:** a sonda mede os PDFs de cartazes de **um** gerador (jsPDF); outra ferramenta (Figma, Affinity) pode ter perfil diferente. Por isso a sonda inclui um PDF vetorial puro gerado na hora, além dos reais.

## Riscos
- **Preview ≠ saída** no modo vetorial (C). Sinal: diferença média > 2/255 no item 4 da sonda.
- **DEC-003 sob pressão:** +400 linhas estimadas (não medido) sobre 2.867. Se C vencer, a WO começa por uma análise curta de modularização.
- **Recorte (modo Preencher) e giro** são onde o vetorial erra calado — a sonda testa os dois de propósito.

## Ponto de decisao
Depois da sonda: **C, B ou A**, segundo o critério acima — e, se C, se vale modularizar o arquivo antes.

---

## Medição pedida *(para o Claude Code — não é WO: não edita o repo, não commita)*

Rode e devolva **número cru + o comando ou o trecho de script que o produziu**, sem interpretar (número primeiro, suspeita depois, separada). Scripts e saídas no scratchpad; **imagens para o dono olhar** em `../261104-SONDA-vetorial/` (pasta-pai). Relatório em `../AAMMDD-HHMM-code-printimposer-probe-vetorial.txt`. Ambiente: `USERPROFILE` e `HOME` temporários (CONTEXT, armadilha 11). `pypdf` só por `pip install --target <pasta temporária> pypdf` e `PYTHONPATH` no processo da sonda — **nunca** no Python do dono. Insumos: `../zz_notas-arquivadas/cartazes-acessorios-2026-11-04-a4.pdf` e `-a5.pdf` (só leitura) e um PDF **vetorial puro** que você gera na hora (texto + retângulos, sem imagem — por exemplo com o `write_pdf` do app NÃO serve, porque ele só grava imagem; use o `pypdfium2` ou o `pypdf` para criar uma página com texto).

1. **Inventário dos insumos**, por página: tamanho em pt; nº de objetos de texto e de caracteres extraíveis (`pypdfium2`: `get_textpage().count_chars()`); nº de imagens, tamanho em px e filtro de cada uma; fontes embutidas (`/FontFile` no binário). Responde: o texto dos PDFs do dono é vetorial?
2. **Protótipo A — `pypdfium2`:** diga se o 5.14 expõe `FPDF_NewXObjectFromPage` e `FPDF_NewFormObjectFromXObject` (no `pypdfium2.raw`). Se sim, gere uma folha A4 com as páginas dos insumos como objetos de formulário em dois layouts: **1×2 com Auto-Rotate** (como o dono usou em 04/11) e **2×2 no modo Preencher** (recorte por clip). Salve.
3. **Protótipo B — `pypdf`** (`merge_transformed_page` + clip): os mesmos dois layouts.
4. Para cada protótipo e layout, contra o **raster sem perda do app a 300 DPI** (mesma grade, gerado pelo `ImpositionEngine` do repo): tamanho em bytes; tempo de geração; render dos dois PDFs a 300 DPI pelo `pypdfium2` e **diferença média por pixel** (0–255); se a posição/escala/giro/recorte bate (diga como conferiu). E **recortes ampliados** (render a 600 DPI, ~500×500 px, num trecho com texto) do raster e do vetorial, lado a lado, em `../261104-SONDA-vetorial/` com nomes que digam o que são.
5. **Entrada raster no modo vetorial:** com um PNG e um JPEG de teste, diga se cada protótipo consegue embutir o arquivo original como imagem escalada **sem reencodar** (compare os bytes da imagem embutida com os do arquivo) e o tamanho resultante.

**O que esta sonda NÃO responde:** se a nitidez extra se vê no papel (isso é o dono, com os recortes e uma impressão de teste); se vale modularizar (decisão posterior); compatibilidade com o leitor de uma gráfica específica.

---

## Resultado da sonda 1 *(2026-11-04, `261104-2007-code-printimposer-probe-vetorial`, arquivado em `zz_notas-arquivadas/`)*

| Critério | Resultado | Situação |
|---|---|---|
| 1. N-up correto (posição, escala, giro, recorte) | os dois protótipos geraram os 6 casos; melhor deslocamento (0,0) em 11/12. `pypdf` acertou de primeira; `pypdfium2` errou a matriz duas vezes antes de acertar (o «erra calado» previsto nos riscos) | ✅ |
| 2. Diferença ≤ 2/255 + ganho visível | 0,63 a 1,56 em 11/12; `vec` 2×2 Preencher 2,171 (1,29 com deslocamento de 2 px — arredondamento de posição do motor raster, não erro de recorte). **Olho do dono: «em todos é perceptível»** — o raster incomoda, inclusive nos cartazes | ✅ |
| 3. Arquivo ≤ 1/3 do raster sem perda a 300 DPI | PDF vetorial sintético: **0,008 a 0,036**. Cartazes do jsPDF: **0,890 a 3,892** — porque são **só foto JPEG** (0 caracteres de texto, ~225 ppi) e o jsPDF compartilha as imagens entre páginas, que a cópia duplica; com deduplicação (`pypdf`), 0,413 | ✅ no vetor, ❌ nos cartazes |

**Achados que ficam, qualquer que seja o desfecho:**
- **Biblioteca:** `pypdf` (wheel puro, `py3-none-any`) — acertou de primeira, honra o recorte pela CropBox sem pré-translação, deduplica imagens repetidas e permite embutir PNG (IDAT + Predictor 15) e JPEG **sem reencodar**. O `pypdfium2` serve, mas não embute PNG sem reencodar (saiu 1,41× o PNG) e não tem clip por objeto.
- **Nos cartazes (foto), o ganho é de qualidade, não de tamanho:** o vetorial guarda o JPEG original byte a byte; o raster reamostra 225 → 300 ppi e regrava. É essa a diferença que o dono viu.
- **Dedup é obrigatório** num modo vetorial: sem ele, PDF de gerador web que compartilha imagens sai até 3,9× maior.

**Leitura do critério:** pelo texto fixado antes de medir, C pede as três condições — o 3 falhou nos únicos PDFs reais medidos, que **não eram vetoriais**. O próprio «melhor argumento contra» desta análise previa isso («outra ferramenta, como Figma ou Affinity, pode ter perfil diferente»). O dono tem agora PDFs reais do Figma em `../este/`. **Não mudar o critério; medir a fonte certa:** a sonda 2 roda o critério 3 nos PDFs do Figma. Se passar, C; se não, B. A decisão final continua sendo do dono.

## Medição pedida 2 *(para o Claude Code — não é WO: não edita o repo, não commita)*

Mesmas regras da medição 1 (número cru + comando; `USERPROFILE`/`HOME` temporários; `pypdf` só em pasta temporária; relatório em `../AAMMDD-HHMM-code-printimposer-probe-vetorial2.txt`; recortes em `../261104-SONDA-vetorial/figma/`). Só o protótipo **`pypdf`**, com `compress_identical_objects(remove_identicals=True, remove_orphans=True)` antes de salvar.

Insumos (só leitura): os 5 PDFs de `../este/` (`260528-Fecha mes.pdf`, `260528-Fecha mes-1.pdf`, `A4-.pdf`, `OFERTAS 2xx.pdf`, `OFERTAS 5x.pdf`). Medido pelo chat por contagem de bytes, a confirmar: produtor «Figma», PDF 1.7, 1 página A4 cada, 0 `/DCTDecode`, 0 `/FontFile*`, 2 `/Subtype /Image` (Flate) por arquivo, operadores de texto presentes. Os `.png` homônimos são os exports PNG do mesmo frame — use-os como referência do que o dono vê.

1. **Inventário por arquivo:** caracteres extraíveis (`count_chars`); objetos por tipo (texto, path, imagem, form); as 2 imagens: px, caixa em pt, % da página, filtro; o texto é fonte (Type3? sem embutir?) ou contorno.
2. **Folhas:** 1×2 com Auto-Rotate e 2×2 Preencher (mesmas margens da sonda 1), com os 5 PDFs como entrada (repita para fechar a grade).
3. **Critério 3:** bytes do vetorial (com dedup) × raster sem perda do app a 300 DPI, mesma grade; razão.
4. **Critério 2:** diferença média por pixel (render 300 DPI) e recortes 600 DPI de um trecho com texto, raster à esquerda e vetorial à direita, nomes como na sonda 1.
5. Tempo de geração de cada lado.

**O que esta sonda NÃO responde:** impressão no papel; leitor da gráfica; Affinity/Canva/Corel (só Figma).

