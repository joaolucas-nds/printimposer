# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.4.1** — 2026-11-04 — Robustez: erro de abertura visível (`last_error.log` + janela), aviso do segundo destino na barra inferior, configuração congelada durante a geração, guia rápido sem amarrar a uma ferramenta. Suíte verde (111 testes; 5 skips de SVG). Roteiro do dono da 1.4.1 pendente.

## 🎯 Foco atual
**Produto:** 1.5.0 (wo0009): SVG sem ampliação, guarda de qualidade dentro do PDF, saída WebP e AVIF. Em paralelo: sonda do portão da imposição vetorial (`meta/analises/261104-ANALISE-portao-vetorial.md`).
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013). WO que muda a interface traz o roteiro do dono **no chat** e a linha `/apply-wo` em bloco cercado.

## ✅ Funcionando *(suíte headless verde; roteiro do dono da 1.4.0 em 04/11; a 1.4.1 aguarda o roteiro)*
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
- Entrada PDF com o `pypdfium2` (instalado no Python do dono desde 04/11): cada página vira um item (`arquivo.pdf · p. 2/5`), rasterizada no tamanho da célula na orientação final; mais de 50 páginas pede confirmação; PDF ilegível/com senha é pulado com aviso; fora da guarda de qualidade.
- Entrada SVG quando há back-end capaz (`cairosvg` ou `svglib`); degrada escondendo `.svg` se não houver.
- Menubar `Arquivo · Opções · Ajuda` com `Ctrl+O` / `Ctrl+Shift+O` / `Ctrl+G`; painel em três zonas com accordion e `sections_open` persistido.
- Presets nomeados (submenu `Opções › Presets`, reconstruído a cada abertura) e persistência de configuração/geometria em `~/.printimposer/`.
- Gerador de `.bat` (ASCII puro, CRLF, sem console) pelo diálogo `Opções › Criar atalho…`, que abre na pasta-pai do projeto.
- Preview em tempo real com debounce; geração em thread com progresso, sobre cópias congeladas da configuração e da lista (mexer na tela durante a geração não mistura folhas).
- Erro ao abrir: `~/.printimposer/last_error.log` + janela de erro, mesmo via `.bat`.
- Barra inferior mostra «Também grava em: …» com o segundo destino ligado (âmbar se inexistente ou temporário).

## 🔧 Em Progresso
- 1.5.0 (wo0009, Parte B). Sonda do portão vetorial pedida na análise de 04/11.

## ❌ Quebrado / Com Problema
- **SVG pode sair ampliado — confirmado por leitura de código em 04/11, não medido em execução:** `open_source` passa a caixa `(cw, ch)` direto para `rasterize_svg`, que ignora o Auto-Rotate e usa sempre a menor escala (no modo Preencher o `_place_image` recorta e amplia). Não se manifesta na máquina do dono (SVG indisponível). Conserto na wo0009.

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Dono:** roteiro da 1.4.1 (no chat da wo0008).
- [ ] **Chat + dono:** portão da imposição vetorial (F4, etapa 3) — análise com sonda própria.
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho».
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — mudou de novo em 04/11 (linha do `/apply-wo` e do roteiro).
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-04** — Dono conferiu a 1.3.0 na tela (tudo certo, PDF sem perda abre num leitor). README atualizado para a 1.3 (wo0006). Regra nova no CEREBRO: WO que muda a interface já vai com o «Roteiro do dono». Próximo: etapa 2 da F4 (1.4.0), entrada PDF via `pypdfium2`.

**2026-11-04 (tarde)** — Etapa 2 implementada pelo Code (wo0007, 1.4.0): entrada PDF por `pypdfium2`, página = item, render na orientação final (sem ampliação). Sonda real: página paisagem em célula retrato pediu a caixa (1754, 1240) e saiu 1748×1241. Suspeita do SVG com Auto-Rotate registrada.

**2026-11-04 (noite)** — Roteiro da 1.4.0 feito pelo dono com PDFs reais (tudo certo). Curadoria: IDEAS (10 ideias mudaram de seção, etiquetas de fase corrigidas, «Figma» generalizado), ROADMAP (F4 por etapas, 1.4.1 intercalada), CONTEXT e README sem amarrar a uma ferramenta. Regras corrigidas no CEREBRO: roteiro do dono **no chat**; `/apply-wo` em bloco cercado. Próximo: 1.4.1 de robustez (wo0008).

**2026-11-04 (madrugada)** — Code aplicou a wo0008: commit A de docs (`29bfe23`), tags `v1.0.0`…`v1.4.0` e a 1.4.1 (erro de abertura visível, aviso do 2º destino, config congelada na geração, guia rápido). 100 → 111 testes. Próximo: roteiro do dono.
