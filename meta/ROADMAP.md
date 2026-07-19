# ROADMAP.md — Plano Intencional de Evolução

> **Opcional.** Use quando o projeto tem um plano em fases — não para tarefas soltas (isso é o Backlog do STATUS) nem para brainstorm (isso é o IDEAS).
> Cada fase tem um objetivo e um critério de conclusão. Marque o estado: 🟢 concluída · 🟡 em curso/próxima · 🔵 futura · 🚫 descartada.
> Médio e longo prazo vivem AQUI, não no STATUS.

---

## 🟢 F1 — Núcleo funcional (v1.0) *(concluída)*
**Objetivo:** transformar "arrastar arquivo por arquivo no Windows" em "selecionar imagens → escolher N-up → gerar folha pronta".
**Critério de conclusão:** gerar PDF/PNG multipágina com N-up, margens, linhas de corte e preview, rodando no Windows.
- Engine de imposição raster (DEC-001) separado da GUI (DEC-004).
- UI em CustomTkinter (DEC-002), arquivo único (DEC-003).
- Saída PDF/PNG/JPEG/TIFF (DEC-006); linhas de corte atravessando a folha (DEC-005).
- Correção do crash PanedWindow×CTkScrollableFrame (FIX-001).

## 🟢 F2 — Controle, persistência e janela *(concluída na 1.1.0)*
**Objetivo:** acabar com a reconfiguração repetida e com a necessidade de editar o código para mudar layout.
**Critério de conclusão:** ✅ atingido no código, ⏳ **pendente de smoke test da GUI** (ver STATUS).
- ✅ Grade livre `cols × rows` até 12×12 (DEC-009) — resolve o 2×6 e qualquer outro.
- ✅ Presets nomeados (.json) com a configuração inteira; miniatura do grid.
- ✅ Persistência de config e geometria em `~/.printimposer/settings.json`.
- ✅ Pastas de entrada e saída independentes; padrão em Downloads; segundo destino.
- ✅ PNG como formato padrão.
- ✅ Janela centralizada com clamp, DPI awareness no Windows, sashes posicionados.
- ✅ Gerador de `.bat`; botão "+ Pasta"; guarda de qualidade.
- ✅ Carregamento: `Image.draft()` em JPEG + cache de miniatura (só a parte segura).
- ✅ Suíte headless com 40 testes.
- ⏳ Smoke test da GUI — único item aberto da fase.

## 🟡 F3 — Qualidade profissional *(próxima)*
**Objetivo:** aproximar a saída do padrão de gráfica e acabar com a perda de qualidade na origem.
**Critério de conclusão:** PDF entra como fonte vetorial; marcas de canto e sangria disponíveis; compressão escolhível.
- ✅ ~~Entrada SVG~~ — antecipada e entregue na 1.1.0.
- Entrada PDF (mesma família do SVG; é o que o Figma exporta em vetor).
- Formatos extras de baixo custo: HEIC/AVIF via `pillow-heif`.
- Marcas de corte de canto (ticks no gutter) como alternativa às linhas atravessadas (DEC-005).
- Sangria (bleed) configurável em mm.
- Escolha de compressão na saída (lossless × JPEG com qualidade).
- Margem por eixo (X/Y independentes) e folga por encolhimento.
- Barra de estado com px, MB estimados e selo de qualidade.
- **Imposição vetorial de ponta a ponta** (pypdf/reportlab): qualidade perfeita e arquivos minúsculos; pode exigir modularizar (revisitar DEC-003).

## 🔵 F4 — Distribuição, fluidez e layouts livres *(futuro, sem data)*
**Objetivo:** facilitar adoção por quem não tem Python e soltar as amarras do grid regular.
**Critério de conclusão:** executável Windows distribuível; manipulação por arraste; layout não-uniforme possível.
- Empacotar como .exe (PyInstaller, com hook do `tkinterdnd2`).
- Drag-and-drop de arquivos na janela; reordenar a lista arrastando.
- Rotação manual por imagem; preenchimento automático para N folhas.
- Layout não-uniforme (moldura 2+1 de 3 fotos) — exige modelo de células de tamanhos diferentes.
- Internacionalização (i18n).
- Imprimir direto, sem salvar arquivo (API de impressão do Windows).

---

## 🚫 Itens descartados desta visão
- **SVG como formato de saída** — sem ganho com arte raster; qualidade vetorial vem da entrada (F3). (Entrada SVG segue ativa.)
- **Raia de desenvolvimento no Claude Code como modo padrão** — ver DEC-007; gatilho de reabertura registrado lá.
- **Software de prepress completo** (separação de cores, trapping, registro multi-plate, booklet) — fora do escopo (ver CONTEXT §"O que o projeto NÃO é").
