# WO 0016 — v1.9.1: linha preta de 1 px no modo Preencher (FIX-007)

## Cabecalho

> **Tipo:** mista — Parte A: registro (ancoras exatas). Parte B: conserto minimo, com teste. Nao muda a interface: o roteiro do dono e so conferir uma folha (no chat).
> **Config sugerida:** Sonnet ou Opus · `/effort` medio (duas linhas de codigo; o cuidado e provar que so os casos do bug mudam).
> **Pre-requisito:** HEAD `2dcc84f` em `main`, empurrado; tag `v1.9.0`. Suite verde (243 testes; 5 skips de SVG). Roteiro do dono da 1.9.0 feito em 10/11: tudo certo.
> **Base:** achado do Code no relatorio `261110-2041-code-printimposer-apply-wo0015.txt`, item (5) (arquivado em `../zz_notas-arquivadas/`).
> **Arquivos que o chat gravou no disco e esta WO versiona** (`sha1sum` medido ao gravar):
> - `e33e9ad1921a8ae158efb50f809652646cece7e3  meta/ROADMAP.md`
> - `5a42a65618d62a67786bf7ab7687611ee527557e  logs/2026-11-10.md`
> **Ancora semantica:** trecho que nao bater EXATAMENTE → **PARE e reporte**.
> **Idempotencia:** texto novo inteiro ja no arquivo e ancora ausente → PULE e diga.
> **Ancoras lidas em:** lidas pelo chat NESTE turno: `meta/STATUS.md` (sha1 `b101d537316dd57c45d90c2b708ec15a505c6acd`; linhas 10, 13, 16, 45–47, 56–60); `meta/DECISIONS.md` (sha1 `7a6f989d86dbb9a51e9d72e3d31bc38d112b305c`; ultima linha); `README.md` (sha1 `ef610978404b26858e23cae2146017bf9dbee9e2`; linhas 1, 73, 257); `imposer_core.py` em `_place_image` (1638–1672).
> **Canal dos meta neste ciclo = CODE** para STATUS, DECISIONS e CHANGELOG. O chat ja gravou o ROADMAP e a parte dele do log de 10/11.
> **Proximo comando:** nenhum.

---

## 1. Por que — causa raiz

No modo Preencher, `_place_image` calcula `scale = max(cw/iw, ch/ih)` e redimensiona para `nw = int(iw * scale)`, `nh = int(ih * scale)`. Exemplo do Code: imagem 1500 × 1500 em slot 1086 × 1601 px → `scale = 1601/1500`, e `1500 × 1601/1500` da `1600,9999…`, que o `int()` trunca para **1600**. A imagem fica 1 px menor que o slot, o `crop((l, t, l + cw, t + ch))` passa da borda, e o Pillow preenche o que falta com **preto**. Vale para a grade (reproduzido em 1×1) e para a moldura. O Ajustar nao sofre: la a imagem ja e menor que a celula, e a sobra e a cor de fundo.

**Conserto minimo:** no Preencher, o tamanho redimensionado nunca e menor que o slot — `nw = max(cw, …)` e `nh = max(ch, …)`. So os casos em que o `int()` truncava abaixo do slot mudam; todo o resto sai byte a byte igual.

---

# PARTE A — registro (commit `docs`, antes do codigo)

## Edicao A1 — `meta/STATUS.md` (quatro trocas)
Pre-condicao: `sha1sum meta/STATUS.md` = `b101d537316dd57c45d90c2b708ec15a505c6acd`.

