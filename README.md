# 🖨 PrintImposer v1.2

**Imposição de páginas para impressão em massa** — junte dezenas de imagens em folhas prontas para imprimir e cortar.

Você tem vários cards (por exemplo, A6 exportados do Figma) e quer imprimi-los quatro por folha A4, sem arrastar arquivo por arquivo no diálogo de impressão. O PrintImposer faz isso em três passos: **escolha a grade → adicione as imagens → gere**.

- Grade livre de **colunas × linhas** (até 12 × 12), com atalhos prontos (2×2, 2×6, 4×3…)
- **Guarda de qualidade**: avisa quando a imagem é pequena demais para a célula e vai perder nitidez
- Saída **PNG** (padrão), **PDF**, **JPEG** ou **TIFF**, em até **dois destinos** ao mesmo tempo
- Entrada PNG, JPEG, TIFF, BMP, WEBP, GIF — e **SVG**, quando há um back-end instalado
- **Presets** nomeados e configuração lembrada entre aberturas
- Atalho `.bat` para abrir com dois cliques, sem janela de console

---

## ⚙️ Instalação

**Pré-requisitos:** Python 3.9 ou superior (testado até 3.14 no Windows).

```
pip install customtkinter pillow
python print_imposer.py
```

### SVG (opcional)
Para aceitar `.svg` como entrada, instale **um** destes back-ends:

```
pip install cairosvg
```
ou
```
pip install svglib rlPyCairo
```

No Windows, nenhum dos dois é 100% Python na hora de desenhar: o `cairosvg` precisa da biblioteca nativa **libcairo**, e o `svglib` precisa do `rlPyCairo`. O app testa se o back-end **desenha de verdade** antes de ligar o recurso. O cabeçalho mostra o resultado: `SVG: cairosvg`, `SVG: svglib` ou `SVG: indisponível`. Indisponível, o `.svg` simplesmente não aparece no seletor — nada quebra.

### Abrir com dois cliques
Use **`Opções › Criar atalho…`**. O diálogo explica o que o atalho faz e sugere salvá-lo na pasta **acima** da pasta do projeto (onde fica a pasta `printimposer`). O `.bat` gerado abre o app sem janela de console e grava caminhos absolutos — se você mover a pasta do projeto, gere outro.

---

## 🖥 A janela

```
┌ PrintImposer   Arquivo  Opções  Ajuda              v1.2.0 · SVG: … ┐
├────────────┬──────────────────────────────┬────────────────────────┤
│ Imagens    │ Grade (colunas × linhas)  ◼◼ │ Preview         ◀  ▶   │
│            │ ┌ seções recolhíveis ──────┐ │                        │
│ + Arquivos │ │ ▸ Papel e resolução      │ │                        │
│ + Pasta    │ │ ▸ Ajuste da imagem       │ │                        │
│            │ │ ▸ Margens e espaçamento  │ │                        │
│            │ │ ▸ Linhas de corte        │ │                        │
│            │ │ ▾ Saída                  │ │                        │
│            │ └──────────────────────────┘ │                        │
│            │ 12 img · 4 por folha · 3 fl. │                        │
│            │ ✔ Qualidade OK · Célula …    │                        │
├────────────┴──────────────────────────────┴────────────────────────┤
│ [Gerar Arquivos]  ███████████░░░░░                        Pronto   │
└────────────────────────────────────────────────────────────────────┘
```

A coluna do meio tem três zonas:
- **Topo, sempre visível — a grade.** É o que muda a cada trabalho.
- **Meio — seções recolhíveis.** Abra quantas quiser; o app lembra quais ficaram abertas. No primeiro uso só **Saída** vem aberta.
- **Rodapé, sempre visível — o resumo:** quantas imagens, quantas por folha, quantas folhas, o tamanho da célula e o selo de qualidade.

