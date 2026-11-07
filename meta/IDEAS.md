# IDEAS.md — Brainstorm e Visão

> **Segundo cérebro** do projeto. Captura TUDO que for mencionado, mesmo solto ou no meio de outro assunto.
> Nunca perde: ideia implementada vai para «Concluídas»; ideia recusada vai para «Descartadas» com o motivo.
> Separar por autor (você × assistente) ajuda a lembrar de onde veio cada coisa.

> **Mudanças nesta revisão (2026-11-04, curadoria pedida pelo dono):**
> - **→ Concluídas** (estavam como ativas já implementadas): compressão configurável (1.3.0), espaçamento por eixo (1.3.0), formatos extras AVIF/HEIC (1.3.0), entrada PDF (1.4.0), `.bat` na pasta-pai (1.2.0), refresh do menu de presets (1.2.0), barra de estado com o custo da folha (rodapé da 1.2.0 + linha da folha da 1.3.0; o «MB estimado» comprimido foi trocado pelo MB bruto, exato — ver SPEC-F4-etapa1 §4).
> - **→ Descartadas:** «Empacotar o SVG junto» — o dono aceitou a recomendação de 04/11: a entrada PDF cobre o caminho vetorial sem depender de cairo; a entrada SVG **continua** para quem tiver o back-end.
> - **→ Adiadas, com gatilho:** «Controle de proporção X/Y» e «Margem do centro vs. bordas» — boa parte já coberta por Esticar, espaçamento X/Y e margens.
> - **Etiquetas de fase corrigidas** para bater com o ROADMAP: várias diziam «F3» (marcas, sangria, vetorial) ou «F4» (moldura, `.exe`) e mudaram de lugar. Ideias sem fase ficam sem etiqueta.
> - **Generalizado «Figma» → qualquer ferramenta** (pedido do dono em 04/11): Figma, Canva, Affinity, Photoshop, Corel, geradores web, foto de celular.
> - **Novas:** o caso do fotógrafo na moldura; saída WebP/AVIF; aviso do segundo destino; tags de versão no git; guarda de qualidade para PDF com imagem raster dentro; feedback ao kit sobre o formato da linha `/apply-wo`.
> - Nada foi apagado: cada ideia que saiu de uma seção está em outra.

---

## 💡 Ideias Ativas — Usuário

### 2026-06 — Moldura de várias fotos (ex.: 2 horizontais iguais + 1 retrato alta)
Layout não-uniforme tipo "moldura". Exige células de tamanhos diferentes — outro modelo que o grid regular. Candidato a "modo de layout customizado". **Caso de uso do dono (04/11):** um fotógrafo pega uma série de fotos e monta, em segundos, várias molduras diferentes com as fotos variadas. **F5.**

### 2026-06 — Fluxo "selecionar forma + selecionar imagens + gerar" (esforço mínimo)
A meta-ideia que guia o produto: depois de exportar as artes — de qualquer ferramenta (Figma, Canva, Affinity, Photoshop, Corel, gerador web) ou de pegar fotos do celular —, só escolher um modo, selecionar as imagens e gerar. Conecta com presets, persistência e hot folder.

### 2026-06 — Borda/traço desenhado na ferramenta de origem como guia de corte
Em vez de o app desenhar marcas, já desenhar a borda fina na arte (frame do Figma, prancheta do Illustrator/Affinity, etc.). Já é possível hoje e é a recomendação atual para arquivos enxutos. Mantido como prática documentada.

### 2026-06 — Imprimir direto, sem salvar arquivo
Mandar para a impressora sem arquivo intermediário. No Windows passa por API de impressão/spooler. Avaliar viabilidade. **F5.**

---

## 🤖 Ideias Ativas — Assistente

