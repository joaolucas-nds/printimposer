# DECISIONS.md — Registro de Decisões

> Arquivo que **cresce devagar**. Guarda o PORQUÊ — o que o código sozinho não conta.
> Duas naturezas: **DEC** (decisões de arquitetura/design) e **FIX** (bugs graves resolvidos, para não repetir).
> Não reescreva entradas antigas; se uma decisão for substituída, marque «SUPERADA por DEC-N» e adicione a nova.
> Quando passar de ~700 linhas, mova as mais antigas para `DECISIONS-archive.md`.

---

## Como usar
Cada decisão recebe um ID sequencial (DEC-001, DEC-002…) e segue o formato abaixo (ADR simplificado). Bugs graves usam FIX-001, FIX-002… com sintoma/causa/solução/lição.

---

## DEC-001 — Imposição raster via Pillow (não vetorial) no v1
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
A entrada são imagens (PNG do Figma). Era preciso escolher entre compor as folhas como raster (juntar imagens numa imagem maior) ou montar um PDF vetorial posicionando páginas/objetos.

### Decisão
v1 compõe cada folha como uma imagem PIL e exporta (PDF/PNG/JPEG/TIFF) a partir dela.

### Alternativas consideradas
- **PDF vetorial (reportlab/pypdf posicionando páginas PDF)** — preserva qualidade perfeita e gera arquivos minúsculos, mas exige entrada em PDF/vetor e mais complexidade. Adiado para o ROADMAP (F3).
- **Render via navegador/HTML→PDF** — overkill, dependência pesada.

### Consequências
- Simples e direto para entrada em imagem; o que se vê no preview é exatamente o que sai.
- Qualidade limitada pelo DPI de rasterização e pelos pixels da fonte (risco de upscale).
- Linhas finas e marcas inflam o arquivo em saída lossless (ver DEC-005).
- Motiva a guarda de qualidade (F2) e o caminho vetorial (F3).

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
- Visual agradável com pouco esforço; widgets prontos.
- Herda limitações do Tkinter e incompatibilidades de aninhamento (ver FIX-001) e de DPI no Windows (F2).
- Drag-and-drop exige extensão externa (`tkinterdnd2`).

---

## DEC-003 — Arquitetura em arquivo único
**Data:** 2026-06-02 · **Status:** substituída pela DEC-017 (2026-11-10)

### Contexto
Utilitário pessoal, distribuído como "baixe e rode".

### Decisão
Todo o app em `print_imposer.py`.

### Alternativas consideradas
- **Pacote multi-módulo** — mais organizado para crescer, porém atrito para distribuir/rodar.

### Consequências
- Fácil de copiar e executar.
- Reavaliar se a F3 (entrada vetorial) chegar: aí o arquivo único pode passar do ponto.
- Reforça DEC-007: sem build e com um arquivo só, a cerimônia do Claude Code não se paga.

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
- Preview e geração final compartilham o mesmo caminho → o preview é fiel.
- **Assimetria importante:** o engine é testável no chat, a GUI **não é** — nenhum bug de interface é pego aqui (foi a origem do FIX-001).
- Custo: o engine troca `cfg.dpi` temporariamente no preview; exige restaurar o valor.

---

## DEC-005 — Linhas de corte atravessando a folha no v1 (marcas de canto adiadas)
**Data:** 2026-06-02 · **Status:** aceita

### Contexto
Para guiar o corte manual, era preciso algum tipo de marca. O padrão profissional são marcas de canto (ticks curtos no gutter), mais trabalhosas de posicionar.

### Decisão
v1 desenha linhas contínuas entre colunas e linhas, atravessando a folha (sólida/tracejada/pontilhada).

### Alternativas consideradas
- **Marcas de corte de canto** — não atravessam a arte, pesam quase nada, mais profissionais. Exigem cálculo por slot e gutter mínimo. Adiado para F3.
- **Sem marcas, confiando na borda feita no Figma** — já é alternativa válida hoje.

### Consequências
- Funciona e é simples.
- Linhas atravessando a arte e em saída lossless aumentam o tamanho do arquivo.

---

## DEC-006 — Saída PDF por rasterização no DPI configurado
**Data:** 2026-06-02 · **Status:** substituída por DEC-014

### Contexto
Era preciso um formato "manda pra gráfica / imprime direto".

### Decisão
Gerar PDF a partir das imagens compostas via `PIL.Image.save(..., "PDF", resolution=dpi)` (multipágina com `append_images`).

### Alternativas consideradas
- **reportlab** — controle fino de PDF, mas para folha já rasterizada não agrega sobre o save do PIL.
- **img2pdf** — embute bytes sem recompressão; vale avaliar quando a escolha de compressão entrar (F3).

### Consequências
- Caminho mais curto para PDF multipágina.
- Não expõe escolha de compressão — tratado em F3.

---

