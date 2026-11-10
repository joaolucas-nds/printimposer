# ANALISE — Portão da moldura (layout não-uniforme) e o arquivo único

> **Status:** Decidida (2026-11-10) — modelo B, 1.8.1 de reorganização, catálogo inicial aprovado; desfecho no fim, DEC-017 e DEC-018
> **Data:** 2026-11-10
> **Elos:** ROADMAP F5 (portão da moldura, 1.9.0) · DEC-003, DEC-009, DEC-015, DEC-016 · `meta/analises/261109-ANALISE-ordem-f5.md` · IDEAS «Moldura de várias fotos» (usuário, 2026-06; caso do fotógrafo em 04/11)

## Problema

Hoje toda folha é uma grade regular `cols × rows` (DEC-009): todas as células têm o mesmo tamanho. O caso que motivou a ideia em 06/2026 não cabe nisso: duas fotos horizontais iguais e uma retrato alta na mesma folha. Em 04/11 o dono descreveu o uso real: um fotógrafo que, com uma série de fotos, monta **em segundos** várias molduras diferentes. É o último item do critério de conclusão da F5 que falta («layout não-uniforme possível»).

Três perguntas precisam de resposta antes de qualquer spec:
1. **Que modelo de layout:** uma lista fixa de molduras prontas, um modelo de divisões, ou um editor livre de caixas?
2. **Como ficam corte, sangria e marcas** quando os cortes não atravessam a folha inteira? A regra da 1.6.0 («uma marca em cada ponta de cada linha de corte») supõe que toda linha vai de borda a borda.
3. **O arquivo único (DEC-003) se divide antes?** A moldura mexe no centro do motor.

Se nada for decidido, a spec da 1.9.0 escolhe um modelo por gosto, e ele é caro de trocar depois: o formato entra nos presets salvos.

## Restrições / o que foi medido

**Lido no repositório neste turno:**
- `print_imposer.py` tem **3.875 linhas**; `tests/test_engine.py`, **2.301** (`wc -l`, 10/11). Na decisão da F5 eram 3.519 e 1.996: a 1.7.0 e a 1.8.0 somaram 356 linhas ao app.
- As seções do arquivo se dividem em duas metades:
  - linhas 1–1.765, **sem Tk**: dependências opcionais, persistência, carregamento, modelo, geometria, escritor de PDF e motor;
  - linhas 1.794–3.779, **GUI**: ingestão, widgets, painéis e app (a ingestão está na faixa da GUI, mas é pura).
- **Onde a grade regular está amarrada** (`grep -c`): `cfg.cols` 8, `cfg.rows` 8, `.nup()` 5, `cell_px(` 4, `sheet_geometry(` 4, `self._grid()` 3, `cell_mm(` 2. São poucos pontos, e todos passam por `sheet_geometry` / `cell_px` / `nup`. A geometria já é uma função pura em mm desde a 1.6.0 (DEC-015): é ela que generaliza.
- O tamanho da célula é **um só** para a folha inteira em três lugares:
  - `cell_px` alimenta a guarda de qualidade;
  - os rasterizadores de PDF e SVG recebem a caixa da célula;
  - o rodapé mostra «Célula: …».

  Com a moldura, cada slot tem o seu tamanho.
- **Cinco testes leem o código-fonte** por AST com o caminho `print_imposer.py` fixo (linhas 802, 909, 979, 1086 e 1187 do teste). Dividir o arquivo mexe neles.

