# CONTEXT.md — PrintImposer

> Arquivo **estável**. O assistente lê ao abrir cada conversa para se ambientar.
> Muda pouco: só em alteração estrutural (stack, arquitetura, escopo, nova armadilha descoberta).
> Mantenha enxuto — descreve o que o projeto É, não o que está acontecendo agora (isso é o STATUS).

---

## Visão Geral
PrintImposer é uma ferramenta desktop de **imposição de páginas** para impressão em massa. O usuário seleciona várias imagens (cards, cartazes ou fotos — exportados de qualquer ferramenta: Figma, Canva, Affinity, Photoshop, Corel, geradores web — ou tirados do celular), escolhe um layout N-up (ex.: 4 por folha) e gera um PDF/PNG/JPEG/TIFF pronto para imprimir — sem arrastar arquivo por arquivo no diálogo do Windows. Foco em uso pessoal/profissional de quem produz cards e precisa agrupá-los em folhas A4 com mínimo esforço repetido.

## Stack Tecnológica
- **Linguagem:** Python 3.9+ (testado até 3.14 no Windows do usuário)
- **GUI:** CustomTkinter (sobre Tkinter) — tema escuro
- **Imagem/composição:** Pillow (PIL) — resize LANCZOS, composição RGBA, export PDF/PNG/JPEG/TIFF
- **Concorrência:** `threading` (geração e preview fora da UI thread)
- **Distribuição:** script único, rodado com `python print_imposer.py`
- **Testes:** `tests/test_engine.py` — suíte headless via stub de tkinter. **Não cobrem a GUI**: janela, divisórias e DPI só se validam abrindo o app (ver CLAUDE.md §Smoke test).
- **SVG (opcional):** `cairosvg` ou `svglib`; ausente, o `.svg` some da lista de formatos.

## Estrutura do Projeto
```
printimposer/
├── print_imposer.py       # TODO o app em um arquivo (~1960 linhas)
├── tests/test_engine.py   # suíte headless (engine + checagens AST do fonte)
├── CLAUDE.md              # guia da raia de execução (Claude Code)
├── .claude/               # settings.json + skills /apply-wo /smoke /wrap /sondar
├── meta/                  # documentação viva (KCM)
│   ├── specs/             # spec de feature: o QUÊ construir (chat escreve)
│   └── workorders/        # WOs: COMO aplicar (chat escreve, Code aplica)
└── README.md              # documentação de uso
```
O arquivo único está organizado em camadas internas (ver Arquitetura).

## Convenções de Código
- **Nomes:** arquivos, funções e variáveis em **inglês**; comentários em **PT-BR**.
- **Comentários:** docstring em função pública; comentário explica o PORQUÊ, não o QUÊ.
- **Commits:** Conventional Commits, descrição no imperativo curto em PT-BR (`feat(engine): ...`).
- **Estilo:** legibilidade primeiro; performance só se medida.
- **Imports/organização:** stdlib → terceiros → locais, com dependência opcional em `try/except ImportError` e degradação elegante (a UI nunca quebra por falta de extra).
- **Terminal/`.bat`:** conteúdo sem acento — o codepage legado do console do Windows corrompe UTF-8.

## Como a imposição funciona (CRÍTICO)
> Mecanismo central. Consultar antes de mexer na composição.

O fluxo de uma folha (`ImpositionEngine.compose_page`):
1. **Página em px** = `tamanho_mm × DPI / 25.4`. Ex.: A4 a 300 DPI → 2480×3508 px.
2. **Grid** vem de `cfg.cols × cfg.rows` — grade livre, sem lista cadastrada (DEC-009). Teto em `MAX_COLS`/`MAX_ROWS` (12×12). O nº de slots por folha é `cols×rows`.
3. **Célula (slot)** = `(largura_página − 2·margem_externa − (cols−1)·margem_entre) / cols`, idem para altura. Tudo em px.
4. Para cada slot, a imagem é colocada por `_place_image` segundo o modo de **ajuste**:
   - `fit` — cabe inteira, sobra cor de fundo (preserva proporção);
   - `fill` — preenche e recorta o excesso (preserva proporção, corta);
   - `stretch` — força o tamanho exato (distorce).
