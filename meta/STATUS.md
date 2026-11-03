# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.1.1** — 2026-07-22 — F2 **concluída**. Smoke de 22/07 passou: app abre, `.bat` funciona, interface aprovada. Fecha FIX-003, FIX-004 e FIX-005.

## 🎯 Foco atual
**Produto:** F3 — Interface e descoberta. Spec aprovada em `meta/specs/SPEC-F3-UI.md`; implementação não começou. Passa a ser do Claude Code, por WO (DEC-012).
**Processo:** KCM em v1.133.0 desde 2026-11-03 — chat planeja com a pasta vinculada, Code implementa e empurra no verde; ASU aposentado.

## ✅ Funcionando *(suíte headless verde; smoke completo de 22/07)*
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
- (vazio)

## ❌ Quebrado / Com Problema
- **Menu de presets não atualiza sem reiniciar** — um preset recém-salvo só aparece na lista depois de reabrir o app. O `configure(values=...)` é feito por varredura frágil da árvore de widgets. **Morre na F3**, quando presets viram submenu reconstruído a cada abertura.

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Chat:** revisar a SPEC-F3 antes da WO — §12 (entrega) muda com a DEC-012; §6 recebe o destino do `.bat` pedido na nota de 2026-07-23: «o .bat é para ser gerado em uma pasta "anterior" a pasta raíz do projeto, entende? E não na área de trabalho».
- [ ] **Code:** implementar a F3, pela WO que o chat escrever.
- [ ] Conferir nitidez em monitor com zoom 125%/150% — segue sem exercitar (monitor a 100%). Entra no smoke da F3.
- [ ] Atualizar o README: ainda documenta a 1.0 (lista fixa de N-up, PDF padrão, saída na Área de Trabalho). Depois de a F3 fechar no smoke.
- [ ] Instalar um back-end de SVG no Windows e confirmar que o cabeçalho mostra o nome certo. `cairosvg` precisa de libcairo; `svglib` precisa de `rlPyCairo` — nenhum é 100% Python puro na hora de desenhar (ver FIX-002).
- [ ] Avaliar `Image.draft()` também no caminho de composição (hoje só na miniatura).
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — a cópia do painel está defasada.
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-03** — Merge do template-update KCM v1.133.0 (o CEREBRO vinha da v1.73.0). CEREBRO adotado inteiro (o vivo não tinha refino local), Instruções fundidas, `commands/` → `skills/`, `settings.json` com push e pasta-pai, DEC-012 (Code implementa; ASU aposentado). Próximo: o chat revisa a SPEC-F3 (§6 e §12) e escreve a WO da F3.
