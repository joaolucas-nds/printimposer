# WO 0014 — v1.8.1: reorganizacao em dois modulos (imposer_core + print_imposer); DEC-017 e DEC-018

## Cabecalho

> **Tipo:** mista — Parte A: registro (ancoras exatas). Parte B: refatoracao a partir da spec, **sem mudanca de comportamento**. Nao muda a interface: **nao ha roteiro do dono** alem de abrir o app uma vez (no chat).
> **Config sugerida:** Opus · `/effort` alto (move ~1.900 linhas; a armadilha e silenciosa: patch de teste que vira inerte).
> **Pre-requisito:** HEAD `08a1a31` em `main`, empurrado; tag `v1.8.0`. Suite verde (218 testes; 5 skips de SVG). Roteiro do dono da 1.8.0 feito em 10/11: tudo certo.
> **Base:** `meta/specs/261110-SPEC-F5-reorganizacao.md`; portao da moldura decidido em 10/11 (`meta/analises/261110-ANALISE-portao-moldura.md`).
> **Arquivos que o chat gravou no disco e esta WO versiona** (`sha1sum` medido ao gravar):
> - `9fc8911ad1bf51c58c5156ae5c8e9714f787bc15  meta/specs/261110-SPEC-F5-reorganizacao.md`
> - `67b41a2adef3b08b5dd87535913a1e779deaeeb3  meta/analises/261110-ANALISE-portao-moldura.md`
> - `98b5f77396dc63cb54334dfe318237c03a15579b  meta/ROADMAP.md`
> - `602718671422603eb1a13840010ae24611cf0d84  logs/2026-11-10.md`
> **Ancora semantica:** trecho que nao bater EXATAMENTE → **PARE e reporte**.
> **Idempotencia:** texto novo inteiro ja no arquivo e ancora ausente → PULE e diga.
> **Ancoras lidas em:** lidas pelo chat NESTE turno: `meta/STATUS.md` (arquivo inteiro, sha1 `14fa92711ef55646e34ad662cf95ef3797900cfe`); `meta/DECISIONS.md` (sha1 `8e9214ad0b39d1a5c5422a4a3ce327460c3b5d3e`; linhas 57–58 e a ultima); `meta/IDEAS.md` (sha1 `ee296d5fbff1c7c2b91877b303d9f57682459c20`; linha 24); `README.md` (sha1 `8ef9da91366c638cb54d4cac34f1e2183589cbbf`; linhas 1, 231 e as versoes); `CLAUDE.md` (sha1 `65373c21367430c95a43d52a420823a84904f258`; linha 9); `tests/test_engine.py` (linhas 1–60 e os 22 patches); `print_imposer.py` (marcadores de secao 98–3779, `__file__` em 464/3571/3654).
> **Canal dos meta neste ciclo = CODE** para STATUS, DECISIONS, IDEAS e CHANGELOG. O chat ja gravou a spec, a analise, o ROADMAP e a parte dele do log de 10/11.
> **Proximo comando:** nenhum.

---

## 1. Por que

Antes da moldura (1.9.0), separar o nucleo sem Tk da GUI, como decidido no portao (DEC-017). Refatoracao pura: a prova e saida **identica byte a byte** a da 1.8.0. Spec: `meta/specs/261110-SPEC-F5-reorganizacao.md`.

---

# PARTE A — registro (commit `docs`, antes do codigo)

## Edicao A1 — `meta/STATUS.md` · substituir o arquivo inteiro
Pre-condicao: `sha1sum meta/STATUS.md` = `14fa92711ef55646e34ad662cf95ef3797900cfe`.

**Atencao:** copie do STATUS atual, sem mudar, a lista inteira «✅ Funcionando» (da linha depois do titulo da secao ate a linha antes de `## 🔧 Em Progresso`) para o lugar marcado `<<FUNCIONANDO — copiar sem mudar>>`. Ela foi escrita pelo Code na wo0013 e esta certa. Tudo o mais, literal:

~~~~
# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.8.0** — 2026-11-10 — Rotação por item (`⟳`: 0° segue o Auto-Rotate; 90/180/270° exatos) e `Preencher ▾` (completar a última folha; exatamente N folhas). Suíte verde (218 testes; 5 skips de SVG). Roteiro do dono feito em 10/11: tudo certo.

