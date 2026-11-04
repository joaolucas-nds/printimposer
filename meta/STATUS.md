# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.4.0** — 2026-11-04 — F4 etapa 2 **feita** (wo0007): entrada PDF via `pypdfium2`, uma página por item, rasterizada na célula já na orientação final. Suíte verde (100 testes; 5 skips de SVG, ou 11 sem `pypdfium2`). **Aguardando o roteiro do dono** (WO 0007, fim). A 1.3.0 já foi conferida na tela.

## 🎯 Foco atual
**Produto:** F4 etapa 2 (1.4.0) implementada, falta o roteiro do dono. Próximo: README da 1.4 e o portão da imposição vetorial (etapa 3, ROADMAP, escada C).
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
- Entrada PDF quando o `pypdfium2` está instalado: cada página vira um item (`arquivo.pdf · p. 2/5`), rasterizada no tamanho da célula na orientação final; mais de 50 páginas pede confirmação; PDF ilegível/com senha é pulado com aviso; fora da guarda de qualidade.
- Entrada SVG quando há back-end capaz (`cairosvg` ou `svglib`); degrada escondendo `.svg` se não houver.
- Menubar `Arquivo · Opções · Ajuda` com `Ctrl+O` / `Ctrl+Shift+O` / `Ctrl+G`; painel em três zonas com accordion e `sections_open` persistido.
- Presets nomeados (submenu `Opções › Presets`, reconstruído a cada abertura) e persistência de configuração/geometria em `~/.printimposer/`.
- Gerador de `.bat` (ASCII puro, CRLF, sem console) pelo diálogo `Opções › Criar atalho…`, que abre na pasta-pai do projeto.
- Preview em tempo real com debounce; geração em thread com progresso.

## 🔧 Em Progresso
- (vazio)

## ❌ Quebrado / Com Problema
- **Suspeita, por leitura de código (não medida):** SVG com Auto-Rotate pode sair **ampliado** — é rasterizado na caixa `(cw, ch)` e só depois girado, então arte deitada numa célula em pé é desenhada pequena e esticada. Não se manifesta hoje (SVG indisponível na máquina do dono). O PDF da 1.4.0 já rasteriza na orientação final; o SVG pede um teste com stub e o mesmo conserto. Ver SPEC-F4-etapa2 §3.

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho». O README hoje não tem imagens; com os prints, o chat os encaixa.
- [ ] **Dono:** roteiro da wo0007 (instalar `pypdfium2`, abrir pelo `.bat`, PDF de várias páginas, página deitada com Auto-Rotate, PDF corrompido). Devolver «wo0007 aplicada e roteiro feito: …».
- [ ] **Chat:** README para a 1.4 (entrada PDF, o limite da guarda de qualidade com PDF que embrulha raster).
- [ ] **Chat + dono:** portão da imposição vetorial (etapa 3).
- [ ] **Dono:** apagar a pasta temporária da sonda `pypdfium2` (`rm -r` negado ao Code na wo0006). No CMD: `rmdir /s /q "%TEMP%\claude\C--Users-alexk-Tools-PrintImposer-printimposer\fe86a394-080c-4ad1-b60b-c223bc59d98a\scratchpad\pdfium"`.
- [ ] Instalar um back-end de SVG no Windows e confirmar que o cabeçalho mostra o nome certo. `cairosvg` precisa de libcairo; `svglib` precisa de `rlPyCairo` — nenhum é 100% Python puro na hora de desenhar (ver FIX-002).
- [ ] Avaliar `Image.draft()` também no caminho de composição (hoje só na miniatura).
- [ ] **Dono:** desmarcar o segundo destino de saída — está ligado apontando para uma pasta temporária do Claude Code (`AppData\Local\Temp\claude\…`), sobra de teste antigo.
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — a cópia do painel está defasada.
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-03** — Merge do KCM v1.133.0 fechado (DEC-012, DEC-013); F3 implementada pelo Code (wo0002, 1.2.0), conferida pelo dono e fechada pela wo0003 (rótulo cortado corrigido); README reescrito para a 1.2 (wo0004). Achado: no Windows `Path.home()` ignora `HOME` — teste do app isola com `USERPROFILE` (CONTEXT, armadilha 11). Próximo: ordem da F4.

**2026-11-03 (noite)** — Ordem da F4 decidida (escada C, DEC-014) e etapa 1 implementada pelo Code (wo0005, 1.3.0): PDF sem perda por escritor próprio (sonda `pypdfium2`: 0 pixels de diferença), compressão escolhível, espaçamento X/Y, folha no rodapé, AVIF/HEIC. Pendente: o dono abrir o PDF num leitor.

**2026-11-04** — Dono conferiu a 1.3.0 na tela (tudo certo, PDF sem perda abre num leitor). README atualizado para a 1.3 (wo0006). Regra nova no CEREBRO: WO que muda a interface já vai com o «Roteiro do dono». Próximo: etapa 2 da F4 (1.4.0), entrada PDF via `pypdfium2`.

**2026-11-04 (tarde)** — Etapa 2 implementada pelo Code (wo0007, 1.4.0): entrada PDF por `pypdfium2`, página = item, render na orientação final (sem ampliação). Sonda real: página paisagem em célula retrato pediu a caixa (1754, 1240) e saiu 1748×1241. Suspeita do SVG com Auto-Rotate registrada. Pendente: roteiro do dono.
