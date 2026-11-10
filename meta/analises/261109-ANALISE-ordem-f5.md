# ANALISE — Ordem interna da F5 (Distribuição, fluidez e layouts livres)

> **Status:** Decidida (2026-11-10) — escada C, com o `.exe` depois da moldura; desfecho no fim e na DEC-016
> **Data:** 2026-11-09
> **Elos:** ROADMAP F5 · DEC-003, DEC-012, DEC-015 · `meta/analises/261103-ANALISE-ordem-f4.md` (mesmo formato de escada) · IDEAS (entradas «F5») · nota do dono `261107-0846.txt` (arquivada em `zz_notas-arquivadas/`)

## Problema

A F5 tem sete candidatos no ROADMAP e mais três no IDEAS, todos sem ordem. O custo deles vai de uma tarde (preencher N folhas) a uma mudança de modelo (moldura com células de tamanhos diferentes). E há dois acoplamentos que a ordem errada transforma em retrabalho:

1. **Moldura × vetorial.** As duas consomem a geometria da folha. Hoje `sheet_geometry` só sabe uma grade regular `cols × rows`. Se a vetorial vier antes, ela nasce desenhando a grade, e a moldura depois tem de generalizar a geometria **e** adaptar dois desenhistas (raster e vetorial). Se a moldura vier antes, a vetorial nasce uma vez, sobre a geometria já generalizada.
2. **`.exe` × dependências opcionais.** O executável tem de levar tudo o que o app usa (`customtkinter`, `pypdfium2`, `tkinterdnd2`, e depois o `pypdf`). Empacotar antes de as dependências da fase existirem obriga a refazer o empacotamento a cada dependência nova.

Além disso, o dono pediu um item em 07/11, por escrito: arrastar imagens e PDFs para a janela e importá-los assim («algo que senti falta», nota `261107-0846.txt`). É o único candidato com pedido explícito depois da F4.

Se nada for decidido, a próxima spec pega o item que parecer mais fácil, e a moldura (o caso do fotógrafo) e a vetorial podem acabar na ordem que gera retrabalho.

## Restrições / o que foi medido

**Lido no repositório neste turno** (ROADMAP, IDEAS, STATUS, CONTEXT, DECISIONS, `print_imposer.py`, `tests/test_engine.py`):

- **Tamanho:** `print_imposer.py` tem **3.519 linhas**; `tests/test_engine.py` tem **1.996** (`wc -l`, contado na cópia do disco de 09/11). A estrutura descrita no CONTEXT ainda fala em «~1960 linhas». A DEC-003 (arquivo único) dizia em 06/2026: «reavaliar se a F3 (entrada vetorial) chegar». A entrada vetorial chegou na 1.4.0 e a reavaliação não foi feita.
- **A entrada de arquivos já tem um funil único:** `plan_ingest(paths, confirm_many)` (linha 1730) decide o que entra a partir de uma lista de caminhos, expande PDF em páginas e pula o ilegível. «+ Arquivos» e «+ Pasta» passam por ele. **O arrastar-e-soltar só precisa entregar uma lista de caminhos ao mesmo funil**: o custo está na integração com a janela, não na ingestão.
- **O item da lista** (`ImageEntry`, linha 748) tem `path`, `page_index`, `quantity` e a miniatura. **Não tem rotação.** Auto-Rotate é global (`cfg.auto_rotate`) e entra em três lugares: `vector_render_box`, `_place_image` e a guarda de qualidade. A rotação por item mexe nesses três.
- **A geometria** (`sheet_geometry`, linha 987) é pura e em mm, mas assume grade regular: cada corte atravessa a folha inteira, e as marcas ficam nas pontas desses cortes. Numa moldura 2+1, os cortes **não** atravessam a folha. A regra das marcas precisa ser repensada lá, não só a posição das células.
- **Critério de conclusão da F5** (ROADMAP): executável Windows, manipulação por arraste, layout não-uniforme. **A vetorial, a rotação por item e preencher N folhas não estão no critério.** A F5 pode fechar sem elas.
- **Gatilho da DEC-015:** a vetorial sobe de prioridade se uma impressão em gráfica de ponta mostrar o texto raster mole. O teste não foi feito (STATUS, backlog opcional do dono).

**Fontes externas, lidas neste turno:**