## 🎯 Foco atual
**Produto:** F5 em curso (escada C). 1.7.0 e 1.8.0 conferidas pelo dono em 10/11; portão da moldura decidido (modelo de divisões sucessivas, DEC-018). Agora: **1.8.1 — reorganização** (wo0014) em dois módulos, sem mudança para quem usa; depois, a **1.9.0 — moldura**.
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013). WO que muda a interface traz o roteiro do dono **no chat** e a linha `/apply-wo` em bloco cercado.

## ✅ Funcionando *(suíte headless verde; roteiro do dono da 1.8.0 feito em 10/11, tudo certo)*
<<FUNCIONANDO — copiar sem mudar>>

## 🔧 Em Progresso
- 1.8.1 — reorganização (wo0014, Parte B).

## ❌ Quebrado / Com Problema
- (nada conhecido.)

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Chat:** depois da 1.8.1, atualizar CONTEXT e GLOSSARY para os dois módulos e escrever a spec da 1.9.0 (moldura, DEC-018).
- [ ] **Dono (opcional):** impressão de teste raster × vetorial numa **gráfica** de ponta (em casa, 06/11, a diferença só aparece de muito perto). Se o texto raster sair mole, reabre a vetorial (gatilho da DEC-015).
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho», e a seção «Corte e sangria» com marcas de canto no preview (as capturas de 07/11 na pasta-pai servem).
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — mudou em 04/11 (linha do `/apply-wo` e do roteiro).
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-10** — Num dia: 1.7.0 (arrastar) e 1.8.0 (tiragem) aplicadas pelo Code e conferidas pelo dono («tudo certo» nas duas). Portão da moldura decidido: divisões sucessivas com catálogo pronto (DEC-018) e o arquivo único dividido em núcleo + GUI numa 1.8.1 (DEC-017). Spec e wo0014 escritas.
~~~~

**Saem do STATUS e por que:** o roteiro da 1.8.0 e a analise da moldura (feitos); as quatro entradas de 09–10/11 de «Ultima conversa», resumidas numa (detalhe em `logs/2026-11-10.md` e no CHANGELOG).
**Conferencia:** `grep -c "<<FUNCIONANDO" meta/STATUS.md` → `0`; `grep -c "Aguardando o roteiro" meta/STATUS.md` → `0`.

## Edicao A2 — `meta/DECISIONS.md`
**A2a. Trocar** o par de linhas:
~~~~
## DEC-003 — Arquitetura em arquivo único
**Data:** 2026-06-02 · **Status:** aceita
~~~~
**por:**
~~~~
## DEC-003 — Arquitetura em arquivo único
**Data:** 2026-06-02 · **Status:** substituída pela DEC-017 (2026-11-10)
~~~~
**A2b. Inserir IMEDIATAMENTE DEPOIS** da ultima linha do arquivo (linha inteira):
~~~~
- A janela principal passa a herdar de uma classe de terceiros que usa `self._w`: o `TkAttributeCollisionTests` continua valendo, e mudança nessa classe pede `/smoke`.
~~~~
**o bloco:**
~~~~

---

## DEC-017 — Dois módulos: núcleo sem Tk (`imposer_core.py`) e GUI (`print_imposer.py`)
**Data:** 2026-11-10 · **Status:** aceita · **Substitui:** DEC-003

### Contexto
A DEC-003 (arquivo único, 06/2026) previa reavaliar «se a entrada vetorial chegar»; ela chegou na 1.4.0. Em 10/11 o arquivo tinha 3.875 linhas, e as linhas 1–1.907 (exceto o import do CustomTkinter e o bloco do arrastar) já não usavam Tk. A moldura (1.9.0) e a vetorial mexem no centro do motor. E o argumento «baixe e rode um arquivo» perdeu força: há um usuário, e o executável vem na 1.10.0. Análise: `meta/analises/261110-ANALISE-portao-moldura.md`.

### Decisão
Dois arquivos na raiz: `imposer_core.py` (dependências opcionais sem Tk, constantes, persistência, modelo, geometria, PDF, motor, `.bat`, ingestão) e `print_imposer.py` (GUI e `main()`, o arquivo que o `.bat` abre). A GUI importa o núcleo; o núcleo nunca importa a GUI nem Tk. `print_imposer.py` reexporta o núcleo (`from imposer_core import *`, mais os nomes com `_` que usa). Feita numa versão só de refatoração (1.8.1), conferida por SHA-256 idêntico das folhas geradas antes e depois.