**A1a.** Na linha que comeca com `**1.9.0** — 2026-11-10 —`, trocar `Aguardando o roteiro do dono.` por `Roteiro do dono feito em 10/11: tudo certo.`
**A1b.** Trocar a linha inteira que comeca com `**Produto:** F5 em curso (escada C).` por:
~~~~
**Produto:** F5 em curso (escada C). 1.7.0 a 1.9.0 conferidas pelo dono em 10/11; dos itens do critério da fase, falta só o executável (1.10.0). Agora: **1.9.1** (wo0016, FIX-007) — linha preta de 1 px no modo Preencher.
~~~~
**A1c.** Trocar `## ✅ Funcionando *(suíte headless verde; 1.9.0 aguardando o roteiro do dono)*` por `## ✅ Funcionando *(suíte headless verde; roteiro do dono da 1.9.0 feito em 10/11, tudo certo)*`
**A1d.** No backlog, remover as duas linhas que comecam com `- [ ] **Dono:** roteiro da 1.9.0` e `- [ ] **Chat:** decidir se o achado da linha preta`; em «🔧 Em Progresso», trocar `- (vazio)` por `- 1.9.1 — FIX-007 (wo0016, Parte B).`
**Conferencia:** `grep -c "Aguardando o roteiro" meta/STATUS.md` → `0`; `grep -c "wo0016" meta/STATUS.md` → `2`.

## Commit A — e push
```
git add -- meta/STATUS.md meta/ROADMAP.md logs/2026-11-10.md meta/workorders/261110-wo0016-fix-linha-preta.md
git commit -m "docs: 1.9.0 conferida e WO do conserto da linha preta (1.9.1)"
git push
```
Conferencia: `git diff --cached --stat` → exatamente esses 4 caminhos.

---

# PARTE B — conserto (commit `fix`)

## Edicao B0 — referencia ANTES de mexer
Com o harness de folhas da wo0015 (fora do repo; recrie se nao existir), gere a referencia com a 1.9.0 **acrescentando** dois casos em Preencher: (a) o do bug — imagem 1500 × 1500, grade 1×1, papel e DPI que deem celula 1086 × 1601 px (o Code ja tem a combinacao); (b) um Preencher que NAO truncava (ex.: imagem 2000 × 1000 em celula 1000 × 500). Guarde os SHA-256.

## Edicao B1 — `imposer_core.py`, em `_place_image`
Trocar o par de linhas:
~~~~
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
~~~~
por:
~~~~
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        if cfg.fit_mode == "fill":
            # `int()` trunca: 1500 × 1601/1500 dá 1600,999… → 1600, e o `crop`
            # abaixo passaria 1 px da imagem — o Pillow pinta esse px de preto.
            # No Preencher a imagem nunca pode ficar menor que a célula. FIX-007.
            nw, nh = max(nw, cw), max(nh, ch)
~~~~
`VERSION = "1.9.1"`; docstring de `print_imposer.py`: `Novidades da 1.9.1: o modo Preencher não deixa mais uma linha preta de 1 px na borda da célula (FIX-007).`
Procure o mesmo padrao (`int(... * scale)` seguido de `crop`) no resto do nucleo e diga se ha outro lugar; **nao conserte** outro sem relatar.

## Edicao B2 — testes headless
- O caso do bug: imagem 1500 × 1500 de cor unica, Preencher, celula 1086 × 1601 → a celula composta nao tem nenhum pixel `(0, 0, 0)` (`getcolors()` → uma cor so).
- O mesmo com a celula transposta (1601 × 1086) e com rotacao manual 90°.
- Na moldura: `1 + 2` em Preencher com tamanhos que truncam → nenhum slot com linha preta.
- Ajustar e Esticar com as mesmas entradas: saida igual a de antes (compare com a referencia da B0, ou com o calculo antigo replicado no teste).

## Edicao B3 — README
Trocar `# 🖨 PrintImposer v1.9` por `# 🖨 PrintImposer v1.9.1`; `v1.9.0 · SVG: … · PDF: … ┐` por `v1.9.1 · SVG: … · PDF: … ┐` (acerte o espaco antes do `┐` se desalinhar); `*PrintImposer v1.9.0 —` por `*PrintImposer v1.9.1 —`.
**Conferencia:** `grep -c "v1.9.0" README.md` → `0`.

