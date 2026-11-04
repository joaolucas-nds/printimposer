# CHANGELOG

> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).
> **Cresce**: entradas novas no topo. Registra só o que foi de fato concluído/entregue.

## [Não lançado]
- (nada pendente.)

---

## [1.4.0] — 2026-11-04
Fase F4, etapa 2 (SPEC-F4-etapa2). Implementada pelo Code (wo0007); a conferência na tela e com um PDF do Figma está com o dono.

### Adicionado
- Entrada PDF via `pypdfium2` (opcional, sondada por render real — FIX-002): cada página vira um item da lista (`arquivo.pdf · p. 2/5`), com miniatura, quantidade, ▲ ▼ e ✕. Sem o pacote, `.pdf` some do seletor e do «+ Pasta» e o app abre como na 1.3.
- A página é rasterizada no tamanho da célula, **já na orientação final**: com Auto-Rotate e orientação diferente da célula, a caixa de render é `(ch, cw)`. Nenhuma ampliação depois do render; fundo branco opaco.
- PDF com mais de 50 páginas pede confirmação; PDF com senha, corrompido ou sem páginas é pulado, e o lote termina com **uma** mensagem listando os pulados e o motivo.
- Item de PDF fica fora da guarda de qualidade (limite: PDF que só embrulha uma imagem raster pequena continua pequeno).
- Cabeçalho `v1.4.0 · SVG: … · PDF: …`; `Ajuda › Sobre` lista «PDF sim/não» em «Formatos extras».
- 15 testes headless (85 → 100): 9 com stub do renderizador e 6 com `pypdfium2` real (pulados sem ele).

### Modificado
- Referência de fonte (`SourceRef`: caminho + página) atravessa o motor (`_expand`, `compose_page`, `open_source`); `compose_page` continua aceitando caminhos puros. Cache de miniatura chaveado também pela página.
- `VERSION` para 1.4.0.

### Documentação
- README atualizado para a 1.3: PDF sem perda por padrão e compressão/qualidade por formato, espaçamento entre colunas e entre linhas, linha da folha no rodapé, AVIF nativo e HEIC opcional, e por que o PDF ficou maior que na 1.2.

---

## [1.3.0] — 2026-11-03
Fase F4, etapa 1 (SPEC-F4-etapa1, DEC-014). Implementada pelo Code (wo0005); a conferência do PDF sem perda num leitor de PDF está com o dono.

### Adicionado
- Escritor de PDF próprio (`write_pdf`, só biblioteca padrão): embute o fluxo Deflate do PNG da folha (`/FlateDecode`, `/Predictor 15`) — PDF **sem perda** por construção. Modo JPEG embute os bytes do JPEG na qualidade escolhida (`/DCTDecode`).
- Seção Saída: «Compressão» (PDF: Sem perda · JPEG) e «Qualidade» (50–100, para JPEG e PDF-JPEG); campos `pdf_compression` e `jpeg_quality` no config e nos presets.
- Espaçamento independente: «Entre colunas (mm)» e «Entre linhas (mm)» (`margin_between_x_mm`, `margin_between_y_mm`); as linhas de corte acompanham cada eixo.
- Rodapé: linha «Folha: L × A px · N MB bruto».
- Entrada AVIF (quando o Pillow lê) e HEIC/HEIF (quando o `pillow-heif` está instalado); `Ajuda › Sobre` mostra «Formatos extras».
- 22 testes headless (63 → 85): estrutura do PDF, `IDAT` byte a byte, `xref`, qualidade, espaçamento X/Y, compatibilidade com a 1.2, AVIF/HEIC.

### Modificado
- `margin_between_mm` virou `margin_between_x_mm` + `margin_between_y_mm`; config e presets da 1.2 carregam com X = Y = valor antigo.
- Linhas do rodapé com altura fixa menor para caberem as quatro dentro dos 84 px.
- `VERSION` para 1.3.0.

### Corrigido
- PDF saía JPEG por dentro sem o usuário escolher (DEC-014; substitui a DEC-006).
- Rótulo do segundo destino de saída cortado a 1366×768 (agora «Salvar cópia em outro destino»).

### Documentação
- README reescrito para a 1.2: grade livre, painel em três zonas, menus e atalhos de teclado, guarda de qualidade, SVG opcional, atalho `.bat` na pasta-pai, local das configurações.

