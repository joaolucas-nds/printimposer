# SPEC — F5 etapa 3: moldura (v1.9.0)

> Spec de feature. Escrita em 2026-11-10, depois do portão da moldura (DEC-018) e da 1.8.1 (núcleo separado, DEC-017).
> Alvo: v1.9.0. Estado: aprovada pelo dono (modelo B e catálogo inicial, 10/11), a implementar — pelo Claude Code, via `meta/workorders/261110-wo0015-f5-moldura.md`.
> Fecha o item «layout não-uniforme possível» do critério da F5.

## Problema

Toda folha é uma grade de células iguais. O dono quer, numa mesma folha, células de tamanhos diferentes. O caso de origem são duas fotos horizontais iguais e uma retrato alta. O uso real é o de um fotógrafo que monta, em segundos, várias molduras com uma série de fotos.

## Critérios de aceite (verificáveis)

### Escolher a moldura
- [ ] A zona fixa do topo passa a se chamar **«Layout»** e ganha, na primeira linha, o seletor `Layout:` com as opções `Grade` · `1 + 2` · `2 + 1` · `1 + 3` · `Destaque + 4` · `1 + 2 + 1`. O padrão é `Grade`.
- [ ] Com `Grade`, tudo é como na 1.8.1: Colunas, Linhas, «Aplicar valores digitados» e Atalhos. **A saída da grade não muda nem 1 byte** (hash contra a 1.8.1).
- [ ] Com uma moldura:
  - Colunas, Linhas, «Aplicar valores digitados» e Atalhos ficam **desativados**, mas mantêm os valores, e voltar a `Grade` os devolve como estavam;
  - aparece `Proporção (%):`, de 20 a 80 com padrão 50, com uma dica cinza que diz o que o número mede (tabela abaixo);
  - a miniatura ao lado desenha a moldura, com os slots numerados na ordem em que as imagens entram.
- [ ] `Layout` e `Proporção` vão nos presets e na configuração salva. Preset ou configuração da 1.8 (sem os campos) abre em `Grade` com 50%. Valor desconhecido também cai em `Grade`; proporção fora da faixa é ajustada.

### O catálogo (proporções da área útil, valem em retrato e em paisagem)

| Moldura | Forma | Slots (ordem de leitura) | `Proporção (%)` mede |
|---|---|---|---|
| `1 + 2` | uma alta à esquerda; duas empilhadas à direita | 3 | a largura da foto da esquerda |
| `2 + 1` | duas lado a lado em cima; uma larga embaixo | 3 | a altura da faixa de cima |
| `1 + 3` | uma larga em cima; três lado a lado embaixo | 4 | a altura da foto de cima |
| `Destaque + 4` | uma larga em cima; 2 × 2 embaixo | 5 | a altura do destaque |
| `1 + 2 + 1` | uma larga; duas lado a lado; uma larga | 4 | a altura da faixa do meio (as outras duas dividem o resto em partes iguais) |

### Folha, corte, sangria e marcas
- [ ] **Espaçamento:** entre partes lado a lado, vale o «Entre colunas»; entre partes empilhadas, o «Entre linhas». Margem externa como hoje.
- [ ] **Preenchimento:** os slots recebem as imagens em ordem de leitura, e todas as folhas do trabalho usam a mesma moldura. «Por folha», o contador de folhas e o `Preencher ▾` usam o número de slots da moldura.
- [ ] **Encaixe:** cada imagem é encaixada no **seu** slot, com o modo de ajuste, o Auto-Rotate (pela forma do slot) e a rotação por item. PDF e SVG são rasterizados já no tamanho e na orientação do slot, sem ampliação depois do render.
- [ ] **Guarda de qualidade:** mede cada imagem contra o slot em que ela cai. O «Ideal: ≥ … px» cita o slot da pior imagem.
- [ ] **Rodapé:** com moldura, a linha da célula vira `Células: {n} · menor {w} × {h} mm ({pw} × {ph} px @ {dpi} DPI)`. Com grade, nada muda.
- [ ] **Marcas de canto:** uma marca em cada ponta de **segmento de corte** que toca a borda da área útil, para fora dela, com comprimento, distância e espessura como hoje. A ponta que encosta noutro corte não leva marca, e marcas repetidas viram uma só.
  - Na `1 + 2` sem espaçamento são **11 marcas**: as 8 dos cantos da área útil (2 por canto), as 2 do corte vertical do meio (em cima e embaixo) e 1 do corte horizontal da direita (só na borda direita: a outra ponta encosta no corte vertical).
  - Com espaçamento > 0, cada borda de corte tem a sua marca, como na grade: o corte vertical do meio dá 4 (duas bordas × em cima e embaixo) e o horizontal da direita dá 2 (duas bordas × só à direita), somando **14**.
  - Os testes conferem as duas contagens.
