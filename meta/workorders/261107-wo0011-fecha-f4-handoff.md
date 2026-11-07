# WO 0011 — Fecha a F4 (1.6.0 conferida pelo dono) e registra o handoff

## Cabecalho

> **Tipo:** registro puro (so documentos, ancoras exatas). **Nao muda a interface** → sem roteiro do dono.
> **Config sugerida:** Sonnet · `/effort` baixo (substituicao de arquivo + uma insercao + commit).
> **Pre-requisito:** HEAD `16dc4cb` em `main`, empurrado; tag `v1.6.0`. Arvore com as 4 mudancas do chat abaixo e mais nada.
> **Base:** roteiro do dono da 1.6.0 feito em 07/11 — «tudo certo» `[relatado pelo dono]`; `261107-0756 Roteiro de Teste.pdf` (2x2, marca dupla por espaco, sangria espelhada visivel) `[visto pelo chat]`; relatorios `261106-1856-…-apply-wo0010.txt` e `261107-0702-…-wrap-wo0010.txt` (ja arquivados em `zz_notas-arquivadas/`).
> **Arquivos que o chat gravou no disco e esta WO versiona** (`sha1sum` medido ao gravar):
> - `625347cca195bf9fc9e069800c46a5cc747f0c40  meta/ROADMAP.md`
> - `c1d39331de4bd379f01192d6f1ec2ea61718a45a  meta/CONTEXT.md`
> - `1e0121800374e70927a5bfc5b193d0bf7cec42e4  meta/GLOSSARY.md`
> - `6312855c1fb01aa9d0ff460dbac5e4fae63994f7  logs/2026-11-07.md`
> - esta WO (`meta/workorders/261107-wo0011-fecha-f4-handoff.md`) — sem hash (nao se mede a si mesma).
> **Ancora semantica:** trecho que nao bater EXATAMENTE → **PARE e reporte**. Hash divergente de arquivo do chat → **PARE e reporte** (nao «conserte»).
> **Idempotencia:** texto novo inteiro ja no arquivo e ancora ausente → PULE e diga.
> **Ancoras lidas em:** lidas pelo chat NESTE turno (07/11): `meta/STATUS.md` (arquivo inteiro, sha1 `6922adee27c7e436d02f3e8674cbb8d3ec3962b1`); `meta/IDEAS.md` (sha1 `fb56b6e1b0b0a81db2a6c12e8e71586fd229f3ed`; linhas 34–36, cabecalho da secao do Assistente e a entrada de 2026-07-22).
> **Canal dos meta neste ciclo = CODE** para STATUS e IDEAS (e a secao do Code no log, se quiser). O chat ja gravou ROADMAP, CONTEXT, GLOSSARY e a parte dele do log.
> **Proximo comando:** nenhum. Depois do push, o dono abre uma conversa nova no chat com o `../261107-HANDOFF-BRIEF.md`.

---

## 1. Por que

O dono conferiu a 1.6.0 e o criterio de conclusao da F4 esta atingido; o chat ja marcou a F4 🟢 no ROADMAP. Esta WO poe o STATUS no estado de handoff (nada em progresso; foco = planejar a F5), captura duas ideias que sairam do ciclo da wo0010 e versiona os documentos do chat. Nao ha codigo nem versao nova: **sem entrada no CHANGELOG, sem tag**.

---

## Edicao 1 — `meta/STATUS.md` · substituir o arquivo inteiro
Pre-condicao: `sha1sum meta/STATUS.md` = `6922adee27c7e436d02f3e8674cbb8d3ec3962b1`.

~~~~
# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.6.0** — 2026-11-06 — Marcas de canto na margem externa e sangria em dois modos (espelhar a borda / a arte já tem sangria), com avisos e confirmação antes de gerar; seção «Corte e sangria». Fecha a F4. Suíte verde (182 testes; 5 skips de SVG). Roteiro do dono feito em 07/11: tudo certo.

## 🎯 Foco atual
**Produto:** F1–F4 concluídas (F4 fechada em 07/11). Próxima frente: **planejar a F5** — ordem interna **ainda não decidida**; começa por análise (`meta/analises/`), não por WO.
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013). WO que muda a interface traz o roteiro do dono **no chat** e a linha `/apply-wo` em bloco cercado. Handoff de 07/11: `../261107-HANDOFF-BRIEF.md` (pasta-pai, fora do repo).