### 2026-11-07 — Marcas de corte nos cantos internos (entre células)
Hoje (1.6.0) as marcas de canto ficam só na margem externa, uma por ponta de cada corte — o padrão de cartões em lote. Marca no cruzamento interno ajudaria quem corta com estilete célula a célula, mas com espaçamento pequeno cairia sobre a arte vizinha; ficou fora de escopo na spec da etapa 4. Só faz sentido com espaçamento ≥ 2 × (distância + comprimento). **F5, se pedido.**

### 2026-11-07 — Aviso de sangria externa limitada pela margem
Com margem externa menor que a sangria, a sangria da borda externa é recortada pela margem **sem aviso próprio** — o aviso âmbar da 1.6.0 só cobre o espaçamento entre células (achado da sonda do Code na wo0010). Proposta: aviso âmbar «A margem externa (X mm) é menor que a sangria (Y mm): a sangria da borda vai até X mm». Pequeno; decisão pendente com o dono. **1.6.1 ou primeira versão da F5.**

### 2026-07-22 — Barra de progresso e status também merecem revisão
A barra inferior tem um `CTkProgressBar` sempre visível mesmo parado, ocupando largura sem informar nada. Poderia aparecer só durante a geração, liberando espaço para o texto de status (onde entra o aviso do segundo destino). Pequeno, cosmético, na linha de "o que não informa não ocupa".

### 2026-07-22 — Atalhos de teclado além dos do menu
A F3 trouxe `Ctrl+O`, `Ctrl+Shift+O` e `Ctrl+G`. Valeria também `Ctrl+S` (salvar preset), `Delete` (remover imagem selecionada) e setas para navegar o preview.

### 2026-07-19 — Detector de colisão com nomes do Tkinter como lint permanente
O `TkAttributeCollisionTests` varre o AST atrás de escrita em nome reservado do Tkinter. Valeria virar um lint rodado no `/wrap`, e não só um teste — o custo é o mesmo e a lição vale para todo widget futuro.

### 2026-07-19 — `Image.draft()` também na composição
Hoje o `draft()` só acelera a miniatura. Na composição, quando a célula é bem menor que a fonte JPEG, o mesmo truque cortaria tempo de decodificação sem perda perceptível. Medir antes de adotar.

### 2026-07-19 — Aviso de grade absurda
O teto de 12×12 impede o extremo, mas 10×10 num A4 dá células de ~20 mm: tecnicamente válido, quase sempre inútil. Um aviso explícito de "célula muito pequena para impressão" seria mais direto que esperar o selo de qualidade.

### 2026-06-15 — Entrada vetorial → imposição vetorial *(grande)*
Posicionar PDFs vetorialmente (pypdf/reportlab) em vez de rasterizar: qualidade perfeita, arquivos minúsculos, marcas sem peso. Mudança de arquitetura. **Portão da F4 decidido em 06/11: vai para a F5 (DEC-015).** Medido: nitidez do texto melhora de forma visível na tela; o arquivo não fica menor para o conteúdo do dono (bitmap embutido). **Volta antes** se uma impressão em gráfica de ponta mostrar o texto raster mole.

### 2026-06-15 — Drag-and-drop de arquivos na janela
Arrastar do Explorer para a lista, via `tkinterdnd2` com wrapper sobre `CTk`. Dependência opcional — degradar com elegância se ausente. **F5.**

### 2026-06-15 — Reordenar a lista arrastando
Drag-and-drop interno (hoje só ▲ ▼). Melhora a UX com muitos itens. **F5.**

### 2026-06-15 — Rotação manual por imagem
Toggle 90° por item, além do Auto-Rotate global. **F5.**

### 2026-06-15 — Preenchimento automático para N folhas
"Repetir até encher a última folha" ou "preencher exatamente X folhas". Acelera tiragens. **F5.**

### 2026-06-15 — Empacotar como .exe (PyInstaller)
Executável Windows para quem não tem Python. **F5.**

---

## 🔧 Feedback para o Kit
> Desvios estruturais e atritos do KCM observados neste projeto. É o material que volta para evoluir o kit.

