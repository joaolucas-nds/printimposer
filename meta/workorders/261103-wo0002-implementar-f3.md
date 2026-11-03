# WO 0002 — Fecha o merge (DEC-013) e implementa a F3 conforme a SPEC-F3-UI (v1.2.0)

## Cabecalho

> **Tipo:** mista — Parte A: WO de DOC (registro, ancoras exatas). Parte B: WO de CODIGO que **delega a implementacao** a partir da spec (sem texto exato de codigo).
> **Config sugerida:** Opus · `/effort` alto (Parte B e reescrita de UI com componente novo e mudanca de persistencia). A Parte A sozinha seria Sonnet medio.
> **Pre-requisito:** HEAD `67e62bb` em `main`, empurrado. Suite verde (48 testes, 5 skips de SVG). Arvore com SO os arquivos que o chat gravou neste turno (lista abaixo).
> **Base:** wo0001 aplicada (relatorio `../261103-1243-code-printimposer-apply-wo0001.txt`); DEC-012; `meta/specs/SPEC-F3-UI.md` revisada em 2026-11-03 (§5, §6, §10, §11, §12).
> **Arquivos que o chat gravou no disco e esta WO versiona** (`sha1sum` medido ao gravar):
> - `5526f0452bb3bcc71038d89d9558add40585c427  .claude/settings.json`
> - `6cf3cbf66802514bab34005b45afeff9c012551d  meta/CEREBRO.md`
> - `3e1b79a3a0e3d6d3a795b1dac0c50165c0a63a76  meta/GLOSSARY.md`
> - `241ceac42b4230cd8c8b25a614a691b5045c6887  meta/specs/SPEC-F3-UI.md`
> - `6f9f74707e1c15386d2b6c9a3ff77490fe7c60d9  logs/2026-11-03.md`
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte**.
> **Idempotencia:** antes de cada edicao da Parte A, procure o texto NOVO INTEIRO; ja la e a ancora nao → PULE e diga.
> **Ancoras lidas em:** lidas pelo chat NESTE turno: `meta/DECISIONS.md` (ultima linha, consequencia da DEC-012 que termina em «o chat revisa a spec antes da WO da F3.»), `meta/HISTORY.md` (linha 4 do cabecalho, «Não é lido no início da sessão; ...»), `meta/IDEAS.md` (entrada «2026-11-03 — Instruções do painel × arquivo do repo divergiram em silêncio.»), `meta/ROADMAP.md` (linha «**Spec:** `meta/SPEC-F3-UI.md` (aprovada em 22/07). **Fundamento:** HISTORY §9.»). Parte B: `print_imposer.py` lido so em `_make_bat` (`initial = str(Path.home() / "Desktop") ...`) e `VERSION  = "1.1.1"`; o resto da implementacao e leitura SUA.
> **Canal dos meta neste ciclo = CODE** para DECISIONS, HISTORY, IDEAS, ROADMAP, STATUS e CHANGELOG. O chat ja gravou CEREBRO, GLOSSARY, a spec, o `settings.json` e a parte dele do log.
> **Proximo comando:** nenhum.

---

## 1. Por que

A wo0001 fechou o merge do kit, mas deixou duas licoes que viram desvio registrado (DEC-013): a skill `/apply-wo` so nascia dentro da propria WO (o dono teve de copiar a pasta de skills a mao) e o `settings.json` tinha regras `Write(...)` no deny que o Claude Code rejeita. O chat ja corrigiu o `settings.json` direto no disco. Com isso o merge fecha, e a frente de produto e a F3: spec aprovada, agora revisada para a DEC-012 e para o destino do `.bat` que o dono pediu.

---

# PARTE A — fechar o merge (commit `docs`)

## Edicao 0 — conferencias

1. `sha1sum` de cada arquivo da lista do cabecalho → todos iguais. Diferente → PARE.
2. Abra o Claude Code e confira que os avisos «Deny rule Write(...) never matches» **nao** aparecem mais.
3. `python tests/test_engine.py` → verde.

- **Nao responde:** se o `settings.json` concede o que a Parte B precisa — isso aparece se algum comando pedir aprovacao; diga quais pediram.

## Edicao A1 — `meta/DECISIONS.md` · DEC-013

**Inserir IMEDIATAMENTE DEPOIS** da ultima linha do arquivo (linha inteira):
~~~~
- A F3 (`meta/specs/SPEC-F3-UI.md`) passa a ser implementada pelo Code. O §12 da spec («entrega em arquivo inteiro») e a última consequência da DEC-011 («conforme DEC-007») ficam superados por esta decisão; o chat revisa a spec antes da WO da F3.
~~~~
**o bloco:**
~~~~

---

## DEC-013 — Nesta máquina o chat grava `.claude/` direto; skill nasce antes da WO que a usa
**Data:** 2026-11-03 · **Status:** aceita · *(desvio registrado do kit v1.133)*

