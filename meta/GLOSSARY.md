# GLOSSARY.md — Termos do Projeto

> **Opcional.** Use quando o projeto tem vocabulário próprio (nomes de módulos, conceitos, identificadores) que o assistente reexplicaria a cada conversa sem isto.
> Mantenha curto: só o que não é óbvio para alguém de fora.

---

## Conceitos de imposição / prepress
- **Imposição (imposition)** — posicionar várias páginas/artes numa folha maior para imprimir e cortar com eficiência. É o que a ferramenta faz.
- **N-up** — quantas imagens por folha. "4-up" = 4 por folha; aqui sempre num grid `cols×rows`.
- **DPI** — pontos por polegada na impressão. 300 DPI é o padrão profissional. Tamanho em px = `mm × DPI / 25.4`.
- **fit / fill / stretch** — modos de ajuste da imagem ao slot: *fit* cabe inteira (sobra fundo), *fill* preenche e recorta, *stretch* força o tamanho (distorce).
- **Auto-Rotate** — girar a imagem 90° quando sua orientação (retrato/paisagem) não bate com a do slot.
- **Slot / célula (cell)** — o retângulo onde uma imagem é colocada dentro do grid da folha.
- **Margem externa** — espaço ao redor de toda a folha (bordas).
- **Margem entre imagens / gutter** — espaço entre os slots. Em prepress, o **gutter** é a folga entre artes que também acomoda marcas de corte e tolerância de corte.
- **Sangria (bleed)** — arte que transborda o limite de corte (tipicamente ~3 mm) para que não apareça borda branca após o corte. *(planejado, F3)*
- **Marca de corte (crop mark)** — guia de onde cortar. Padrão de indústria: ticks curtos nos cantos, no gutter (não atravessam a arte). v1 usa linhas atravessando a folha. *(canto: F3)*
- **Marca de registro (registration mark)** — alinhamento entre plates de cores diferentes na impressão offset. Fora do escopo deste projeto.
- **Step-and-repeat** — repetir a mesma arte N vezes na folha. O campo "quantidade" por imagem faz uma versão básica.
- **Cut & stack** — ordenar cópias para que, após cortar e empilhar, a sequência fique correta. Fora do escopo atual.
- **Compressão (lossless × lossy)** — *lossless* (PNG/Flate) preserva tudo, arquivo maior; *lossy* (JPEG) reduz tamanho com perda. Reamostrar para um DPI menor também perde qualidade. Ver HISTORY §2.

## Arquiteturas / módulos (no código)
- **ImpositionEngine** — núcleo de composição; não depende de Tkinter. Métodos-chave: `compose_page`, `generate_all`, `preview_page`, `save`. Ver DEC-004.
- **LayoutConfig** — estado de configuração (papel, DPI, margens, corte, saída). Tem `to_dict`/`from_dict` (base para presets).
- **ImageEntry** — uma imagem + quantidade + miniatura.
- **PrintImposerApp** — janela principal (CTk) que orquestra os painéis.
- **ImageListPanel / ConfigPanel / PreviewPanel** — os três painéis da UI (lista, configurações, preview).
- **ImageRow** — uma linha da lista (miniatura, nome, quantidade, botões).
- **`imposer_core` (núcleo)** — o módulo sem Tk desde a 1.8.1 (DEC-017): dependências opcionais, constantes, modelo, geometria, PDF, motor e ingestão. `print_imposer.py` é a GUI e o reexporta.

## Comandos / artefatos
- **`print_imposer.py`** — o app inteiro; rodar com `python print_imposer.py`.
- **`compose_page(page_idx, paths, override_dpi=None)`** — monta uma folha; com `override_dpi=72` é o caminho do preview.

## Termos da F3 (interface)
- **Zona fixa** — faixa do painel de configuração que não rola: a Grade no topo, o contador + guarda de qualidade no rodapé. Existe porque conteúdo essencial não pode depender de rolagem (DEC-011).
- **Accordion** — seções colapsáveis empilhadas. No PrintImposer é **multi-aberto** (abrir uma não fecha as outras) e o estado persiste em `sections_open`.
- **Progressive disclosure** — mostrar o essencial e deferir o raramente usado para uma tela secundária (Nielsen, 1995). É o princípio que manda `.bat`, presets e "sobre" para a menubar.
- **Ação × configuração** — distinção que guia o que fica no painel e o que vai para o menu: configuração descreve *como* a folha é montada; ação é algo que se *faz* uma vez (gerar atalho, salvar preset).

## Termos da 1.1
- **Área útil (work area)** — retângulo da tela sem a barra de tarefas. No Windows vem de `SPI_GETWORKAREA`. Diferente de `winfo_screenheight()`, que é a tela física (FIX-005).
- **Nome reservado do Tkinter** — atributo que `tkinter.Misc` usa internamente (`_w`, `_name`, `_tclCommands`, `master`, `tk`, `children`). Escrever neles a partir de uma subclasse quebra o widget (FIX-003).
- **Grade livre** — `cfg.cols × cfg.rows` arbitrários (até 12×12), sem lista cadastrada. Substituiu o dict `NUP_LAYOUTS` (DEC-009).
- **Atalho de grade** (`NUP_SHORTCUTS`) — menu de combinações comuns que apenas *preenche* colunas/linhas. Conveniência, não a fonte de verdade.
- **Preset** — configuração de layout salva com nome em `~/.printimposer/presets.json`. Guarda grade, papel, DPI, margens, corte e formato; **não** guarda caminhos de pasta.
- **Guarda de qualidade** — comparação entre os pixels da imagem-fonte e os da célula no DPI alvo. Veredito: `ok` (≥100%), `warn` (≥75%), `bad` (<75%), `none` (nada a julgar). SVG fica de fora.
- **Back-end de SVG** — `cairosvg` ou `svglib`, escolhido por sondagem com render real (FIX-002). Ausente, `.svg` some da lista de formatos.
- **Smoke test** — checklist manual de 9 itens da GUI, no `CLAUDE.md`. É o que a suíte headless não alcança.
- **Raia de execução** — papel do Claude Code desde a DEC-012: implementa o código a partir da spec/WO, roda suíte e GUI, faz o smoke, commita e empurra no verde. O chat é a raia de planejamento (spec, análise, WO). *(Até 2026-11-03 era «raia de validação», DEC-010.)*

