# WO 0017 — fechamento da sessao: 1.9.1 conferida, projeto em stand by, handoff

## Cabecalho

> **Tipo:** so documentos (ancoras exatas). Nao toca o produto: sem build, sem teste; a rede e o `git diff`.
> **Config sugerida:** Sonnet · `/effort` baixo. Rode numa sessao limpa (`/clear` antes).
> **Pre-requisito:** HEAD `8a08da3` em `main`, empurrado; tag `v1.9.1`. Arvore com 5 arquivos modificados pelo chat (os do bloco abaixo) — nada mais.
> **Base:** relatorio `261110-2128-code-printimposer-apply-wo0016.txt` (verde; arquivado em `../zz_notas-arquivadas/`); o dono conferiu uma folha em Preencher na 1.9.1 em 10/11 («sem linha preta») e decidiu pausar o projeto `[relatado pelo dono]`.
> **Arquivos que o chat gravou no disco e esta WO versiona** (`sha1sum` medido ao gravar):
> - `c392d3873d3940154e722d6c96b3ef6c9e4e1b64  meta/ROADMAP.md`
> - `a98dda82277092366198f4e6c78cc10bf1c8d7c3  meta/CONTEXT.md`
> - `03e011c3e30deca3bc6bd7d993c7ae0c535a3973  meta/GLOSSARY.md`
> - `c41c038c9070eb342cc7a1a212ef107a22fda7ba  meta/CEREBRO.md`
> - `c831d014e29f308f764030465c4e11260a3ff69a  logs/2026-11-10.md`
> **Ancora semantica:** trecho que nao bater EXATAMENTE → **PARE e reporte**.
> **Idempotencia:** texto novo inteiro ja no arquivo e ancora ausente → PULE e diga.
> **Ancoras lidas em:** lidas pelo chat NESTE turno: `meta/STATUS.md` (sha1 `a6f1dcc5cda8437bf262625f429019aff2f04d5e`; linhas 10, 12, 15, 46, 52–60); `meta/IDEAS.md` (sha1 `061a54b9f9cfd0722438dbc96277e00176ca1582`; linhas 34–37).
> **Canal dos meta neste ciclo = CODE** para STATUS e IDEAS. O `meta/CEREBRO.md` foi editado pelo chat (o `settings.json` proibe o Code de edita-lo; aqui o Code so o VERSIONA).
> **Proximo comando:** nenhum.

---

## Edicao 0 — conferencia
`sha1sum` dos 5 arquivos acima = os do cabecalho; `sha1sum meta/STATUS.md meta/IDEAS.md` = os das «Ancoras lidas em». `git status --short` → so os 5 ` M` do bloco (mais esta WO, `??`). Diferente → PARE.

## Edicao 1 — `meta/STATUS.md` (cinco trocas)
**1a.** Trocar a linha inteira que comeca com `**1.9.1** — 2026-11-10 — Conserto da linha preta` por:
~~~~
**1.9.1** — 2026-11-10 — Conserto da linha preta de 1 px no modo Preencher (FIX-007, wo0016). Suíte verde (248 testes; 5 skips de SVG). O dono conferiu uma folha em 10/11: sem linha preta.
~~~~
**1b.** Remover a linha inteira que comeca com `**1.9.0** — 2026-11-10 — Moldura por divisões sucessivas` e a linha em branco depois dela (a 1.9.0 esta no CHANGELOG; «Versão Atual» guarda so a atual).
**1c.** Trocar a linha inteira que comeca com `**Produto:** F5 em curso (escada C).` por:
~~~~
**Produto:** ⏸ **Em stand by desde 10/11** (férias do dono). Estável na **1.9.1**: F1–F4 concluídas; da F5 estão feitas a 1.7.0 (arrastar), a 1.8.0 (tiragem), a 1.8.1 (dois módulos), a 1.9.0 (moldura) e a 1.9.1 (FIX-007), todas conferidas pelo dono. Restam, para a volta: **1.10.0** (executável + GitHub Releases — último item do critério da fase) e a **vetorial** (fora do critério; pode ir para a F6). Brief de retomada: `../261110-HANDOFF-BRIEF.md` (pasta-pai).
~~~~
**1d.** Trocar a linha inteira `- [ ] **Chat:** depois do roteiro da 1.9.0, a frente seguinte da F5: 1.10.0 (executável + GitHub Releases); antes, confirmar com o dono se o repositório é público.` por:
~~~~
- [ ] **Chat (na volta):** 1.10.0 — executável (PyInstaller `--onedir`) + GitHub Releases por GitHub Actions. Antes da spec, perguntar ao dono se o repositório `joaolucas-nds/printimposer` é público (só assim qualquer pessoa baixa sem login) e se quer adiantar as Releases das tags antigas (`v1.0.0` … `v1.9.1`) só com as notas.
~~~~
**1e.** Em «💬 Última conversa», remover os dois paragrafos que comecam com `**2026-11-10 (Code)** — wo0014 aplicada` e `**2026-11-10 (20h)** — Dono abriu a 1.8.1` (cada um com a linha em branco depois), e acrescentar no FIM do arquivo:
~~~~

