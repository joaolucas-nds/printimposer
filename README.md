# 🖨 PrintImposer v1.0
**Ferramenta de Imposição de Páginas para Impressão em Massa**

---

## 📋 O que é?

PrintImposer resolve um problema muito específico e prático: você tem dezenas de imagens
(ex.: cards A6 exportados do Figma) e quer agrupá-las em folhas A4 para imprimir tudo de
uma vez, sem ficar arrastando arquivo por arquivo no diálogo de impressão do Windows.

Com PrintImposer você:
- Seleciona todas as imagens de uma vez
- Configura quantas por folha (1-up, 2-up, 4-up, 6-up, 8-up, 9-up, até 16-up)
- Define margens, espaçamento e linhas de corte
- Gera um PDF (ou PNG/JPEG/TIFF) em alta resolução, pronto para imprimir

---

## ⚙️ Instalação

### Pré-requisitos
- Python 3.9 ou superior
- pip

### Dependências
```bash
pip install customtkinter pillow
```

### Executar
```bash
python print_imposer.py
```

> No Windows, você pode criar um atalho `.bat`:
> ```bat
> @echo off
> python "C:\caminho\para\print_imposer.py"
> ```

---

## 🖥 Interface — Guia de Uso

A janela é dividida em três áreas:

```
┌──────────────────────────────────────────────────────────────┐
│  🖨 PrintImposer — Imposição de Páginas                       │
├──────────────┬──────────────────────┬────────────────────────┤
│              │                      │                        │
│  📁 Imagens  │  ⚙️ Configurações    │  👁 Preview            │
│  (Lista)     │                      │                        │
│              │                      │                        │
├──────────────┴──────────────────────┴────────────────────────┤
│  [⚡ Gerar]   ████████████░░░░  Status…                       │
└──────────────────────────────────────────────────────────────┘
```

---

### 📁 Painel Esquerdo — Lista de Imagens

| Elemento | Função |
|---|---|
| **+ Adicionar** | Abre seletor de arquivos para múltiplas imagens |
| **Limpar** | Remove todas as imagens da lista |
| Linha da imagem | Mostra miniatura, nome e quantidade |
| **Qtd +/−** | Define quantas cópias daquela imagem entram no layout |
| **↑ ↓** | Reordena as imagens na lista |
| **✕** | Remove a imagem da lista |
| Rodapé | Mostra total de arquivos e cópias somadas |

**Dica:** Se você quer imprimir 4 cópias do mesmo card, adicione-o uma vez e coloque Qtd = 4.

---

### ⚙️ Painel Central — Configurações

#### 📐 Layout de Impressão

| Opção | Descrição |
|---|---|
| **N-up** | Quantas imagens por folha (1×1, 2×1, 2×2, 3×2, 4×2, 3×3, 4×3, 4×4) |
| **Ajuste** | Como a imagem preenche o espaço: |
| → *Ajustar (fit)* | Imagem inteira visível, pode ter bordas na cor de fundo |
| → *Preencher (fill)* | Imagem recortada para preencher todo o espaço (sem bordas) |
| → *Esticar (stretch)* | Força o tamanho exato (pode distorcer proporções) |
| **Auto-Rotate** | Gira automaticamente imagens retrato em slots paisagem e vice-versa |

**Recomendação para cards do Figma:** Use *Ajustar* + *Auto-Rotate* ativado.

---

#### 📄 Papel e Resolução

| Opção | Valores típicos |
|---|---|
| **Papel** | A3, A4, A5, A6, Letter, Legal, Tabloid, Custom |
| **Largura/Altura (mm)** | Editável ao escolher "Custom" |
| **DPI** | 300 (padrão) · 150 (rascunho) · 600 (máxima qualidade) |

> **Por que DPI importa?**
> Uma folha A4 a 300 DPI tem **2480 × 3508 pixels**. Isso garante 300 pontos por polegada
> na impressão final — o padrão profissional. Se suas imagens do Figma foram exportadas a
> 300 DPI (ou com o dobro do tamanho em pixels), a qualidade é preservada ao máximo.

**Tamanhos de folha gerados (pixels a 300 DPI):**
| Papel | Largura px | Altura px |
|---|---|---|
| A3 | 3508 | 4961 |
| A4 | 2480 | 3508 |
| A5 | 1748 | 2480 |
| A6 | 1240 | 1748 |
| Letter | 2550 | 3300 |

