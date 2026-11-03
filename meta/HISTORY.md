# HISTORY.md — Conhecimento Consolidado

> **Opcional.** Arquivo-baú para conhecimento denso que já foi aprendido e não muda mais — guias técnicos, análises de viabilidade, notas de migração — que tornariam o CONTEXT pesado demais.
> Não é lido no início da sessão; o assistente consulta sob demanda quando o assunto aparece.

---

## 1. Qualidade de impressão e DPI (guia de fonte → folha)

A folha é rasterizada no DPI configurado. Tamanho em pixels: `px = mm × DPI / 25.4`.

Tamanhos-alvo (a 300 DPI):
| Papel | px (L × A) |
|---|---|
| A3 | 3508 × 4961 |
| A4 | 2480 × 3508 |
| A5 | 1748 × 2480 |
| A6 | 1240 × 1748 |
| Letter | 2550 × 3300 |

**Regra prática:** para um card A6 imprimir a 300 DPI, a imagem-fonte deve ter **≥ 1240×1748 px**. Se tiver menos, a ferramenta faz *upscale* e a impressão perde nitidez — daí a "guarda de qualidade" planejada (avisar quando fonte < célula).

**Sobre "exportar 4× no Figma = 300 DPI":** só é verdade se o frame-base tiver os pixels certos. Exportar a 4× multiplica os pixels por 4; o resultado só atinge 1240×1748 se o frame a 1× for ~310×437 px. **Mire o alvo em pixels, não a escala** — ou use exportação por tamanho fixo em px no Figma. Quando em dúvida, exporte maior; reduzir preserva qualidade, ampliar não.

## 2. O que é "compressão" aqui (respondendo a dúvida do usuário)

Sim, "compressão" é o termo correto. Há duas perdas distintas envolvidas:

1. **Reamostragem (resampling):** encaixar a imagem na célula muda sua contagem de pixels. Reduzir para caber é seguro; ampliar (upscale) inventa pixels e borra. Isso é independente do formato.
2. **Compressão do arquivo:**
   - *Lossless* (PNG, TIFF/LZW, Flate no PDF) — preserva todos os pixels; arquivo maior. Linhas finas e bordas nítidas incham o arquivo (detalhe de alta frequência).
   - *Lossy* (JPEG) — descarta informação para reduzir tamanho; cria artefatos em bordas e texto. Bom para foto, ruim para linhas nítidas.

**O que o Windows faz no "4 imagens por folha":** o driver reamostra cada imagem para o tamanho do slot e rasteriza a folha, normalmente recomprimindo no caminho — é dessa reamostragem + recompressão que vem a perda que o usuário notou. A ferramenta resolve isso controlando o DPI explicitamente e (planejado) expondo a escolha de compressão, para o usuário decidir o trade-off tamanho × qualidade conscientemente.

**Maior salto possível:** não rasterizar. Se a entrada for PDF vetorial (export do Figma), dá para posicionar as páginas vetorialmente — qualidade perfeita, arquivo minúsculo, marcas sem peso. É a F3 do ROADMAP.

## 3. SVG como entrada — por que não é direto e qual o caminho

Pillow **não rasteriza SVG** (não tem renderizador de vetor). Para aceitar SVG seria preciso um conversor:
- **cairosvg** (puro Python + cairo) — `cairosvg.svg2png(...)` para um buffer e então abrir no Pillow. Dependência adicional.
- **Inkscape** por linha de comando — robusto, mas exige Inkscape instalado (dependência externa pesada).

Decisão atual: exportar PNG do Figma (caminho mais simples e confiável). SVG de **entrada** segue como ideia ativa com ressalva de dependência. SVG de **saída** foi descartado: com arte raster, o SVG só embutiria os bitmaps — nenhum ganho.

## 4. Pesquisa de imposição/prepress profissional (2026) — o que mirar

Levantamento de ferramentas de referência (Kodak Preps, Ultimate Impostrip, Montax Imposer, Metrix, PDF Press, DevaliPI Imposition Studio) e do que elas oferecem, filtrado pelo escopo deste projeto (N-up plano para corte, uso pessoal/semi-profissional):