### Alternativas consideradas
- **Manter o arquivo único** — a moldura o levaria a mais de 4.300 linhas, com âncoras de WO cada vez mais frágeis.
- **Pacote com muitos módulos** — mais imports cruzados (os globais dos back-ends são lidos dos dois lados) e um diff maior, sem ganho a mais para um projeto de um usuário.

### Consequências
- Patch de teste mira o módulo que **lê** o nome (`imposer_core`, quase sempre): patch em `print_imposer` vira inerte em silêncio.
- Testes de AST leem o arquivo certo; um teste guarda a fronteira (o núcleo sem import de Tk).
- O núcleo pode ser testado sem o stub de Tk.

---

## DEC-018 — Moldura por divisões sucessivas, com catálogo pronto
**Data:** 2026-11-10 · **Status:** aceita (implementação na 1.9.0)

### Contexto
O critério da F5 pede layout não-uniforme. Caso do dono: duas fotos horizontais iguais e uma retrato alta na mesma folha; uso real (04/11): um fotógrafo monta, em segundos, várias molduras com uma série de fotos. O Lightroom separa grade, «Picture Package» e «Custom Package», e otimiza o arranjo para o menor número de cortes; as folhas «divididas» dos laboratórios (ex.: 1× 5×7 + 2× 4×5 numa 8×10) se cortam com cortes retos, pedaço por pedaço.

### Decisão
Uma moldura é uma **árvore de divisões**: cada nó divide o espaço em partes, na vertical ou na horizontal, com proporções; as folhas da árvore são os slots, preenchidos em ordem de leitura. A grade `cols × rows` é o caso particular e não muda de saída. A 1.9.0 entrega um catálogo — `1 + 2`, `2 + 1`, `1 + 3`, `Destaque + 4`, `1 + 2 + 1` — com um controle de proporção por modelo. Cortes viram **segmentos**; marcas vão nas pontas de segmento que tocam a borda da área útil (na grade, exatamente as da 1.6.0); divisão vertical usa o espaçamento entre colunas, horizontal o entre linhas; sangria como na 1.6.0; a guarda de qualidade mede cada item contra o slot em que ele cai.

### Alternativas consideradas
- **Lista fixa desenhada à mão** — cada moldura seria código novo, sem proporção ajustável.
- **Editor livre de caixas** — a maior UI da fase; caixas soltas não garantem cortes retos e deixam marcas e sangria sem regra.
- **Células por tamanho físico com arranjo automático** — problema de empacotamento; o resultado dele é uma árvore desta decisão, então pode vir depois por cima.

### Consequências
- O preset ganha um campo opcional (`layout`); ausente, vale a grade.
- Um editor de divisões e o arranjo por tamanho físico podem vir depois sobre o mesmo formato, sem migração.
- O desenhista vetorial da F5 desenha a geometria já generalizada, uma vez só.
~~~~
**Conferencia:** `grep -c "^## DEC-017 \|^## DEC-018 " meta/DECISIONS.md` → `2`; `grep -c "substituída pela DEC-017" meta/DECISIONS.md` → `1`.

## Edicao A3 — `meta/IDEAS.md`
**Trocar** a linha inteira que comeca com `Layout não-uniforme tipo "moldura". Exige células de tamanhos diferentes` por:
~~~~
Layout não-uniforme tipo "moldura". Exige células de tamanhos diferentes — outro modelo que o grid regular. **Caso de uso do dono (04/11):** um fotógrafo pega uma série de fotos e monta, em segundos, várias molduras diferentes com as fotos variadas. **Decidido em 10/11 (DEC-018):** divisões sucessivas com catálogo pronto (`1 + 2`, `2 + 1`, `1 + 3`, `Destaque + 4`, `1 + 2 + 1`) e um controle de proporção por modelo; entra na **1.9.0**. Editor de divisões e arranjo por tamanho físico ficam para depois, sobre o mesmo modelo.
~~~~
**Conferencia:** `grep -c "DEC-018" meta/IDEAS.md` → `1`.

## Commit A — e push
```
git add -- meta/STATUS.md meta/DECISIONS.md meta/IDEAS.md meta/ROADMAP.md meta/specs/261110-SPEC-F5-reorganizacao.md meta/analises/261110-ANALISE-portao-moldura.md logs/2026-11-10.md meta/workorders/261110-wo0014-reorganizacao.md
git commit -m "docs: portao da moldura decidido (DEC-017, DEC-018) e spec da 1.8.1"
git push
```
Conferencia: `git diff --cached --stat` → exatamente esses 8 caminhos.

