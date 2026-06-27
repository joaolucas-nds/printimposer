# DECISIONS.md — Registro de Decisões

> Arquivo que **cresce devagar**. Guarda o PORQUÊ — o que o código sozinho não conta.
> Duas naturezas: **DEC** (decisões de arquitetura/design) e **FIX** (bugs graves resolvidos, para não repetir).
> Não reescreva entradas antigas; se uma decisão for substituída, marque «SUPERADA por DEC-N» e adicione a nova.
> Quando passar de ~700 linhas, mova as mais antigas para `DECISIONS-archive.md`.

---

## DEC-001 — Imposição raster via Pillow (não vetorial) no v1
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
A entrada são imagens (PNG do Figma). Era preciso escolher entre compor as folhas como raster (juntar imagens numa imagem maior) ou montar um PDF vetorial posicionando páginas/objetos.

### Decisão
v1 compõe cada folha como uma imagem PIL e exporta (PDF/PNG/JPEG/TIFF) a partir dela.

### Alternativas consideradas
- **PDF vetorial (reportlab/pypdf posicionando páginas PDF)** — preserva qualidade perfeita e gera arquivos minúsculos, mas exige entrada em PDF/vetor e mais complexidade. Adiado para o ROADMAP (F3) como o maior salto de qualidade futuro.
- **Render via navegador/HTML→PDF** — overkill, dependência pesada.

### Consequências
- Simples e direto para entrada em imagem; o que se vê no preview é exatamente o que sai.
- Qualidade limitada pelo DPI de rasterização e pelos pixels da fonte (risco de upscale).
- Linhas finas e marcas inflam o arquivo em saída lossless (ver DEC-005).
- Abre a porta para a dúvida do usuário sobre "compressão": a folha é reamostrada no DPI escolhido — daí a importância da guarda de qualidade (STATUS backlog) e do caminho vetorial futuro.

---

## DEC-002 — CustomTkinter para a GUI
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
Precisávamos de interface desktop nativa no Windows, com visual moderno, sem servidor nem build web.

### Decisão
Usar CustomTkinter (sobre Tkinter), tema escuro.

### Alternativas consideradas
- **Tkinter puro** — feio por padrão, mais trabalho de estilo.
- **PyQt/PySide** — mais poderoso, porém licença/peso e curva maiores para um utilitário pessoal.
- **Web (Electron/PyWebView)** — distribuição e footprint piores para o caso.

### Consequências
- Visual agradável com pouco esforço; widgets prontos (OptionMenu, ScrollableFrame, ProgressBar).
- Herda limitações do Tkinter e algumas incompatibilidades de aninhamento (ver FIX-001).
- Drag-and-drop de arquivos exige extensão externa (tkinterdnd2) com wrapper — viável, planejado em IDEAS.

---

## DEC-003 — Arquitetura em arquivo único
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
Utilitário pessoal, distribuído como "baixe e rode".

### Decisão
Todo o app em `print_imposer.py`.

### Alternativas consideradas
- **Pacote multi-módulo** — mais organizado para crescer, porém atrito para distribuir/rodar.

### Consequências
- Fácil de copiar e executar (`python print_imposer.py`).
- Se o projeto crescer muito (entrada vetorial, i18n, perfis), pode valer modularizar — reavaliar em F3.

---

## DEC-004 — Separar `ImpositionEngine` da camada de GUI
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
Lógica de composição precisa ser confiável e, idealmente, testável sem abrir janela.

### Decisão
`ImpositionEngine` (núcleo) não importa nem depende de Tkinter; recebe `entries` + `LayoutConfig` e produz imagens/arquivos. O preview reaproveita `compose_page` com `override_dpi=72`.

### Alternativas consideradas
- **Lógica acoplada nos widgets** — mais rápido de escrever, impossível de testar headless e propenso a duplicação preview×geração.

### Consequências
- Dá para testar o engine com um stub de tkinter (já validado nesta forma).
- Preview e geração final compartilham o mesmo caminho de código → o preview é fiel.
- Custo: o engine troca `cfg.dpi` temporariamente no preview; exige restaurar o valor (armadilha registrada em CONTEXT §3).

---

## DEC-005 — Linhas de corte atravessando a folha no v1 (marcas de canto adiadas)
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
Para guiar o corte manual, era preciso algum tipo de marca. O padrão profissional são marcas de canto (ticks curtos no gutter), mas são mais trabalhosas de posicionar.

### Decisão
v1 desenha linhas contínuas entre colunas e linhas, atravessando a folha (sólida/tracejada/pontilhada).

### Alternativas consideradas
- **Marcas de corte de canto (padrão de indústria)** — não atravessam a arte, pesam quase nada no arquivo, mais profissionais. Exigem cálculo por slot e um gutter mínimo. Adiado para ROADMAP F3.
- **Sem marcas, confiando na borda feita no Figma** — já é uma alternativa válida hoje (o usuário pode desenhar a borda no frame).

### Consequências
- Funciona e é simples; cobre o caso "quero uma guia visual".
- Linhas atravessando a arte e em saída lossless aumentam o tamanho do arquivo (ver DEC-001).
- Marcas de canto profissionais + caminho vetorial (F3) resolvem qualidade e peso de uma vez.

---

## DEC-006 — Saída PDF por rasterização no DPI configurado
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
Era preciso um formato "manda pra gráfica / imprime direto". PDF é o candidato natural.

### Decisão
Gerar PDF a partir das imagens compostas via `PIL.Image.save(..., "PDF", resolution=dpi)` (multipágina com `append_images`).

### Alternativas consideradas
- **reportlab** — controle fino de PDF, mas para folha já rasterizada não agrega sobre o save do PIL.
- **img2pdf** — embute bytes da imagem sem recompressão (ótimo para qualidade), porém o nosso caso compõe uma imagem nova por folha, então o ganho é menor; vale avaliar para escolher compressão explícita.

### Consequências
- Caminho mais curto para PDF multipágina.
- Não expõe escolha de compressão (lossless × JPEG/qualidade) — exatamente a dúvida do usuário sobre "níveis de compressão". Registrar como melhoria (IDEAS) e tratar em F2/F3.

---

## FIX-001 — `tk.PanedWindow` não adota `CTkScrollableFrame` como filho
**Data:** 2026-06-15 *(diagnóstico/correção)* · *(bug presente desde o v1.0.0)*

- **Sintoma:** ao abrir o app no Windows (Python 3.14), crash imediato:
  `_tkinter.TclError: can't add .!panedwindow.!panedwindow.!ctkframe.!canvas.!ctkscrollableframe to .!panedwindow.!panedwindow`.
- **Causa raiz:** `CTkScrollableFrame` cria internamente um canvas aninhado. Ao passá-lo diretamente para `tk.PanedWindow.add()`, o PanedWindow tenta adotar como filho um widget que não é descendente direto dele na hierarquia esperada → o Tk recusa. O mesmo vale para qualquer painel CTk com canvas interno colocado direto no PanedWindow.
- **Solução:** envolver cada painel em um `tk.Frame` simples (com `rowconfigure/columnconfigure` peso 1) e adicionar ESSE frame ao PanedWindow; o conteúdo CTk vai dentro do wrapper via `grid(sticky="nsew")`. Aplicado aos três painéis (lista, configurações, preview).
- **Lição:** ao misturar widgets CustomTkinter com geometria nativa do Tkinter (PanedWindow, e por tabela outros gerenciadores que assumem filiação direta), **sempre interponha um `tk.Frame` neutro**. Virou armadilha nº1 em CONTEXT.