## ✅ Funcionando *(suíte headless verde; roteiro do dono da 1.6.0 feito em 07/11, tudo certo)*
- Grade livre `cols × rows` até 12×12, com atalhos e miniatura do grid.
- Lista de imagens com miniatura, quantidade, reordenação; "+ Arquivos" e "+ Pasta".
- Ajuste fit / fill / stretch + Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI 72–1200; margens e cor de fundo.
- Seção «Corte e sangria»: guia de corte `Nenhuma` / `Linhas atravessando` (sólida/tracejada/pontilhada, com espessura, traço e cor) / `Marcas de canto` (comprimento, distância e espessura em pt; 4 mm, 3 mm, 0,25 pt); sangria 0–10 mm, `Estender a borda (espelhar)` ou `A arte já tem sangria`; avisos âmbar/cinza e confirmação antes de gerar. Geometria em mm numa função pura (`sheet_geometry`).
- Guarda de qualidade (OK / atenção / perda visível) com confirmação antes de gerar.
- Saída PNG (padrão), PDF, JPEG, TIFF, WebP e AVIF, com prefixo/sufixo/contador, anti-overwrite e até dois destinos. WebP (sem perda ou com perda) e AVIF são para compartilhar e só aparecem se o Pillow grava.
- PDF sem perda por padrão (escritor próprio, DEC-014) ou JPEG; qualidade JPEG 50–100 escolhível.
- Espaçamento separado entre colunas e entre linhas; rodapé mostra a folha em px e MB bruto.
- Entrada AVIF (Pillow) e HEIC/HEIF (com `pillow-heif`, opcional; hoje ausente neste Python).
- Entrada PDF com o `pypdfium2` (instalado no Python do dono desde 04/11): cada página vira um item (`arquivo.pdf · p. 2/5`), rasterizada no tamanho da célula na orientação final; mais de 50 páginas pede confirmação; PDF ilegível/com senha é pulado com aviso; a guarda de qualidade olha as imagens embutidas na página (≥ 10% dela) e cita `(imagem interna)` no selo; PDF só de vetor fica fora.
- Entrada SVG quando há back-end capaz (`cairosvg` ou `svglib`); degrada escondendo `.svg` se não houver. Rasterizada na orientação final e com a escala do modo de ajuste (provado com stub; back-end real não ligou nesta máquina).
- Menubar `Arquivo · Opções · Ajuda` com `Ctrl+O` / `Ctrl+Shift+O` / `Ctrl+G`; painel em três zonas com accordion e `sections_open` persistido.
- Presets nomeados (submenu `Opções › Presets`, reconstruído a cada abertura) e persistência de configuração/geometria em `~/.printimposer/`; preset da 1.5 com `cut_lines` abre convertido para `cut_guide`.
- Gerador de `.bat` (ASCII puro, CRLF, sem console) pelo diálogo `Opções › Criar atalho…`, que abre na pasta-pai do projeto.
- Preview em tempo real com debounce; geração em thread com progresso, sobre cópias congeladas da configuração e da lista (mexer na tela durante a geração não mistura folhas).
- Erro ao abrir: `~/.printimposer/last_error.log` + janela de erro, mesmo via `.bat`.
- Barra inferior mostra «Também grava em: …» com o segundo destino ligado (âmbar se inexistente ou temporário).

## 🔧 Em Progresso
- (vazio)

## ❌ Quebrado / Com Problema
- (nada conhecido.)

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Chat:** planejar a F5 — análise da ordem interna (moldura de várias fotos, drag-and-drop, `.exe`, imposição vetorial do PDF, preencher N folhas, rotação por item). Nada decidido ainda.
- [ ] **Chat → dono (decidir):** aviso próprio quando a margem externa é menor que a sangria (hoje a sangria da borda externa é recortada pela margem sem aviso; o aviso âmbar só cobre o espaçamento). Ver IDEAS de 2026-11-07. Pequeno; pode entrar como 1.6.1 ou dentro da primeira versão da F5.
- [ ] **Dono (opcional):** impressão de teste raster × vetorial numa **gráfica** de ponta (em casa, 06/11, a diferença só aparece de muito perto). Se o texto raster sair mole, reabre a vetorial (gatilho da DEC-015).
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho», e agora a seção «Corte e sangria» com marcas de canto no preview.
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — mudou em 04/11 (linha do `/apply-wo` e do roteiro).
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-06** — Portão vetorial decidido **B** com duas sondas (jsPDF e Figma): N-up correto e nitidez visível, mas o arquivo vetorial não fica ≤ 1/3 do raster (0,41–4,0×). Teste de papel em casa: diferença só de muito perto. Vetorial vai para a F5 (DEC-015). Spec da etapa 4 escrita (marcas + sangria).