- **2026-07-18 — `HISTORICO.md` → `HISTORY.md`.** O kit v1.73 padronizou o nome em inglês; o projeto nasceu com o nome em PT. Renomeado nesta sessão (ver DEC-008). Atrito de uma vez só, mas vale o kit sinalizar a renomeação em updates futuros.
- **2026-07-18 — Template-update veio com `Code nao` e apagaria a raia Code.** O pacote genérico não sabe quais modos o projeto tinha ligados; adotá-lo cru teria removido 67 linhas de comportamento. O protocolo de "reportar, não aplicar" funcionou — mas o manifesto poderia avisar explicitamente quais seções o update REMOVE em relação ao vivo.
- **2026-07-18 — `DECISOES.md` × `DECISIONS.md` no CEREBRO.** A raia Code do kit referenciava `meta/DECISOES.md` em 3 pontos, enquanto o arquivo real é `DECISIONS.md`. Inconsistência do próprio template; resolvida ao remover a seção.
- **2026-07-18 — Seções «Feedback para o Kit» e «Feedback para o ASU» não estão no template do IDEAS.** O CEREBRO exige as duas, mas o `IDEAS__template-update.md` não as traz — quem gera o IDEAS do zero pelo template nasce sem elas (foi o que aconteceu aqui). Sugestão: incluí-las no molde.
- **2026-07-18 — Instruções do template chegam em 6.892 de 6.900 caracteres.** Zero folga para especializar. Enxugadas para 5.350 nesta sessão cortando descrições que já vivem no CEREBRO. Sugestão: o molde já entregar as descrições curtas.
- **2026-11-03 — CEREBRO de fusão sem nenhuma linha própria.** Das 182 linhas não vazias do CEREBRO vivo (v1.73), as 46 ausentes do template v1.133 eram todas texto antigo do kit, a seção ASU e o carimbo — a «fusão» virou adoção. Sugestão: o manifesto mandar medir isto PRIMEIRO (linhas do vivo ausentes do template), porque decide se o merge é fusão ou troca e poupa a comparação bloco a bloco.
- **2026-11-03 — Revogação pelo fato achou o que o termo não acha.** A linha revogada v1.104 («não empurrar») vivia também no `.claude/settings.json` (deny `git push`), que nenhum `grep` pelo texto da tabela alcança. Sugestão: a tabela de revogadas citar também a forma em config, não só em prosa.
- **2026-11-03 — `IDEAS__template-update` ainda traz «Feedback para o ASU» com o pacote declarando `ASU nao`.** Inconsistência do molde: a seção devia sair junto do modo.
- **2026-11-03 — Instruções do painel × arquivo do repo divergiram em silêncio.** O painel do Projeto ficou com a versão genérica enquanto o arquivo do repo evoluía (ASU, nome de download). A regra «a fonte é o arquivo do repositório» só chegou na v1.133; antes dela não havia quem notasse.
- **2026-11-03 — A WO de migração para skills dependia da skill que ela criava.** O pacote v1.133 manda migrar `.claude/commands/` → `.claude/skills/` por WO, e a WO se aplica com `/apply-wo` — que é uma das skills a criar. Projeto vindo de `commands/` trava no primeiro passo. Sugestão: o `_UPDATE-PROMPT` mandar instalar as skills do pacote ANTES de qualquer WO (fora da WO), e a regra «a ponte do chat não grava em `.claude/`» virar «confira se grava» — nesta máquina grava (DEC-013).
- **2026-11-04 — A linha `/apply-wo` das Instruções é modelada em código inline, contra a regra do bloco cercado.** O CEREBRO manda «todo comando que o dono copia vai em bloco cercado, nunca em código inline», mas a linha das Instruções que o assistente lê a cada turno mostra o comando inline («entregue junto a linha `/apply-wo <arquivo>`») — e é o exemplo que vence. O dono reclamou depois de sete WOs. Sugestão: a própria linha das Instruções dizer «em bloco cercado» e o esqueleto do fecho trazer o bloco. No mesmo espírito: o roteiro que é do dono vai **no chat**, não só dentro do arquivo da WO — a regra «no MESMO turno» não diz ONDE, e o assistente o escondeu no arquivo.