### Contexto
O kit manda o chat entregar o `settings.json` na pasta-pai para o dono copiar («a ponte do chat não grava em `.claude/`») e manda skill mudar por WO. Na wo0001 isso gerou dois atritos: a WO pedia `/apply-wo` e só criava a skill dentro dela — o dono teve de copiar a pasta de skills à mão para o Code conseguir começar [relatado pelo dono] —, e o `settings.json` entregue trazia regras `Write(...)` no deny que o Claude Code rejeita («never matches · use Edit»). No mesmo dia o chat corrigiu o `settings.json` gravando direto: a ponte desta máquina grava em `.claude/` [medido pelo chat].

### Decisão
O chat grava `.claude/settings.json` e `.claude/skills/*` direto no lugar definitivo; a WO só os versiona, com `sha1sum` no cabeçalho. Skill que dirige a aplicação de uma WO existe no disco ANTES de a WO ser entregue. Deny de arquivo usa só `Edit(...)`, que já cobre a escrita.

### Alternativas consideradas
- **Seguir o kit (pasta-pai + cópia pelo dono)** — passo manual sem necessidade nesta máquina; foi o que travou a wo0001.
- **O Code edita `.claude/`** — o classificador bloqueia autoconcessão de permissão, e com razão.

### Consequências
- A barreira de autoconcessão continua: quem grava a permissão é o chat, quem a usa é o Code.
- Se a ponte deixar de gravar em `.claude/` (outra máquina, outra versão do app), volta a regra do kit. O caso está em «Técnicas específicas» do CEREBRO.
~~~~

**Conferencia:** `grep -c "^## DEC-013 " meta/DECISIONS.md` → `1`.

## Edicao A2 — `meta/HISTORY.md` · cabecalho

**Trocar** a linha inteira:
~~~~
> Não é lido no início da sessão; o assistente consulta sob demanda quando o assunto aparece.
~~~~
**por:**
~~~~
> Não é lido ao abrir a conversa; o assistente consulta sob demanda quando o assunto aparece.
~~~~

## Edicao A3 — `meta/IDEAS.md` · feedback ao kit

**Inserir IMEDIATAMENTE DEPOIS** da linha inteira:
~~~~
- **2026-11-03 — Instruções do painel × arquivo do repo divergiram em silêncio.** O painel do Projeto ficou com a versão genérica enquanto o arquivo do repo evoluía (ASU, nome de download). A regra «a fonte é o arquivo do repositório» só chegou na v1.133; antes dela não havia quem notasse.
~~~~
**o bloco:**
~~~~
- **2026-11-03 — A WO de migração para skills dependia da skill que ela criava.** O pacote v1.133 manda migrar `.claude/commands/` → `.claude/skills/` por WO, e a WO se aplica com `/apply-wo` — que é uma das skills a criar. Projeto vindo de `commands/` trava no primeiro passo. Sugestão: o `_UPDATE-PROMPT` mandar instalar as skills do pacote ANTES de qualquer WO (fora da WO), e a regra «a ponte do chat não grava em `.claude/`» virar «confira se grava» — nesta máquina grava (DEC-013).
~~~~

## Edicao A4 — `meta/ROADMAP.md` · caminho da spec

**Trocar:**
~~~~
**Spec:** `meta/SPEC-F3-UI.md` (aprovada em 22/07). **Fundamento:** HISTORY §9.
~~~~
**por:**
~~~~
**Spec:** `meta/specs/SPEC-F3-UI.md` (aprovada em 22/07, revisada em 03/11). **Implementação:** Claude Code, `wo0002`. **Fundamento:** HISTORY §9.
~~~~

## Commit A — e push

```
git add -- .claude/settings.json meta/CEREBRO.md meta/GLOSSARY.md meta/specs/SPEC-F3-UI.md meta/workorders/261103-wo0002-implementar-f3.md logs/2026-11-03.md meta/DECISIONS.md meta/HISTORY.md meta/IDEAS.md meta/ROADMAP.md
git commit -m "docs: fecha merge do KCM (DEC-013) e revisa spec da F3"
git push
```
**Conferencia antes do commit:** `git diff --cached --stat` → exatamente esses 10 caminhos. `git status --short` depois → vazio.

---

# PARTE B — implementar a F3 (commit `feat`)

## Edicao B1 — implementar `meta/specs/SPEC-F3-UI.md`