## Termos da F4 (qualidade, corte e sangria)
- **PDF sem perda** — saída PDF do escritor próprio (DEC-014): o fluxo do PNG da folha embutido com `/FlateDecode`, sem recomprimir. O PDF antigo era JPEG por dentro.
- **Guarda de qualidade (imagem interna)** — desde a 1.5.0 a guarda mede também as imagens embutidas numa página PDF (as que cobrem ≥ 10% dela); o selo cita `… .pdf · p. N (imagem interna)`.
- **Corte (trim)** — a borda final da peça depois de cortada; em cada célula, é o retângulo da célula.
- **Sangria (bleed)** — faixa da arte além do corte, para não sobrar fio branco se o corte desviar; padrão de mercado 3 mm. Modos: **espelhar** (o app estende a borda) e **a arte já tem sangria** (a arte foi exportada maior, ex.: A6 = 111 × 154 mm).
- **Marcas de canto (crop marks)** — traços curtos na margem externa, um em cada ponta de cada linha de corte; padrão 4 mm, a 3 mm do corte, 0,25 pt, preto. Com espaçamento entre células, cada espaço tem duas (uma por corte).
- **`sheet_geometry`** — função pura que calcula em mm células, sangria, cortes, marcas e avisos; o motor raster desenha a partir dela, e o desenhista vetorial da F5 vai reusá-la.
- **Portão (da F4)** — a decisão sobre a imposição vetorial, tomada por critério fixado antes de medir; resultado B (DEC-015).
- **Sonda** — medição que o Code roda sem editar o repo nem commitar, devolvendo número cru + comando; o relatório vai para a pasta-pai.
- **Roteiro do dono** — o que o dono abre, faz e vê quando está certo, para conferir uma mudança de interface; vai escrito no chat, no mesmo turno da WO.

## Termos da F5
- **Alça (`≡`)** — o ponto de cada linha da lista por onde se arrasta a imagem para reordenar (1.7.0).
- **Rotação por item (`⟳`)** — 0° segue o Auto-Rotate; 90°, 180° e 270° são exatos e desligam o Auto-Rotate só para aquele item (1.8.0).
- **Preencher** — `Completar a última folha` e `Exatamente N folhas…`: mexem nas quantidades à vista, não num modo escondido (1.8.0).
- **Moldura** — layout não-uniforme: células de tamanhos diferentes na mesma folha (1.9.0, DEC-018).
- **Divisões sucessivas** — o modelo da moldura: a área útil é dividida na vertical ou na horizontal, com proporções, e cada parte pode ser dividida de novo; cortável na guilhotina por construção. A grade `cols × rows` é o caso particular.
- **Slot** — cada célula onde entra uma imagem; na moldura, cada slot tem o seu tamanho e é preenchido em ordem de leitura.
- **Segmento de corte** — na moldura, o corte que atravessa só o pedaço da vez (não a folha inteira); as marcas vão nas pontas que tocam a borda da área útil.

## Ferramentas do fluxo de trabalho
- **KCM / Kit de Contexto Universal** — o sistema de documentação (CEREBRO, CONTEXT, STATUS, DECISIONS…) que permite trocar de conversa sem perder contexto. Versão adotada: v1.133.0 (2026-11-03).
- **ASU (Atualizador Automático de Scripts)** — ferramenta que aplica edições cirúrgicas em arquivos a partir de uma instrução `.yaml`. **Aposentado em 2026-11-03 (DEC-012)**; foi o modo de edição de código de 18/07 a 03/11 (DEC-007). Guia arquivado em `zz_backups/261103-INSTRUCTION_GUIDE-asu.md`.
- **Instrução ASU** — arquivo `AAMMDD-asuNNNN.yaml` com âncoras copiadas literalmente do arquivo real. Aplicada com `python -m src apply <arquivo>.yaml --root <RAIZ> --dry-run`.
- **FlatDrop** — ferramenta que achata a pasta do projeto para upload no Projeto do Claude, gerando `_MANIFEST.md` (mapa nome-plano → caminho real) e `_TREE.md`. O `.flatdropignore` controla o que sobe.
- **WO (ordem de trabalho)** — `meta/workorders/AAMMDD-woNNNN-desc.md`: instrução de APLICAÇÃO (âncora + texto exato) que o chat escreve e o Code aplica com `/apply-wo`. Spec diz o QUÊ; WO diz COMO aplicar.
- **Template-update** — pacote de arquivos genéricos do KCM com sufixo `__template-update`, para comparar com os vivos. Nunca sobrescreve conteúdo vivo.

## Identificadores
- **DEC-N** — decisão de arquitetura/design em DECISIONS.md.
- **FIX-N** — bug grave resolvido em DECISIONS.md.
- **F1…F5** — fases do ROADMAP (F1–F4 concluídas; F5 em curso).
- **N-up livre** — grade definida por `colunas × linhas` arbitrárias, sem lista cadastrada (DEC-009).
- **Preset** — configuração inteira salva com nome: grade + papel + DPI + margens + corte + formato.
