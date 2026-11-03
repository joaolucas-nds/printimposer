# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log da sessão.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.1.1** — 2026-07-22 — F2 **concluída**. Segundo smoke passou: app abre, `.bat` funciona, interface aprovada. Fecha FIX-003, FIX-004 e FIX-005.

## 🎯 Foco atual
**F3 — Interface e descoberta.** Spec aprovada em `meta/SPEC-F3-UI.md`; implementação ainda não começou.
A instrução `260722-asu0003.yaml` já foi aplicada e verificada (VERSION 1.1.1, docstrings realinhadas). A conversa foi transferida em 2026-07-22 por peso; retomar pelo `260722-HANDOFF-BRIEF.md`.

## ✅ Funcionando *(48 testes verdes; smoke completo de 22/07)*
- Grade livre `cols × rows` até 12×12, com atalhos e miniatura do grid.
- Lista de imagens com miniatura, quantidade, reordenação; "+ Arquivos" e "+ Pasta".
- Ajuste fit / fill / stretch + Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI 72–1200; margens e cor de fundo.
- Linhas de corte sólida/tracejada/pontilhada, com espessura, traço e cor.
- Guarda de qualidade (OK / atenção / perda visível) com confirmação antes de gerar.
- Saída PNG (padrão), PDF, JPEG, TIFF, com prefixo/sufixo/contador, anti-overwrite e até dois destinos.
- Entrada SVG quando há back-end capaz (`cairosvg` ou `svglib`); degrada escondendo `.svg` se não houver.
- Presets nomeados e persistência de configuração/geometria em `~/.printimposer/`.
- Gerador de `.bat` (ASCII puro, CRLF, sem console).
- Preview em tempo real com debounce; geração em thread com progresso.

## 🔧 Em Progresso
- (vazio) — F2 entregue; aguardando o smoke test para fechar.

## ❌ Quebrado / Com Problema
- **Menu de presets não atualiza sem reiniciar** — um preset recém-salvo só aparece na lista depois de reabrir o app. O `configure(values=...)` é feito por varredura frágil da árvore de widgets. **Morre na F3**, quando presets viram submenu reconstruído a cada abertura.

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nas próximas sessões. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **(1º na próxima conversa)** Tratar o update do KCM v1.101.0, se o usuário o subir — comparar e reportar, não aplicar.
- [ ] Implementar a F3 conforme `meta/SPEC-F3-UI.md`.
- [ ] Conferir nitidez em monitor com zoom 125%/150% — segue sem exercitar (monitor a 100%).
- [ ] Atualizar o README: ainda documenta a 1.0 (lista fixa de N-up, PDF padrão, saída na Área de Trabalho).
- [ ] Instalar um back-end de SVG no Windows e confirmar que o cabeçalho mostra o nome certo. `cairosvg` precisa de libcairo; `svglib` precisa de `rlPyCairo` — nenhum é 100% Python puro na hora de desenhar (ver FIX-002).
- [ ] Menu de presets: os valores só recarregam ao reabrir o app; fazer o refresh na hora de salvar.
- [ ] Avaliar `Image.draft()` também no caminho de composição (hoje só na miniatura).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `print_imposer.py` — app inteiro (~1960 linhas). Antes de tocar na composição, ler CONTEXT §"Como a imposição funciona". `compose_page` **não muta mais `cfg.dpi`** — o DPI desce por parâmetro (FIX-004). Não reintroduza mutação: preview e geração compartilham o `LayoutConfig` entre threads.
- `tests/test_engine.py` — 48 testes headless; a única rede antes do smoke. Três deles inspecionam o **código-fonte** (colisão com nomes do Tkinter, contrato da área útil), porque o stub headless não consegue reproduzir esses bugs. Rodar antes de qualquer commit.
- `CLAUDE.md` / `.claude/` — contrato da raia de validação (DEC-010). O `settings.json` proíbe de propósito editar CEREBRO, Instruções e LOG-TEMPLATE.
- `meta/CEREBRO.md` — alinhado ao kit v1.73.0; customização volta a divergir dos updates, então registre em «Feedback para o Kit».

## 💬 Última Sessão

**2026-07-22 (fim)** — F2 fechada e spec da F3 aprovada. Confirmado que o `260722-asu0003.yaml` aplicou certo (VERSION 1.1.1, 0 docstrings desalinhadas; 48 testes verdes na estrutura real `printimposer/tests/`). Conversa transferida por peso — a próxima arranca do `260722-HANDOFF-BRIEF.md`, e deve começar pelo update do KCM (CEREBRO em v1.73.0, KCM real em v1.101.0). Próximo passo de código: implementar a F3 (`meta/SPEC-F3-UI.md`), em arquivo inteiro.

