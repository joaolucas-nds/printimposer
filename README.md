# 🖨 PrintImposer v1.5

**Imposição de páginas para impressão em massa** — junte dezenas de imagens em folhas prontas para imprimir e cortar.

Você tem vários cards, cartazes ou fotos — feitos no Figma, Canva, Affinity, Photoshop, Corel, num gerador web, ou tirados do celular — e quer imprimi-los, por exemplo, quatro por folha A4, sem arrastar arquivo por arquivo no diálogo de impressão. O PrintImposer faz isso em três passos: **escolha a grade → adicione as imagens → gere**.

- Grade livre de **colunas × linhas** (até 12 × 12), com atalhos prontos (2×2, 2×6, 4×3…)
- **Guarda de qualidade**: avisa quando a imagem é pequena demais para a célula e vai perder nitidez
- Saída **PNG** (padrão), **PDF sem perda**, **JPEG**, **TIFF** — e **WebP**/**AVIF** para compartilhar —, em até **dois destinos** ao mesmo tempo
- Entrada PNG, JPEG, TIFF, BMP, WEBP, GIF, **AVIF** — e **PDF**, **SVG** e **HEIC**, quando há o extra instalado
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

### PDF (opcional)
Para aceitar `.pdf` como entrada (o export vetorial de Figma, Affinity, Illustrator, Canva e afins):

```
python -m pip install pypdfium2
```

Cada **página** do PDF vira um item da lista (`arquivo.pdf · p. 2/5`) e é desenhada já no tamanho e na orientação da célula — sem ampliação. PDF com senha ou corrompido é pulado, com aviso. Sem o pacote, o cabeçalho diz `PDF: indisponível` e o `.pdf` não aparece no seletor.

### HEIC (opcional)
Fotos de iPhone em `.heic`/`.heif` entram com:

```
pip install pillow-heif
```

Sem ele, esses arquivos só não aparecem no seletor. O **AVIF** não precisa de nada: o Pillow recente já lê sozinho. `Ajuda › Sobre` mostra a linha «Formatos extras: AVIF sim/não · HEIC sim/não».

### Abrir com dois cliques
Use **`Opções › Criar atalho…`**. O diálogo explica o que o atalho faz e sugere salvá-lo na pasta **acima** da pasta do projeto (onde fica a pasta `printimposer`). O `.bat` gerado abre o app sem janela de console e grava caminhos absolutos — se você mover a pasta do projeto, gere outro.

---

## 🖥 A janela

```
┌ PrintImposer   Arquivo  Opções  Ajuda   v1.5.0 · SVG: … · PDF: … ┐
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
│            │ Folha: 2480 × 3508 px · …    │                        │
├────────────┴──────────────────────────────┴────────────────────────┤
│ [Gerar Arquivos]  ███████████░░░░░                        Pronto   │
└────────────────────────────────────────────────────────────────────┘
```

A coluna do meio tem três zonas:
- **Topo, sempre visível — a grade.** É o que muda a cada trabalho.
- **Meio — seções recolhíveis.** Abra quantas quiser; o app lembra quais ficaram abertas. No primeiro uso só **Saída** vem aberta.
- **Rodapé, sempre visível — o resumo:** quantas imagens, quantas por folha, quantas folhas, o tamanho da célula, o selo de qualidade e o tamanho da folha (em px e em MB **bruto**, isto é, sem compressão — o arquivo final sai menor).

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
| **Margens e espaçamento** | Margem externa; espaço **entre colunas** e **entre linhas**, separados, em mm; cor de fundo das áreas vazias. |
| **Linhas de corte** | Sólida, tracejada ou pontilhada; espessura em px, tamanho do traço e cor. As linhas atravessam a folha entre as colunas e linhas. |
| **Saída** | Formato, **compressão/qualidade** (quando o formato tem), prefixo, sufixo, pasta de saída e, se quiser, **uma cópia em outro destino** — enquanto ela estiver ligada, a barra inferior avisa «Também grava em: …». |

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

| Formato | Compressão | Quando usar |
|---|---|---|
| **PNG** (padrão) | sempre sem perda | Imprimir em casa ou guardar. |
| **PDF** | **Sem perda** (padrão) ou **JPEG** com qualidade 50–100 | Mandar para gráfica ou imprimir direto — todas as folhas num arquivo. Sem perda tem a mesma qualidade do PNG; JPEG dá arquivo bem menor. |
| **JPEG** | qualidade 50–100 (padrão 95) | Arquivo menor para compartilhar. |
| **TIFF** | sempre sem perda (LZW) | Gráfica que pede TIFF; arquivo grande. |
| **WebP** | **Sem perda** ou **Com perda** com qualidade 50–100 | Compartilhar por mensagem ou e-mail: bem menor que PNG. Não é para gráfica. |
| **AVIF** | qualidade 50–100 | Tamanho parecido com o WebP com perda (medido numa folha: 71 KB × 68 KB); nem todo programa abre. Não é para gráfica. |

O campo «Qualidade» é um só: vale para o JPEG e para o PDF em modo JPEG.

---

## 📋 Menus e atalhos de teclado

| Menu | Itens |
|---|---|
| **Arquivo** | Adicionar arquivos… `Ctrl+O` · Adicionar pasta… `Ctrl+Shift+O` · Limpar lista · Gerar arquivos `Ctrl+G` · Abrir pasta de saída · Sair `Alt+F4` |
| **Opções** | **Presets ▸** (lista os salvos, *Salvar atual…*, *Excluir…*) · **Criar atalho…** · **Restaurar configurações padrão** |
| **Ajuda** | Guia rápido: da arte à impressão · Sobre o PrintImposer (versão, extras disponíveis, onde ficam as configurações) |

- **Presets** guardam o layout — grade, papel, DPI, ajuste, margens e espaçamentos, corte, formato, compressão e qualidade. Não guardam pastas: pasta é da máquina, não do layout. Presets da 1.2 (com um espaçamento só) abrem com o mesmo valor nos dois campos.
- **Restaurar configurações padrão** volta o layout ao padrão e mantém as suas pastas.

---

## 🎯 Da arte à impressora — cards A6, quatro por folha A4

1. **Na sua ferramenta** (Figma, Canva, Affinity, Photoshop, Corel, um gerador web…)
   - Crie os cards no tamanho A6 (105 × 148 mm).
   - Exporte **PDF** (melhor: o texto e os traços saem vetoriais — precisa do `pypdfium2`) ou **PNG com pelo menos 1240 × 1748 px** — confira o tamanho em pixels, não só a escala do export.
   - Quer guia de corte desenhado na arte? Uma borda fina na prancheta funciona; aí deixe as linhas de corte do app desligadas.
   - **Fotos do celular** entram direto (JPEG, AVIF, e HEIC com o extra).
2. **No PrintImposer**
   - **+ Pasta** → a pasta com as artes.
   - Grade **2 × 2** (atalho «4 por folha»), papel **A4**, **300 DPI**.
   - Ajuste **Ajustar (fit)** com **Auto-Rotate** ligado.
   - Margem externa **0** (ou **5 mm** se a impressora não imprime até a borda) e **0** entre colunas e entre linhas.
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
Serve para a maioria, desde que o selo de qualidade esteja verde. Desde a 1.3 o PDF sai **sem perda** por padrão — a mesma qualidade do PNG, num arquivo só. Ele é **rasterizado** no DPI escolhido (uma imagem por página, não vetor). Se a gráfica exige PDF vetorial, mande o PDF exportado direto da sua ferramenta.

**Por que o PDF ficou maior que antes?**
Até a 1.2 o PDF saía comprimido em JPEG por dentro, com perda, sem você escolher. Agora o padrão é sem perda. Para voltar a um arquivo pequeno, escolha **Compressão: JPEG** e ajuste a qualidade.

**Posso usar PDF como entrada?**
Sim, com o `pypdfium2` (ver *Instalação › PDF*). Duas observações: (1) a página é desenhada no DPI escolhido — para PDF, use **300 DPI**, porque não há fonte pequena limitando e o texto sai mais nítido; (2) desde a 1.5, a guarda de qualidade **olha as imagens dentro do PDF**: se a página embrulha uma imagem pequena (alguns geradores web fazem isso), o selo avisa como avisaria com um PNG.

**Abri pelo atalho e nada aconteceu.**
Desde a 1.4.1, se o app falhar ao abrir, ele mostra uma janela com o erro e grava o detalhe em `%USERPROFILE%\.printimposer\last_error.log` — mande esse arquivo junto com a descrição do problema.

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

*PrintImposer v1.5.0 — uso pessoal/profissional de impressão em massa.*