- [ ] **Linhas atravessando:** na moldura, cada linha vai no meio do espaçamento daquela divisão e atravessa só o pedaço que a divisão corta. Onde esse pedaço encosta na borda da área útil, a linha segue até a borda do papel, como na grade.
- [ ] **Sangria:** como na 1.6.0. Em cada lado do slot, ela vai até a metade do espaçamento da divisão vizinha ou até a margem externa, e **nunca pinta pixel do slot vizinho** (teste por pixel). Os avisos âmbar da 1.6.0 e da 1.7.0 valem igual. O de espaçamento olha as divisões que a moldura tem em cada eixo.
- [ ] **Preview** idêntico à saída (mesmo `compose_page`).

### Geral
- [ ] Suíte verde com os testes novos; `/smoke` sem FALHOU.

## Decisões de design

### 1. Uma árvore no núcleo, uma chave no preset
- O catálogo mora em `imposer_core.py`: cada moldura é uma árvore de divisões, `("v" | "h", [(peso, filho), ...])`, em que o filho `None` é um slot, e os pesos são funções da proporção.
- O preset guarda **a chave e a proporção** (`layout`, `layout_ratio_pct`), não a árvore. É mais simples e não perde nada enquanto só existe o catálogo.
- Um editor de divisões, no futuro, ganha um campo próprio para a árvore (DEC-018, consequências).

### 2. A grade continua no caminho dela
- `sheet_geometry` com `layout == "grid"` segue **exatamente** o código da 1.6.0–1.8.1.
- A moldura ganha uma função nova, `frame_geometry(cfg)`, que devolve o mesmo `SheetGeometry`. O `sheet_geometry` delega a ela quando o layout não é grade.
- O `SheetGeometry` ganha, no fim, o campo `cuts: Tuple[Segment, ...] = ()`, com os segmentos de corte.
- No motor, `compose_page` tem dois ramos: o da grade fica intocado, e o da moldura usa o retângulo de cada slot (px arredondados por borda, uma vez, a partir de mm).
- O preço são dois ramos parecidos. O ganho é a grade **provadamente** idêntica, por hash.

### 3. Uma função pura para a árvore
`frame_cells(key, ratio_pct, rect, gap_x, gap_y) -> (cells, cuts)` percorre a árvore:
- em cada divisão, o comprimento útil é o lado menos os espaçamentos (`(n − 1) × gap`), repartido pelos pesos;
- `cells` sai em ordem de leitura;
- `cuts` traz as bordas de cada parte ao longo da divisão, atravessando o pedaço dividido.

Testável sem Tk nem Pillow.

### 4. `nup` e tamanhos de célula
- `LayoutConfig.nup()` devolve o número de slots da moldura, ou `cols × rows` na grade.
- Na grade, `cell_px` e `cell_mm` seguem como estão.
- Para a moldura há `slot_rects_px(dpi)` e `slot_rects_mm()`. O que hoje supõe uma célula única (guarda de qualidade, rodapé, caixa de render) passa a pedir o slot quando o layout não é grade.

### 5. Interface
- O seletor `Layout:` fica na zona fixa do topo, porque o layout muda a cada trabalho.
- A proporção é um campo numérico como os outros (`_num_entry`), e não um controle deslizante: um slider num CTk dentro do accordion se arrasta sem querer ao rolar.
- Atributos novos com prefixo (FIX-003).

## Fora de escopo
- Editor de divisões (dividir/juntar slots), arranjo automático por tamanho físico, molduras diferentes por folha e molduras definidas pelo usuário.
- Marcas nos cantos internos.
- Desenhista vetorial.
- Mudar a grade.

## Passos
1. Catálogo, `frame_cells` e `frame_geometry` (cortes, marcas, sangria, avisos), com testes.
2. Campos `layout` e `layout_ratio_pct` (config, preset, `from_dict`, `nup`).
3. Motor: ramo da moldura em `compose_page`, guarda de qualidade por slot, caixas de render por slot, linhas atravessando por segmento.
4. UI: seletor, proporção com dica, controles da grade desativados, miniatura da moldura, rodapé.
5. Hash da grade contra a 1.8.1; README; `/smoke`; roteiro do dono.
