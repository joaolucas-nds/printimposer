# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.3.0** — 2026-11-03 — F4 etapa 1 **feita** (wo0005): PDF sem perda, compressão, espaçamento X/Y, folha no rodapé, AVIF/HEIC. Suíte verde (85 testes, 5 skips de SVG). Conferida na tela pelo dono em 04/11, inclusive o PDF sem perda num leitor.

## 🎯 Foco atual
**Produto:** F4 etapa 1 (1.3.0) entregue. Próximo: etapa 2 (1.4.0), entrada PDF via `pypdfium2` (ROADMAP, escada C).
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013).

## ✅ Funcionando *(suíte headless verde; conferência visual do dono em 04/11)*
- Grade livre `cols × rows` até 12×12, com atalhos e miniatura do grid.
- Lista de imagens com miniatura, quantidade, reordenação; "+ Arquivos" e "+ Pasta".
- Ajuste fit / fill / stretch + Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI 72–1200; margens e cor de fundo.
- Linhas de corte sólida/tracejada/pontilhada, com espessura, traço e cor.
- Guarda de qualidade (OK / atenção / perda visível) com confirmação antes de gerar.
- Saída PNG (padrão), PDF, JPEG, TIFF, com prefixo/sufixo/contador, anti-overwrite e até dois destinos.
- PDF sem perda por padrão (escritor próprio, DEC-014) ou JPEG; qualidade JPEG 50–100 escolhível.
- Espaçamento separado entre colunas e entre linhas; rodapé mostra a folha em px e MB bruto.
- Entrada AVIF (Pillow) e HEIC/HEIF (com `pillow-heif`, opcional; hoje ausente neste Python).
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
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho». O README hoje não tem imagens; com os prints, o chat os encaixa.
- [ ] **Chat:** etapa 2 (1.4.0) — entrada PDF via `pypdfium2`.
- [ ] Instalar um back-end de SVG no Windows e confirmar que o cabeçalho mostra o nome certo. `cairosvg` precisa de libcairo; `svglib` precisa de `rlPyCairo` — nenhum é 100% Python puro na hora de desenhar (ver FIX-002).
- [ ] Avaliar `Image.draft()` também no caminho de composição (hoje só na miniatura).
- [ ] **Dono:** desmarcar o segundo destino de saída — está ligado apontando para uma pasta temporária do Claude Code (`AppData\Local\Temp\claude\…`), sobra de teste antigo.
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — a cópia do painel está defasada.
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-03** — Merge do KCM v1.133.0 fechado (DEC-012, DEC-013); F3 implementada pelo Code (wo0002, 1.2.0), conferida pelo dono e fechada pela wo0003 (rótulo cortado corrigido); README reescrito para a 1.2 (wo0004). Achado: no Windows `Path.home()` ignora `HOME` — teste do app isola com `USERPROFILE` (CONTEXT, armadilha 11). Próximo: ordem da F4.

**2026-11-03 (noite)** — Ordem da F4 decidida (escada C, DEC-014) e etapa 1 implementada pelo Code (wo0005, 1.3.0): PDF sem perda por escritor próprio (sonda `pypdfium2`: 0 pixels de diferença), compressão escolhível, espaçamento X/Y, folha no rodapé, AVIF/HEIC. Pendente: o dono abrir o PDF num leitor.

**2026-11-04** — Dono conferiu a 1.3.0 na tela (tudo certo, PDF sem perda abre num leitor). README atualizado para a 1.3 (wo0006). Regra nova no CEREBRO: WO que muda a interface já vai com o «Roteiro do dono». Próximo: etapa 2 da F4 (1.4.0), entrada PDF via `pypdfium2`.