## DEC-007 — Modo ASU no lugar da raia de desenvolvimento no Claude Code
**Data:** 2026-07-18 · **Status:** substituída por DEC-012

### Contexto
O CEREBRO trazia uma raia "chat ↔ Claude Code" (specs em `meta/specs/`, `CLAUDE.md`, `.claude/`, build e commit pelo agente). O template-update v1.73.0 chegou sem essa raia e com a seção "Saída de código via ASU (patch)". Era preciso escolher um método para editar arquivos existentes sem reescrevê-los inteiros.

### Decisão
Adotar o **ASU** (instrução `.yaml` para baixar) como método padrão de edição, e remover a raia Claude Code do CEREBRO. Geração de arquivo novo e reescrita profunda continuam como **arquivo inteiro para baixar** (modo vanilla do KCM).

### Alternativas consideradas
- **Manter a raia Claude Code** — os benefícios reais do Code (rodar build, rodar suíte, editar muitos arquivos, commitar) não se aplicam: o projeto é **um arquivo**, **sem build** e **sem suíte**. A raia nunca foi montada — o repo não tem `CLAUDE.md` nem `.claude/`. Custo de cerimônia sem contrapartida.
- **Manter os dois** — duas fontes de verdade para "como editar código" é exatamente o tipo de duplicação que a higiene do kit proíbe.
- **Só arquivo inteiro (vanilla puro)** — honesto, mas `print_imposer.py` tem ~1190 linhas: reentregar tudo a cada ajuste custa caro em token e aumenta o risco de regressão por reescrita.

### Consequências
- O ASU já está instalado e documentado no conhecimento do Projeto (`INSTRUCTION_GUIDE.md`, `PROMPT_IA.md`, `GUIA_PASSO_A_PASSO.md`, `demo.yaml`) — adoção sem custo de setup.
- Some do CEREBRO a inconsistência `DECISOES.md` × `DECISIONS.md`, que só existia dentro da raia Code.
- **Ponto cego assumido:** o chat **não executa a GUI**. Bugs de runtime de interface (como o FIX-001) continuam passando. Mitigação atual: entregar dizendo o que abrir e conferir.
- **Gatilho de reabertura:** se aparecerem 2+ bugs de runtime de GUI que o chat não pegou, ou se o projeto modularizar em F3, reavaliar o Claude Code — ele roda o app e vê o traceback, coisa que o chat não faz.

---

## DEC-008 — `HISTORICO.md` renomeado para `HISTORY.md`
**Data:** 2026-07-18 · **Status:** aceita

### Contexto
O projeto nasceu com `meta/HISTORICO.md`; o kit v1.73.0 padronizou o nome em inglês (`HISTORY.md`), gerando divergência com o CEREBRO e as Instruções.

### Decisão
Renomear o arquivo para `HISTORY.md`, preservando 100% do conteúdo, e atualizar as referências em CEREBRO, Instruções e CONTEXT.

### Alternativas consideradas
- **Manter `HISTORICO.md`** — evitaria o rename agora, mas deixaria o projeto divergindo do kit em todo update futuro, e contra a convenção do próprio projeto (nomes de arquivo em inglês, CONTEXT §Convenções).

### Consequências
- Alinhamento com o kit e com a convenção de idioma do projeto.
- `git mv` preserva o histórico; nenhuma perda de conteúdo.

---

## DEC-009 — Grade livre (cols × rows) em vez de lista de layouts cadastrados
**Data:** 2026-07-18 · **Status:** aceita *(a implementar em F2)*

### Contexto
`NUP_LAYOUTS` é um dict fixo no código; toda combinação faltante (ex.: 2×6) exige editar o `.py`. A proposta inicial era mover a lista para um JSON editável pela interface.

### Decisão
Expor **dois spinners `colunas × linhas`** na UI, permitindo qualquer grade sem cadastro. A lista fixa vira apenas **atalhos** para as combinações mais usadas, e os **presets nomeados** (.json) passam a guardar a configuração inteira — grade + papel + margens + corte + formato — não só a grade.

### Alternativas consideradas
- **Lista de layouts em JSON com editor na UI** — resolve o sintoma (falta o 2×6) mas mantém a causa (só existe o que foi cadastrado) e exige construir um CRUD de lista na interface. Mais trabalho, menos liberdade.
- **Continuar editando o código** — inviável como produto.

### Consequências
- Qualquer grade passa a existir sem cadastro; a causa-raiz morre.
- Menos UI para construir do que um editor de lista.
- A persistência em JSON continua — o que foi descartado é a lista de layouts como estrutura de dados, não o JSON.
- Grades muito grandes ficam possíveis (ex.: 12×12): precisa de um teto sensato e do aviso de qualidade para não gerar folha inútil.

---

## DEC-010 — Claude Code como raia de validação, não de desenvolvimento
**Data:** 2026-07-19 · **Status:** substituída por DEC-012 · *(refinava a DEC-007, não a revogava)*

