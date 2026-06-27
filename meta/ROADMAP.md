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

## 🟡 F2 — Praticidade e confiança *(próxima)*
**Objetivo:** reduzir o esforço repetido e dar segurança de qualidade — o coração do "esforço mínimo" do usuário, com baixo risco de arquitetura.
**Critério de conclusão:** dá para salvar um preset, recarregar, adicionar uma pasta inteira, e o app avisa quando a impressão vai sair com qualidade ruim.
- [ ] Guarda de qualidade: aviso de upscale quando a fonte < célula (IDEAS / STATUS backlog).
- [ ] Presets de configuração (.json) salvar/carregar — `LayoutConfig` já tem `to_dict`/`from_dict`.
- [ ] Adicionar pasta inteira (ordem natural de nome).
- [ ] Lembrar últimas configurações e última pasta entre execuções.
- [ ] Escolha de compressão na saída (lossless × JPEG/qualidade).
- [ ] Primeiros testes headless do engine (folhas, tamanho de página, fit/fill).

## 🔵 F3 — Qualidade profissional e UX rica *(futuro, sem data)*
**Objetivo:** aproximar a saída do padrão de gráfica e tornar a manipulação mais fluida.
**Critério de conclusão:** marcas de corte de canto + sangria disponíveis; arrastar arquivos para a janela e reordenar arrastando; caminho vetorial em avaliação/protótipo.
- Marcas de corte de canto (ticks no gutter) como alternativa às linhas atravessadas (DEC-005).
- Sangria (bleed) configurável em mm.
- Drag-and-drop de arquivos (tkinterdnd2 + wrapper).
- Reordenar a lista arrastando; rotação manual por imagem.
- Preenchimento automático para N folhas.
- **Entrada vetorial (PDF) → imposição vetorial** (pypdf/reportlab): maior salto de qualidade e arquivos minúsculos; pode exigir modularizar (revisitar DEC-003).

## 🔵 F4 — Distribuição e alcance *(futuro, sem data)*
**Objetivo:** facilitar adoção por quem não tem Python e por outros idiomas.
**Critério de conclusão:** executável Windows distribuível; base pronta para i18n.
- Empacotar como .exe (PyInstaller, com hook do tkinterdnd2).
- Internacionalização (i18n) — interface em inglês além do PT-BR.
- Layout customizado não-uniforme (ex.: moldura 2+1 de 3 fotos) — exige planejamento de UI próprio.

---

## 🚫 Itens descartados desta visão
- **SVG como formato de saída** — sem ganho com arte raster; qualidade vetorial vem da entrada PDF (F3). (Entrada SVG segue como ideia ativa.)
- **Software de prepress completo** (separação de cores, trapping, registro multi-plate, booklet) — fora do escopo do produto (ver CONTEXT §"O que o projeto NÃO é").