## 🔩 Feedback para o ASU
> **Congelado em 2026-11-03:** o ASU foi aposentado (DEC-012). As entradas abaixo ficam como histórico; nada novo entra aqui.
- **2026-07-22 — Transferência de conversa via ASU funciona, com uma ressalva.** O prompt de handoff do KCM manda atualizar os `.md` por instrução ASU (não devolver arquivo inteiro). Respeitado nesta transferência: as mudanças eram pequenas e pontuais (marcar o ASU0003 como aplicado, apontar o brief), caso ideal para `replace_line_pattern`/`replace_context_block`. Ressalva honesta: quando a atualização de fim de sessão reescreve **seções inteiras** de um doc rolante (STATUS, IDEAS), o ASU perde para o arquivo inteiro — múltiplas âncoras num texto que mudou muito é frágil. Regra prática: mudança pontual no `.md` → ASU; reescrita de seção → arquivo inteiro. O KCM poderia distinguir os dois casos no prompt de handoff.
> Limitações e pedidos de melhoria da ferramenta, observados em uso.

- **2026-07-22 — `replace_method` desalinha continuação de docstring multi-linha.** Aplicando `260719-asu0002.yaml`, o re-indent deslocou **10 linhas** de continuação de docstring (ficaram em 4 espaços dentro de método indentado a 4, quando deveriam ter 8). Sem efeito na execução — está dentro de string literal — mas feio. Parece que o re-indent trata só a primeira linha de cada statement. **Contorno adotado:** para consertar, usar `replace_line_pattern` e `replace_context_block`, que gravam verbatim e não passam pelo re-indent.
- **2026-07-22 — `insert_before_pattern` insere verbatim; `replace_method` re-indenta.** Os dois se comportam de forma oposta quanto à indentação, e isso não está explícito no guia. Custou a falha do `260719-asu0001.yaml`: emiti o `content` dedentado (como se faz no `replace_method`), o `def` entrou na coluna 0, **fechou a classe** e engoliu 12 métodos como funções aninhadas. Sugestão para o guia: uma linha na tabela de estratégias dizendo qual estratégia re-indenta e qual não.
- **2026-07-22 — Simulador de instrução precisa espelhar a ferramenta, não idealizá-la.** Meu simulador reindentava o `insert`, então a instrução passava na simulação e falhava na aplicação. Lição: simular com a semântica real e rodar `ast.parse` **a cada passo**, não só no fim.
- **2026-07-22 — Âncora de `replace_context_block` precisa de duas linhas às vezes.** `        cfg = self.cfg` sozinho aparece 2× no arquivo; `        cfg = self.cfg\n        cols, rows = self._grid()` é único. Vale o guia sugerir explicitamente âncoras multi-linha quando a linha isolada é genérica.
- **2026-07-19 — Primeira instrução ASU do projeto: `260719-asu0001.yaml`.** 12 modificações em 2 arquivos, todas `replace_method` / `insert_before_pattern` / `replace_line_pattern`. Observações de uso: (a) `replace_method` foi a estratégia mais confortável — dispensa âncora literal, então não há risco de errar indentação; (b) a única inserção precisou de `pattern` com regex escapado (`^    def _setup_geometry\(self\):`), e foi tranquilo; (c) **antes de emitir, simulei a aplicação** e comparei com o arquivo já testado — o resultado bateu byte a byte. Recomendo que isso vire hábito: instrução ASU gerada às cegas é aposta.
- **2026-07-19 — A F2 não usou ASU, e o motivo vale registrar.** A entrega tocou constantes, `LayoutConfig`, o engine, três painéis e o `main()`. Um patch com 15+ âncoras num arquivo em reestruturação é frágil e não dá para verificar sem aplicar. Foi entregue arquivo inteiro, como a DEC-007 prevê para reescrita profunda. **O ASU passa a ser o caminho natural agora**: com a 1.1.0 estabilizada, os próximos ajustes são localizados (ex.: o refresh do menu de presets) — exatamente o caso dele.