**Pesquisa de domínio (10/11):**
- O módulo de impressão do Lightroom Classic separa três estilos de layout:
  - **Single Image/Contact Sheet** — grade, tudo do mesmo tamanho; é o que o PrintImposer faz hoje;
  - **Picture Package** — uma foto em vários tamanhos na folha;
  - **Custom Package** — várias fotos em vários tamanhos.

  ([Adobe — layouts e modelos](https://helpx.adobe.com/lightroom/help/print-module-layouts-templates.html)). Nos dois «Package», o usuário **monta as células à mão**, e o Lightroom tem um arranjo automático que otimiza a folha para o **menor número de cortes** (mesma página).
- Na prática dos laboratórios, a folha de 8×10" é a unidade, e as combinações também são vendidas «divididas»: 2× 5×7, 4× 3½×5, 8 carteiras, ou mistas como 1× 5×7 + 2× 4×5 ([Full Color — unidades](https://www.fullcolor.com/sports-school/school/full-color-ordering-system-new/products.html)). Todas essas folhas se cortam com **cortes retos que atravessam o pedaço da vez**, e é assim que se corta na guilhotina.
- **Consequência para o modelo:** uma moldura feita de **divisões sucessivas** — cortar a folha em duas, depois cortar um dos pedaços em dois, e assim por diante — é, por construção, cortável na guilhotina. Ela tem cortes bem definidos e cobre a 2+1 do dono e as folhas «divididas» dos laboratórios. Isso é **deduzido** da forma das folhas acima, não citado de uma fonte.

## Opções consideradas — modelo de layout

### A — Lista fixa de molduras prontas, cada uma desenhada à mão no código
- **Ganha:** o mais barato; UI de uma lista.
- **Perde:** cada moldura nova é código novo. Não há proporção ajustável («a alta ocupa 60%, não 50%»). A geometria, as marcas e a sangria têm de ser escritas caso a caso, ou por um modelo genérico, que é a opção B.
- **Descartada:** é a B sem a parte que paga a conta.

### B — Divisões sucessivas (árvore), com catálogo de modelos prontos *(recomendada)*
Uma moldura é uma árvore: cada nó **divide** o espaço em duas ou mais partes, na vertical ou na horizontal, com proporções (ex.: `[1, 1]`, `[2, 1]`); as folhas da árvore são os slots.
- A grade regular vira o caso particular «N colunas iguais, cada uma com M linhas iguais», e **a saída da grade não muda**.
- Para o dono, a 1.9.0 entrega um **catálogo de modelos prontos**, escritos como árvores. Começo proposto, aberto a troca:
  - `1 + 2` — uma alta à esquerda, duas empilhadas à direita: o caso do dono;
  - `2 + 1` — duas em cima, uma larga embaixo;
  - `1 + 3` — uma grande em cima, três embaixo;
  - `Destaque + 4` — uma grande em cima, 2×2 embaixo;
  - `1 + 2 + 1` — uma larga, duas no meio, uma larga.
- Cada modelo tem **um controle de proporção** («divisão principal: 50%»). Ele cobre o «a alta maior» sem editor.
- **Ganha:**
  - cortável na guilhotina por construção;
  - espaçamento X/Y, sangria e marcas com regra única;
  - o preset guarda a árvore (JSON aninhado, pequeno);
  - o desenhista vetorial da F5 desenha uma vez só;
  - um editor de divisões («dividir esta célula», «juntar») pode vir depois **sobre o mesmo modelo**, sem migração.
- **Perde:** nem todo layout é árvore. Um «cata-vento» de 4 retângulos em volta de um quadrado central, por exemplo, não é. E o caminho até o editor completo fica para outra versão.

### C — Editor livre de caixas (como o Custom Package do Lightroom)
Cada célula é um retângulo `x, y, w, h` que o usuário arrasta e redimensiona.
- **Ganha:** qualquer arranjo.
- **Perde:**
  - é a maior UI da F5 (arrastar, redimensionar, encaixe, sobreposição);
  - caixas soltas não garantem cortes retos;
  - a regra de marcas e sangria fica indefinida (com quem uma caixa «divide» o corte?);
  - o «em segundos» do dono vira «monte a página».
- **Descartada para a 1.9.0.** Se um dia vier, a árvore da B continua sendo o formato dos modelos prontos.

### D — Células por tamanho físico, com arranjo automático (Picture Package)
O usuário pede «1× 13×18 cm + 2× 9×13 cm», e o app arruma na folha.
- **Ganha:** é a linguagem do laboratório.
- **Perde:** é um problema de empacotamento, e a resposta pode não caber ou desperdiçar papel.
- **Descartada para a 1.9.0.** O resultado de um arranjo automático **é uma árvore da B**, então D pode vir depois por cima dela.

## Corte, sangria e marcas na moldura (para a opção B)

- **Cortes:** cada divisão gera **segmentos** de corte, não linhas de borda a borda. Na `1 + 2`, o corte vertical atravessa a folha, e o horizontal só atravessa o pedaço da direita.
- **Marcas:** uma marca em cada ponta de segmento que **toca a borda da área útil**. A ponta que encosta noutro corte não leva marca: depois do primeiro corte, ela vira borda do pedaço.
  - Na grade, todo segmento toca as duas bordas, então **a regra dá exatamente as marcas da 1.6.0**. Isso vira teste de não-regressão.
  - **A conferir na spec:** se, depois do primeiro corte, o operador ainda acha o segundo corte sem uma marca interna. Na prática de laboratório, sim, pela marca da borda externa daquele pedaço.
- **Espaçamento:** divisão vertical usa o «Entre colunas»; divisão horizontal, o «Entre linhas». Sem campo novo.
- **Sangria:** igual à 1.6.0. Cada lado vai até metade do espaçamento da divisão vizinha, ou até a margem na borda.
- **«Linhas atravessando»:** na moldura, desenham os **segmentos**, não a folha inteira. Na grade, nada muda.
- **Ordem dos slots:** ordem de leitura da árvore (de cima para baixo, da esquerda para a direita), e a lista preenche os slots nessa ordem, como hoje. Todas as folhas do trabalho usam a mesma moldura; trocar de moldura é trocar no seletor e gerar de novo.
- **Guarda de qualidade:** mede cada item contra **o slot em que ele cai**, e não contra uma célula única.

## Opções consideradas — o arquivo único (DEC-003)

### 1 — Manter o arquivo único
- **Ganha:** zero trabalho agora.
- **Perde:** a moldura soma, por estimativa, de 400 a 600 linhas (modelo, catálogo, seletor), e o arquivo passa de 4.300. A cada WO, quem aplica lê trechos de um arquivo de 160 KB, e uma âncora errada custa mais.

### 2 — Dividir em dois módulos antes da moldura, sem mudar comportamento *(recomendada)*
- `imposer_core.py` recebe tudo o que não usa Tk: dependências, modelo, geometria, PDF, motor e ingestão.
- `print_imposer.py` fica com a GUI e o `main()`, e continua sendo o arquivo que o `.bat` abre. Ele reexporta os nomes do núcleo, para `import print_imposer as pi` dos testes seguir funcionando.
- Os 5 testes de AST passam a ler os dois arquivos.
- **Ganha:**
  - a moldura e a vetorial nascem num núcleo de cerca de 1.900 linhas, testável sem o stub de Tk;
  - o empacotamento (1.10.0) não muda nada (o PyInstaller segue os imports);
  - a DEC-003 já previa reavaliar «se a entrada vetorial chegar», e ela chegou na 1.4.0.
- **Perde:** uma versão só de refatoração (1.8.1). É mecânica, mas mexe em todo o arquivo.
- **O risco é auditável por comando**, e é por isso que a recomendo (CEREBRO: «risco que se confere por comando é custo de conferência»):
  - antes e depois, a mesma suíte (218 testes);
  - o mesmo `/smoke`;
  - **hash idêntico** das folhas geradas para um conjunto fixo de configurações (grade, marcas, sangria, PDF, SVG, rotação).

  Qualquer diferença aparece na hora.

### 3 — Pacote com muitos módulos (`printimposer/engine.py`, `geometry.py`, `gui/…`)
- **Ganha:** a organização «de livro».
- **Perde:** mais imports cruzados (os globais `PDF_OK`, `SVG_BACKEND`, `DND_PKG_OK` são lidos dos dois lados) e um diff maior, sem ganho a mais para um projeto de um usuário.
- **Descartada:** a 2 pega 90% do ganho por uma fração do risco.

## Recomendação

1. **Modelo B:** divisões sucessivas, com catálogo de modelos prontos e um controle de proporção por modelo. Atende o «em segundos» do fotógrafo, é cortável na guilhotina por construção, generaliza a geometria da 1.6.0 sem mudar a saída da grade, e deixa C e D como camadas futuras sobre o mesmo formato.
2. **Dividir o arquivo em dois módulos numa 1.8.1 só de refatoração**, antes da moldura, conferida por hash idêntico das folhas.

Com isso, a ordem da F5 fica: 1.8.1 refatoração → 1.9.0 moldura → 1.10.0 executável e GitHub Releases → vetorial (ou F6).

**Melhor argumento contra a 1.8.1:** é uma versão sem nada novo para quem usa. Resposta: ela custa uma WO, a conferência é automática, e cada WO seguinte (moldura, vetorial, empacotamento) fica mais barata e menos frágil de aplicar.

## Riscos

- **O catálogo errar o gosto do dono.** Os cinco modelos acima são palpite do chat. Sinal: o dono não usar nenhum no roteiro da 1.9.0. Remédio: ele diz quais molduras usa e a lista muda antes da spec (ponto de decisão 3).
- **Moldura × presets antigos.** O preset da grade não pode mudar de forma. A árvore entra como campo novo e opcional (`layout`). Ausente, vale a grade `cols × rows` de hoje.
- **Moldura × orientação do papel.** Um modelo desenhado para retrato pode ficar estranho em paisagem. A recomendação para a spec é o modelo ser definido em proporções da área útil (vale nas duas) e o catálogo mostrar a miniatura já no papel escolhido.
- **Refatoração que muda saída em silêncio.** Por exemplo, a ordem de importação mudando qual back-end de SVG ou PDF liga. Sinal: o hash das folhas, ou o cabeçalho (`SVG: … · PDF: … · Arrastar: …`) diferente da 1.8.0. Comando de auditoria: `python -c "import print_imposer as pi; print(pi.SVG_BACKEND, pi.PDF_BACKEND, pi.DND_PKG_OK)"`, antes e depois.
- **Marca sem ponto de referência num corte interno.** Se o operador sentir falta de marca nos cortes que não tocam a borda, a ideia das «marcas nos cantos internos» (IDEAS, «se pedido») ganha um pedido.

## Ponto de decisão

1. **Modelo da moldura:** aprova a **B** (divisões sucessivas, catálogo pronto e um controle de proporção por modelo)?
2. **Dividir o arquivo** em núcleo + GUI numa **1.8.1** só de refatoração, antes da moldura?
3. **O catálogo inicial** (`1 + 2`, `2 + 1`, `1 + 3`, `Destaque + 4`, `1 + 2 + 1`): fica assim, ou há molduras que o seu fotógrafo usa e que devem entrar?

## Desfecho *(2026-11-10)*

**Decisão do dono:** as três recomendações aprovadas — modelo **B** (divisões sucessivas, catálogo pronto e um controle de proporção por modelo); **1.8.1** só de reorganização antes da moldura; catálogo inicial `1 + 2`, `2 + 1`, `1 + 3`, `Destaque + 4`, `1 + 2 + 1`.

**Pergunta do dono, respondida no chat:** «os dois como opção configurável?» — não se aplica: o modelo da moldura é decisão de **produto** (o que o usuário vê), e a divisão do arquivo é de **organização do código** (invisível para quem usa). Não são alternativas entre si, e a divisão do arquivo não tem o que configurar.

**Registro:** DEC-017 (dois módulos; substitui a DEC-003) e DEC-018 (modelo da moldura), com o texto na wo0014. Spec da 1.8.1: `meta/specs/261110-SPEC-F5-reorganizacao.md`. A spec da 1.9.0 (moldura) vem depois do roteiro da 1.8.1.