Leia a spec INTEIRA antes de escrever codigo. Implemente §4 a §10 em `print_imposer.py`:
- topbar com menubar `Arquivo · Opções · Ajuda` (§5), via `CTkButton` + `tk.Menu.tk_popup()` ancorado em `winfo_rootx/rooty`;
- diálogo «Criar atalho» (§6) com `initialdir` na **pasta-pai da raiz do projeto** (`Path(__file__).resolve().parent.parent`, reserva `Path.home()`);
- guia rápido (§7) lendo de **uma constante única** no módulo;
- `CollapsibleSection` (§8): fechar com `grid_remove()`, `row=` fixo por seção, cabeçalho focável por `Tab` e acionável por `Espaço`/`Enter`, **nenhum atributo com nome reservado do Tkinter** (prefixo próprio);
- `ConfigPanel` reestruturado nas três zonas (§4), zona inferior com altura ≤ 84 px;
- `sections_open` no `settings.json` (§9), compatível com arquivo da 1.1.x;
- presets como submenu reconstruído a cada abertura (§10) — o bug «menu de presets não atualiza» tem de morrer aqui;
- `VERSION = "1.2.0"`.

**Limites:** fora do escopo da §13 da spec, e nada no `ImpositionEngine`. Decisão de arquitetura que a spec não cobre → **PARE e relate** (spec §12). Detalhe de codigo e seu.

## Edicao B2 — testes headless (spec §11)

Acrescente em `tests/test_engine.py`:
1. contrato de `sections_open`: round-trip; arquivo sem a chave → padrão (só `saida` aberta); chave desconhecida → ignorada;
2. presença dos itens de menu esperados (os rótulos da §5, inclusive `Criar atalho…`);
3. o `initialdir` do atalho aponta para a pasta-pai da raiz (checagem pelo código-fonte, se o stub não permitir chamar o diálogo — como os testes AST que já existem).

A `TkAttributeCollisionTests` existente tem de continuar verde com a classe nova.

## Edicao B3 — validacao

1. `python tests/test_engine.py` → verde. Diga quantos testes antes (48) e depois.
2. `/smoke` — os 9 itens do `CLAUDE.md` **e** os 5 itens novos da spec §11. O que só o olho humano confirma (nitidez em 125%/150%, aparência do tema dos menus) sai marcado «confirmar com o dono», nunca PASSOU por inferência.

- **Quem roda:** você. **Chega no ramo:** suíte verde + smoke sem FALHOU → Edicao B4; qualquer FALHOU → vermelho (sem commit B, menu de opções). **Nao responde:** a nitidez em zoom — este monitor está a 100%.

## Edicao B4 — registro

- `meta/CHANGELOG.md`: nova entrada `## [1.2.0] — <data de hoje>` no topo (abaixo de `[Não lançado]`), com Adicionado / Modificado / Corrigido (o bug dos presets) / Removido (seções `.bat` e Presets do painel).
- `meta/STATUS.md`: Versão Atual 1.2.0; F3 implementada aguardando a conferência visual do dono; sai o bug dos presets de «Quebrado»; Backlog sem o item «implementar a F3»; «Última conversa» atualizada. Procure o valor antigo (`1.1.1`) no arquivo inteiro.
- `meta/IDEAS.md`: na ideia «### 2026-07-23 — `.bat` gerado na pasta-pai do projeto...», acrescente no fim do parágrafo: `**Implementada na 1.2.0.**`
- `meta/ROADMAP.md`: F3 continua 🟡 — só vira 🟢 depois da conferência visual do dono.
- `logs/2026-11-03.md`: sua seção no FIM (`## Conversa 1 — Code (aplicacao da wo0002)`).

## Commit B — e push

```
git add -- print_imposer.py tests/test_engine.py meta/CHANGELOG.md meta/STATUS.md meta/IDEAS.md logs/2026-11-03.md
git commit -m "feat(ui): fase F3 - menubar, accordion e zonas fixas (v1.2.0)" -m "Painel em tres zonas com CollapsibleSection e sections_open persistido; menubar Arquivo/Opcoes/Ajuda; dialogo do atalho .bat sugere a pasta-pai do projeto; presets em submenu dinamico. SPEC-F3-UI."
git push
```

---

## Fora de escopo

`ImpositionEngine`, README (depois da conferência do dono), `meta/CONTEXT.md`, `meta/GLOSSARY.md`, `meta/CEREBRO.md`, Instruções, `.claude/`.

## Armadilhas desta WO

- **Commit A antes de qualquer linha de código.** Os docs do merge não podem sair no commit `feat`.
- **Nome reservado do Tkinter** em widget novo (`_w`, `_name`, `master`, `tk`, `children`) quebra o app sem a suíte ver (FIX-003). Prefixe tudo.
- **Não mutar `cfg` no engine** (FIX-004) — a F3 não toca o engine; se parecer precisar, é arquitetura: PARE.
- **Geometria pela área útil** (FIX-005): a zona fixa inferior não pode empurrar «Gerar arquivos» para baixo da barra de tarefas em 1366×768 (smoke 4).
- **`grid_remove()`, não `destroy()`**, ao fechar seção — senão os campos perdem estado.

## Relatorio de aplicacao

Formato da skill `/apply-wo`; gravar em `../AAMMDD-HHMM-code-printimposer-apply-wo0002.txt`. Se só a Parte A fechar verde, empurre o commit A e relate a Parte B como vermelha, com o menu.
