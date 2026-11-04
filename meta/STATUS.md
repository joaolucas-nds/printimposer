# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.4.0** — 2026-11-04 — F4 etapa 2 **concluída**: entrada PDF via `pypdfium2`, uma página por item, rasterizada na orientação final. Roteiro do dono feito em 04/11 (tudo certo, com os PDFs reais de cartazes). Suíte verde (100 testes; 5 skips de SVG, ou 11 sem `pypdfium2`).

## 🎯 Foco atual
**Produto:** 1.4.1 de robustez (wo0008) — erro de abertura visível, aviso do segundo destino, configuração congelada durante a geração, guia rápido sem amarrar a uma ferramenta. Depois: portão da imposição vetorial (F4, etapa 3).
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013). WO que muda a interface traz o roteiro do dono **no chat** e a linha `/apply-wo` em bloco cercado.

## ✅ Funcionando *(suíte headless verde; roteiro do dono da 1.4.0 em 04/11)*
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
- Preview em tempo real com debounce; geração em thread com progresso.

## 🔧 Em Progresso
- 1.4.1 de robustez (wo0008, Parte B).

## ❌ Quebrado / Com Problema
- **Suspeita, por leitura de código (não medida):** SVG com Auto-Rotate pode sair **ampliado** — é rasterizado na caixa `(cw, ch)` e só depois girado, então arte deitada numa célula em pé é desenhada pequena e esticada. Não se manifesta hoje (SVG indisponível na máquina do dono). O PDF da 1.4.0 já rasteriza na orientação final; o SVG pede um teste com stub e o mesmo conserto. Ver SPEC-F4-etapa2 §3.

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Chat + dono:** portão da imposição vetorial (F4, etapa 3) — análise com sonda própria.
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho».
- [ ] **Dono:** apagar as duas pastas temporárias das sondas `pypdfium2` (o classificador nega `rm -r` ao Code). No CMD, um comando de cada vez: `rmdir /s /q "%TEMP%\claude\C--Users-alexk-Tools-PrintImposer-printimposer\fe86a394-080c-4ad1-b60b-c223bc59d98a\scratchpad\pdfium"` e `rmdir /s /q "%TEMP%\claude\C--Users-alexk-Tools-PrintImposer-printimposer\610902cd-2ed1-4042-b35e-173e9707e5c6\scratchpad\pdfium"`.
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — mudou de novo em 04/11 (linha do `/apply-wo` e do roteiro).
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-04** — Dono conferiu a 1.3.0 na tela (tudo certo, PDF sem perda abre num leitor). README atualizado para a 1.3 (wo0006). Regra nova no CEREBRO: WO que muda a interface já vai com o «Roteiro do dono». Próximo: etapa 2 da F4 (1.4.0), entrada PDF via `pypdfium2`.

**2026-11-04 (tarde)** — Etapa 2 implementada pelo Code (wo0007, 1.4.0): entrada PDF por `pypdfium2`, página = item, render na orientação final (sem ampliação). Sonda real: página paisagem em célula retrato pediu a caixa (1754, 1240) e saiu 1748×1241. Suspeita do SVG com Auto-Rotate registrada.

**2026-11-04 (noite)** — Roteiro da 1.4.0 feito pelo dono com PDFs reais (tudo certo). Curadoria: IDEAS (10 ideias mudaram de seção, etiquetas de fase corrigidas, «Figma» generalizado), ROADMAP (F4 por etapas, 1.4.1 intercalada), CONTEXT e README sem amarrar a uma ferramenta. Regras corrigidas no CEREBRO: roteiro do dono **no chat**; `/apply-wo` em bloco cercado. Próximo: 1.4.1 de robustez (wo0008).
