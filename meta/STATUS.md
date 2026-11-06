# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.6.0** — 2026-11-06 — Marcas de canto na margem externa e sangria em dois modos (espelhar a borda / a arte já tem sangria), com avisos e confirmação antes de gerar; seção «Corte e sangria». Fecha a F4. Suíte verde (182 testes; 5 skips de SVG). **Aguardando o roteiro do dono da 1.6.0.**

## 🎯 Foco atual
**Produto:** 1.6.0 entregue (wo0010); falta o roteiro do dono. Portão vetorial decidido em 06/11: **B** (vetorial vai para a F5, DEC-015).
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013). WO que muda a interface traz o roteiro do dono **no chat** e a linha `/apply-wo` em bloco cercado.

## ✅ Funcionando *(suíte headless verde; smoke programático da 1.6.0 passou; a 1.6.0 aguarda o roteiro do dono)*
- Grade livre `cols × rows` até 12×12, com atalhos e miniatura do grid.
- Lista de imagens com miniatura, quantidade, reordenação; "+ Arquivos" e "+ Pasta".
- Ajuste fit / fill / stretch + Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI 72–1200; margens e cor de fundo.
- Seção «Corte e sangria»: guia de corte `Nenhuma` / `Linhas atravessando` (sólida/tracejada/pontilhada, com espessura, traço e cor) / `Marcas de canto` (comprimento, distância e espessura em pt; 4 mm, 3 mm, 0,25 pt); sangria 0–10 mm, `Estender a borda (espelhar)` ou `A arte já tem sangria`; avisos âmbar/cinza e confirmação antes de gerar.
- Guarda de qualidade (OK / atenção / perda visível) com confirmação antes de gerar.
- Saída PNG (padrão), PDF, JPEG, TIFF, WebP e AVIF, com prefixo/sufixo/contador, anti-overwrite e até dois destinos. WebP (sem perda ou com perda) e AVIF são para compartilhar e só aparecem se o Pillow grava.
- PDF sem perda por padrão (escritor próprio, DEC-014) ou JPEG; qualidade JPEG 50–100 escolhível.
- Espaçamento separado entre colunas e entre linhas; rodapé mostra a folha em px e MB bruto.
- Entrada AVIF (Pillow) e HEIC/HEIF (com `pillow-heif`, opcional; hoje ausente neste Python).
- Entrada PDF com o `pypdfium2` (instalado no Python do dono desde 04/11): cada página vira um item (`arquivo.pdf · p. 2/5`), rasterizada no tamanho da célula na orientação final; mais de 50 páginas pede confirmação; PDF ilegível/com senha é pulado com aviso; a guarda de qualidade olha as imagens embutidas na página (≥ 10% dela) e cita `(imagem interna)` no selo; PDF só de vetor fica fora.
- Entrada SVG quando há back-end capaz (`cairosvg` ou `svglib`); degrada escondendo `.svg` se não houver. Rasterizada na orientação final e com a escala do modo de ajuste (provado com stub; back-end real não ligou nesta máquina).
- Menubar `Arquivo · Opções · Ajuda` com `Ctrl+O` / `Ctrl+Shift+O` / `Ctrl+G`; painel em três zonas com accordion e `sections_open` persistido.
- Presets nomeados (submenu `Opções › Presets`, reconstruído a cada abertura) e persistência de configuração/geometria em `~/.printimposer/`.
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
- [ ] **Chat:** marcar a F4 🟢 no ROADMAP depois do roteiro do dono da 1.6.0; planejar a F5 (moldura, drag-and-drop, `.exe`, vetorial).
- [ ] **Dono (opcional):** impressão de teste raster × vetorial numa **gráfica** de ponta (em casa, 06/11, a diferença só aparece de muito perto). Se o texto raster sair mole, reabre a vetorial (gatilho da DEC-015).
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho».
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — mudou em 04/11 (linha do `/apply-wo` e do roteiro).
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-04 (madrugada 2)** — Code aplicou a wo0009: commit A de docs (`f2ec5fe`) e a 1.5.0 (WebP/AVIF, guarda dentro do PDF, SVG na orientação final). 111 → 136 testes. Cartazes reais do dono: selo verde (razão 2,12 a 150 DPI e 1,06 a 300 DPI).

**2026-11-06** — Portão vetorial decidido **B** com duas sondas (jsPDF e Figma): N-up correto e nitidez visível, mas o arquivo vetorial não fica ≤ 1/3 do raster (0,41–4,0×). Teste de papel em casa: diferença só de muito perto. Vetorial vai para a F5 (DEC-015). Spec da etapa 4 escrita (marcas + sangria). Próximo: wo0010.

**2026-11-06 (Code)** — Code aplicou a wo0010: commit A de docs (`b165a32`) e a 1.6.0 (marcas de canto + sangria; `sheet_geometry` em mm). 136 → 182 testes; smoke programático 9 + 5 itens passou. Falta o roteiro do dono (preview, papel, preset antigo).
