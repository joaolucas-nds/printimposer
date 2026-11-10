# SPEC — F5 etapa 2: tiragem (v1.8.0)

> Spec de feature. Escrita em 2026-11-10, depois do roteiro da 1.7.0 («tudo certo»).
> Alvo: v1.8.0. Estado: aprovada pelo plano da escada C (`meta/analises/261109-ANALISE-ordem-f5.md`), a implementar — pelo Claude Code, via `meta/workorders/261110-wo0013-f5-tiragem.md`.
> Fora do critério de conclusão da F5: são os dois ganhos baratos de uso diário que a escada pôs antes da moldura.

## Problema

**Rotação.** O Auto-Rotate é global. Ele acerta a orientação de quase tudo, mas não resolve dois casos:
- arte de ponta-cabeça: um card exportado invertido, ou uma foto do celular sem a marcação de orientação;
- quem quer uma imagem girada para o outro lado (270° em vez de 90°).

Hoje, o único jeito é girar o arquivo em outro programa e importá-lo de novo.

**Tiragem.** Com 7 imagens num 2×2, a segunda folha sai com uma célula vazia. Para completá-la, ou para tirar «10 folhas destes cards», o dono faz a conta de cabeça e digita a quantidade item por item.

## Critérios de aceite (verificáveis)

### Rotação por item
- [ ] Cada linha da lista ganha um botão `⟳` que gira a imagem 90° no sentido horário a cada clique: `0° → 90° → 180° → 270° → 0°`.
- [ ] Com rotação diferente de 0°, a linha mostra o ângulo ao lado do nome (`  · 90°`) e a miniatura aparece girada.
- [ ] **0° segue o Auto-Rotate global**, como hoje. **90°, 180° e 270° são exatos:** a imagem sai girada desse tanto em relação ao arquivo, e o Auto-Rotate **não** age sobre ela.
- [ ] Vale para raster, PDF e SVG. As fontes vetoriais continuam rasterizadas **já na orientação final**, sem ampliação depois do render (a lição da FIX-006).
- [ ] A guarda de qualidade mede a fonte na orientação efetiva do item.
- [ ] O preview mostra exatamente a saída (mesmo `compose_page`).
- [ ] A rotação vai com o item: reordenar, mudar a quantidade ou soltar novos arquivos não a perde. Como a lista não é salva entre sessões, a rotação também não é.

### Preencher folhas
- [ ] A barra da lista ganha, depois de «+ Pasta», o botão `Preencher ▾`, que abre um menu com duas opções.
- [ ] **«Completar a última folha»:** soma às quantidades as cópias que faltam para fechar a última folha. As cópias são distribuídas uma por item, na ordem da lista, a partir do primeiro, dando quantas voltas forem precisas.
  - Exemplo: 7 cópias em 2×2 → faltam **1**, e a 1ª imagem ganha +1. Com 5 cópias em 3×3 vindas de 2 imagens, faltam 4: +2 para cada uma.
  - Se a última folha já está cheia, aparece «A última folha já está cheia.» e nada muda.
- [ ] **«Exatamente N folhas…»:** pede N (1–999) num diálogo e **troca** as quantidades para que o total seja `N × cópias por folha`, igual para todos os itens. Quando a divisão não é exata, os primeiros da lista recebem uma cópia a mais.
  - Antes de trocar, pede confirmação com os números: «Isto troca as quantidades: {itens} imagens em {N} folha(s) de {nup} = {total} cópias. Continuar?»
  - Se há mais itens que lugares (`itens > N × nup`), avisa «Em {N} folha(s) de {nup} cabem {total} cópias, e a lista tem {itens} imagens.» e nada muda.
- [ ] Com a lista vazia, as duas opções mostram «A lista está vazia.» e nada muda.
- [ ] Depois de preencher, os campos «Qtd», a contagem de cópias, o contador de folhas e o preview refletem as quantidades novas (o mesmo `on_change` de sempre). As quantidades continuam editáveis à mão.

### Geral
- [ ] Suíte verde com os testes novos; `/smoke` sem FALHOU.

## Decisões de design

### 1. Regra da rotação: «0° automático, o resto exato»
Duas regras foram consideradas:
- **Somar a manual à automática.** Descartada: com Auto-Rotate ligado, girar 90° uma imagem retrato numa célula retrato a deixaria paisagem, e o Auto-Rotate a giraria de volta. O clique pareceria não fazer nada.
- **«0° automático, o resto exato».** Escolhida: os quatro estados cobrem todos os casos. Quem quer que o app decida deixa em 0°. Quem quer um lado específico escolhe 90°, 180° ou 270°, e é isso que sai.

O único caso sem atalho é «sem rotação e sem Auto-Rotate só para este item». Ele é raro, e desligar o Auto-Rotate global cobre.

### 2. Onde a rotação mora
- `ImageEntry.rotation` (0/90/180/270, sentido horário).
- `SourceRef` ganha um terceiro campo `rotation: int = 0`, com padrão, para não quebrar quem cria `SourceRef(path)` ou `SourceRef(path, page)`.
- `ImageEntry.ref` passa a levar a rotação, e o motor a recebe pelo mesmo caminho que já recebe a página.
- Uma função pura decide o giro efetivo: `effective_rotation(src_w, src_h, cell_w, cell_h, auto_rotate, manual) -> int`.
  - `manual ≠ 0` → devolve `manual`.
  - `manual = 0` → devolve 90 se o Auto-Rotate está ligado e a orientação da fonte difere da célula; senão, 0.
- `vector_render_box`, `_place_image`, `pdf_inner_ratio` e a guarda de qualidade passam a usar essa função, e não `auto_rotate` direto. Com 90° ou 270° a caixa de render é `(ch, cw)`; com 0° ou 180°, `(cw, ch)`.
- **Sentido:** o `Image.rotate` do Pillow gira no sentido **anti-horário**. 90° horário é `rotate(-90, expand=True)`. O giro do Auto-Rotate continua sendo o de hoje (`rotate(90, expand=True)`), para a saída das imagens com 0° não mudar nem 1 px.

### 3. Preencher mexe nas quantidades, à vista
Um «modo preencher» escondido na configuração mudaria a saída sem que a lista mostrasse por quê. Mudar as quantidades deixa tudo visível e editável, e não muda o motor. Duas funções puras:
- `fill_last_sheet(quantities, nup) -> List[int]`;
- `fill_n_sheets(n_items, nup, n_sheets) -> Optional[List[int]]` (devolve `None` quando não cabe).

### 4. Nomes do Tkinter
Atributos novos na `ImageRow` e no `ImageListPanel` levam prefixo (`_rot_btn`, `_fill_menu`…). O diálogo de N usa `tkinter.simpledialog.askinteger` (FIX-003, armadilha 3).

## Fora de escopo
- Rotação em ângulos livres e espelhamento.
- Rotação aplicada a vários itens de uma vez (seleção múltipla).
- Salvar a lista, e com ela a rotação, entre sessões.
- «Preencher» como modo permanente na configuração ou nos presets.

## Passos
1. `effective_rotation`, `fill_last_sheet` e `fill_n_sheets`, com testes.
2. `SourceRef.rotation`, `ImageEntry.rotation` e `ref`; motor (`_place_image`, caixa de render vetorial), `pdf_inner_ratio` e guarda de qualidade passando pela função.
3. Botão `⟳`, rótulo do ângulo e miniatura girada na `ImageRow`.
4. `Preencher ▾` com as duas opções e os diálogos.
5. README, `/smoke` e roteiro do dono.