---

# PARTE B — implementar `meta/specs/261110-SPEC-F5-reorganizacao.md` (commit `refactor`)

## Edicao B0 — referencia ANTES de mexer (no codigo da 1.8.0)
1. Em pasta temporaria **fora do repo**, com `USERPROFILE` e `HOME` temporarios, um script que importa o `print_imposer` atual e gera, pelo `ImpositionEngine`, o conjunto da spec (grade 2×2 sem guia; linhas; marcas + sangria espelhada; sangria incluida; uma pagina de PDF de `../este/`, so leitura; SVG se houver back-end; rotacao 90°) em PNG, PDF sem perda, PDF JPEG e JPEG — com imagens de teste geradas pelo script (cores e tamanhos fixos) mais o PDF do dono. Guarde `nome → sha256` num JSON na pasta temporaria. **O mesmo script, sem mudar uma linha, roda depois da divisao.**
   - Se algum formato embute data/hora (ex.: metadado de PDF), compare os pixels decodificados (`Image.tobytes()`) em vez dos bytes do arquivo, e diga qual e por que.
2. `python -c "import print_imposer as pi; print(pi.VERSION, pi.SVG_BACKEND, pi.PDF_BACKEND, pi.DND_PKG_OK, sorted(pi.SUPPORTED_EXT))"` → guarde a saida.
3. Suite: diga o numero (218) e o tempo.

## Edicao B1 — dividir
Siga a spec («O que vai para cada lado», «Como a GUI e os testes enxergam o nucleo»). **Mova as secoes sem editar o corpo delas**: as unicas linhas novas sao imports, o docstring curto do `imposer_core.py` (o que ele e, a fronteira, ponteiro para a DEC-017) e o `VERSION = "1.8.1"` (que passa a morar no nucleo). Comentarios existentes vao junto do codigo que comentam. Decisao de arquitetura nao coberta → **PARE e relate**.
- `print_imposer.py`: docstring de versoes ganha `Novidades da 1.8.1: o nucleo sem Tk foi para imposer_core.py (DEC-017); nada muda para quem usa.`

## Edicao B2 — testes
- Os 22 patches (`mock.patch.object(pi, …)` e afins): cada um passa a mirar o modulo que LE o nome. **Relatorio:** tabela `linha | nome | alvo antes | alvo depois | quem le`.
- Os 5 testes de AST: o arquivo certo por teste (spec §4); `TkAttributeCollisionTests` le os dois.
- Novos: (a) fronteira — o AST de `imposer_core.py` nao tem import de `tkinter`, `customtkinter` nem `tkinterdnd2`; (b) em subprocesso, `import imposer_core` deixa `tkinter`, `customtkinter` e `tkinterdnd2` fora de `sys.modules`; (c) `mock.patch.object(core, "PDF_OK", False)` faz a guarda de qualidade pular o PDF.
- `test_versao`: `1.8.1`.
- Nenhum teste apagado: diga a contagem antes e depois.

## Edicao B3 — README e CLAUDE.md (texto exato)
**B3a.** `README.md`: trocar `├── print_imposer.py      # o app inteiro, em um arquivo` por:
~~~~
├── print_imposer.py      # a janela (GUI) — é este que se abre
├── imposer_core.py       # o motor: cálculo, geometria, PDF, sem interface
~~~~
**B3b.** `README.md`: trocar `# 🖨 PrintImposer v1.8` por `# 🖨 PrintImposer v1.8.1`; `v1.8.0 · SVG: … · PDF: … ┐` por `v1.8.1 · SVG: … · PDF: … ┐`; `*PrintImposer v1.8.0 —` por `*PrintImposer v1.8.1 —`. Se o diagrama desalinhar por um caractere, acerte o espaco antes do `┐`.
**B3c.** `CLAUDE.md`: trocar `ex.: 4 cards A6 numa folha A4, prontos para imprimir e cortar. Arquivo único: `print_imposer.py`.` por:
~~~~
ex.: 4 cards A6 numa folha A4, prontos para imprimir e cortar. Dois módulos (DEC-017): `imposer_core.py` (motor, sem Tk) e `print_imposer.py` (GUI e `main()`).
~~~~
**Conferencia:** `grep -c "imposer_core.py" README.md CLAUDE.md` → `README.md:1` e `CLAUDE.md:1`; `grep -c "v1.8.0" README.md` → `0`.