### Imagens (esquerda)
| Elemento | O que faz |
|---|---|
| **+ Arquivos** / **+ Pasta** | Adiciona imagens soltas ou uma pasta inteira. Não muda a pasta de saída. |
| **Limpar** | Esvazia a lista. |
| **Qtd** (`+`/`−` ou digitar) | Quantas cópias daquela imagem entram nas folhas. |
| **▲ ▼** e **✕** | Reordena ou remove a imagem. |

**Dica:** para 4 cópias do mesmo card, adicione-o uma vez e ponha **Qtd = 4**.

### Grade (topo)
Use `+`/`−` em **Colunas** e **Linhas**, ou digite os números e clique em **Aplicar valores digitados**. A miniatura ao lado mostra a ordem das células. O menu **Atalhos** tem as grades mais comuns:

| Atalho | Grade |
|---|---|
| 1 por folha | 1 × 1 |
| 2 lado a lado / 2 empilhadas | 2 × 1 · 1 × 2 |
| **4 por folha** — 4 cards A6 numa A4 | **2 × 2** |
| 6 por folha | 3 × 2 · 2 × 3 |
| 8 por folha | 4 × 2 |
| 9 por folha | 3 × 3 |
| 12 por folha | 2 × 6 · 4 × 3 |
| 16 por folha | 4 × 4 |

Qualquer outra combinação até 12 × 12 funciona sem cadastro.

### Seções
| Seção | Opções |
|---|---|
| **Papel e resolução** | A3, A4, A5, A6, Letter, Legal, Tabloid ou Custom (largura/altura em mm). DPI de 72 a 1200 — **300** é o padrão de impressão. |
| **Ajuste da imagem** | *Ajustar (fit)* — imagem inteira, pode sobrar borda na cor de fundo · *Preencher (fill)* — preenche e recorta o excesso · *Esticar (stretch)* — força o tamanho, pode distorcer. **Auto-Rotate** gira a imagem quando a orientação dela não bate com a da célula. |
| **Margens e espaçamento** | Margem externa e espaço entre imagens, em mm; cor de fundo das áreas vazias. |
| **Linhas de corte** | Sólida, tracejada ou pontilhada; espessura em px, tamanho do traço e cor. As linhas atravessam a folha entre as colunas e linhas. |
| **Saída** | Formato, prefixo, sufixo, pasta de saída e, se quiser, **uma cópia em outro destino**. |

### Guarda de qualidade (rodapé)
A folha é montada no DPI escolhido. Se a imagem tem menos pixels que a célula, ela é **ampliada** — e perde nitidez na impressão. O selo compara a pior imagem da lista com a célula:

| Selo | Significa |
|---|---|
| ✔ verde | A imagem tem pixels de sobra (≥ 100 % da célula). |
| ⚠ amarelo | Entre 75 % e 100 %: ampliação leve. |
| ✖ vermelho | Abaixo de 75 %: a perda aparece no papel. O app pede confirmação antes de gerar. |

**Quanto é suficiente?** Uma célula A6 a 300 DPI pede **1240 × 1748 px**. Uma A4 inteira a 300 DPI tem 2480 × 3508 px. SVG é desenhado já no tamanho da célula, então nunca é ampliado e fica fora da guarda.

### Preview (direita)
Mostra a folha em baixa resolução, com o mesmo cálculo da saída final. Atualiza sozinho depois de cada mudança; `◀ ▶` navegam entre as folhas.

### Gerar
**Gerar Arquivos** (ou `Ctrl+G`) monta as folhas em segundo plano — a janela não trava — e oferece abrir a pasta de saída no fim.

**Nomes dos arquivos:** `prefixo` + número de três dígitos + `sufixo` — por exemplo `folha_001.png`, `folha_002.png`. O PDF sai como um arquivo único, com todas as folhas. **Nada é sobrescrito:** se o nome já existe, o app acrescenta `_2`, `_3`…

| Formato | Quando usar |
|---|---|
| **PNG** (padrão) | Sem perda; bom para imprimir em casa ou guardar. |
| **PDF** | Mandar para gráfica ou imprimir direto — todas as folhas num arquivo. |
| **JPEG** | Arquivo menor para compartilhar (com compressão). |
| **TIFF** | Gráfica que pede TIFF; arquivo grande. |

