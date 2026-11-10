# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log do dia.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.6.0** — 2026-11-06 — Marcas de canto na margem externa e sangria em dois modos (espelhar a borda / a arte já tem sangria), com avisos e confirmação antes de gerar; seção «Corte e sangria». Fecha a F4. Suíte verde (182 testes; 5 skips de SVG). Roteiro do dono feito em 07/11: tudo certo.

## 🎯 Foco atual
**Produto:** F5 em curso — ordem decidida em 10/11 (escada C, `meta/analises/261109-ANALISE-ordem-f5.md`). Agora: **1.7.0 — arrastar** (wo0012): soltar arquivos e pastas na janela, reordenar a lista arrastando, aviso de sangria externa.
**Processo:** KCM v1.133.0 — chat planeja com a pasta vinculada, Code implementa e empurra no verde (DEC-012, DEC-013). WO que muda a interface traz o roteiro do dono **no chat** e a linha `/apply-wo` em bloco cercado.

## ✅ Funcionando *(suíte headless verde; roteiro do dono da 1.6.0 feito em 07/11, tudo certo)*
- Grade livre `cols × rows` até 12×12, com atalhos e miniatura do grid.
- Lista de imagens com miniatura, quantidade, reordenação; "+ Arquivos" e "+ Pasta".
- Ajuste fit / fill / stretch + Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI 72–1200; margens e cor de fundo.
- Seção «Corte e sangria»: guia de corte `Nenhuma` / `Linhas atravessando` (sólida/tracejada/pontilhada, com espessura, traço e cor) / `Marcas de canto` (comprimento, distância e espessura em pt; 4 mm, 3 mm, 0,25 pt); sangria 0–10 mm, `Estender a borda (espelhar)` ou `A arte já tem sangria`; avisos âmbar/cinza e confirmação antes de gerar. Geometria em mm numa função pura (`sheet_geometry`).
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
- 1.7.0 — arrastar (wo0012, Parte B).

## ❌ Quebrado / Com Problema
- (nada conhecido.)

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nos próximos turnos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] **Chat:** depois do roteiro da 1.7.0, spec da 1.8.0 (rotação por item + preencher N folhas) e, em paralelo, a análise do portão da moldura.
- [ ] **Dono (opcional):** impressão de teste raster × vetorial numa **gráfica** de ponta (em casa, 06/11, a diferença só aparece de muito perto). Se o texto raster sair mole, reabre a vetorial (gatilho da DEC-015).
- [ ] **Dono (opcional):** prints para o README — a janela inteira com imagens carregadas, o menu `Opções` aberto, o diálogo «Criar atalho», e a seção «Corte e sangria» com marcas de canto no preview (as capturas de 07/11 na pasta-pai servem).
- [ ] **Dono:** colar o `INSTRUCOES-DO-PROJETO.md` do repo no painel do Projeto — mudou em 04/11 (linha do `/apply-wo` e do roteiro).
- [ ] **Dono:** limpar `.claude/settings.local.json` (≈20 permissões avulsas dos testes de julho; agora ignorado pelo git).

## 💬 Última conversa

**2026-11-07** — Dono fez o roteiro da 1.6.0: tudo certo. Chat fechou a F4 no ROADMAP, acrescentou a armadilha 12 e os termos da F4 no GLOSSARY, e gravou o brief de handoff. Code aplicou a wo0011 (só documentos).

**2026-11-09/10** — Análise da ordem da F5 (escada C) e medição `probe-f5`: `tkinterdnd2` 0.7.0 carrega com a raiz CTk (tkDnD 2.10.3). Dono aprovou a escada; o `.exe` foi para depois da moldura (hoje só ele usa) e vai sair publicado no GitHub Releases. Spec e wo0012 da 1.7.0 escritas.
