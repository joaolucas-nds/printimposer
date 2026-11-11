# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.9.1** — 2026-11-10 — Conserto da linha preta de 1 px no modo Preencher (FIX-007, wo0016). Suíte verde (248 testes; 5 skips de SVG). O dono conferiu uma folha em 10/11: sem linha preta.

## 🎯 Foco atual
**Produto:** ⏸ **Em stand by desde 10/11** (férias do dono). Estável na **1.9.1**: F1–F4 concluídas; da F5 estão feitas a 1.7.0 (arrastar), a 1.8.0 (tiragem), a 1.8.1 (dois módulos), a 1.9.0 (moldura) e a 1.9.1 (FIX-007), todas conferidas pelo dono. Restam, para a volta: **1.10.0** (executável + GitHub Releases — último item do critério da fase) e a **vetorial** (fora do critério; pode ir para a F6). Brief de retomada: `../261110-HANDOFF-BRIEF.md` (pasta-pai).
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013). WO que muda a interface traz o roteiro do dono **no chat** e a linha `/apply-wo` em bloco cercado.

## ✅ Funcionando *(suíte headless verde; roteiro do dono da 1.9.0 feito em 10/11, tudo certo)*
- Layout: grade livre `cols × rows` até 12×12 (atalhos e miniatura) ou moldura (`1 + 2`, `2 + 1`, `1 + 3`, `Destaque + 4`, `1 + 2 + 1`) com proporção ajustável, DEC-018.
- Lista de imagens com miniatura, quantidade, reordenação por ▲ ▼ ou arrastando pela alça `≡`; rotação por item com `⟳`; `Preencher ▾` (completar a última folha ou exatamente N folhas); "+ Arquivos" e "+ Pasta", ou soltar arquivos e pastas em qualquer ponto da janela (com `tkinterdnd2`; sem ele o cabeçalho diz `Arrastar: indisponível`).
- Ajuste fit / fill / stretch + Auto-Rotate; rotação manual por item (0° segue o Auto-Rotate; 90/180/270° exatos).
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI 72–1200; margens e cor de fundo.
- Seção «Corte e sangria»: guia de corte `Nenhuma` / `Linhas atravessando` (sólida/tracejada/pontilhada, com espessura, traço e cor) / `Marcas de canto` (comprimento, distância e espessura em pt; 4 mm, 3 mm, 0,25 pt); sangria 0–10 mm, `Estender a borda (espelhar)` ou `A arte já tem sangria`; avisos âmbar/cinza (inclusive margem externa menor que a sangria) e confirmação antes de gerar. Geometria em mm numa função pura (`sheet_geometry`).
- Guarda de qualidade (OK / atenção / perda visível) com confirmação antes de gerar.
- Saída PNG (padrão), PDF, JPEG, TIFF, WebP e AVIF, com prefixo/sufixo/contador, anti-overwrite e até dois destinos. WebP (sem perda ou com perda) e AVIF são para compartilhar e só aparecem se o Pillow grava.
- PDF sem perda por padrão (escritor próprio, DEC-014) ou JPEG; qualidade JPEG 50–100 escolhível.
- Espaçamento separado entre colunas e entre linhas; rodapé mostra a folha em px e MB bruto.
- Entrada AVIF (Pillow) e HEIC/HEIF (com `pillow-heif`, opcional; hoje ausente neste Python).
- Entrada PDF com o `pypdfium2` (instalado no Python do dono desde 04/11): cada página vira um item (`arquivo.pdf · p. 2/5`), rasterizada no tamanho da célula na orientação final; mais de 50 páginas pede confirmação; PDF ilegível/com senha é pulado com aviso; a guarda de qualidade olha as imagens embutidas na página (≥ 10% dela) e cita `(imagem interna)` no selo; PDF só de vetor fica fora.
- Entrada SVG quando há back-end capaz (`cairosvg` ou `svglib`); degrada escondendo `.svg` se não houver. Rasterizada na orientação final e com a escala do modo de ajuste (provado com stub; back-end real não ligou nesta máquina).
- Menubar `Arquivo · Opções · Ajuda` com `Ctrl+O` / `Ctrl+Shift+O` / `Ctrl+G`; painel em três zonas com accordion e `sections_open` persistido.
- Presets nomeados (submenu `Opções › Presets`, reconstruído a cada abertura) e persistência de configuração/geometria em `~/.printimposer/`; preset da 1.5 com `cut_lines` abre convertido para `cut_guide`.
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
- [ ] **Chat (na volta):** 1.10.0 — executável (PyInstaller `--onedir`) + GitHub Releases por GitHub Actions. Antes da spec, perguntar ao dono se o repositório `joaolucas-nds/printimposer` é público (só assim qualquer pessoa baixa sem login) e se quer adiantar as Releases das tags antigas (`v1.0.0` … `v1.9.1`) só com as notas.
- [ ] **Dono (opcional):** impressão de teste raster × vetorial numa **gráfica** de ponta (em casa, 06/11, a diferença só aparece de muito perto). Se o texto raster sair mole, reabre a vetorial (gatilho da DEC-015).
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho», e a seção «Corte e sangria» com marcas de canto no preview (as capturas de 07/11 na pasta-pai servem).
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — mudou em 04/11 (linha do `/apply-wo` e do roteiro).
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-10 (Code)** — wo0015 aplicada: Parte A (docs, `af7bb8b`) e Parte B (1.9.0, moldura). Grade idêntica por SHA-256 (48 de 48), 221 → 243 testes. Achado fora da WO: no modo `fill`, `_place_image` pode deixar 1 linha preta (herança da grade; ver o log). Falta o dono rodar o roteiro.

**2026-11-10 (Code)** — wo0016 aplicada: Parte A (docs, `79148ea`) e Parte B (1.9.1, FIX-007). No Preencher o tamanho redimensionado nunca é menor que a célula; 150 de 159 casos do harness iguais, os 9 diferentes eram todos com preto antes e sem preto depois. 243 → 248 testes.

**2026-11-10 (21h30)** — Dono conferiu a 1.9.1 (sem linha preta) e pôs o projeto em stand by. Chat fechou a sessão: ROADMAP (1.9.1 ✅, F5 em pausa), CONTEXT (armadilha 14), GLOSSARY (harness de folhas), CEREBRO (uma sessão limpa do Code por WO), IDEAS (duas ideias) e o brief de handoff na pasta-pai.