**Recursos que fazem sentido adotar (viraram IDEAS/ROADMAP):**
- **Entrada/saída em PDF vetorial** — preserva qualidade e reduz drasticamente o tamanho. O diferencial de qualidade nº1.
- **Marcas de corte de canto** (ticks no gutter) em vez de linhas atravessando a folha — padrão de indústria, quase sem peso no arquivo.
- **Sangria (bleed)** ~3 mm (1/8") — evita borda branca no corte de artes sem margem.
- **Templates / hot folders** — salvar uma configuração e só jogar os arquivos para processar. Mapeia direto no desejo de "esforço mínimo" → presets (.json) + (futuro) pasta observada.
- **Preview em tempo real** — destacado até por ferramentas pagas como diferencial; o PrintImposer **já tem**.
- **Step-and-repeat** — duplicar uma arte N vezes; versão básica já existe via "quantidade".

**Recursos deliberadamente fora do escopo:**
- Imposição de cadernos/booklet (saddle stitch, perfect binding) e *cut & stack* com ordenação de pilha.
- Registro multi-plate / separação de cores / trapping / overprint (offset).
- Nesting de formas irregulares e imposição de embalagem (die-line, step-and-repeat de formas).
- Variable Data Printing (VDP), JDF/JMF, integração com RIP/MIS.

**Terminologia de marcas (para implementar marcas de canto corretamente, F3):**
- *Crop/trim marks*: indicam onde cortar (tamanho final). Ficam nos cantos, fora da arte, no gutter.
- *Bleed marks*: como as de corte, mas no limite da sangria.
- *Registration marks*: alinhamento entre cores; fora do escopo.
- Gutter mínimo é necessário para haver espaço onde desenhar as marcas de canto sem invadir a arte.

## 5. Nota técnica — CustomTkinter + Tkinter nativo

- **Aninhar CTk em geometria nativa:** widgets CustomTkinter com canvas interno (ex.: `CTkScrollableFrame`) não podem ser adicionados diretamente a `tk.PanedWindow`; interponha um `tk.Frame` neutro. Causa raiz e correção em FIX-001.
- **Drag-and-drop de arquivos:** não há suporte nativo; usa-se `tkinterdnd2` com um wrapper de classe sobre `CTk` (padrão confirmado na comunidade). É dependência opcional — degradar com elegância se ausente. Tem hook próprio para PyInstaller, útil na F4.
- **PDF a partir de imagem:** `PIL.Image.save(..., "PDF", resolution=dpi, save_all=True, append_images=[...])` gera multipágina. Para escolher compressão/embutir sem recomprimir, avaliar `img2pdf`. Para imposição vetorial (F3), `pypdf`/`reportlab` posicionam páginas PDF.

## 4. Grade livre × lista de layouts (análise de 2026-07)

O problema relatado: falta a combinação 2×6, e a única saída é abrir o `.py` e editar `NUP_LAYOUTS`.

Duas formas de resolver:

| | Lista em JSON + editor na UI | Grade livre `cols × rows` |
|---|---|---|
| Resolve o 2×6 | sim, cadastrando | sim, por construção |
| Resolve o 5×3 que vou querer amanhã | não, cadastrando de novo | sim |
| UI a construir | CRUD de lista (criar/editar/apagar/ordenar) | dois spinners |
| Risco | usuário cria entradas inválidas/duplicadas | grade absurda (ex.: 20×20) sem aviso |

A grade livre ataca a causa (só existe o que foi cadastrado), a lista ataca o sintoma (falta um item). Decisão em DEC-009: grade livre + lista fixa reduzida a **atalhos** + presets nomeados guardando a configuração inteira.

**Onde o JSON continua fazendo sentido:** não para listar grades, e sim para os **presets** — `{nome, cols, rows, papel, dpi, margens, corte, formato}`. É o que de fato se repete entre sessões.

**Teto sensato:** limitar a grade a algo como 10×10 e acoplar o aviso de qualidade — uma folha A4 em 12×12 dá células de ~17×24 mm, quase sempre inútil. Melhor avisar do que impedir.

## 5. Entrada SVG — o ganho é maior do que parece

Rasterizar SVG **na resolução exata da célula** significa **zero upscale, por construção**: um card em SVG sempre imprime nítido, em qualquer DPI, porque o desenho é recalculado, não esticado. Isso resolve na origem a preocupação com perda de qualidade em relação ao export do Figma — sem esperar a imposição vetorial completa (F3).

Duas bibliotecas para Windows:

| | `cairosvg` | `svglib` + `reportlab` |
|---|---|---|
| Dependência nativa | **sim** (libcairo2) | **sim, para desenhar** — ver correção abaixo |
| Fidelidade de SVG | melhor (testado contra a suíte do W3C) | boa, cobre o comum |
| Controle de saída | `output_width`/`scale`/`dpi` | via `renderPM` |

> **Correção (2026-07-19, verificada na prática).** A afirmação original de que o `svglib` seria "Python puro, sem dependência nativa" está **errada** e custou um bug. O `svglib` **analisa** SVG em Python puro, mas **desenhar** passa pelo `renderPM` do reportlab, que exige `rlPyCairo` (→ pycairo → cairo nativo) ou a extensão C `_rl_renderPM`. Ou seja: **os dois caminhos querem cairo por baixo**. Não existe, hoje, rota 100% Python puro de SVG para pixel.

Recomendação revista: tentar `cairosvg`, cair para `svglib`, e — crucialmente — **validar com um render real, não com o import** (ver FIX-002). Sem back-end capaz, esconder `.svg` dos formatos aceitos; nunca quebrar o app por falta de dependência opcional.

Consequência prática: no Windows, instalar um back-end é um passo real de setup, não um `pip install` garantido. Ideia registrada para a F4 (empacotar as DLLs no .exe).

**Armadilhas do SVG:** (a) sem `viewBox`, ou com dimensões em cm/in, o render sai em tamanho errado → sempre forçar largura de saída; (b) fontes não instaladas caem para uma fonte padrão → converter texto em contorno no Figma antes de exportar; (c) filtros (blur, sombra) são lentos.

**PDF é da mesma família:** o Figma exporta PDF vetorial, e o ganho é idêntico. Vale tratar SVG e PDF como a mesma classe de "entrada vetorial".

## 6. Por que a janela abre mal (diagnóstico)

Três causas prováveis, somando efeito:

1. **Geometria fixa sem clamp** — `self.geometry("1100x780")` não pergunta o tamanho do monitor. Em tela menor (ou com a barra de tarefas), parte da janela fica fora. Correção: ler `winfo_screenwidth/height`, limitar a geometria a ~90% e centralizar calculando `x = (tela_w - jan_w) // 2`.
2. **Sem DPI awareness no Windows** — sem declarar consciência de DPI, o Windows escala a janela por **bitmap** em telas com zoom (125%/150%): texto borrado e geometria calculada em coordenadas erradas. Correção no início do `main()`, antes de criar a janela:
   ```python
   # Windows: sem isto, o SO escala a janela por bitmap em telas com zoom (texto borrado).
   if sys.platform == "win32":
       try:
           from ctypes import windll
           windll.shcore.SetProcessDpiAwareness(1)
       except Exception:
           pass  # Windows antigo ou shcore ausente: segue sem DPI awareness
   ```
3. **Sashes sem posição inicial** — `tk.PanedWindow` distribui o espaço na primeira renderização; os `width=` passados no `add()` são sugestões. Se o conteúdo pedir mais do que há, um painel come o outro. Correção: fixar as posições com `sash_place` num `after(...)` depois do primeiro render.

## 7. Gerador de `.bat` da GUI

Padrão observado nos `.bat` que o usuário já usa:

- `start "" pythonw "<caminho>\run.py"` — abre **sem janela de console** (`pythonw`, não `python`).
- Com venv: `start "" /d "<pasta de trabalho>" "<venv>\Scripts\pythonw.exe" -m src.gui` — o `/d` fixa o CWD, o que importa quando o app grava log/cache relativo.
- Cabeçalho em `rem`/`REM` explicando o que é e avisando que o caminho precisa ser ajustado se a ferramenta mudar de lugar.
- **Comentários sem acento** ("grafica", "rapido", "area de trabalho"). Não é descuido: o console do Windows usa codepage legado (cp850/cp437) e acentua errado o UTF-8 do arquivo. Escrever em ASCII puro é a forma simples de nunca ver `grÃ¡fica` no terminal.

Para gerar de dentro do app: `sys.executable` dá o interpretador atual; trocar `python.exe` por `pythonw.exe` no mesmo diretório dá a versão sem console (confirmar que existe antes de usar). O caminho do script é `Path(__file__).resolve()`. Oferecer salvar direto na Área de Trabalho é o caso de uso real.

## 8. Otimização de carregamento — o que é seguro e o que não é

Hoje, `ImageEntry._load_thumb` abre a imagem inteira só para gerar uma miniatura de 56×56 px. Com cards A6 a 300 DPI (~2 MP cada), 40 imagens significam decodificar ~87 MP para exibir 40 quadradinhos.

**Seguro (recomendado):**
- `Image.draft("RGB", (w, h))` antes do `load()` — para **JPEG**, o decodificador entrega direto em escala reduzida (1/2, 1/4, 1/8). Ganho grande, risco ~zero, e é ignorado silenciosamente em outros formatos.
- **Cache de miniatura** em memória por caminho+mtime — evita reprocessar ao reordenar ou mudar a quantidade.
- Gerar as miniaturas **em lote numa thread** com placeholder cinza, como o preview já faz.

**Arriscado (não fazer agora):**
- Lazy loading por scroll (só gerar a miniatura do que está visível) — mexe no ciclo de vida dos widgets e pode reintroduzir problemas de aninhamento como o do FIX-001.
- Cache em disco — inventa gestão de invalidação e lixo por um ganho pequeno nesta escala.

Alinhado à ressalva do usuário: aplicar só o seguro; o resto não compensa o risco.


## 9. Pesquisa de UX para o painel de configuração (2026-07)

Levantamento feito antes de reestruturar o painel central (DEC-011, SPEC-F3-UI).

### Accordion × tabs — o critério de decisão

| | Tabs | Accordion |
|---|---|---|
| Quantidade que suporta | 3–5; quebra acima disso | 5 a 20, escala bem |
| Rótulos longos | quebram a linha ou truncam | sem problema (espaço horizontal sobra) |
| Alternar muito entre seções | bom | custa um clique a mais |
| Comparar duas seções ao mesmo tempo | impossível | possível se multi-aberto |
| Tela estreita/baixa | conteúdo é empurrado para fora | espelha o comportamento amplo |

Regra prática que saiu disso: **tabs para modos de visualização mutuamente exclusivos; accordion para blocos de configuração independentes.** O padrão do Asana é citado como referência — tabs separam modos de visualização, accordion organiza a lista dentro.

No PrintImposer, tabs foram descartadas por dois motivos independentes: são 6 seções com rótulos longos em PT-BR ("Margens e espaçamento"), e as duas mais mexidas — Grade e Saída — cairiam em abas diferentes, exatamente o cenário em que tabs perdem.

### Erros a evitar (valem como checklist)
1. **Esconder conteúdo essencial** dentro de painel colapsado que o usuário pode nunca abrir — inclui CTA, campo obrigatório e, no nosso caso, **aviso de qualidade e contador de folhas**. Foi o erro mais grave da v1.1.
2. **Nenhuma seção aberta por padrão** — a tela parece vazia e não convida. Sempre abrir a mais importante.
3. **Rótulos vagos** — se o usuário não consegue prever o que tem dentro, não clica.
4. **Excesso de cliques** — colapsar tudo transfere trabalho para o usuário.

### Progressive disclosure (Nielsen, 1995)
Definição: *deferir funcionalidades avançadas ou raramente usadas para uma tela secundária, tornando a aplicação mais fácil de aprender e menos propensa a erro.* Números citados na literatura: **30–50% mais rápido** na conclusão da tarefa inicial, mantendo **70–90%** de descoberta das funções avançadas.

Mecanismos que a fazem funcionar: padrões default que servem à maioria sem configuração; affordances óbvias de expansão (chevron, "Avançado"); transição suave; e reversibilidade.

Como decidir o que é essencial × avançado: **análise de frequência 80/20** por task analysis. No PrintImposer:

| Muda a cada trabalho | Configura uma vez |
|---|---|
| Grade (cols × rows) · prefixo/formato de saída | Papel · DPI · modo de ajuste · margens · linhas de corte |

E uma terceira categoria que a análise revelou: **ação, não configuração** — gerar `.bat`, salvar/carregar preset, ver "sobre". Não pertencem a um painel de configuração; pertencem a um menu. É o que motivou a menubar.

### Menubar em CustomTkinter — nota de implementação
Não existe menubar CTk nativa. Três caminhos:
- `self.config(menu=tk.Menu(...))` — menubar real do SO. Mais barato e acessível, mas no Windows a faixa é desenhada pelo SO em cinza claro, destoando de um app escuro.
- `CTkButton` + `tk.Menu.tk_popup()` — faixa no tema do app, dropdown nativo (teclado e dismissal de graça). **Escolhido.**
- Popups próprios com `CTkToplevel` — controle total do visual, muito mais código e mais superfície para bugs de aninhamento (classe do FIX-003).