---

#### 📏 Margens e Espaçamento

| Opção | Descrição |
|---|---|
| **Margem ext. (mm)** | Margem ao redor de toda a folha (bordas externas) |
| **Entre imagens (mm)** | Espaço entre as imagens no grid |
| **Cor de fundo** | Cor das áreas vazias (padrão: branco #FFFFFF) |

**Para impressão sem margem:** deixe ambos em `0`.
**Para facilitar o corte manual:** use `0` de margem ext. e adicione linhas de corte.
**Para impressão doméstica:** a maioria das impressoras tem margem mínima de ~5mm.

---

#### ✂️ Linhas de Corte

Quando ativadas, o script desenha linhas guia entre as imagens.

| Opção | Descrição |
|---|---|
| **Habilitar** | Liga/desliga o recurso |
| **Estilo** | Sólida / Tracejada / Pontilhada |
| **Espessura (px)** | Largura da linha em pixels (1px ≈ 0,085mm a 300 DPI) |
| **Comprimento do traço** | Para estilos Tracejada/Pontilhada, tamanho de cada traço |
| **Cor** | Qualquer cor (padrão: cinza claro #999999) |

> **Alternativa:** Se você já adicionou borda/traço nas imagens no Figma, não precisa
> usar esta opção — as bordas já funcionam como guia de corte.

---

#### 💾 Saída

| Opção | Descrição |
|---|---|
| **Formato** | PDF (multi-página) · PNG · JPEG · TIFF |
| **Prefixo** | Texto no início do nome do arquivo (ex: `impressao_`) |
| **Sufixo** | Texto no fim do nome (ex: `_v2`) |
| **Pasta** | Onde salvar os arquivos gerados |

**Nomeação automática:**
- PDF: `prefixo001sufixo.pdf` (arquivo único com todas as folhas)
- Outros: `prefixo001sufixo.png`, `prefixo002sufixo.png`, etc.
- Se o arquivo já existir, adiciona `_2`, `_3`, etc. automaticamente.

**Quando usar cada formato:**
| Formato | Quando usar |
|---|---|
| **PDF** | ✅ Enviar para gráfica, imprimir direto — melhor opção |
| **PNG** | Quando precisa de imagem com transparência |
| **JPEG** | Arquivo menor, para compartilhar — sem transparência |
| **TIFF** | Gráfica profissional, máxima qualidade, arquivo grande |

---

### 👁 Painel de Preview

- Mostra uma versão em baixa resolução (72 DPI) do resultado
- Navega entre folhas com os botões **◀ ▶**
- Atualiza automaticamente sempre que qualquer configuração muda
- Mostra o número da folha atual e total

---

### ⚡ Botão Gerar Arquivos

1. Clique em **⚡ Gerar Arquivos**
2. A barra de progresso mostra duas fases:
   - 0–70%: composição das folhas
   - 70–100%: salvamento dos arquivos
3. Ao concluir, pergunta se deseja abrir a pasta de saída

---

## 🎯 Fluxo de Trabalho Recomendado (Figma → PrintImposer)

### Para Cards A6 → Folha A4 (4 por folha)

1. **No Figma:**
   - Crie seus cards em frames A6 (105 × 148 mm)
   - Se quiser linhas de corte automáticas: adicione uma borda fina (0.5pt) na cor
     desejada dentro do frame
   - Exporte todos os frames como PNG, escala 4× (resulta em ~300 DPI)
   - Salve tudo em uma pasta

2. **No PrintImposer:**
   - Clique **+ Adicionar** → selecione todos os PNGs da pasta
   - Configure:
     - N-up: `4-up (2×2)`
     - Papel: `A4`
     - DPI: `300`
     - Margem ext.: `0` (ou `5` para impressão doméstica)
     - Entre imagens: `0`
     - Ajuste: `Ajustar (fit)`
     - Auto-Rotate: ✅ ativado
     - Linhas de corte: depende (se já tem borda no Figma, deixe desativado)
   - Clique **⚡ Gerar Arquivos**
   - Abra o PDF e imprima

3. **Na Impressora:**
   - Selecione "Tamanho real" ou "100%" (NÃO "ajustar à página")
   - Margens: mínimas ou zero (impressão borda a borda se suportado)

---

## 🔧 Configurações N-up — Referência Completa

| N-up | Grid | Uso típico |
|---|---|---|
| 1-up (1×1) | 1 coluna × 1 linha | Imagem única por folha |
| 2-up (2×1) | 2 colunas × 1 linha | 2 imagens lado a lado (paisagem) |
| 2-up (1×2) | 1 coluna × 2 linhas | 2 imagens empilhadas (retrato) |
| 4-up (2×2) | 2 colunas × 2 linhas | **4 cards A6 em A4** ← mais usado |
| 6-up (3×2) | 3 colunas × 2 linhas | 6 imagens por folha |
| 6-up (2×3) | 2 colunas × 3 linhas | 6 imagens (orientação diferente) |
| 8-up (4×2) | 4 colunas × 2 linhas | 8 imagens pequenas |
| 8-up (2×4) | 2 colunas × 4 linhas | 8 imagens verticais |
| 9-up (3×3) | 3 colunas × 3 linhas | 9 imagens por folha |
| 12-up (4×3) | 4 colunas × 3 linhas | 12 imagens (cartões de visita, etc.) |
| 16-up (4×4) | 4 colunas × 4 linhas | 16 imagens pequenas |

---

## ❓ Perguntas Frequentes

**P: A última folha fica com imagens em branco se não completar o grid?**
R: Sim. Os espaços restantes ficam com a cor de fundo configurada. Isso é o comportamento
correto — a folha fica "pronta para imprimir" e você descarta o espaço vazio.

**P: Posso misturar imagens de tamanhos diferentes?**
R: Sim. O AutoRotate e o modo de Ajuste lidam com isso. Use *Ajustar (fit)* para
manter a proporção original de cada imagem.

**P: O PDF gerado tem qualidade suficiente para gráfica?**
R: Sim, desde que suas imagens originais estejam em 300 DPI (ou pixels suficientes).
O script gera PDFs baseados em imagem rasterizada a 300 DPI. Para gráficas que exigem
PDF vetorial, exporte diretamente do Figma como PDF.

**P: Posso usar SVG como entrada?**
R: Não diretamente (Pillow não suporta SVG). Exporte do Figma como PNG 4× e use PNG.

**P: O script modifica os arquivos originais?**
R: Nunca. Só lê os arquivos e cria novos na pasta de saída.

**P: Como duplicar uma imagem para ter 4 cópias na mesma folha?**
R: Adicione a imagem e defina Qtd = 4. Com 4-up e 4 cópias, a folha terá 4 vezes a
mesma imagem.

---

## 📦 Estrutura do Projeto

```
PrintImposer/
├── print_imposer.py   ← Script principal (tudo em um arquivo)
└── README.md          ← Esta documentação
```

---

## 🛠 Arquitetura do Código

O script está organizado em camadas:

```
PrintImposerApp (GUI / CTk)
├── ImageListPanel          ← Lista com ImageRows
├── ConfigPanel             ← Todos os controles de configuração
└── PreviewPanel            ← Canvas de preview

ImpositionEngine (Core)
├── compose_page()          ← Monta uma página PIL
├── generate_all()          ← Gera todas as páginas em alta resolução
├── preview_page()          ← Versão rápida a 72 DPI para preview
└── save()                  ← Salva PDF / PNG / JPEG / TIFF

LayoutConfig (Model)        ← Estado de configuração (dataclass)
ImageEntry (Model)          ← Representa uma imagem + quantidade
```

**Threading:** A geração e o preview rodam em threads separadas para não travar a UI.
**Debounce:** O preview aguarda 300ms após a última mudança antes de recalcular.

---

## 🔮 Melhorias Futuras Planejadas

- [ ] Layout personalizado de 3 fotos (tipo moldura 2+1)
- [ ] Arrastar e soltar arquivos na janela
- [ ] Salvar/carregar perfil de configuração (.json)
- [ ] Suporte a SVG via Inkscape/CairoSVG
- [ ] Numeração automática de folhas (watermark de página)
- [ ] Exportação direta para impressora sem salvar arquivo
- [ ] Interface em inglês (i18n)

---

*PrintImposer v1.0 — Gerado para uso pessoal/profissional de impressão em massa.*
"# printimposer" 
