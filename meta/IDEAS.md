# IDEAS.md — Brainstorm e Visão

> **Segundo cérebro** do projeto. Captura TUDO que for mencionado, mesmo solto ou no meio de outro assunto.
> Nunca perde: ideia implementada vai para «Concluídas»; ideia recusada vai para «Descartadas» com o motivo.
> Separar por autor (você × assistente) ajuda a lembrar de onde veio cada coisa.

---

## 💡 Ideias Ativas — Usuário

### 2026-06 — Moldura de 3 fotos (2 horizontais iguais + 1 retrato alta)
Layout não-uniforme tipo "moldura". Exige células de tamanhos diferentes — outro modelo que o grid regular. Candidato a "modo de layout customizado". **F4.**

### 2026-06 — Fluxo "selecionar forma + selecionar imagens + gerar" (esforço mínimo)
A meta-ideia que guia o produto: depois de exportar os A6 do Figma, só escolher um modo, selecionar as imagens e gerar. Conecta com presets, persistência e hot folder.

### 2026-06 — Borda/traço desenhado no Figma como guia de corte
Em vez de o script desenhar marcas, já desenhar a borda fina no frame. Já é possível hoje e é a recomendação atual para arquivos enxutos. Mantido como prática documentada.

### 2026-06 — Controle de proporção X/Y das imagens
Ajustar a proporção horizontal/vertical dentro do slot, além de fit/fill/stretch. Investigar se agrega sobre os três modos ou vira opção avançada.

### 2026-06 — Níveis de qualidade/compressão configuráveis
Escolher o grau de compressão da saída (lossless × JPEG com qualidade). Ver HISTORY §2. **F3.**

### 2026-06 — Margem do centro vs. margem das bordas (e encolher a imagem para criar folga)
Controle separado: aumentar a margem entre imagens OU as bordas externas, encolhendo a imagem proporcionalmente para criar a folga.

### 2026-06 — Margem por eixo (só horizontal ou só vertical)
Espaçamento independente em X e em Y, em vez de um valor único "entre imagens".

### 2026-06 — Imprimir direto, sem salvar arquivo
Mandar para a impressora sem arquivo intermediário. No Windows passa por API de impressão/spooler. Avaliar viabilidade.

### 2026-07-23 — `.bat` gerado na pasta-pai do projeto, não na Área de Trabalho
Nota do dono: «o .bat é para ser gerado em uma pasta "anterior" a pasta raíz do projeto, entende? E não na área de trabalho, assim fica mais fácil para mim, organizar.» Vira requisito do diálogo do `.bat` na F3 (SPEC-F3 §6). **F3.**

---

## 🤖 Ideias Ativas — Assistente

### 2026-07-19 — Empacotar o SVG junto (resolver a dependência no Windows)
Descoberto na implementação: **nenhum dos dois back-ends é Python puro na hora de desenhar** — `cairosvg` quer libcairo, `svglib` quer `rlPyCairo`/`_rl_renderPM` (ver FIX-002). Para o SVG funcionar na máquina do usuário sem dor, avaliar: (a) documentar o `pip install` certo para Windows, (b) embutir as DLLs no .exe da F4, ou (c) um terceiro caminho (`resvg` via binário, Inkscape CLI). Sem isso, o recurso existe mas pode nunca ligar.

### 2026-07-22 — Barra de progresso e status também merecem revisão
A F3 arruma a coluna central, mas a barra inferior continua com um `CTkProgressBar` sempre visível mesmo parado, ocupando largura sem informar nada. Poderia aparecer só durante a geração, liberando espaço para o texto de status. Pequeno, cosmético, mas na mesma linha de "o que não informa não ocupa".

### 2026-07-22 — Atalhos de teclado além dos do menu
A F3 traz `Ctrl+O`, `Ctrl+Shift+O` e `Ctrl+G`. Valeria também `Ctrl+S` (salvar preset), `Delete` (remover imagem selecionada) e setas para navegar o preview. Só depois que a menubar existir, para não espalhar binding.

### 2026-07-19 — Detector de colisão com nomes do Tkinter como lint permanente
O `TkAttributeCollisionTests` varre o AST atrás de escrita em nome reservado do Tkinter. Hoje cobre `GridPreview` e qualquer classe que herde de `tk.*`/`ctk.*`. Valeria virar um lint rodado no `/wrap`, e não só um teste — o custo é o mesmo e a lição vale para todo widget futuro.

### 2026-07-19 — Congelar o `LayoutConfig` durante a geração
FIX-004 tirou a mutação, mas o engine ainda **lê** o `cfg` vivo enquanto compõe: mudar o papel no meio de uma geração longa ainda produziria folhas com geometrias diferentes na mesma leva. Uma cópia (`dataclasses.replace` / `copy`) no início de `generate_all` fecharia isso de vez. Não é urgente — exige mexer nas opções durante a geração —, mas é a mesma classe de problema.

