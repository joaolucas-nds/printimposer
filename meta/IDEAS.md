# IDEAS.md — Brainstorm e Visão

> **Segundo cérebro** do projeto. Captura TUDO que for mencionado, mesmo solto ou no meio de outro assunto.
> Nunca perde: ideia implementada vai para «Concluídas»; ideia recusada vai para «Descartadas» com o motivo.
> Separar por autor (você × assistente) ajuda a lembrar de onde veio cada coisa.

---

## 💡 Ideias Ativas — Usuário

### 2026-06 — Fluxo "selecionar forma + selecionar imagens + gerar" (esforço mínimo)
A meta-ideia que guia o produto: depois de exportar os A6 do Figma, só escolher um modo de impressão, selecionar as imagens e gerar — sem reconfigurar nada toda vez. Conecta com presets (.json) e hot folder.

### 2026-06 — Moldura de 3 fotos (2 horizontais iguais + 1 retrato alta)
Layout não-uniforme tipo "moldura": duas imagens horizontais de mesmo tamanho e uma retrato ocupando a altura. Hoje o grid é regular (cols×rows); isto exige layout por células de tamanhos diferentes. Candidato a um "modo de layout customizado". Requer planejamento de UI próprio.

### 2026-06 — Borda/traço desenhado no Figma como guia de corte
Em vez de o script desenhar marcas, já desenhar a borda fina dentro do frame no Figma; ao juntar 4, os riscos já vêm prontos. Já é possível hoje e é a recomendação atual para arquivos enxutos. Mantido como prática documentada (CONTEXT/README).

### 2026-06 — Controle de proporção X/Y das imagens
Poder ajustar a proporção horizontal/vertical da imagem dentro do slot, além de fit/fill/stretch. Investigar se agrega sobre os três modos atuais ou vira opção avançada.

### 2026-06 — Níveis de qualidade/compressão configuráveis
Escolher o grau de compressão da saída (lossless × JPEG com qualidade ajustável). Responde diretamente à dúvida "é compressão mesmo?" — sim. Ver HISTORICO §2. Bom par com a guarda de qualidade.

### 2026-06 — Margem do centro vs. margem das bordas (e encolher a imagem para criar folga)
Controle separado de espaçamento: aumentar a margem entre as imagens (centro) OU as bordas externas, e, ao aumentar, encolher proporcionalmente as imagens para criar a folga. Hoje há "margem externa" e "entre imagens" em mm; falta a noção de margem por eixo (só horizontal ou só vertical) e o feedback de encolhimento.

### 2026-06 — Margem por eixo (só horizontal ou só vertical)
Permitir definir espaçamento independente em X e em Y (não um valor único "entre imagens"). Extensão natural do item acima.

### 2026-06 — Imprimir direto, sem salvar arquivo
Mandar para a impressora sem gerar arquivo intermediário. No Windows isso passa por API de impressão (ex.: enviar o PDF para o spooler). Avaliar viabilidade/portabilidade.

### 2026-06 — SVG como entrada
Aceitar SVG direto. Pillow não rasteriza SVG; exigiria cairosvg ou Inkscape como conversor. Ver HISTORICO §3 para o porquê e o caminho. Mantida ativa, com ressalva de dependência.

---

## 🤖 Ideias Ativas — Assistente
> Surgidas da pesquisa profissional de imposição/prepress (HISTORICO §4). Ordenadas ~por relação valor/custo.

### 2026-06-15 — Guarda de qualidade (avisar upscale)
No preview/geração, comparar pixels da fonte com o tamanho da célula no DPI alvo; se a fonte for menor, avisar que haverá upscale e perda. Baixo custo, alto valor — ataca direto a preocupação "não perder qualidade do Figma". Já no backlog do STATUS.

### 2026-06-15 — Presets de configuração (.json) salvar/carregar
Salvar combinações (ex.: "A6→A4 4-up, sem margem, sem corte") e recarregar com um clique. Núcleo do "esforço mínimo". `LayoutConfig` já tem `to_dict`/`from_dict` — falta a UI e a persistência.

### 2026-06-15 — Adicionar pasta inteira
Botão "Adicionar pasta" que varre e inclui todas as imagens suportadas de um diretório, em ordem natural de nome. Menos cliques que multi-seleção.

### 2026-06-15 — Lembrar últimas configurações e última pasta
Persistir o último estado (config + pasta de saída) entre execuções, em um `~/.printimposer.json`. Reduz reconfiguração.

### 2026-06-15 — Drag-and-drop de arquivos na janela
Arrastar imagens do Explorer para a lista. Viável via `tkinterdnd2` com wrapper de classe sobre `CTk` (confirmado na comunidade CustomTkinter). Dependência externa opcional — degradar com elegância se ausente.

### 2026-06-15 — Marcas de corte de canto (padrão de indústria)
Substituir/complementar as linhas que atravessam a folha por ticks curtos nos cantos de cada slot, dentro do gutter. Mais profissional e quase sem peso no arquivo. Requer gutter mínimo. Par natural do caminho vetorial (F3).

### 2026-06-15 — Sangria (bleed) configurável
Campo de bleed em mm: a arte transborda o limite de corte para evitar borda branca após o corte. Para cards sem borda é importante. Define como o slot recorta/estende a imagem.

### 2026-06-15 — Reordenar a lista arrastando
Drag-and-drop interno para reordenar imagens (hoje só ↑↓). Melhora a UX quando há muitos itens.

### 2026-06-15 — Rotação manual por imagem
Toggle 90° por item, além do Auto-Rotate global, para casos em que o automático não acerta a intenção.

### 2026-06-15 — Preenchimento automático para N folhas
Modo "preencher X folhas": dada uma seleção, repetir as imagens para completar exatamente X folhas (ou "repetir até encher a última"). Acelera tiragens.

### 2026-06-15 — Entrada vetorial (PDF) → imposição vetorial *(grande)*
Aceitar PDFs do Figma e posicioná-los vetorialmente (pypdf/reportlab), preservando qualidade perfeita e gerando arquivos minúsculos. É o maior salto de qualidade possível e resolve junto o peso das marcas. Mudança de arquitetura — fase própria no ROADMAP (F3).

### 2026-06-15 — Escolha de compressão na saída
Expor lossless × JPEG (com slider de qualidade) na geração; avaliar `img2pdf` para PDF. Implementa o desejo do usuário de "níveis de compressão" de forma explícita e consciente.

### 2026-06-15 — Empacotar como .exe (PyInstaller)
Distribuir um executável Windows para quem não tem Python. `tkinterdnd2` tem hook próprio para PyInstaller. Facilita adoção.

---

## ✅ Concluídas
> Ideia que virou realidade. Mantida aqui para histórico (com referência à versão/decisão).
- **Imposição N-up de imagens em folhas com preview e saída multi-formato** — implementada em 1.0.0.
- **Auto-Rotate de imagens conforme orientação do slot** — implementada em 1.0.0.
- **Linhas de corte com estilo/espessura/cor** — implementada em 1.0.0 (forma de canto fica para F3, ver DEC-005).
- **Quantidade por imagem (step-and-repeat básico)** — implementada em 1.0.0.

---

## 🚫 Descartadas
> Ideia avaliada e recusada. O motivo evita reabrir a discussão depois.
- **SVG como formato de saída** — descartada porque, com imagens raster compostas, o SVG só embutiria os rasters (nenhum ganho de qualidade ou tamanho); o caminho correto para qualidade vetorial é PDF vetorial de entrada (ver ideia do assistente / F3). *(Entrada SVG continua ativa; é a saída SVG que foi descartada.)*