5. **Auto-Rotate**: se a orientação da imagem (retrato/paisagem) ≠ orientação do slot, gira 90°.
6. **Linhas de corte** (opcional): desenhadas DEPOIS da composição, atravessando a folha entre colunas/linhas. Estilos sólida/tracejada/pontilhada.

**SVG é caso à parte:** em vez de abrir e redimensionar, é **rasterizado já no tamanho da célula** (`open_source` → `rasterize_svg`). Por isso nunca sofre upscale e fica fora da guarda de qualidade. Ver HISTORY §5.

O preview usa o MESMO `compose_page` com `override_dpi=72` e depois reduz — garante fidelidade visual ao resultado final, só que rápido. Ver DEC-004.

A relação **qualidade × DPI**: a folha é rasterizada no DPI escolhido. Se a imagem-fonte tem menos pixels que a célula, há **upscale** (perda). Para A6 a 300 DPI a fonte deve ter ≥ 1240×1748 px. Detalhe completo em HISTORY §1.

## Arquitetura — pontos-chave
- **Separação Engine × GUI** — `ImpositionEngine` não depende de Tkinter; dá para testar headless. Ver DEC-004.
- **Raster, não vetorial (v1)** — composição via Pillow; PDF é imagem rasterizada. Ver DEC-001.
- **CustomTkinter para a UI** — visual moderno com baixo custo. Ver DEC-002.
- **Arquivo único** — simplicidade de distribuição. Ver DEC-003.
- **Linhas de corte atravessam a folha (v1)** — marcas de canto profissionais ficaram para depois. Ver DEC-005.
- **Grade de layout livre (`cols × rows`), não uma lista cadastrada** — implementada na 1.1.0. Ver DEC-009.
- **O chat planeja, o Claude Code implementa** — spec, análise e WO no chat; código, testes, smoke, commit e push no Code. Ver DEC-012 (substitui DEC-007 e DEC-010).

## Armadilhas Conhecidas (o que NÃO fazer)
> Cada armadilha já custou tempo uma vez. O que parece certo → por que morde → o certo.