### Contexto
A DEC-007 dispensou o Claude Code como modo de desenvolvimento e registrou um gatilho de reabertura: "se aparecerem 2+ bugs de runtime de GUI que o chat não pegou". A F2 mudou justamente a geometria da janela, o DPI awareness e as divisórias — três coisas que **só se validam com a janela aberta** e que o chat estruturalmente não executa.

### Decisão
Montar `CLAUDE.md` e `.claude/` para o Claude Code atuar como **raia de execução e validação** (rodar, ver traceback, smoke test, corrigir o que só aparece rodando), mantendo **o chat como raia de autoria e curadoria** (arquitetura, escrita do código, curadoria dos `meta/`).

### Alternativas consideradas
- **Seguir só no chat** — aceitável enquanto a mudança era de engine (testável headless). Deixou de ser: a F2 é majoritariamente de interface.
- **Migrar o desenvolvimento para o Code** — reabriria o custo que a DEC-007 recusou, e sem necessidade: a autoria no chat vem funcionando.

### Consequências
- O ponto cego assumido na DEC-007 ganha uma cobertura real, sem trazer de volta a cerimônia recusada.
- O `CLAUDE.md` precisa de disciplina: instrui o Code a **preferir o menor diff** e a **relatar em vez de decidir** quando o problema for de arquitetura — senão surgem duas fontes de verdade.
- `.claude/settings.json` proíbe editar `CEREBRO.md`, as Instruções e o `LOG-TEMPLATE.md`, e proíbe `git push`: curadoria de comportamento continua sendo do chat.
- Edições do Code nos `meta/` são **append-only** (STATUS e DECISIONS), como o `/wrap` reforça.

---

## FIX-001 — `tk.PanedWindow` não adota `CTkScrollableFrame` como filho
**Data:** 2026-07-18 *(diagnóstico/correção)* · *(bug presente desde o v1.0.0)* · **Status:** resolvida

- **Sintoma:** ao abrir o app no Windows (Python 3.14), crash imediato:
  `_tkinter.TclError: can't add .!panedwindow.!panedwindow.!ctkframe.!canvas.!ctkscrollableframe to .!panedwindow.!panedwindow`.
- **Causa raiz:** `CTkScrollableFrame` cria internamente um canvas aninhado. Ao passá-lo diretamente para `tk.PanedWindow.add()`, o PanedWindow tenta adotar como filho um widget que não é descendente direto dele na hierarquia esperada → o Tk recusa.
- **Solução:** envolver cada painel em um `tk.Frame` simples (com `rowconfigure/columnconfigure` peso 1) e adicionar ESSE frame ao PanedWindow; o conteúdo CTk vai dentro do wrapper via `grid(sticky="nsew")`. Aplicado aos três painéis.
- **Lição:** ao misturar widgets CustomTkinter com geometria nativa do Tkinter, **sempre interponha um `tk.Frame` neutro**. Virou armadilha nº1 em CONTEXT.
- **Lição de processo:** o bug passou porque o chat **não executa a GUI** — o engine foi testado headless e aprovado, a janela nunca abriu. Registrado como consequência assumida em DEC-004 e DEC-007.


---

## FIX-002 — Detecção de dependência opcional por `import` não prova capacidade
**Data:** 2026-07-19 *(capturado em desenvolvimento, nunca chegou a ser publicado)* · **Status:** resolvida

- **Sintoma:** com `svglib` instalado, `SVG_BACKEND` era definido e `.svg` entrava na lista de formatos aceitos — mas gerar a folha estourava `RenderPMError: cannot import desired renderPM backend rlPyCairo`. O usuário só descobriria na hora de imprimir.
- **Causa raiz:** a sondagem testava só `import svglib`. Acontece que `svglib` **analisa** SVG em Python puro, mas **desenhar** depende do `renderPM` do reportlab, que por sua vez exige `rlPyCairo` ou a extensão C `_rl_renderPM`. Importar a biblioteca não prova que ela consegue produzir um pixel.
- **Solução:** `_probe_svg_backend()` passou a fazer um **render real** de um SVG mínimo em memória. Só um back-end que efetivamente desenha é aceito; do contrário `.svg` some da lista de formatos e o app segue normalmente.
- **Segundo bug, mesma investigação:** o probe importava os módulos em escopo local, então `rasterize_svg` levantava `NameError: name 'cairosvg' is not defined` ao rodar. Corrigido guardando as referências em `_SVG_MODS`.
- **Lição:** para dependência opcional, **sonde a capacidade, não a presença** — e guarde a referência do módulo obtido, não só o nome do back-end. Ambos os bugs foram pegos pela suíte headless; nenhum apareceria em revisão de código.


---

## DEC-011 — Painel de configuração híbrido: zonas fixas + accordion, e menubar para ações
**Data:** 2026-07-22 · **Status:** aceita *(a implementar na F3)*