---

## [1.2.0] — 2026-11-03
Fase F3 (SPEC-F3-UI): painel de configuração reestruturado e menubar. Implementada pelo Code (DEC-012); a conferência visual do dono ainda está pendente.

### Adicionado
- Menubar `Arquivo · Opções · Ajuda` na topbar (botões + `tk.Menu.tk_popup` ancorado no botão), com `Ctrl+O`, `Ctrl+Shift+O` e `Ctrl+G` valendo com o foco em qualquer painel.
- `CollapsibleSection` (accordion): cabeçalho focável por `Tab` e acionável por `Espaço`/`Enter`; fechar usa `grid_remove()`, então os campos mantêm o estado.
- `sections_open` no `settings.json`: as seções abertas voltam ao reabrir o app. Arquivo da 1.1.x (sem a chave) cai no padrão, só `Saída` aberta.
- Diálogo `Opções › Criar atalho…` que explica o `.bat` antes de gerar e mostra interpretador e script; o seletor abre na pasta-pai da raiz do projeto (pedido do dono, 2026-07-23).
- `Ajuda › Guia rápido: Figma → impressão` (constante única `QUICK_GUIDE`) e `Ajuda › Sobre o PrintImposer`.
- `Opções › Restaurar configurações padrão` (mantém as pastas de entrada e saída).
- 15 testes headless (48 → 63): contrato do `sections_open`, rótulos e ligação dos menus, `initialdir` do atalho, `grid_remove` no accordion e teto da zona inferior.

### Modificado
- Painel central em três zonas: grade fixa no topo, accordion rolável (Papel, Ajuste, Margens, Corte, Saída; só Saída aberta por padrão) e resumo fixo embaixo (contador, célula e guarda de qualidade), com altura ≤ 84 px.
- Presets viraram o submenu `Opções › Presets`, reconstruído a cada abertura.
- `VERSION` para 1.2.0.

### Corrigido
- **Menu de presets não atualizava sem reiniciar:** o submenu é reconstruído a cada abertura, sem varrer a árvore de widgets.

### Removido
- Seções `Atalho` (`.bat`) e `Presets` do painel de configuração.

---

## [1.1.1] — 2026-07-22
Correções apontadas pelo primeiro smoke test da GUI (raia de validação, DEC-010).

### Corrigido
- **A 1.1.0 não abria.** `GridPreview` sobrescrevia `self._w`, que no Tkinter guarda o pathname Tcl do widget — toda chamada ao Tk virava `invalid command name "70"`. Renomeado para `_box_w`/`_box_h`. Ver FIX-003.
- **Folha gerada saía em 72 DPI sem aviso** quando o preview ainda estava compondo: `compose_page` mutava `cfg.dpi` num `LayoutConfig` compartilhado entre threads. O DPI virou parâmetro; não há mais mutação de estado compartilhado. Ver FIX-004.
- **Janela invadia a barra de tarefas**, escondendo o botão "Gerar Arquivos": a geometria usava a tela física em vez da área útil. Novo helper `_work_area()` com `SPI_GETWORKAREA` no Windows. Ver FIX-005.
- Miniaturas da lista passaram a usar `CTkImage` em vez de `ImageTk.PhotoImage`, eliminando o aviso do CustomTkinter e o borrão em telas com zoom 125%/150%.

### Modificado
- `VERSION` para 1.1.1 e realinhamento de 10 continuações de docstring que o re-indent do `replace_method` do ASU havia deslocado (cosmético, sem efeito na execução).

### Adicionado
- 8 testes de regressão (40 → 48): varredura AST contra colisão com nomes reservados do Tkinter, teste de corrida de DPI com thread concorrente, e verificação do contrato da área útil.

---

## [1.1.0] — 2026-07-19
Fase **F2 — Controle, persistência e janela** do ROADMAP, completa.

