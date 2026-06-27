# CONTEXT.md — PrintImposer

> Arquivo **estável**. O assistente lê no início de cada sessão para se ambientar.
> Muda pouco: só em alteração estrutural (stack, arquitetura, escopo, nova armadilha descoberta).
> Mantenha enxuto — descreve o que o projeto É, não o que está acontecendo agora (isso é o STATUS).

---

## Visão Geral
PrintImposer é uma ferramenta desktop de **imposição de páginas** para impressão em massa. O usuário seleciona várias imagens (tipicamente cards A6 exportados do Figma), escolhe um layout N-up (ex.: 4 por folha) e gera um PDF/PNG/JPEG/TIFF pronto para imprimir — sem arrastar arquivo por arquivo no diálogo do Windows. Foco em uso pessoal/profissional de quem produz cards e precisa agrupá-los em folhas A4 com mínimo esforço repetido.

## Stack Tecnológica
- **Linguagem:** Python 3.9+ (testado até 3.14 no Windows do usuário)
- **GUI:** CustomTkinter (sobre Tkinter) — tema escuro
- **Imagem/composição:** Pillow (PIL) — resize LANCZOS, composição RGBA, export PDF/PNG/JPEG/TIFF
- **Concorrência:** `threading` (geração e preview fora da UI thread)
- **Distribuição:** script único, rodado com `python print_imposer.py`
- **Testes:** nenhum automatizado ainda (ver STATUS/ROADMAP). Engine é testável headless via stub de tkinter.

## Estrutura do Projeto
```
PrintImposer/
├── print_imposer.py   # TODO o app em um arquivo (~1190 linhas)
└── README.md          # Documentação de uso (guia completo)
```
O arquivo único está organizado em camadas internas (ver Arquitetura).

## Convenções de Código
- **Nomes:** arquivos, funções e variáveis em **inglês**; comentários em **PT-BR**.
- **Comentários:** docstring em função pública; comentário explica o PORQUÊ, não o QUÊ.
- **Commits:** Conventional Commits, descrição no imperativo curto em PT-BR (`feat(engine): ...`).
- **Estilo:** legibilidade primeiro; performance só se medida.

## Como a imposição funciona (CRÍTICO)
> Mecanismo central. Consultar antes de mexer na composição.

O fluxo de uma folha (`ImpositionEngine.compose_page`):
1. **Página em px** = `tamanho_mm × DPI / 25.4`. Ex.: A4 a 300 DPI → 2480×3508 px.
2. **Grid** vem de `NUP_LAYOUTS[nup_key]` → `(cols, rows)`. O nº de slots por folha é `cols×rows`.
3. **Célula (slot)** = `(largura_página − 2·margem_externa − (cols−1)·margem_entre) / cols`, idem para altura. Tudo em px.
4. Para cada slot, a imagem é colocada por `_place_image` segundo o modo de **ajuste**:
   - `fit` — cabe inteira, sobra cor de fundo (preserva proporção);
   - `fill` — preenche e recorta o excesso (preserva proporção, corta);
   - `stretch` — força o tamanho exato (distorce).
5. **Auto-Rotate**: se a orientação da imagem (retrato/paisagem) ≠ orientação do slot, gira 90°.
6. **Linhas de corte** (opcional): desenhadas DEPOIS da composição, atravessando a folha entre colunas/linhas. Estilos sólida/tracejada/pontilhada.

O preview usa o MESMO `compose_page` com `override_dpi=72` e depois reduz — garante fidelidade visual ao resultado final, só que rápido. Ver DEC-004.

A relação **qualidade × DPI**: a folha é rasterizada no DPI escolhido. Se a imagem-fonte tem menos pixels que a célula, há **upscale** (perda). Para A6 a 300 DPI a fonte deve ter ≥ 1240×1748 px. Detalhe completo em HISTORICO §1.

## Arquitetura — pontos-chave
- **Separação Engine × GUI** — `ImpositionEngine` não depende de Tkinter; dá para testar headless. Ver DEC-004.
- **Raster, não vetorial (v1)** — composição via Pillow; PDF é imagem rasterizada. Ver DEC-001.
- **CustomTkinter para a UI** — visual moderno com baixo custo. Ver DEC-002.
- **Arquivo único** — simplicidade de distribuição. Ver DEC-003.
- **Linhas de corte atravessam a folha (v1)** — marcas de canto profissionais ficaram para depois. Ver DEC-005.

## Armadilhas Conhecidas (o que NÃO fazer)
> Cada armadilha já custou tempo uma vez. O que parece certo → por que morde → o certo.

1. **Passar um `CTkScrollableFrame` direto para um `tk.PanedWindow`** — parece natural, mas o CTk cria um canvas aninhado que o PanedWindow não adota como filho → `TclError: can't add ...`. → **Envolva em um `tk.Frame` simples** antes do `.add()`. Ver FIX-001.
2. **Confiar que "exportar 4× no Figma" = 300 DPI** — só vale se o frame-base tiver os pixels certos. → Mire o **alvo em pixels** (≥1240×1748 para A6), não a escala. Ver HISTORICO §1.
3. **Mexer no DPI dentro de `compose_page` sem restaurar** — o método troca `cfg.dpi` temporariamente para preview; sempre restaure no `finally`/fim. Já está tratado; não remova a restauração.
4. **Achar que SVG entra direto** — Pillow não rasteriza SVG. → Exporte PNG do Figma, ou (futuro) converta via cairosvg/Inkscape. Ver IDEAS.
5. **Linhas de corte finas em saída lossless** — inflam o arquivo (detalhe de alta frequência). → Para arquivos enxutos, prefira marcas de canto (futuro) ou borda feita no Figma. Ver DEC-005 e ROADMAP F3.

## Contexto de Produto
- **Usuário-alvo:** quem produz cards/artes em lote no Figma e imprime em casa ou manda para gráfica.
- **Dor que resolve:** agrupar dezenas de imagens em folhas A4 sem trabalho manual repetido a cada impressão.
- **O que é sucesso:** "selecionar a forma de impressão → selecionar as imagens → gerar" — esforço mínimo, qualidade preservada do export do Figma.
- **O que o projeto deliberadamente NÃO é:** não é editor de imagem, não é software de prepress completo (sem separação de cores, trapping, registro multi-plate, booklet/imposição de cadernos). Foco em N-up plano para corte.