- **`tkinterdnd2`** — o pacote é mantido; versões 0.6.0 a 0.6.2 saíram em julho de 2026 ([piwheels](https://www.piwheels.org/project/tkinterdnd2/)). Wheel `py3-none-any` com os binários do tkDnD dentro. O uso documentado troca a janela raiz por `TkinterDnD.Tk()` ([PyPI](https://pypi.org/project/tkinterdnd2/0.4.4.1/)). Como a raiz do app é `ctk.CTk`, isso não serve direto: é preciso misturar `DnDWrapper` na classe da janela e carregar o tkDnD à mão. Esse caminho é **deduzido do código do pacote, não medido**; está na medição pedida, abaixo.
- **`tkinterdnd2` no PyInstaller** — o pacote traz um `hook-tkinterdnd2.py` que coleta os binários; sem ele, o executável falha com «Unable to load tkdnd library» ([PyPI](https://pypi.org/project/tkinterdnd2/0.4.4.1/); relato no Stack Overflow, via [espelho](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/a/68702416)).
- **CustomTkinter no PyInstaller** — a documentação oficial manda usar `--onedir` (uma pasta, não um `.exe` solto) e incluir a pasta do `customtkinter` com `--add-data`, porque a biblioteca traz arquivos `.json` e `.otf` que o PyInstaller não pega sozinho ([CustomTkinter — Packaging](https://customtkinter.tomschimansky.com/documentation/packaging)). Ou seja: o «.exe» da F5 é, na prática, **uma pasta com um .exe dentro**.

**Não medido — pedido ao Code (seção «Medição pedida», no fim):** se o `tkinterdnd2` carrega com uma raiz `ctk.CTk` no Python do dono; a versão do Python em uso hoje; se o PyInstaller tem wheel para esse Python.

## Opções consideradas

### A — Só o critério: arraste → `.exe` → moldura; o resto vai para a F6
- **Ganha:** a fase fecha pelo caminho mais curto até o que o ROADMAP promete.
- **Perde:** rotação por item e preencher N folhas são baratos e úteis no dia a dia, e esperariam uma fase inteira sem motivo técnico.
- **Descartada como plano inteiro**, mas a ideia de que **a vetorial não segura o fechamento da fase** sobrevive na opção C.

### B — Vetorial primeiro
A geometria em mm da 1.6.0 já existe, e a análise do portão já está feita.
- **Ganha:** reaproveita o trabalho da etapa 4 enquanto está fresco.
- **Perde:** o gatilho da DEC-015 não disparou. O ganho medido é nitidez do texto de perto; o tamanho do arquivo fica igual ou maior. Nasceria sobre a grade regular e seria refeita quando a moldura generalizar a geometria. E ignora o único pedido explícito do dono.
- **Descartada**, salvo se o gatilho disparar (ver Riscos).

### D — Moldura primeiro
É o caso de produto mais forte (o fotógrafo que monta várias molduras em segundos).
- **Ganha:** o maior salto de produto vem logo.
- **Perde:** é o item mais caro e o menos especificado. Ainda não se sabe se a moldura é uma lista de modelos prontos (2+1, 1+2, 3 colunas desiguais…) ou um editor livre. Ela pede análise própria e provavelmente a decisão sobre o arquivo único (DEC-003). Abrir a fase por ela atrasa em semanas o que o dono pediu em 07/11.
- **Descartada como primeiro passo.** A moldura entra na escada, depois de uma análise própria.

### C — Escada: o pedido do dono primeiro, o barato em seguida, o caro com decisão própria *(recomendada)*

| Etapa | Itens | Versão | Por que nesta posição |
|---|---|---|---|
| **1. Arrastar** | Soltar arquivos e pastas na lista (`tkinterdnd2` opcional; sem ele, o app segue igual) · reordenar a lista arrastando (Tk puro, sem dependência) · aviso âmbar de sangria externa limitada pela margem (backlog de 07/11) | 1.7.0 | É o pedido do dono. Reusa `plan_ingest`, então o risco está todo na janela, e um `/smoke` cobre os dois arrastes. O aviso de sangria é pequeno demais para uma 1.6.1 sozinha. |
| **2. Tiragem** | Rotação manual por item (0/90/180/270, compondo com o Auto-Rotate) · preencher N folhas («completar a última folha» e «exatamente X folhas») | 1.8.0 | Os dois mexem no motor e se testam sem tela (headless), com pouca interface. Ficam antes do `.exe` para não forçar um reempacotamento por causa deles. |
| **3. Executável** | PyInstaller `--onedir` com `customtkinter`, `pypdfium2` e o hook do `tkinterdnd2` · «Criar atalho» passa a apontar para o `.exe` quando o app roda empacotado · README de instalação | 1.9.0 | As dependências da fase já existem nesse ponto (falta só o `pypdf`, que é Python puro). A posição depende do ponto de decisão 2. |
| **4. Portão: moldura** | Análise própria: modelo das células (modelos prontos ou editor livre), cortes e marcas em layout não-uniforme, e se o arquivo único se divide antes (DEC-003) | — | Decisão, não código. É a etapa que generaliza `sheet_geometry` de grade para lista de retângulos. |
| **5. Moldura** | O que o portão decidir | 1.10.0 (ou 2.0.0, se o modelo de preset mudar de forma incompatível) | Fecha o critério da F5. |
| **6. Vetorial** | Modo «Vetorial» no PDF via `pypdf`, como segundo desenhista sobre a geometria já generalizada (DEC-015) | 1.11.0 | Depois da moldura, para ser desenhada uma vez só. Não está no critério: se o gatilho não tiver disparado, pode passar à F6 sem reabrir nenhuma decisão. |
| **Cauda (sem versão)** | Marcas nos cantos internos («se pedido») · i18n · imprimir direto · nitidez em zoom 125%/150% | — | Nenhuma tem pedido nem dado. Ficam no IDEAS e no ROADMAP até ganharem um dos dois. |

## Recomendação

**Opção C.** Ela entrega primeiro o que o dono pediu, por um caminho barato, porque a ingestão já é um funil único. Põe em seguida dois ganhos que se testam sem tela. Empacota quando as dependências da fase já existem. E deixa os dois itens caros e acoplados (moldura e vetorial) na ordem que desenha a geometria uma vez só, com a moldura passando por uma análise própria, como a vetorial passou na F4.

**Melhor argumento contra:** a moldura é o maior salto de produto e fica na quinta posição. Resposta: as etapas 1 a 3 são pequenas (estimativa: uma WO cada, como as da F4). A análise da moldura pode até correr em paralelo à 1.8.0, porque não toca código.

**Sobre a DEC-003 (arquivo único), recomendo decidir no portão da moldura, não agora.** Nas etapas 1 a 3 o crescimento é pequeno e espalhado. A moldura mexe no centro do motor, e é lá que a divisão compensa. Com o `.exe` pronto na 1.9.0, o argumento de «baixe e rode um arquivo» também perde força, e a decisão fica mais barata.

## Riscos

- **O `tkinterdnd2` não carregar com a raiz `CTk`.** Seria o caso de o tkDnD não achar o Tcl do Python do dono, ou de o `DnDWrapper` brigar com o CustomTkinter. Sinal: o item 2 da medição pedida. Plano B: soltar só na janela inteira (registrar a raiz), ou adiar o arraste externo e manter só a reordenação na 1.7.0.
- **O `DnDWrapper` usa `self._w`.** Faz isso legitimamente, para registrar o widget no Tcl. O `TkAttributeCollisionTests` procura **escrita** em nome reservado, não leitura, então não deve disparar. Mas a mistura de classes na janela é exatamente o terreno da FIX-003: confira com `/smoke`, não só com a suíte.
- **Caminhos com espaço no evento de soltar.** O tkDnD entrega a lista numa string Tcl, com chaves em volta dos caminhos que têm espaço (`{C:/minha pasta/a.png}`). Separar à mão com `split()` quebra esses caminhos. O certo é `self.tk.splitlist(event.data)`. Vai para as armadilhas da WO da 1.7.0.
- **O `.exe` numa pasta surpreende.** Quem esperava um arquivo único recebe uma pasta. Sinal: a primeira pessoa que recebe pergunta «qual eu abro?». Remédio: atalho na raiz da pasta e uma linha no README.
- **O gatilho da DEC-015 disparar no meio da escada.** Se a impressão em gráfica mostrar o texto raster mole, a vetorial sobe para logo depois da etapa em curso e nasce sobre a grade regular. O custo é conhecido: a moldura passa a adaptar dois desenhistas. Vale saber disso antes, não descobrir na hora.
- **Rotação por item × Auto-Rotate.** As duas giram a mesma imagem. A spec da 1.8.0 tem de dizer quem vence (recomendação: a manual soma à automática, e «0°» quer dizer «deixa o Auto-Rotate decidir»), ou o preview e a guarda de qualidade vão divergir.

## Ponto de decisão

1. **Aprova a escada C?** A ordem seria: 1.7.0 arrastar → 1.8.0 tiragem → 1.9.0 `.exe` → portão da moldura → moldura → vetorial.
2. **O `.exe` tem pressa?** A pergunta é se alguém além de você vai rodar o app em breve. Se sim, ele fica na 1.9.0. Se não, desce para depois da moldura, onde empacota uma vez só, já com o `pypdf`. A recomendação é **1.9.0**: o `.exe` está no critério da fase, e empacotar cedo revela problemas de empacotamento enquanto o app ainda é pequeno.

## Medição pedida *(para o Claude Code — não é WO: não edita, não commita)*

Rode e devolva **número cru + o comando que o produziu**, sem interpretar (se achar que um número indica problema, diga o número primeiro e a suspeita depois). Grave o relatório em `../AAMMDD-HHMM-code-printimposer-probe-f5.txt`, com o `AAMMDD-HHMM` tirado de `date +%y%m%d-%H%M`. Ambiente isolado: crie uma pasta temporária e defina `USERPROFILE` **e** `HOME` para ela antes de importar o app (CONTEXT, armadilha 11). **Não instale nada no Python do dono**; apague o que criar.

1. `python --version` e `python -c "import tkinter; print(tkinter.TkVersion, tkinter.Tcl().eval('info patchlevel'))"`.
2. `tkinterdnd2` com raiz CustomTkinter: `pip install --target <tmp>/dnd tkinterdnd2`. Depois, com `PYTHONPATH=<tmp>/dnd`, um script de poucas linhas que:
   - cria uma classe `class Win(ctk.CTk, TkinterDnD.DnDWrapper)`;
   - instancia a janela e chama `TkinterDnD._require(win)`;
   - registra um `ctk.CTkFrame` filho com `drop_target_register(DND_FILES)` e liga `dnd_bind('<<Drop>>', ...)`;
   - imprime a versão do tkDnD devolvida e destrói a janela com `after(500, win.destroy)`.

   Diga: o nome do wheel baixado, a saída do script ou o traceback inteiro. **Não é preciso soltar nada:** a pergunta é só se carrega e registra.
3. `pip download pyinstaller --no-deps -d <tmp>/pi`: diga o nome do arquivo baixado (traz a versão e a plataforma).
4. `wc -l print_imposer.py tests/test_engine.py` e o número de testes da suíte (`python -m unittest` ou o comando do CLAUDE.md), para a linha de base da F5.

**O que esta medição NÃO responde:** se o arrastar funciona de verdade a partir do Explorer (isso é `/smoke`, na 1.7.0) e se o `.exe` abre (isso é a própria 1.9.0).

## Registro pendente *(vai na WO da primeira versão, não antes)*

- IDEAS: a ideia «Drag-and-drop de arquivos na janela» (assistente, 2026-06-15) ganha a nota «pedido do dono em 07/11 (`261107-0846.txt`): arrastar imagens e PDFs para a janela».
- ROADMAP: a F5 ganha a linha «Ordem: escada C — `meta/analises/261109-ANALISE-ordem-f5.md`», depois de aprovada.
- CONTEXT: a contagem «~1960 linhas» da estrutura está velha (3.519 em 09/11). Corrigir quando o chat regravar o CONTEXT.

## Desfecho *(2026-11-10)*

**Decisão do dono:** escada C aprovada. O `.exe` **não tem pressa** («sou só eu usando»): desce para depois da moldura, onde empacota uma vez só. O dono pediu, para essa etapa, publicação «profissional» no GitHub — página de Releases com o executável para baixar.

**Ordem final:** 1.7.0 arrastar → 1.8.0 tiragem → portão da moldura → 1.9.0 moldura → 1.10.0 executável + GitHub Releases → vetorial (ou F6). Registrada no ROADMAP.

**Medição** (`261110-1206-code-printimposer-probe-f5.txt`, arquivada em `zz_notas-arquivadas/`):

| Item | Resultado |
|---|---|
| Python / Tk | 3.13.13 · Tk 8.6 · Tcl 8.6.15 |
| `tkinterdnd2` com raiz CTk | wheel `tkinterdnd2-0.7.0-py3-none-any` (a análise citava 0.6.x); `class Win(ctk.CTk, TkinterDnD.DnDWrapper)` + `TkinterDnD._require(win)` → `tkdnd version: 2.10.3`; `CTkFrame` filho registrado com `DND_FILES`, sem traceback |
| PyInstaller | `pyinstaller-6.22.3-py3-none-win_amd64` |
| Linha de base | 3.519 + 1.996 linhas; 182 testes OK (5 skips) em 11,1 s (o CLAUDE.md diz ~2 s) |

**Consequências:** o risco nº 1 (o `tkinterdnd2` não carregar com a raiz CTk) caiu. A decisão de arquitetura do arrastar virou DEC-016. Spec: `meta/specs/261110-SPEC-F5-arrastar.md`. Os itens do «Registro pendente» vão na wo0012.