## Edicao B4 — validacao
1. Rode o script da B0 **sem mudar nada nele** e compare: diga `N de N iguais`, ou a lista dos que diferem — **diferenca = vermelho**, PARE e relate.
2. O comando da B0.2 de novo: so a versao pode mudar.
3. `python -c "import sys, imposer_core; print([m for m in ('tkinter','customtkinter','tkinterdnd2') if m in sys.modules])"` → `[]`.
4. Suite verde: contagem e tempo.
5. `/smoke` (9 itens), com o app isolado. Diga tambem que o `Opções › Criar atalho…` gera o `.bat` apontando para `print_imposer.py`.
6. `wc -l imposer_core.py print_imposer.py tests/test_engine.py`.
7. Depois do push do commit B: tag `v1.8.1` no commit B e `git push origin v1.8.1`.

## Edicao B5 — registro
- `meta/CHANGELOG.md`: `## [1.8.1] — <data>` com **Modificado** (código dividido em `imposer_core.py` e `print_imposer.py`, DEC-017; saída idêntica à 1.8.0, conferida por SHA-256) e **Corrigido**, se a B2 achar patch inerte (diga qual).
- `meta/STATUS.md`: Versao 1.8.1 (aguardando o dono abrir o app uma vez); Em Progresso → `(vazio)`; «Ultima conversa» ganha uma entrada.
- `logs/<data de hoje>.md`: sua secao no FIM (se `2026-11-10`, depois da «Continuação — chat (noite)»; se outro dia, arquivo novo no formato do `meta/LOG-TEMPLATE.md`).

## Commit B — e push
```
git add -- imposer_core.py print_imposer.py tests/test_engine.py README.md CLAUDE.md meta/CHANGELOG.md meta/STATUS.md logs/
git commit -m "refactor: divide o app em imposer_core e print_imposer (v1.8.1)" -m "Nucleo sem Tk em imposer_core.py; GUI e main em print_imposer.py, que reexporta o nucleo (DEC-017). Saida identica a 1.8.0, conferida por SHA-256 das folhas. Patches dos testes miram o modulo que le o nome."
git push
```

---

## Fora de escopo
Mudanca de comportamento, de texto de UI ou de nome de funcao; dividir a GUI; renomear `print_imposer.py`; moldura; CONTEXT e GLOSSARY (o chat atualiza depois do relatorio); ROADMAP; `~/.printimposer` real do dono; `.claude/`.

## Armadilhas desta WO
- **Commit A antes do codigo; referencia (B0) antes de mexer.**
- **Patch inerte:** depois da divisao, `pi.X` e copia do nome do nucleo; trocar a copia nao muda o que o nucleo le. Teste que «passa» por isso nao testa nada — por isso a tabela da B2.
- **Globais mutaveis:** se algum codigo da GUI ATRIBUI a um global que o nucleo le (ex.: `_SVG_MODS`, `_PDF_MODS`, `OUT_FORMATS`), a atribuicao tem de ir ao modulo do nucleo (`core.X = …`). Procure `global ` e atribuicoes a nomes do nucleo na GUI e liste no relatorio.
- **Ordem dos probes:** os probes de SVG/PDF/AVIF/HEIC rodam no import do nucleo, como antes; o do arrastar fica na GUI. O cabecalho tem de mostrar o mesmo que na 1.8.0.
- **`__file__`:** `shortcut_initial_dir` (nucleo) e o `script` do atalho (GUI) — o `.bat` continua apontando para `print_imposer.py`.
- **Mover, nao reescrever:** `git diff --stat` deve mostrar remocoes no `print_imposer.py` ≈ insercoes no `imposer_core.py`; diga os dois numeros.
- **Isolamento:** `USERPROFILE` e `HOME` temporarios (CONTEXT, armadilha 11). As folhas de referencia e o script ficam FORA do repo.

## Relatorio de aplicacao
Formato `/apply-wo`, em `../AAMMDD-HHMM-code-printimposer-apply-wo0014.txt`. Se so a Parte A fechar verde, empurre o commit A e relate a Parte B como vermelha, com o menu. **Hash diferente na B4.1 e vermelho**, mesmo com a suite verde.

---

## Roteiro do dono *(copia — o original esta na resposta do chat de 10/11)*
1. Abra pelo `printimposer.bat` e gere uma folha qualquer, como sempre. Certo: cabeçalho `v1.8.1` e tudo igual à 1.8.0 — a mudança desta versão é só por dentro.