---

## 📋 Menus e atalhos de teclado

| Menu | Itens |
|---|---|
| **Arquivo** | Adicionar arquivos… `Ctrl+O` · Adicionar pasta… `Ctrl+Shift+O` · Limpar lista · Gerar arquivos `Ctrl+G` · Abrir pasta de saída · Sair `Alt+F4` |
| **Opções** | **Presets ▸** (lista os salvos, *Salvar atual…*, *Excluir…*) · **Criar atalho…** · **Restaurar configurações padrão** |
| **Ajuda** | Guia rápido: Figma → impressão · Sobre o PrintImposer (versão, back-end de SVG, onde ficam as configurações) |

- **Presets** guardam o layout — grade, papel, DPI, ajuste, margens, corte, formato. Não guardam pastas: pasta é da máquina, não do layout.
- **Restaurar configurações padrão** volta o layout ao padrão e mantém as suas pastas.

---

## 🎯 Do Figma à impressora — cards A6, quatro por folha A4

1. **No Figma**
   - Crie os cards em frames A6 (105 × 148 mm).
   - Exporte PNG com **pelo menos 1240 × 1748 px** — confira o tamanho em pixels, não só a escala do export.
   - Quer guia de corte desenhado na arte? Uma borda fina no frame funciona; aí deixe as linhas de corte do app desligadas.
2. **No PrintImposer**
   - **+ Pasta** → a pasta com os PNGs.
   - Grade **2 × 2** (atalho «4 por folha»), papel **A4**, **300 DPI**.
   - Ajuste **Ajustar (fit)** com **Auto-Rotate** ligado.
   - Margem externa **0** (ou **5 mm** se a impressora não imprime até a borda) e **0** entre imagens.
   - Confira o selo verde no rodapé e clique em **Gerar Arquivos**.
3. **Na impressora**
   - Escolha **«Tamanho real» / 100 %**. Nunca «ajustar à página»: isso reescala a folha e o corte deixa de bater.

---

## ❓ Perguntas frequentes

**A última folha sai incompleta?**
Sim, de propósito: as células sem imagem ficam na cor de fundo. A folha continua no tamanho certo para imprimir.

**Posso misturar imagens de tamanhos diferentes?**
Pode. Use *Ajustar (fit)* para manter a proporção de cada uma e deixe o Auto-Rotate ligado.

**O PDF serve para gráfica?**
Serve para a maioria, desde que o selo de qualidade esteja verde. O PDF é **rasterizado** no DPI escolhido (é uma imagem por página, não vetor). Se a gráfica exige PDF vetorial, exporte direto do Figma.

**Posso usar SVG?**
Sim, com um back-end instalado (ver *Instalação › SVG*). O SVG é desenhado já no tamanho da célula, sem perda.

**O app altera minhas imagens?**
Nunca. Só lê os originais e grava arquivos novos na pasta de saída.

**Onde ficam as configurações?**
Em `%USERPROFILE%\.printimposer\` (no Linux/macOS, `~/.printimposer/`): `settings.json` (configuração, tamanho da janela e seções abertas) e `presets.json`. Apagar a pasta volta tudo ao padrão.

---

## 📦 Estrutura do projeto

```
printimposer/
├── print_imposer.py      # o app inteiro, em um arquivo
├── tests/test_engine.py  # suíte headless: python tests/test_engine.py
├── CLAUDE.md             # guia para o Claude Code
├── .claude/              # permissões e skills do Claude Code
├── meta/                 # documentação viva: contexto, estado, decisões, roadmap
└── logs/                 # diário de trabalho
```

O motor de composição (`ImpositionEngine`) não depende da interface: testes e preview usam o mesmo código que gera os arquivos finais. Detalhes de arquitetura, decisões e armadilhas estão em `meta/CONTEXT.md` e `meta/DECISIONS.md`; o que vem pela frente está em `meta/ROADMAP.md`.

---

*PrintImposer v1.2.0 — uso pessoal/profissional de impressão em massa.*
