# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.2.0** — 2026-11-03 — F3 **concluída**: implementada na wo0002, conferida na tela pelo dono em 03/11. Suíte verde (63 testes, 5 skips de SVG).

## 🎯 Foco atual
**Produto:** F3 fechada. Próximo: atualizar o README (documenta a 1.0) e escolher a ordem interna da F4 — Qualidade profissional (ROADMAP).
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013).

## ✅ Funcionando *(suíte headless verde; conferência visual do dono em 03/11)*
- Grade livre `cols × rows` até 12×12, com atalhos e miniatura do grid.
- Lista de imagens com miniatura, quantidade, reordenação; "+ Arquivos" e "+ Pasta".
- Ajuste fit / fill / stretch + Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI 72–1200; margens e cor de fundo.
- Linhas de corte sólida/tracejada/pontilhada, com espessura, traço e cor.
- Guarda de qualidade (OK / atenção / perda visível) com confirmação antes de gerar.
- Saída PNG (padrão), PDF, JPEG, TIFF, com prefixo/sufixo/contador, anti-overwrite e até dois destinos.
- Entrada SVG quando há back-end capaz (`cairosvg` ou `svglib`); degrada escondendo `.svg` se não houver.
- Menubar `Arquivo · Opções · Ajuda` com `Ctrl+O` / `Ctrl+Shift+O` / `Ctrl+G`; painel em três zonas com accordion e `sections_open` persistido.
- Presets nomeados (submenu `Opções › Presets`, reconstruído a cada abertura) e persistência de configuração/geometria em `~/.printimposer/`.
- Gerador de `.bat` (ASCII puro, CRLF, sem console) pelo diálogo `Opções › Criar atalho…`, que abre na pasta-pai do projeto.
- Preview em tempo real com debounce; geração em thread com progresso.

## 🔧 Em Progresso
- (vazio)

## ❌ Quebrado / Com Problema
- (nada conhecido.)

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Chat:** atualizar o README para a 1.2 (ainda documenta a 1.0: lista fixa de N-up, PDF padrão, saída na Área de Trabalho). Prints sugeridos: a janela inteira, o menu `Opções`, o diálogo «Criar atalho».
- [ ] **Chat + dono:** escolher a ordem interna da F4.
- [ ] Instalar um back-end de SVG no Windows e confirmar que o cabeçalho mostra o nome certo. `cairosvg` precisa de libcairo; `svglib` precisa de `rlPyCairo` — nenhum é 100% Python puro na hora de desenhar (ver FIX-002).
- [ ] Avaliar `Image.draft()` também no caminho de composição (hoje só na miniatura).
- [ ] **Dono:** desmarcar o segundo destino de saída — está ligado apontando para uma pasta temporária do Claude Code (`AppData\Local\Temp\claude\…`), sobra de teste antigo.
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — a cópia do painel está defasada.
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-03** — Merge do KCM v1.133.0 fechado (DEC-012, DEC-013); F3 implementada pelo Code (wo0002, 1.2.0), conferida pelo dono e fechada pela wo0003 (rótulo cortado corrigido). Próximo: README e ordem da F4.