### Contexto
O painel central empilhava 7 seções numa rolagem única (~1400 px). O contador de folhas e a guarda de qualidade — que são feedback, não configuração — só apareciam no fim da rolagem. O gerador de `.bat`, usado uma vez na vida, ocupava espaço permanente.

### Decisão
Três zonas: **fixa no topo** (Grade + mini-grid), **accordion no meio** (Papel, Ajuste, Margens, Corte, Saída — esta aberta por padrão), **fixa no rodapé** (contador, guarda de qualidade, tamanho da célula). Ações que não são configuração — `.bat`, presets, sobre, guia — migram para uma **menubar `Arquivo · Opções · Ajuda`** na topbar. Accordion é multi-aberto e o estado persiste entre sessões.

### Alternativas consideradas
- **Tabs** — descartadas por dois motivos independentes: são 6 seções com rótulos longos em PT-BR, acima do limite prático de 3–5 abas; e as duas mais mexidas (Grade e Saída) cairiam em abas diferentes, forçando alternância constante. A pesquisa é explícita: tabs perdem quando o usuário precisa ir e voltar.
- **Accordion puro** — mais simples, mas colapsaria a Grade (a seção com feedback visual, mexida a cada trabalho) e deixaria a guarda de qualidade dependente de abrir algo. Contraria diretamente a regra de não esconder conteúdo essencial.
- **Manter a rolagem e só mover o `.bat`** — resolveria um sintoma e deixaria a causa.
- **Menubar nativa** (`self.config(menu=…)`) — mais barata, mas o Windows desenha a faixa em cinza claro, destoando do tema escuro. Optou-se por `CTkButton` + `tk.Menu.tk_popup()`: faixa no tema do app, dropdown nativo (teclado e dismissal de graça).

### Consequências
- Altura empilhada da coluna cai de ~1400 px para ~560 px: sem rolagem no uso normal em 768 px.
- O bug do menu de presets que não atualizava morre por construção — o submenu é reconstruído a cada abertura.
- Novo componente `CollapsibleSection` e nova chave `sections_open` no `settings.json` (compatível para trás: arquivo antigo cai no padrão).
- Mais superfície de UI para o smoke test cobrir; quatro itens novos no checklist.
- Entrega em **arquivo inteiro** — reescrita profunda de `ConfigPanel`, conforme DEC-007.

---

## FIX-003 — Sobrescrever `_w` colide com o Tkinter e impede o app de abrir
**Data:** 2026-07-19 · **Gravidade: bloqueador** — a 1.1.0 não abria. · **Status:** resolvida

- **Sintoma:** `python print_imposer.py` morria na construção da UI com `_tkinter.TclError: invalid command name "70"`, no `GridPreview.draw` → `self.delete("all")`.
- **Causa raiz:** `GridPreview.__init__` fazia `self._w, self._h = w, h` para guardar as dimensões da caixa. Só que em `tkinter.Misc`, **`_w` é o pathname Tcl do widget** (`'.!canvas'`) — é o nome pelo qual o Tk conhece o objeto. Sobrescrevendo com `70`, toda chamada passou a montar o comando `70 delete`, e o Tcl respondeu que não existe comando chamado "70". Atingia 3 linhas.
- **Solução:** renomear para `self._box_w` / `self._box_h`.
- **Por que a suíte não pegou:** o stub de `tkinter` da suíte headless é uma classe vazia — não define `_w`, então a colisão simplesmente não existe lá. **Os 40 testes passavam com o app quebrado.** Só o smoke test com janela real revelou.
- **Guarda de regressão:** `TkAttributeCollisionTests` faz uma varredura **AST do código-fonte** procurando escrita em nome reservado do Tkinter (`_w`, `_name`, `_tclCommands`, `master`, `tk`, `children`) em qualquer classe que herde de `tk.*`/`ctk.*`. É a única forma headless de guardar esta lição — e vale para qualquer widget futuro, não só o `GridPreview`.
- **Lição:** ao herdar de widget Tk, **prefixe atributos próprios** (`_box_w`, não `_w`). O namespace do `self` é compartilhado com a implementação do Tkinter. E, mais importante: *suíte verde não é o mesmo que app que abre* — foi exatamente o buraco que a DEC-010 previu.

---

## FIX-004 — Corrida de DPI entre a thread de preview e a de geração
**Data:** 2026-07-19 · **Gravidade: alta** — saída silenciosamente errada. · **Status:** resolvida