## Edicao B4 — validacao
1. Harness: diga `N de N iguais` **exceto** o caso (a) do bug, que tem de mudar — e diga o `getcolors()` dele antes e depois. Qualquer outro diferente = vermelho, PARE.
2. Suite verde: antes (243) e depois, e o tempo.
3. `/smoke` programatico curto: o app abre, gera uma folha em Preencher.
4. Depois do push do commit B: tag `v1.9.1` no commit B e `git push origin v1.9.1`.

## Edicao B5 — registro
- `meta/DECISIONS.md`: **inserir IMEDIATAMENTE DEPOIS** da ultima linha do arquivo (`- O desenhista vetorial da F5 desenha a geometria já generalizada, uma vez só.`) o bloco:
~~~~

---

## FIX-007 — Linha preta de 1 px no modo Preencher
**Data:** 2026-11-10 · **Versão:** 1.9.1

- **Sintoma:** no modo Preencher, com certos tamanhos de célula, saía uma linha preta de 1 px numa borda (achado do Code na wo0015, na grade 1×1 e na moldura).
- **Causa raiz:** `_place_image` redimensionava para `int(lado × escala)`; com a escala exata da célula, o produto dava 1600,999… e o `int()` truncava para 1 px a menos. O `crop` da célula passava da borda da imagem, e o Pillow preenche o que falta com preto.
- **Conserto:** no Preencher, o tamanho redimensionado nunca é menor que a célula (`max(nw, cw)`, `max(nh, ch)`). Os casos que não truncavam saem byte a byte iguais.
- **Lição:** `int()` sobre um produto em ponto flutuante que «deveria» dar inteiro trunca para baixo; quando o resultado tem de cobrir uma área, garanta o mínimo explicitamente.
~~~~
- `meta/CHANGELOG.md`: `## [1.9.1] — <data>` com **Corrigido** (linha preta no Preencher, FIX-007).
- `meta/STATUS.md`: Versao 1.9.1 (aguardando o dono conferir uma folha); Em Progresso → `(vazio)`; «Ultima conversa» ganha uma entrada. Procure `1.9.0` e `243 testes` e atualize o que for estado.
- `logs/<data de hoje>.md`: sua secao no FIM.

## Commit B — e push
```
git add -- imposer_core.py print_imposer.py tests/test_engine.py README.md meta/DECISIONS.md meta/CHANGELOG.md meta/STATUS.md logs/
git commit -m "fix: linha preta de 1 px no modo Preencher (v1.9.1)" -m "No Preencher, o tamanho redimensionado nunca e menor que a celula: o int() truncava 1 px e o crop passava da borda da imagem, que o Pillow pinta de preto (FIX-007). Ajustar e Esticar inalterados."
git push
```

---

## Fora de escopo
Qualquer outra mudanca no `_place_image` (ex.: transparencia no Preencher), interface, ROADMAP, `~/.printimposer` real do dono, `.claude/`.

## Armadilhas desta WO
- **Commit A antes do codigo; referencia (B0) antes de mexer.**
- **So o Preencher muda:** o `max` fica dentro do `if cfg.fit_mode == "fill"`; no Ajustar ele aumentaria a imagem alem da celula.
- **Patch no modulo que le o nome** (CONTEXT, armadilha 13).
- **Isolamento:** `USERPROFILE` e `HOME` temporarios (CONTEXT, armadilha 11).

## Relatorio de aplicacao
Formato `/apply-wo`, em `../AAMMDD-HHMM-code-printimposer-apply-wo0016.txt`.

---

## Roteiro do dono *(copia — o original esta na resposta do chat de 10/11)*
1. Abra pelo `printimposer.bat`, ponha uma foto com fundo claro, `Ajuste da imagem: Preencher (fill)` e gere em PNG. Certo: cabeçalho `v1.9.1`; ampliando as bordas da folha gerada, nenhuma linha preta fina na borda de nenhuma célula.