---

## 🛌 Adiadas
> Decisão consciente de não fazer agora. Cada item com **o gatilho que a traz de volta**: ideia adiada sem gatilho é ideia perdida.
- **Corrigir a numeração duplicada do HISTORY (seções 4 e 5 aparecem duas vezes)** — adiada porque renumerar quebra ponteiros: o código cita HISTORY §6 e §8, a SPEC-F3 e o ROADMAP citam §9 — **volta quando** o HISTORY ganhar a próxima seção (aí resolve-se com sufixo nas duplicadas, sem renumerar as citadas).
- **Controle de proporção X/Y das imagens** *(usuário, 2026-06)* — ajustar a proporção horizontal/vertical dentro do slot, além de fit/fill/stretch. Adiada em 04/11: o modo Esticar já força proporção livre e o espaçamento X/Y da 1.3 cobre a folga por eixo — **volta quando** aparecer uma arte concreta que nenhum dos três modos encaixe direito.
- **Margem do centro vs. margem das bordas (encolher a imagem para criar folga)** *(usuário, 2026-06)* — controle separado de margem entre imagens e bordas externas, encolhendo a imagem para criar a folga. Adiada em 04/11: margem externa e espaçamento X/Y já são independentes e a célula encolhe junto — **volta quando** faltar um ajuste que esses três campos não façam.

---

## ✅ Concluídas
> Ideia que virou realidade. Mantida aqui para histórico (com referência à versão/decisão).
- **Marcas de corte de canto** *(assistente, 2026-06-15)* — implementadas na 1.6.0 (F4, etapa 4), na margem externa, uma por ponta de cada linha de corte; padrão 4 mm, a 3 mm, 0,25 pt. Cantos internos ficaram de fora.
- **Sangria configurável** *(assistente, 2026-06-15)* — implementada na 1.6.0 (F4, etapa 4): espelhar a borda ou usar a sangria da arte; limitada ao espaço entre as células.
- **Saída WebP e AVIF** *(usuário, 2026-11-04)* — implementada na 1.5.0, para compartilhar (WebP sem perda ou com perda; AVIF com qualidade).
- **Guarda de qualidade olhando as imagens dentro do PDF** *(assistente, 2026-11-04)* — implementada na 1.5.0: imagens que cobrem ≥ 10% da página entram no selo com a resolução efetiva na célula.
- **Erro de abertura visível mesmo via `.bat`** *(assistente, 2026-07-19)* — implementado na 1.4.1: janela de erro + `~/.printimposer/last_error.log`.
- **Configuração congelada durante a geração** *(assistente, 2026-07-19)* — implementado na 1.4.1: a geração trabalha sobre cópias do `LayoutConfig` e da lista.
- **Aviso visível do segundo destino** *(assistente, 2026-11-04)* — implementado na 1.4.1: «Também grava em: …» na barra inferior, em âmbar para pasta inexistente ou temporária.
- **Tags de versão no git** *(assistente, 2026-11-04)* — criadas na wo0008 (`v1.1.1` … `v1.4.1`).
- **Entrada PDF** *(assistente, 2026-07-18)* — implementada na 1.4.0 (F4 etapa 2), via `pypdfium2` opcional; uma página por item, rasterizada já na orientação final (`meta/specs/261104-SPEC-F4-etapa2.md`).
- **Compressão configurável na saída** *(usuário, 2026-06)* — implementada na 1.3.0: PDF sem perda por padrão (DEC-014) ou JPEG com qualidade 50–100; medido em 03/11 que o PDF antigo era JPEG por dentro.
- **Espaçamento por eixo (X/Y)** *(usuário, 2026-06)* — implementado na 1.3.0, compatível com presets antigos.
- **Formatos de entrada extras** *(assistente, 2026-07-18)* — AVIF nativo do Pillow 12.2 e HEIC via `pillow-heif` opcional, na 1.3.0. GIF já entrava.
- **Barra de estado com o "custo" da folha** *(assistente, 2026-07-18)* — rodapé fixo da 1.2.0 (selo de qualidade e célula) + linha «Folha: … px · … MB bruto» da 1.3.0. O MB **comprimido** estimado foi recusado por não ser honesto (depende do conteúdo).
- **Refresh imediato do menu de presets** *(assistente, 2026-07-19)* — resolvido na 1.2.0 por construção: o submenu `Opções › Presets` é reconstruído a cada abertura.
- **`.bat` gerado na pasta-pai do projeto** *(usuário, 2026-07-23)* — implementado na 1.2.0 (SPEC-F3 §6).
- **Menubar, accordion e resumo fixo** — implementados na 1.2.0 (F3, DEC-011).
- **Grade livre `cols × rows` pela interface** — implementada na 1.1.0 (DEC-009). Resolve o 2×6 sem editar código.
- **Persistência de configuração e presets nomeados** — implementada na 1.1.0 (`~/.printimposer/`).
- **Janela centralizada, com clamp e DPI awareness** — implementada na 1.1.0.
- **Pasta de saída em Downloads; entrada e saída independentes; segundo destino** — implementados na 1.1.0.
- **PNG como formato padrão** — implementado na 1.1.0.
- **Entrada SVG** — implementada na 1.1.0, antecipada da F3 (zero upscale por construção).
- **Gerador de `.bat` da GUI** — implementado na 1.1.0 (ASCII puro, CRLF, sem console).
- **Guarda de qualidade (aviso de upscale)** — implementada na 1.1.0.
- **Miniatura do grid** e **botão "+ Pasta"** — implementados na 1.1.0.
- **Otimização segura de carregamento** — `Image.draft()` em JPEG + cache de miniatura, na 1.1.0.
- **Imposição N-up com preview e saída multi-formato** — implementada em 1.0.0.
- **Auto-Rotate conforme orientação do slot** — implementada em 1.0.0.
- **Linhas de corte com estilo/espessura/cor** — implementada em 1.0.0 (forma de canto vai para a F4, etapa 4; ver DEC-005).
- **Quantidade por imagem (step-and-repeat básico)** — implementada em 1.0.0.