**2026-11-10 (21h30)** — Dono conferiu a 1.9.1 (sem linha preta) e pôs o projeto em stand by. Chat fechou a sessão: ROADMAP (1.9.1 ✅, F5 em pausa), CONTEXT (armadilha 14), GLOSSARY (harness de folhas), CEREBRO (uma sessão limpa do Code por WO), IDEAS (duas ideias) e o brief de handoff na pasta-pai.
~~~~
**Conferencia:** `grep -c "aguardando o dono conferir" meta/STATUS.md` → `0`; `grep -c "stand by" meta/STATUS.md` → `2`; `grep -c "^\*\*1.9.0\*\*" meta/STATUS.md` → `0`.

## Edicao 2 — `meta/IDEAS.md`
**Inserir IMEDIATAMENTE DEPOIS** da linha `## 🤖 Ideias Ativas — Assistente` e da linha em branco que a segue (isto e: antes de `### 2026-11-07 — Marcas de corte nos cantos internos (entre células)`):
~~~~
### 2026-11-10 — Versionar o harness de folhas (SHA-256)
As WOs 0014, 0015 e 0016 provaram «saída idêntica» com um script que gera folhas fixas e compara SHA-256 — e o script foi **refeito do zero a cada WO**, porque morava numa pasta temporária (relatórios da wo0015 e da wo0016: «o harness não existia»). Cada refazer é um conjunto diferente de casos (48, 48 com outra composição, 159). Proposta: guardar o gerador no repo (ex.: `tests/sheet_harness.py`), sem guardar os hashes (mudam com a versão do Pillow): o uso é rodar antes e depois na mesma máquina. Pequeno; candidato a entrar junto da próxima WO de código.

### 2026-11-10 — Suspeita: transparência perdida no modo Preencher
**Deduzido do código, não medido.** No `_place_image`, o Ajustar cola a imagem com a máscara alfa, mas o Preencher cola `img.convert("RGB")` sem máscara — numa PNG com fundo transparente, a área transparente sairia com a cor guardada no pixel (muitas vezes preto) em vez da cor de fundo. Conferir com uma PNG transparente em Preencher antes de tratar como bug; se confirmar, vira FIX com o mesmo padrão do FIX-007.

~~~~
**Conferencia:** `grep -c "^### " meta/IDEAS.md` → o numero de antes + 2 (diga os dois); `grep -c "Versionar o harness" meta/IDEAS.md` → `1`.

## Commit — e push
```
git add -- meta/STATUS.md meta/IDEAS.md meta/ROADMAP.md meta/CONTEXT.md meta/GLOSSARY.md meta/CEREBRO.md logs/2026-11-10.md meta/workorders/261110-wo0017-stand-by-handoff.md
git commit -m "docs: 1.9.1 conferida, projeto em stand by e handoff da sessao"
git push
```
Conferencia: `git diff --cached --stat` → exatamente esses 8 caminhos; depois do push, `git status --short` vazio e `git rev-parse HEAD` = `git rev-parse origin/main`.

---

## Fora de escopo
Codigo, testes, README, CHANGELOG (nada foi entregue nesta WO), DECISIONS (sem decisao nova: a pausa e de calendario, nao de arquitetura), tag (nao ha versao nova), `.claude/`.

## Relatorio de aplicacao
Formato `/apply-wo`, em `../AAMMDD-HHMM-code-printimposer-apply-wo0017.txt`. Na volta, o chat le este relatorio primeiro.
