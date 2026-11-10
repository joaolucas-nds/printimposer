# SPEC — F5: reorganização em dois módulos (v1.8.1)

> Spec de refatoração. Escrita em 2026-11-10, depois do portão da moldura (`meta/analises/261110-ANALISE-portao-moldura.md`, decidido: DEC-017).
> Alvo: v1.8.1. Estado: aprovada pelo dono em 10/11, a implementar — pelo Claude Code, via `meta/workorders/261110-wo0014-reorganizacao.md`.
> **Nenhuma mudança para quem usa.** O critério principal é a saída **idêntica byte a byte**.

## Problema

`print_imposer.py` tem 3.875 linhas. A moldura (1.9.0) e a vetorial vão mexer no centro do motor. Fazer isso num arquivo de 160 KB, que mistura cálculo e janela, encarece cada WO e torna cada âncora mais frágil. As linhas 1–1.907, exceto o import do CustomTkinter e o bloco do arrastar, **já não usam Tk**: a divisão existe, só não está no disco.

## Critérios de aceite (verificáveis)

- [ ] Dois arquivos na raiz do repo:
  - **`imposer_core.py`** — tudo o que não usa Tk;
  - **`print_imposer.py`** — a GUI e o `main()`.
- [ ] `python print_imposer.py` abre o app como antes, e o `.bat` gerado continua apontando para `print_imposer.py`.
- [ ] `imposer_core.py` **não importa** `tkinter`, `customtkinter` nem `tkinterdnd2`, nem direta nem indiretamente. Conferência: `python -c "import sys, imposer_core; print([m for m in ('tkinter','customtkinter','tkinterdnd2') if m in sys.modules])"` imprime `[]`.
- [ ] `import print_imposer as pi` continua dando acesso a todos os nomes que os testes usam hoje (`pi.sheet_geometry`, `pi.ImpositionEngine`, `pi._PDF_MODS`…).
- [ ] **Saída idêntica:** um conjunto fixo de folhas gerado com a 1.8.0 (`08a1a31`) e com a 1.8.1 tem o mesmo SHA-256, folha por folha. O conjunto cobre:
  - grade 2×2 sem guia;
  - linhas atravessando;
  - marcas + sangria espelhada;
  - sangria incluída;
  - PDF de entrada;
  - SVG, se houver back-end (senão, diga);
  - rotação manual 90°;
  - saídas PNG, PDF sem perda, PDF JPEG e JPEG.
- [ ] O cabeçalho do app mostra os mesmos back-ends de antes. Conferência: `python -c "import print_imposer as pi; print(pi.VERSION, pi.SVG_BACKEND, pi.PDF_BACKEND, pi.DND_PKG_OK, sorted(pi.SUPPORTED_EXT))"`, antes e depois; só a versão muda.
- [ ] Suíte verde com **os mesmos 218 testes** (mais os novos desta spec), e nenhum teste apagado.
- [ ] `/smoke` sem FALHOU.

## Decisões de design

### 1. O que vai para cada lado
- **`imposer_core.py`:**
  - os imports sem Tk (`os`, `sys`, `PIL`…);
  - as seções «SUPORTE OPCIONAL A SVG», «… A PDF (ENTRADA)» e «… A AVIF / HEIC»;
  - «CONSTANTES», **inteira**, inclusive os rótulos de interface: são dados puros, e separá-los fica para quando doer;
  - «PERSISTÊNCIA», «CARREGAMENTO DE IMAGEM», «MODELO DE DADOS», «GEOMETRIA DE CORTE E SANGRIA», «AVISO DO SEGUNDO DESTINO», «ESCRITOR DE PDF», «MOTOR DE IMPOSIÇÃO», «GERADOR DE .BAT» e «INGESTÃO DE ARQUIVOS»;
  - as funções de ajuda puras que hoje estão no meio da GUI, se alguma for usada pelo núcleo. Liste no relatório.
- **`print_imposer.py`:**
  - o docstring de versões (o histórico «Novidades da 1.x» fica aqui);
  - os imports de Tk e CustomTkinter, com o `set_appearance_mode`/`set_default_color_theme`;
  - a seção «SUPORTE OPCIONAL A ARRASTAR E SOLTAR»;
  - os widgets, os painéis, a `PrintImposerApp`, `enable_dpi_awareness`, os relatórios de erro de abertura e o `main()`.
- **Fronteira:** `print_imposer.py` importa o núcleo; **o núcleo nunca importa `print_imposer`**.

### 2. Como a GUI e os testes enxergam o núcleo
- No topo de `print_imposer.py`: `import imposer_core as core` e `from imposer_core import *`.
- Os nomes com `_` que a GUI ou os testes usam não vêm pelo `*`. Importe-os um por um (`from imposer_core import _PDF_MODS, …`) e liste-os no relatório.
- O núcleo ganha `VERSION`. O `print_imposer.py` não redefine a versão: usa a do núcleo.

### 3. Patches nos testes: onde o nome é LIDO
Esta é a armadilha da divisão. Hoje há 22 `mock.patch.object(pi, …)` ou equivalentes. Depois da divisão, `pi.X` é **uma cópia** do nome do núcleo, e trocar a cópia não muda o que as funções do núcleo leem. O teste passaria por não testar mais nada.

- Cada patch passa a mirar o **módulo que lê o nome** (`core`, quase sempre).
- O relatório traz a tabela: patch, alvo antigo, alvo novo, e quem lê o nome.
- Um teste novo prova a regra: com `mock.patch.object(core, "PDF_OK", False)`, a guarda de qualidade pula o PDF (o mesmo efeito do teste da linha 1414 de hoje).

### 4. Testes que leem o código-fonte
Os 5 testes de AST com caminho fixo `print_imposer.py`:
- a colisão com nomes do Tk (FIX-003) e os da GUI (área útil, `main`, worker) leem **`print_imposer.py`**;
- os que olham o núcleo leem **`imposer_core.py`**.

O `TkAttributeCollisionTests` lê **os dois**. Um teste novo confere a fronteira: o AST de `imposer_core.py` não tem `import tkinter`, `import customtkinter` nem `tkinterdnd2`.

### 5. `__file__`
`shortcut_initial_dir` usa `Path(__file__).resolve().parent.parent` (a pasta-pai do projeto). Os dois arquivos ficam na mesma pasta, então o resultado não muda, mas confira com o teste que já existe. O `script` do atalho `.bat` continua sendo `print_imposer.py`.

### 6. Documentos que citam «arquivo único»
- README (estrutura do projeto) e CLAUDE.md (linha 9) mudam pela WO.
- CONTEXT e GLOSSARY são do chat, e mudam depois do relatório.
- A DEC-003 fica «substituída pela DEC-017».

## Fora de escopo
- Qualquer mudança de comportamento, de texto de interface ou de nome de função.
- Dividir a GUI em vários arquivos; mover constantes de rótulo para a GUI.
- Renomear `print_imposer.py`.
- Moldura (1.9.0).

## Passos
1. Gerar as folhas de referência com a 1.8.0 e guardar os SHA-256 **fora do repo** (pasta temporária).
2. Criar `imposer_core.py` movendo as seções, sem editar o conteúdo delas (só imports).
3. Ajustar o topo de `print_imposer.py`.
4. Testes: patches no alvo certo, AST nos dois arquivos, testes novos de fronteira e de patch.
5. Regerar as folhas e comparar os hashes; conferir os back-ends.
6. README, CLAUDE.md, `/smoke`.