- **Sintoma:** gerar logo depois de mexer numa opção produzia a folha em **72 DPI** em vez do DPI configurado, sem aviso nenhum. Reproduzido: preview em voo → 595×842 px; preview assentado → 1240×1754 px, para o mesmo A4 a 150 DPI.
- **Causa raiz:** `compose_page` mutava `cfg.dpi`, compunha, e restaurava num `finally`. Correto para uso **sequencial** — mas preview e geração rodam em **threads distintas sobre o mesmo `LayoutConfig`**. Enquanto a thread do preview segurava `cfg.dpi = 72`, a thread de geração lia esse valor e compunha a folha inteira em 72 DPI. O `finally` restaurava depois, tarde demais.
- **Solução:** **parar de mutar estado compartilhado.** O DPI virou parâmetro que desce por `_mm_px`, `_page_px` e `cell_px`; `compose_page` não escreve mais em `cfg`, e o `finally` deixou de ser necessário porque não há nada a restaurar.
- **Guarda de regressão:** `DpiRaceTests` roda uma thread martelando `preview_page()` enquanto a principal compõe folhas, e exige que todas saiam no tamanho do DPI configurado.
- **Lição:** a armadilha nº3 do CONTEXT ("restaure sempre o DPI") estava **certa e insuficiente**: restaurar resolve o caso sequencial e mascara o concorrente. Quando há threads, a pergunta não é "eu restaurei?", é **"por que estou mutando estado compartilhado?"**. Parâmetro > mutação com restauração.

---

## FIX-005 — Geometria usava a tela física, não a área útil
**Data:** 2026-07-19 · **Gravidade: média** — parte da UI inacessível. · **Status:** resolvida

- **Sintoma:** em tela de 1366×768, a janela abria com base em y=737 contra uma área útil de 720 px: a barra de ação inferior — inclusive o botão **"Gerar Arquivos"** — ficava sob a barra de tarefas.
- **Causa raiz:** `_setup_geometry` calculava o clamp com `winfo_screenheight()`, que devolve a **tela física**, ignorando a barra de tarefas e qualquer outra barra acoplada.
- **Solução:** novo helper `_work_area()`, que no Windows consulta `SystemParametersInfoW(SPI_GETWORKAREA)` e devolve `(x, y, w, h)` da área realmente utilizável; fora do Windows (ou se a API falhar) desconta uma faixa de cortesia de 60 px. O posicionamento passou a ser relativo à origem da área útil, não a (0,0).
- **Guarda de regressão:** `WorkAreaTests` verifica que `_setup_geometry` chama `_work_area()` e **não** usa `winfo_screenheight()` diretamente.
- **Lição:** "caber na tela" e "caber na área utilizável" são coisas diferentes. Tela cheia de barras é o caso comum, não a exceção.

---

## DEC-012 — Claude Code implementa; o chat planeja com a pasta vinculada (ASU aposentado)
**Data:** 2026-11-03 · **Status:** aceita · *(substitui DEC-007 e DEC-010)*

### Contexto
Duas mudanças chegaram juntas. O template-update KCM v1.133.0 veio com o modo Code ligado e o ASU desligado, e o chat passou a trabalhar com a pasta do projeto vinculada — lê e grava no disco. O gatilho de reabertura da DEC-007 («2+ bugs de runtime de GUI que o chat não pegou») já tinha disparado na F2: FIX-003, FIX-004 e FIX-005. E o ASU custou duas instruções defeituosas por semântica de indentação não documentada (ver «Feedback para o ASU» no IDEAS).

### Decisão
O **chat planeja**: spec, análise e WO; cura CEREBRO, CONTEXT, GLOSSARY, Instruções e LOG-TEMPLATE, gravando direto na pasta. O **Claude Code implementa**: escreve o código a partir da spec ou da WO, roda a suíte e a GUI, faz o smoke, edita STATUS, DECISIONS e CHANGELOG (e IDEAS por WO), commita e **empurra quando verde**. Edição de arquivo existente sai como **WO** em `meta/workorders/`, aplicada com `/apply-wo`. O ASU sai de cena.

### Alternativas consideradas
- **Manter ASU + Code validando (DEC-007/010)** — dois canais para editar código, e o do ASU com falhas medidas de indentação; quem escrevia não rodava o que escrevia.
- **Chat escreve o código direto na pasta, Code só valida** — possível agora, mas mantém quem escreve longe de quem roda: o ciclo bug → traceback → correção passa por dois atores.
- **Push só pelo dono** — a DEC-010 proibia; o kit mediu que o passo manual é o primeiro a ser pulado. O freio fica no vermelho: suíte falhou, âncora sumiu ou diff fora do previsto → sem commit, menu de opções.

### Consequências
- `.claude/commands/` migrou para `.claude/skills/` (`apply-wo`, `wrap`, `sondar`, `smoke`). O `settings.json` ganhou `Write`, `additionalDirectories: ["../"]` e `git push`; o deny de o Code editar CEREBRO, Instruções e LOG-TEMPLATE ficou.
- Cada tarefa do Code grava relatório na pasta-pai (`AAMMDD-HHMM-code-printimposer-<ato>-<alvo>.txt`).
- O guia do ASU foi para `zz_backups/`; as entradas «Feedback para o ASU» ficam no IDEAS como histórico.
- A F3 (`meta/specs/SPEC-F3-UI.md`) passa a ser implementada pelo Code. O §12 da spec («entrega em arquivo inteiro») e a última consequência da DEC-011 («conforme DEC-007») ficam superados por esta decisão; o chat revisa a spec antes da WO da F3.

