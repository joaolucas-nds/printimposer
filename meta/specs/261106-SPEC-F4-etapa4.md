# SPEC — F4 etapa 4: marcas de canto e sangria (v1.6.0)

> Spec de feature. Escrita em 2026-11-06, depois do portão da etapa 3 (opção B, `meta/analises/261104-ANALISE-portao-vetorial.md`).
> Alvo: v1.6.0. Estado: aprovada pelo plano da escada C, a implementar — pelo Claude Code, via `meta/workorders/261106-wo0010-f4-etapa4.md`.
> Fecha a F4: com ela, os três itens do critério de conclusão da fase (PDF como fonte, marcas e sangria, compressão) existem.

## Problema

Hoje a única guia de corte são **linhas que atravessam a folha** no meio do espaçamento (DEC-005). Elas riscam por cima da arte quando o espaçamento é zero, não marcam as duas bordas quando há espaçamento, e não dizem onde está o corte de verdade. E não existe **sangria**: arte com fundo colorido até a borda deixa um fio branco se o corte desviar 0,5 mm — o defeito mais comum de impressão de cards.

## Fundamento (pesquisa de 06/11)

| Achado | Fonte | Aplicação |
|---|---|---|
| Sangria de **3 mm por lado**; 4–5 mm se o corte for manual e menos preciso | [Cursa — margens, sangria e marcas de corte](https://cursa.app/pt/pagina/margens-sangria-e-marcas-de-corte-na-papelaria-personalizada) | padrão 3 mm |
| Marcas com **3–5 mm** de comprimento, **2–3 mm** de distância do corte, traço **0,25–0,5 pt** | idem | padrões 4 mm / 3 mm / 0,25 pt |
| Em lote (cartões), os itens ficam **encostados** e as marcas vão **só na borda externa da grade**, alinhadas a cada corte; 5 mm, 0,25 pt, 100% preto | [Tuts+ — impor cartões para impressão digital](https://design.tutsplus.com/tutorials/quick-tip-how-to-impose-business-cards-for-digital-printing-with-indesign--vector-4290) | marcas na margem externa, uma por linha de corte |
| Com sangria, é preciso **marca dupla** — uma para cada borda de corte — e espaço entre os itens | idem | dois cortes por espaçamento |
| Marca não pode cair dentro da sangria (senão é cortada junto ou aparece na arte) | prática corrente nos fóruns de pré-impressão (ex.: Adobe Community, «print marks showing up in the bleed area») | distância efetiva = maior entre a escolhida e a sangria |

## Critérios de aceite (verificáveis)

- [ ] A seção **«Linhas de corte»** passa a se chamar **«Corte e sangria»** (a chave persistida continua `corte`).
- [ ] **Guia de corte** com três opções: `Nenhuma` · `Linhas atravessando` (o comportamento de hoje, inalterado) · `Marcas de canto`. Preset e configuração da 1.5 com `cut_lines = true` abrem em `Linhas atravessando`; com `false`, em `Nenhuma`.
- [ ] Com **Marcas de canto**: para cada linha de corte da grade (cada borda de célula que vira corte), um traço curto **na margem externa da folha**, nas duas pontas da linha — nunca dentro da área das células nem da sangria. Com espaçamento 0, células vizinhas dividem um corte (uma marca); com espaçamento > 0, cada borda tem a sua (duas marcas).
- [ ] Comprimento, distância do corte e espessura configuráveis; padrões **4 mm**, **3 mm** e **0,25 pt**; cor **preta 100%**. A distância efetiva nunca é menor que a sangria.
- [ ] Quando a margem externa não comporta distância + comprimento, as marcas **não são cortadas pela metade em silêncio**: aviso âmbar na seção («A margem externa precisa de pelo menos X mm para as marcas») e confirmação antes de gerar, como a guarda de qualidade.
- [ ] **Sangria** em mm (padrão 0 = desligada) com dois modos:
  - `Estender a borda (espelhar)` — a arte é encaixada no corte como hoje e a faixa de sangria é preenchida espelhando a borda da célula;
  - `A arte já tem sangria` — a arte é encaixada na célula **aumentada pela sangria** (a parte de dentro cai no corte, a borda sobra para fora).
- [ ] A sangria nunca invade a célula vizinha: entre células ela vai até **metade do espaçamento**; na borda externa, até a margem. Se o espaçamento for menor que 2× a sangria, aviso âmbar com o valor que de fato coube.
- [ ] Linhas atravessando + sangria > 0 → aviso cinza: «com sangria, use marcas de canto: as linhas riscam a sangria».
- [ ] Preview mostra marcas e sangria exatamente como a saída (mesmo `compose_page`).
- [ ] A guarda de qualidade, no modo `A arte já tem sangria`, mede a fonte contra a célula aumentada.
- [ ] Suíte verde com os testes novos; `/smoke` sem FALHOU.

## Decisões de design

### 1. Geometria separada do desenho
Uma função pura (ex.: `sheet_geometry(cfg) -> SheetGeometry`) calcula **em mm**, a partir de papel, grade, margens, espaçamentos, sangria e marcas: o retângulo de corte de cada célula; o retângulo de sangria de cada célula já recortado pelo espaço disponível; as posições únicas de corte em X e em Y; a lista de segmentos de marca; e a lista de avisos. O motor raster converte para px no DPI pedido (`override_dpi` incluído) na hora de desenhar. **Por quê:** é a mesma geometria que o desenhista vetorial da F5 vai usar (portão B) — calcular em mm agora evita refazer depois, e a função pura é testável sem Tk.

### 2. Onde ficam as marcas
**Só na margem externa da folha, uma por ponta de cada linha de corte** — o padrão de cartões em lote. Marca em canto interno (entre células) fica **fora** desta etapa: com espaçamento pequeno ela cairia sobre a arte vizinha. Regra de posição: para cada X de corte, dois traços verticais — um acima da grade e um abaixo —, começando a `distância efetiva` da borda da grade e com o `comprimento` escolhido; idem para cada Y de corte, à esquerda e à direita.

### 3. Sangria — os dois modos
- **Espelhar:** depois de compor a célula no tamanho de corte (como hoje), acrescentar em volta faixas de largura `b` (limitada pelo espaço) com a imagem da célula espelhada na borda. Funciona com raster, PDF e SVG, e com qualquer modo de ajuste (onde o modo Ajustar deixa fundo, o espelho é fundo).
- **A arte já tem sangria:** a caixa de encaixe da fonte vira `(cw + 2b) × (ch + 2b)` centrada na célula; a fonte é encaixada nela com o modo de ajuste escolhido (fontes vetoriais rasterizadas já nesse tamanho, na orientação final), e o resultado é recortado pela área de sangria disponível.
- Sem sangria (`b = 0`): nada muda em relação à 1.5.

### 4. Campos novos (LayoutConfig e PRESET_FIELDS)
`cut_guide` (`"none"` · `"lines"` · `"marks"`, substitui `cut_lines`), `mark_length_mm` (4.0), `mark_offset_mm` (3.0), `mark_width_pt` (0.25), `bleed_mm` (0.0), `bleed_mode` (`"mirror"` · `"included"`, padrão `"mirror"`). Compatibilidade: `from_dict` com `cut_lines` e sem `cut_guide` converte (`true → "lines"`, `false → "none"`). Espessura em px = `max(1, round(pt × dpi / 72))`. Valores fora de faixa (comprimento 1–15 mm, distância 0–15 mm, espessura 0,1–2 pt, sangria 0–10 mm) são ajustados ao limite.

### 5. Interface (seção «Corte e sangria»)
De cima para baixo: **Guia** (`Nenhuma` / `Linhas atravessando` / `Marcas de canto`) → com Linhas, os controles de hoje (estilo, espessura, traço, cor) → com Marcas, **Comprimento (mm)**, **Distância do corte (mm)**, **Espessura (pt)** → **Sangria (mm)** → **Modo da sangria** (só aparece com sangria > 0) → os avisos, em âmbar ou cinza. Rótulos exatos na WO.

## Fora de escopo
- Marcas em cantos internos (entre células).
- Marcas de registro, barras de cor, informação de página (slug).
- Margem de segurança desenhada (guia interna).
- Desenhista vetorial (F5, portão B).
- Linhas atravessando com sangria «inteligente» (continuam como hoje, com o aviso).

## Passos
1. `sheet_geometry` em mm + testes (contagens e posições de marca, recorte da sangria, avisos).
2. Campos novos + compatibilidade de `from_dict` + presets.
3. Desenho raster: marcas; sangria espelhada; sangria incluída (caixa aumentada, inclusive PDF/SVG na orientação final).
4. Guarda de qualidade no modo incluída.
5. UI da seção + avisos + confirmação antes de gerar.
6. README + `/smoke` + roteiro do dono.