### 2026-07-19 — Aviso quando `pythonw` engole o traceback
O smoke mostrou que, via `.bat` com `pythonw`, uma falha na abertura é **100% silenciosa**: duplo clique e nada acontece. Vale um `try/except` no `main()` que grave o traceback em `~/.printimposer/last_error.log` e mostre um `messagebox` — assim o usuário vê o erro mesmo sem console.

### 2026-07-19 — Refresh imediato do menu de presets
O `CTkOptionMenu` de presets só reflete um preset recém-salvo depois de reabrir o app: o `configure(values=...)` está sendo feito por varredura frágil da árvore de widgets. Guardar a referência do menu num atributo e atualizar direto. Pequeno, mas é atrito visível.

### 2026-07-19 — `Image.draft()` também na composição
Hoje o `draft()` só acelera a miniatura. Na composição, quando a célula é bem menor que a fonte JPEG, o mesmo truque cortaria tempo de decodificação sem perda perceptível — o alvo já é uma redução. Medir antes de adotar.

### 2026-07-19 — Aviso de grade absurda
O teto de 12×12 impede o extremo, mas 10×10 num A4 dá células de ~20 mm: tecnicamente válido, quase sempre inútil. A guarda de qualidade já avisa por causa do upscale, mas um aviso explícito de "célula muito pequena para impressão" seria mais direto.

### 2026-07-18 — Entrada PDF (vetorial) — irmã da entrada SVG
O Figma exporta PDF. PDF de entrada tem o mesmo ganho do SVG (rasterizar na resolução exata da célula, zero upscale) e é o degrau natural para a imposição vetorial. Tratar SVG e PDF como a mesma família de entrada.

### 2026-07-18 — Formatos de entrada extras de baixo custo
`pillow-heif` (HEIC/AVIF, fotos de celular) e GIF/ICO já suportados pelo Pillow. Custo quase zero, cobre "arrastei o que tinha na pasta".

### 2026-07-18 — Barra de estado com o "custo" da folha
Mostrar, ao vivo: tamanho final em px, MB estimados e um selo verde/amarelo/vermelho de qualidade. Transforma DPI e upscale em algo visível antes de gerar.

### 2026-06-15 — Drag-and-drop de arquivos na janela
Arrastar do Explorer para a lista, via `tkinterdnd2` com wrapper sobre `CTk`. Dependência opcional — degradar com elegância se ausente.

### 2026-06-15 — Marcas de corte de canto (padrão de indústria)
Ticks curtos nos cantos de cada slot, dentro do gutter, em vez de linhas atravessando a folha. Mais profissional e quase sem peso no arquivo. **F3.**

### 2026-06-15 — Sangria (bleed) configurável
Campo em mm: a arte transborda o limite de corte para evitar borda branca depois do corte. **F3.**

### 2026-06-15 — Reordenar a lista arrastando
Drag-and-drop interno (hoje só ↑↓). Melhora a UX com muitos itens.

### 2026-06-15 — Rotação manual por imagem
Toggle 90° por item, além do Auto-Rotate global.

### 2026-06-15 — Preenchimento automático para N folhas
"Repetir até encher a última folha" ou "preencher exatamente X folhas". Acelera tiragens.

### 2026-06-15 — Entrada vetorial → imposição vetorial *(grande)*
Posicionar PDFs vetorialmente (pypdf/reportlab) em vez de rasterizar: qualidade perfeita, arquivos minúsculos, marcas sem peso. Mudança de arquitetura. **F3.**

### 2026-06-15 — Empacotar como .exe (PyInstaller)
Executável Windows para quem não tem Python. **F4.**

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

---

## ✅ Concluídas
> Ideia que virou realidade. Mantida aqui para histórico (com referência à versão/decisão).
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
- **Linhas de corte com estilo/espessura/cor** — implementada em 1.0.0 (forma de canto fica para F3, ver DEC-005).
- **Quantidade por imagem (step-and-repeat básico)** — implementada em 1.0.0.

---

## 🚫 Descartadas
> Ideia avaliada e recusada. O motivo evita reabrir a discussão depois.
- **SVG como formato de saída** — com arte raster, o SVG só embutiria os bitmaps: nenhum ganho de qualidade ou tamanho. O caminho para qualidade vetorial é a entrada PDF (F3). *(Entrada SVG continua ativa.)*
- **Raia de desenvolvimento no Claude Code** — descartada como modo padrão em 2026-07-18 (DEC-007): o projeto é um arquivo único, sem build e sem suíte, onde a cerimônia do Code (CLAUDE.md, `.claude/`, specs) custa mais do que rende. Substituída pelo ASU. *Gatilho de reabertura registrado na DEC-007.* **Reaberta e adotada em 2026-11-03 — ver DEC-012:** o gatilho disparou na F2 (FIX-003..005) e o kit v1.133 ligou o modo Code.
- **Cadastro de layouts em lista JSON editável pela UI** — substituído pela grade livre `cols × rows` + presets nomeados, que resolve o mesmo problema sem construir um editor de lista. *(A persistência em JSON continua — o que caiu foi a lista de layouts como estrutura.)*