### Adicionado
- **Grade livre `colunas × linhas`** (DEC-009): qualquer combinação — 2×6, 5×3, 7×2 — sem editar código. A lista fixa `NUP_LAYOUTS` virou um menu de atalhos; o teto é 12×12.
- Miniatura do grid, desenhada ao vivo, para identificar o layout de relance.
- **Presets nomeados** em `~/.printimposer/presets.json`: guardam grade + papel + DPI + margens + corte + formato (não guardam caminhos de pasta).
- **Persistência** em `~/.printimposer/settings.json`: última configuração e geometria da janela voltam ao reabrir.
- **Guarda de qualidade**: compara os pixels da fonte com a célula no DPI alvo e classifica em OK / atenção / perda visível, com confirmação antes de gerar em caso ruim.
- **Entrada SVG** (antecipada da F3), com back-end opcional `cairosvg` ou `svglib`: rasteriza na resolução exata da célula — zero upscale por construção.
- **Segundo destino de saída**: grava a mesma geração em duas pastas de uma vez.
- Botão **"+ Pasta"**: adiciona todas as imagens suportadas de um diretório, em ordem natural de nome.
- **Gerador de `.bat`**: cria um atalho que abre a GUI sem janela de console, em ASCII puro e CRLF.
- Indicador de tamanho da célula em mm e px, ao lado da grade.
- Suíte headless com **40 testes** (`python tests/test_engine.py`).
- `CLAUDE.md` e `.claude/` para o Claude Code atuar como raia de validação (DEC-010).

### Modificado
- **PNG virou o formato de saída padrão** (era PDF) e passou a ser o primeiro da lista.
- **Pasta de saída padrão agora é Downloads** (era Área de Trabalho), com Desktop e home como reserva.
- **Pastas de entrada e saída ficaram independentes**: escolher imagens não mexe mais em onde salvar.
- Janela abre **centralizada e limitada ao monitor**, com DPI awareness no Windows e posição inicial definida para as divisórias.
- Miniaturas usam `Image.draft()` em JPEG e cache por caminho+mtime.
- `.gif` entrou na lista de formatos aceitos.

### Corrigido
- Detecção de back-end de SVG que aceitava `.svg` sem conseguir renderizar, e referência de módulo perdida no probe. Ver FIX-002.
- `compose_page` passou a restaurar o DPI em `finally`, garantindo a restauração mesmo se a composição levantar exceção.

---

## [1.0.1] — 2026-07-18
### Corrigido
- Crash ao abrir no Windows por incompatibilidade entre `tk.PanedWindow` e `CTkScrollableFrame`: os três painéis (lista, configurações, preview) passaram a ser envolvidos em `tk.Frame` neutro antes de entrar no PanedWindow. Ver FIX-001.

### Adicionado
- Kit de documentação de contexto do projeto (CONTEXT, STATUS, DECISIONS, CHANGELOG, IDEAS, ROADMAP, GLOSSARY, HISTORY, LOG-TEMPLATE e log de sessão).
- `.gitignore` (lixo de SO/editor + artefatos Python + saídas locais).
- `.flatdropignore` — corta `logs/` e `outputs/` do que sobe ao Projeto do Claude.

### Modificado
- Documentação alinhada ao Kit de Contexto Universal v1.73.0: modo ASU adotado no lugar da raia Claude Code (DEC-007); `HISTORICO.md` renomeado para `HISTORY.md` (DEC-008); Instruções do Projeto enxugadas de 6.892 para 5.350 caracteres.

---

## [1.0.0] — 2026-06-02
### Adicionado
- Seleção em massa de imagens (PNG, JPG, JPEG, TIFF, BMP, WebP) com lista de miniaturas.
- Quantidade por imagem (duplicação para impressão) e reordenação por botões ↑↓.
- Layouts N-up: 1×1, 2×1, 1×2, 2×2, 3×2, 2×3, 4×2, 2×4, 3×3, 4×3, 4×4.
- Modos de ajuste por slot: fit / fill / stretch, com Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom e DPI configurável (72–1200).
- Margem externa e entre imagens (mm); cor de fundo configurável.
- Linhas de corte opcionais: estilos sólida/tracejada/pontilhada, espessura, comprimento de traço e cor.
- Saída em PDF (multipágina), PNG, JPEG e TIFF, com prefixo/sufixo/contador automático e proteção contra sobrescrita.
- Preview em tempo real (72 DPI) com navegação entre folhas e atualização com debounce.
- Geração em thread separada com barra de progresso em duas fases e atalho para abrir a pasta de saída.
- README com guia de uso completo, fluxo Figma → PrintImposer e FAQ.