1. **Passar um `CTkScrollableFrame` direto para um `tk.PanedWindow`** — parece natural, mas o CTk cria um canvas aninhado que o PanedWindow não adota como filho → `TclError: can't add ...`. → **Envolva em um `tk.Frame` simples** antes do `.add()`. Ver FIX-001.
2. **Confiar que "exportar 4× no Figma" = 300 DPI** — só vale se o frame-base tiver os pixels certos. → Mire o **alvo em pixels** (≥1240×1748 para A6), não a escala. Ver HISTORY §1.
3. **Escrever em `self._w` (ou outro nome do Tkinter) numa classe que herda de widget** — parece um atributo livre, mas `_w` é o **pathname Tcl** do widget: sobrescrever quebra toda chamada ao Tk com «invalid command name» e o app não abre. → **Prefixe os seus** (`_box_w`). Ver FIX-003.
4. **Mutar `cfg` dentro do engine, mesmo restaurando depois** — preview e geração rodam em **threads distintas sobre o mesmo `LayoutConfig`**; restaurar num `finally` conserta o caso sequencial e esconde o concorrente (a folha saía em 72 DPI sem aviso). → **Passe o valor por parâmetro**, não mute estado compartilhado. Ver FIX-004.
5. **Usar `winfo_screenheight()` para dimensionar a janela** — devolve a tela **física**; a barra de tarefas come o rodapé e o botão de ação some. → Use a **área útil** (`SPI_GETWORKAREA` no Windows). Ver FIX-005.
6. **Confiar que suíte verde = app funcional** — os 40 testes da 1.1.0 passavam com o app sem abrir, porque o stub de `tkinter` não reproduz o ambiente real. → Mudança de GUI **exige smoke test** (CLAUDE.md); e, quando dá, guarde a lição com uma checagem AST do código-fonte.
7. **Reintroduzir o `cfg.dpi` temporário em `compose_page`** — a versão antiga trocava o DPI para o preview e restaurava no `finally`; parecia seguro e causou a FIX-004. Desde então o DPI desce por parâmetro (`override_dpi`) e não há nada a restaurar. → Não volte a mutar; ver armadilha 4.
8. **Assumir que dependência opcional importada = dependência funcional** — `svglib` importa sem erro mas só desenha com `rlPyCairo`/`_rl_renderPM`. → **Sonde a capacidade com um render real**, não o import, e guarde a referência do módulo. Ver FIX-002.
9. **Geometria de janela fixa sem clamp e sem DPI awareness** — `geometry("1100x780")` parece inofensivo, mas ignora o tamanho real do monitor e, sem `SetProcessDpiAwareness`, o Windows escala por bitmap em telas com zoom → janela cortada e texto borrado. → Centralize com clamp e declare DPI awareness antes de criar a janela. Ver HISTORY §6.
10. **Linhas de corte finas em saída lossless** — inflam o arquivo (detalhe de alta frequência). → Para arquivos enxutos, prefira marcas de canto (futuro) ou borda feita na própria arte. Ver DEC-005 e ROADMAP F3.
11. **Isolar o app num teste definindo só `HOME`** — parece criar um usuário limpo, mas no Windows, desde o Python 3.8, `Path.home()` lê `USERPROFILE` e **ignora `HOME`**; o `SettingsStore` (`Path.home() / ".printimposer"`) grava então nas configurações reais do dono. Em 03/11 o dono achou o segundo destino ligado apontando para `AppData\Local\Temp\claude\…`, sobra de teste. → Para abrir o app em teste, defina `USERPROFILE` **e** `HOME` para a pasta temporária, e confira no Sobre qual `settings.json` está em uso antes de mexer em qualquer campo.
12. **Usar `cut_lines` em código novo** — o campo existiu até a 1.5 e parece vivo nos presets antigos, mas desde a 1.6.0 o modelo usa `cut_guide` (`"none"`/`"lines"`/`"marks"`); `cut_lines` só é lido no `from_dict`, para converter config e preset antigos. → Leia e grave `cut_guide`. E a geometria de corte, sangria e marcas vem de `sheet_geometry` (em mm): não recalcule posição de célula à parte, ou preview e saída divergem em 1–2 px.

## 📁 Arquivos Críticos (não mexer sem contexto)
> Conhecimento **estável**, não estado do agora — por isso vive aqui, e não no STATUS.
- `print_imposer.py` — app inteiro. Antes de tocar na composição, ler «Como a imposição funciona» acima. `compose_page` **não muta `cfg`**: preview e geração compartilham o `LayoutConfig` entre threads (FIX-004).
- `tests/test_engine.py` — a única rede antes do smoke. Três testes inspecionam o **código-fonte** por AST (colisão com nomes do Tkinter, contrato da área útil), porque o stub headless não reproduz esses bugs. Rodar antes de qualquer commit de código.
- `CLAUDE.md` / `.claude/` — contrato da raia de execução (DEC-012). O `settings.json` proíbe de propósito o Code editar CEREBRO, Instruções e LOG-TEMPLATE, e o chat não grava em `.claude/`: mudança de permissão chega como arquivo na pasta-pai e o dono copia.
- `meta/CEREBRO.md` — alinhado ao kit v1.133.0; o que é só deste projeto vai na seção «Técnicas específicas», que nenhum update sobrescreve.

## Contexto de Produto
- **Usuário-alvo:** quem produz cards, cartazes ou artes em lote — em qualquer ferramenta (Figma, Canva, Affinity, Photoshop, Corel, geradores web) — ou quem tem uma série de fotos (inclusive fotógrafos e fotos de celular), e imprime em casa ou manda para gráfica. **Não amarrar o produto, os textos nem a UI a uma ferramenta de origem** (pedido do dono, 2026-11-04).
- **Dor que resolve:** agrupar dezenas de imagens em folhas A4 sem trabalho manual repetido a cada impressão.
- **O que é sucesso:** "selecionar a forma de impressão → selecionar as imagens → gerar" — esforço mínimo, qualidade preservada do export de origem.
- **O que o projeto deliberadamente NÃO é:** não é editor de imagem, não é software de prepress completo (sem separação de cores, trapping, registro multi-plate, booklet/imposição de cadernos). Foco em N-up plano para corte.