**2026-11-06 (Code)** — Code aplicou a wo0010: commit A de docs (`b165a32`) e a 1.6.0 (marcas de canto + sangria; `sheet_geometry` em mm). 136 → 182 testes; smoke programático 9 + 5 itens passou.

**2026-11-07** — Dono fez o roteiro da 1.6.0: tudo certo. Chat fechou a F4 no ROADMAP (🟢; F5 🟡, não planejada), acrescentou a armadilha 12 (`cut_lines` → `cut_guide`) e os termos da F4 no GLOSSARY, e gravou o brief de handoff na pasta-pai. Code aplicou a wo0011 (só documentos). Próximo: conversa nova do chat para planejar a F5.
~~~~

## Edicao 2 — `meta/IDEAS.md` · inserir duas ideias no topo da secao do Assistente
Pre-condicao: `sha1sum meta/IDEAS.md` = `fb56b6e1b0b0a81db2a6c12e8e71586fd229f3ed`.

**Ancora** (linha unica, hoje a 36): `### 2026-07-22 — Barra de progresso e status também merecem revisão`

**Inserir ANTES da ancora** (o texto abaixo, seguido de uma linha em branco):

~~~~
### 2026-11-07 — Marcas de corte nos cantos internos (entre células)
Hoje (1.6.0) as marcas de canto ficam só na margem externa, uma por ponta de cada corte — o padrão de cartões em lote. Marca no cruzamento interno ajudaria quem corta com estilete célula a célula, mas com espaçamento pequeno cairia sobre a arte vizinha; ficou fora de escopo na spec da etapa 4. Só faz sentido com espaçamento ≥ 2 × (distância + comprimento). **F5, se pedido.**

### 2026-11-07 — Aviso de sangria externa limitada pela margem
Com margem externa menor que a sangria, a sangria da borda externa é recortada pela margem **sem aviso próprio** — o aviso âmbar da 1.6.0 só cobre o espaçamento entre células (achado da sonda do Code na wo0010). Proposta: aviso âmbar «A margem externa (X mm) é menor que a sangria (Y mm): a sangria da borda vai até X mm». Pequeno; decisão pendente com o dono. **1.6.1 ou primeira versão da F5.**
~~~~

---

## Commit — e push

Antes: `git status --short` deve listar so `meta/ROADMAP.md`, `meta/CONTEXT.md`, `meta/GLOSSARY.md`, `meta/STATUS.md`, `meta/IDEAS.md`, `logs/2026-11-07.md` e `meta/workorders/261107-wo0011-fecha-f4-handoff.md`. Qualquer outro arquivo → PARE e reporte.

```
git add -- meta/ROADMAP.md meta/CONTEXT.md meta/GLOSSARY.md meta/STATUS.md meta/IDEAS.md logs/2026-11-07.md meta/workorders/261107-wo0011-fecha-f4-handoff.md
git commit -m "docs: fecha a F4 (1.6.0 conferida pelo dono) e registra o handoff" -m "ROADMAP com a F4 concluida e a F5 como proxima, ainda nao planejada. Armadilha 12 (cut_lines virou cut_guide) e termos da F4 no glossario. STATUS sem nada em progresso e duas ideias novas: marcas nos cantos internos e aviso de sangria externa limitada pela margem."
git push
```

Depois: `git status --short` vazio e `git log -1 origin/main` igual ao HEAD. Sem tag (nao ha versao nova).

---

## Fora de escopo
Codigo, README, CHANGELOG, DECISIONS, tag, `.claude/`, CEREBRO, Instrucoes, `~/.printimposer` real do dono.

## Armadilhas desta WO
- **Gravar o STATUS sem interpretar escapes** (ja houve `\f` comido num caminho Windows, wo0007). Este texto nao tem barra invertida, mas use escrita literal mesmo assim.
- **Nao reescrever os 4 arquivos do chat** — so conferir o hash e versionar.

## Relatorio de aplicacao
Formato `/apply-wo`, em `../AAMMDD-HHMM-code-printimposer-apply-wo0011.txt`: hashes conferidos (os 4 do chat + pre-condicoes), sha1 final de STATUS e IDEAS, hash do commit, saida do `git status` e do `git log -1 origin/main` depois do push. Se quiser, acrescente a secao do Code no `logs/2026-11-07.md` ANTES do commit (e diga que acrescentou).