---

## 🚫 Descartadas
> Ideia avaliada e recusada. O motivo evita reabrir a discussão depois.
- **Empacotar ou instalar um back-end de SVG no Windows** *(assistente, 2026-07-19)* — descartada em 04/11 por recomendação aceita pelo dono: nenhum back-end é Python puro (cairo nativo, ver FIX-002), e a entrada PDF da 1.4.0 cobre o caminho vetorial com um `pip install` só. **A entrada SVG continua** para quem já tiver `cairosvg` ou `svglib`; só deixa de ser meta instalá-la aqui.
- **SVG como formato de saída** — com arte raster, o SVG só embutiria os bitmaps: nenhum ganho de qualidade ou tamanho. O caminho para qualidade vetorial é a entrada PDF (1.4.0) e, se aprovada, a imposição vetorial. *(Entrada SVG continua ativa.)*
- **Raia de desenvolvimento no Claude Code** — descartada como modo padrão em 2026-07-18 (DEC-007): o projeto é um arquivo único, sem build e sem suíte, onde a cerimônia do Code (CLAUDE.md, `.claude/`, specs) custa mais do que rende. Substituída pelo ASU. *Gatilho de reabertura registrado na DEC-007.* **Reaberta e adotada em 2026-11-03 — ver DEC-012:** o gatilho disparou na F2 (FIX-003..005) e o kit v1.133 ligou o modo Code.
- **Cadastro de layouts em lista JSON editável pela UI** — substituído pela grade livre `cols × rows` + presets nomeados, que resolve o mesmo problema sem construir um editor de lista. *(A persistência em JSON continua — o que caiu foi a lista de layouts como estrutura.)*