---

## DEC-013 — Nesta máquina o chat grava `.claude/` direto; skill nasce antes da WO que a usa
**Data:** 2026-11-03 · **Status:** aceita · *(desvio registrado do kit v1.133)*

### Contexto
O kit manda o chat entregar o `settings.json` na pasta-pai para o dono copiar («a ponte do chat não grava em `.claude/`») e manda skill mudar por WO. Na wo0001 isso gerou dois atritos: a WO pedia `/apply-wo` e só criava a skill dentro dela — o dono teve de copiar a pasta de skills à mão para o Code conseguir começar [relatado pelo dono] —, e o `settings.json` entregue trazia regras `Write(...)` no deny que o Claude Code rejeita («never matches · use Edit»). No mesmo dia o chat corrigiu o `settings.json` gravando direto: a ponte desta máquina grava em `.claude/` [medido pelo chat].

### Decisão
O chat grava `.claude/settings.json` e `.claude/skills/*` direto no lugar definitivo; a WO só os versiona, com `sha1sum` no cabeçalho. Skill que dirige a aplicação de uma WO existe no disco ANTES de a WO ser entregue. Deny de arquivo usa só `Edit(...)`, que já cobre a escrita.

### Alternativas consideradas
- **Seguir o kit (pasta-pai + cópia pelo dono)** — passo manual sem necessidade nesta máquina; foi o que travou a wo0001.
- **O Code edita `.claude/`** — o classificador bloqueia autoconcessão de permissão, e com razão.

### Consequências
- A barreira de autoconcessão continua: quem grava a permissão é o chat, quem a usa é o Code.
- Se a ponte deixar de gravar em `.claude/` (outra máquina, outra versão do app), volta a regra do kit. O caso está em «Técnicas específicas» do CEREBRO.

---

## DEC-014 — PDF por escritor próprio, sem perda por padrão (fluxo do PNG embutido)
**Data:** 2026-11-03 · **Status:** aceita · *(substitui DEC-006)*

### Contexto
Medido em 2026-11-03: o PDF gerado por `Image.save(..., "PDF")` tinha `/DCTDecode` = 1 e `/FlateDecode` = 0 numa folha A4 2×2 a 300 DPI. O Pillow grava imagem RGB em PDF sempre como JPEG (`PdfImagePlugin.py` do Pillow 12.2.0, linhas 118–121; documentação: «L, RGB and CMYK mode images use JPEG encoding») e não oferece `quality` nem caminho sem perda. O formato recomendado «para gráfica» perdia qualidade sem o usuário escolher. O dono decidiu: PDF sem perda por padrão (análise `261103-ANALISE-ordem-f4`).

### Decisão
O PDF passa a ser escrito por uma função própria, só com a biblioteca padrão. Para cada folha, a página é salva como PNG em memória e os dados dos blocos `IDAT` são embutidos como imagem do PDF com `/FlateDecode` e `/Predictor 15` — sem recomprimir, portanto **sem perda por construção**. O modo JPEG do PDF embute os bytes de `save(..., "JPEG", quality=q)` com `/DCTDecode`, com a qualidade escolhida pelo usuário.

### Alternativas consideradas
- **`Image.save(..., "PDF")` (DEC-006)** — não tem caminho sem perda para RGB.
- **`img2pdf`** — faz exatamente isso, mas depende do `pikepdf` (C++) e é LGPL-3: duas dependências novas para o formato **padrão**, que pela regra do projeto não pode depender de extra opcional.
- **`reportlab` / `pypdf`** — servem, mas trazem dependência para algo que cabe em ~100 linhas de stdlib; o `pypdf` volta a ser avaliado no portão da imposição vetorial (F4, etapa 3).

### Consequências
- PDF sem perda fica do tamanho do PNG (maior que o JPEG de antes — medido numa folha sintética: PNG 11,3 MB × PDF-JPEG 3,2 MB); o modo JPEG continua disponível para arquivo menor.
- O projeto passa a manter um escritor de PDF mínimo: estrutura (catálogo, páginas, `xref`) coberta por testes headless, e equivalência de pixels conferida por sonda com `pypdfium2` fora do Python do dono.
- Se a imposição vetorial for aprovada no portão, este escritor é substituído pelo pipeline vetorial; até lá, é o único caminho de PDF.

---

## FIX-006 — SVG saía ampliado com Auto-Rotate e no modo Preencher
**Data:** 2026-11-04 · **Gravidade: baixa** — latente: não se manifestava na máquina do dono (sem back-end de SVG). · **Status:** resolvida na 1.5.0 (wo0009)

- **Sintoma (por leitura de código, não medido em execução):** arte SVG deitada numa célula em pé saía pequena e esticada; no modo Preencher, o `_place_image` recortava e ampliava.
- **Causa raiz:** `open_source` passava a caixa `(cw, ch)` direto a `rasterize_svg`, que ignorava o Auto-Rotate (o giro vinha depois do render) e usava sempre a menor escala, qualquer que fosse o modo de ajuste.
- **Solução:** `svg_intrinsic_size` (width/height, viewBox ou medida do back-end) dá a proporção; `vector_render_box` (regra única, também usada pelo PDF) gira a caixa; `rasterize_svg` segue fit/fill/stretch como o `rasterize_pdf`.
- **Guarda de regressão:** `SvgFinalOrientationTests`, com stub do rasterizador (sem back-end). Back-end real não ligou nesta máquina (`libcairo` ausente), então a prova é o stub.
- **Lição:** ao dar à fonte vetorial a caixa de render, a orientação e o modo de ajuste valem para TODA fonte vetorial — conserto num formato (PDF, 1.4.0) pede a conferência do irmão.

---

## DEC-015 — Imposição vetorial do PDF vai para a F5 (portão da F4, opção B)
**Data:** 2026-11-06 · **Status:** aceita

### Contexto
O portão da etapa 3 da F4 perguntava se a saída PDF devia posicionar as páginas de entrada sem rasterizar. Critério fixado antes de medir (`meta/analises/261104-ANALISE-portao-vetorial.md`): C (agora) exigia (1) N-up correto, (2) diferença ≤ 2/255 com ganho visível e (3) arquivo vetorial ≤ 1/3 do raster sem perda a 300 DPI. Duas sondas: cartazes do jsPDF (só foto JPEG, 0 caracteres de texto) e 5 PDFs do Figma (texto Type3 + uma imagem de logo de 404 KB por arquivo).

### Decisão
**Opção B:** a imposição vetorial vai para a F5, como segundo desenhista sobre a geometria em mm que a etapa 4 cria. A etapa 4 (marcas e sangria) vem primeiro, no motor raster.

### Alternativas consideradas
- **C — agora, como modo «Vetorial» no PDF** — critérios 1 e 2 passaram (os dois protótipos montaram as folhas; o dono viu a diferença em todos os recortes), mas o 3 falhou nas duas fontes reais: jsPDF 0,89–3,89× (0,41× com dedup), Figma 1,87–4,00× (0,57–1,12× com 3 passadas de dedup). O peso dos PDFs do dono é bitmap embutido; o ganho é nitidez do texto, não tamanho.
- **A — descartar** — os protótipos funcionaram e o ganho de nitidez é real; descartar jogaria fora evidência boa.

### Consequências
- Biblioteca para quando voltar: `pypdf` (acertou de primeira, preserva bytes de JPEG e PNG, deduplica com passadas repetidas). O `pypdfium2` errou a matriz duas vezes e não embute PNG sem reencodar.
- Teste de papel em casa (06/11): diferença só de muito perto. **Gatilho de reabertura:** impressão numa gráfica de ponta mostrar o texto raster visivelmente mole.
- O DEC-001 («qualidade perfeita e arquivos minúsculos») vale pela metade para o conteúdo do dono: qualidade sim, tamanho não.

---

## DEC-016 — Arrastar e soltar via `tkinterdnd2` opcional, registrado na janela inteira
**Data:** 2026-11-10 · **Status:** aceita

### Contexto
O dono pediu, em 07/11, arrastar imagens e PDFs para a janela. O Tk não tem soltar arquivos nativo; o `tkinterdnd2` embrulha o tkDnD, mas o uso documentado troca a raiz por `TkinterDnD.Tk()`, e a raiz do app é `ctk.CTk`. Medido em 10/11 (`probe-f5`): `class Win(ctk.CTk, TkinterDnD.DnDWrapper)` + `TkinterDnD._require(win)` carrega o tkDnD 2.10.3 no Python 3.13.13 do dono, e um `CTkFrame` filho registra `DND_FILES` sem erro.

### Decisão
- `tkinterdnd2` é **dependência opcional**, como `pypdfium2`: sem ela, o app abre igual à 1.6.0 e o cabeçalho diz `Arrastar: indisponível`.
- A `PrintImposerApp` mistura `DnDWrapper` quando o import funciona; o recurso só liga depois que `TkinterDnD._require(self)` devolve uma versão (capacidade provada, FIX-002).
- O alvo do soltar é a **janela inteira**; os caminhos saem de `self.tk.splitlist(event.data)` e passam pelo funil de sempre (`expand_dropped` → `plan_ingest`).
- A reordenação da lista arrastando é **Tk puro** (eventos de mouse na alça da linha), sem `tkinterdnd2`.

### Alternativas consideradas
- **Registrar só a lista** — o tkDnD entrega ao widget sob o ponteiro, e as linhas são recriadas a cada mudança: cada uma teria de se registrar. Mais superfície para errar, sem ganho para o usuário.
- **`WM_DROPFILES` via `ctypes`** — só Windows, com gancho de janela escrito à mão; o `tkinterdnd2` já estava medido.
- **Dependência obrigatória** — contraria a regra de degradação elegante do projeto (CONTEXT, convenções).

### Consequências
- O executável (1.10.0) precisa do hook do `tkinterdnd2` no PyInstaller, ou falha com «Unable to load tkdnd library».
- A janela principal passa a herdar de uma classe de terceiros que usa `self._w`: o `TkAttributeCollisionTests` continua valendo, e mudança nessa classe pede `/smoke`.


---

## DEC-017 — Dois módulos: núcleo sem Tk (`imposer_core.py`) e GUI (`print_imposer.py`)
**Data:** 2026-11-10 · **Status:** aceita · **Substitui:** DEC-003

### Contexto
A DEC-003 (arquivo único, 06/2026) previa reavaliar «se a entrada vetorial chegar»; ela chegou na 1.4.0. Em 10/11 o arquivo tinha 3.875 linhas, e as linhas 1–1.907 (exceto o import do CustomTkinter e o bloco do arrastar) já não usavam Tk. A moldura (1.9.0) e a vetorial mexem no centro do motor. E o argumento «baixe e rode um arquivo» perdeu força: há um usuário, e o executável vem na 1.10.0. Análise: `meta/analises/261110-ANALISE-portao-moldura.md`.

### Decisão
Dois arquivos na raiz: `imposer_core.py` (dependências opcionais sem Tk, constantes, persistência, modelo, geometria, PDF, motor, `.bat`, ingestão) e `print_imposer.py` (GUI e `main()`, o arquivo que o `.bat` abre). A GUI importa o núcleo; o núcleo nunca importa a GUI nem Tk. `print_imposer.py` reexporta o núcleo (`from imposer_core import *`, mais os nomes com `_` que usa). Feita numa versão só de refatoração (1.8.1), conferida por SHA-256 idêntico das folhas geradas antes e depois.

### Alternativas consideradas
- **Manter o arquivo único** — a moldura o levaria a mais de 4.300 linhas, com âncoras de WO cada vez mais frágeis.
- **Pacote com muitos módulos** — mais imports cruzados (os globais dos back-ends são lidos dos dois lados) e um diff maior, sem ganho a mais para um projeto de um usuário.

### Consequências
- Patch de teste mira o módulo que **lê** o nome (`imposer_core`, quase sempre): patch em `print_imposer` vira inerte em silêncio.
- Testes de AST leem o arquivo certo; um teste guarda a fronteira (o núcleo sem import de Tk).
- O núcleo pode ser testado sem o stub de Tk.

---

## DEC-018 — Moldura por divisões sucessivas, com catálogo pronto
**Data:** 2026-11-10 · **Status:** aceita (implementação na 1.9.0)

### Contexto
O critério da F5 pede layout não-uniforme. Caso do dono: duas fotos horizontais iguais e uma retrato alta na mesma folha; uso real (04/11): um fotógrafo monta, em segundos, várias molduras com uma série de fotos. O Lightroom separa grade, «Picture Package» e «Custom Package», e otimiza o arranjo para o menor número de cortes; as folhas «divididas» dos laboratórios (ex.: 1× 5×7 + 2× 4×5 numa 8×10) se cortam com cortes retos, pedaço por pedaço.

### Decisão
Uma moldura é uma **árvore de divisões**: cada nó divide o espaço em partes, na vertical ou na horizontal, com proporções; as folhas da árvore são os slots, preenchidos em ordem de leitura. A grade `cols × rows` é o caso particular e não muda de saída. A 1.9.0 entrega um catálogo — `1 + 2`, `2 + 1`, `1 + 3`, `Destaque + 4`, `1 + 2 + 1` — com um controle de proporção por modelo. Cortes viram **segmentos**; marcas vão nas pontas de segmento que tocam a borda da área útil (na grade, exatamente as da 1.6.0); divisão vertical usa o espaçamento entre colunas, horizontal o entre linhas; sangria como na 1.6.0; a guarda de qualidade mede cada item contra o slot em que ele cai.

### Alternativas consideradas
- **Lista fixa desenhada à mão** — cada moldura seria código novo, sem proporção ajustável.
- **Editor livre de caixas** — a maior UI da fase; caixas soltas não garantem cortes retos e deixam marcas e sangria sem regra.
- **Células por tamanho físico com arranjo automático** — problema de empacotamento; o resultado dele é uma árvore desta decisão, então pode vir depois por cima.

### Consequências
- O preset ganha um campo opcional (`layout`); ausente, vale a grade.
- Um editor de divisões e o arranjo por tamanho físico podem vir depois sobre o mesmo formato, sem migração.
- O desenhista vetorial da F5 desenha a geometria já generalizada, uma vez só.
