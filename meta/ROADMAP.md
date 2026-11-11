# ROADMAP.md — Plano Intencional de Evolução

> **Opcional.** Use quando o projeto tem um plano em fases — não para tarefas soltas (isso é o Backlog do STATUS) nem para brainstorm (isso é o IDEAS).
> Cada fase tem um objetivo e um critério de conclusão. Marque o estado: 🟢 concluída · 🟡 em curso/próxima · 🔵 futura · 🚫 descartada.
> Médio e longo prazo vivem AQUI, não no STATUS.

---

## 🟢 F1 — Núcleo funcional (v1.0) *(concluída)*
**Objetivo:** transformar "arrastar arquivo por arquivo no Windows" em "selecionar imagens → escolher N-up → gerar folha pronta".
**Critério de conclusão:** gerar PDF/PNG multipágina com N-up, margens, linhas de corte e preview, rodando no Windows.
- Engine de imposição raster (DEC-001) separado da GUI (DEC-004).
- UI em CustomTkinter (DEC-002), arquivo único (DEC-003).
- Saída PDF/PNG/JPEG/TIFF (DEC-006); linhas de corte atravessando a folha (DEC-005).
- Correção do crash PanedWindow×CTkScrollableFrame (FIX-001).

## 🟢 F2 — Controle, persistência e janela *(concluída na 1.1.1)*
**Objetivo:** acabar com a reconfiguração repetida e com a necessidade de editar o código para mudar layout.
**Critério de conclusão:** ✅ atingido. O 1º smoke achou três bugs (FIX-003/004/005); corrigidos, o 2º smoke passou em 2026-07-22.
- ✅ Grade livre `cols × rows` até 12×12 (DEC-009) — resolve o 2×6 e qualquer outro.
- ✅ Presets nomeados (.json) com a configuração inteira; miniatura do grid.
- ✅ Persistência de config e geometria em `~/.printimposer/settings.json`.
- ✅ Pastas de entrada e saída independentes; padrão em Downloads; segundo destino.
- ✅ PNG como formato padrão.
- ✅ Janela centralizada com clamp, DPI awareness no Windows, sashes posicionados.
- ✅ Gerador de `.bat`; botão "+ Pasta"; guarda de qualidade.
- ✅ Carregamento: `Image.draft()` em JPEG + cache de miniatura (só a parte segura).
- ✅ Suíte headless com 40 testes.
- ✅ 1º smoke: itens 2–7 e 9 passaram; 1 e 8 falharam pelo bloqueador.
- ✅ 2º smoke (22/07): app abre, `.bat` funciona, interface aprovada pelo usuário.
- ⏳ Nitidez em zoom 125%/150% — segue sem exercitar (monitor a 100%). Movida para a F3.

## 🟢 F3 — Interface e descoberta *(concluída na 1.2.0)*
**Objetivo:** acabar com a rolagem para configurar, e tirar do painel o que é ação em vez de configuração.
**Critério de conclusão:** em 1366×768, configurar um trabalho comum sem rolar; contador e guarda de qualidade sempre visíveis; `.bat`, presets, sobre e guia acessíveis por menubar.
**Spec:** `meta/specs/SPEC-F3-UI.md` (aprovada em 22/07, revisada em 03/11). **Implementação:** Claude Code, `wo0002`. **Fundamento:** HISTORY §9.
- ✅ `CollapsibleSection` — accordion multi-aberto, com `grid_remove()` e cabeçalho focável.
- ✅ Zona fixa superior: Grade + mini-grid (fora do accordion).
- ✅ Zona fixa inferior: contador de folhas, guarda de qualidade e tamanho da célula.
- ✅ Menubar `Arquivo · Opções · Ajuda` na topbar, com atalhos de teclado.
- ✅ Diálogo "Criar atalho" que explica antes de gerar (substitui a seção `.bat`).
- ✅ Presets migram para `Opções › Presets ▸` — mata o bug do menu que não atualizava.
- ✅ Guia rápido "Figma → impressão" em Ajuda *(rótulo generalizado para qualquer ferramenta na 1.4.1)*.
- ✅ `sections_open` no `settings.json`, com padrão para arquivo antigo.
- ⏳ Nitidez em zoom 125%/150% — segue sem exercitar (monitor a 100%). Movida para a F4.
- ✅ Conferência visual do dono (03/11): menus, accordion, atalhos de teclado, presets sem reiniciar, atalho na pasta-pai — tudo certo.

## 🟢 F4 — Qualidade profissional *(concluída na 1.6.0 — 07/11)*
**Objetivo:** aproximar a saída do padrão de gráfica e acabar com a perda de qualidade na origem.
**Critério de conclusão:** PDF entra como fonte vetorial; marcas de canto e sangria disponíveis; compressão escolhível.
**Ordem (escada C — `meta/analises/261103-ANALISE-ordem-f4.md`, aprovada em 03/11):**
- ✅ **Etapa 1 — 1.3.0** (`meta/specs/261103-SPEC-F4-etapa1.md`, conferida pelo dono em 04/11): PDF sem perda por padrão (DEC-014) e compressão escolhível; espaçamento X/Y; folha em px e MB bruto no rodapé (cobre a antiga «barra de estado com o custo da folha»); AVIF nativo e HEIC opcional.
- ✅ **Etapa 2 — 1.4.0** (`meta/specs/261104-SPEC-F4-etapa2.md`, roteiro do dono em 04/11: tudo certo): entrada PDF via `pypdfium2` opcional, uma página por item, rasterizada na orientação final.
- ✅ **Intercalada — 1.4.1, robustez** (pedido do dono em 04/11; roteiro feito em 04/11: tudo certo): erro de abertura gravado e mostrado mesmo via `.bat`; aviso visível do segundo destino; configuração congelada durante a geração; guia rápido sem amarrar a uma ferramenta.
- ✅ **Intercalada — 1.5.0** (escolha do dono em 04/11): SVG sem ampliação com Auto-Rotate e Preencher; guarda de qualidade olhando as imagens dentro do PDF; saída WebP e AVIF para compartilhar. Roteiro do dono em 04/11: tudo certo. Em paralelo, as sondas do portão (`meta/analises/261104-ANALISE-portao-vetorial.md`).
- ✅ **Etapa 3 — portão (decidido em 06/11): opção B** — imposição vetorial vai para a **F5**. Critério 3 (arquivo ≤ 1/3 do raster) falhou nas duas fontes reais do dono (jsPDF: 0,41–3,9×; Figma: 0,57–4,0×); o ganho medido é nitidez do texto, não tamanho. Gatilho de reabertura: impressão de teste mostrar o texto do raster mole no papel. `meta/analises/261104-ANALISE-portao-vetorial.md`.
- ✅ **Etapa 4 — 1.6.0** (`meta/specs/261106-SPEC-F4-etapa4.md`, roteiro do dono em 07/11: tudo certo): marcas de corte de canto (ticks no gutter, alternativa às linhas atravessadas, DEC-005) + sangria em mm. A geometria (corte, sangria, segmentos de marca) nasce separada do desenho, porque PNG/JPEG/TIFF/WebP seguem raster qualquer que seja o portão.
- ✅ **Critério de conclusão atingido (07/11):** PDF entra como fonte (1.4.0, rasterizado na célula; a imposição vetorial foi para a F5 pela DEC-015); marcas de canto e sangria (1.6.0); compressão escolhível (1.3.0).
- ✅ ~~Entrada SVG~~ — antecipada e entregue na 1.1.0.
- ⏳ Nitidez em zoom 125%/150% — conferir quando houver monitor ou escala para testar (herdada da F3).

## 🟡 F5 — Distribuição, fluidez e layouts livres *(em pausa desde 10/11, por decisão do dono — projeto estável na 1.9.1; restam 1.10.0 e a vetorial)*
**Objetivo:** facilitar adoção por quem não tem Python e soltar as amarras do grid regular.
**Critério de conclusão:** executável Windows distribuível; manipulação por arraste; layout não-uniforme possível.
**Ordem (escada C — `meta/analises/261109-ANALISE-ordem-f5.md`, aprovada em 10/11; o `.exe` foi para depois da moldura porque hoje só o dono usa o app):**
- ✅ **1.7.0 — Arrastar** (`meta/specs/261110-SPEC-F5-arrastar.md`, wo0012; roteiro do dono em 10/11: tudo certo, inclusive o soltar do Explorer sobre o preview): soltar arquivos e pastas na janela (`tkinterdnd2` opcional, DEC-016); reordenar a lista arrastando pela alça; aviso âmbar de sangria externa limitada pela margem.
- ✅ **1.8.0 — Tiragem** (`meta/specs/261110-SPEC-F5-tiragem.md`, wo0013; roteiro do dono em 10/11: tudo certo): rotação manual por imagem (0° segue o Auto-Rotate; 90/180/270° são exatos); preencher folhas (completar a última; exatamente N folhas), mexendo nas quantidades à vista.
- ✅ **Portão da moldura** (`meta/analises/261110-ANALISE-portao-moldura.md`, decidido em 10/11): modelo de **divisões sucessivas** (DEC-018) — cortável na guilhotina, grade = caso particular, catálogo inicial `1 + 2`, `2 + 1`, `1 + 3`, `Destaque + 4`, `1 + 2 + 1` com um controle de proporção por modelo; o arquivo único se divide (DEC-017).
- ✅ **1.8.1 — Reorganização** (`meta/specs/261110-SPEC-F5-reorganizacao.md`, wo0014; 24 de 24 folhas com SHA-256 idêntico à 1.8.0; o dono abriu em 10/11: tudo igual): `imposer_core.py` (sem Tk) + `print_imposer.py` (GUI e `main()`), sem mudar comportamento — conferida por hash idêntico das folhas.
- ✅ **1.9.0 — Moldura** (`meta/specs/261110-SPEC-F5-moldura.md`, wo0015; grade idêntica à 1.8.1 em 48 de 48 SHA-256; roteiro do dono em 10/11: tudo certo): layout não-uniforme (moldura 2+1 de 3 fotos, e outras). Caso de uso do dono (04/11): um fotógrafo monta, em segundos, várias molduras diferentes com uma série de fotos. Generaliza `sheet_geometry` de grade para lista de retângulos.
- ✅ **1.9.1 — Conserto da linha preta no modo Preencher** (wo0016, FIX-007): achado do Code na wo0015, vale também para a grade. 150 de 159 casos do harness iguais; os 9 que mudaram tinham preto antes e não têm depois; o dono conferiu uma folha em 10/11: sem linha preta.
- 🔵 **1.10.0 — Executável e publicação:** PyInstaller `--onedir` (o CustomTkinter não empacota em arquivo único), com o hook do `tkinterdnd2`; publicado no **GitHub Releases** por GitHub Actions a cada tag — zip versionado, soma SHA-256 e notas tiradas do CHANGELOG. Sem assinatura de código, o Windows mostra o aviso do SmartScreen na primeira execução.
- 🔵 **Imposição vetorial do PDF** (vinda do portão da F4, DEC-015): modo «Vetorial» na compressão do PDF via `pypdf`, como segundo desenhista sobre a geometria já generalizada pela moldura. Ganho medido: nitidez do texto; tamanho ≈ igual ao raster. **Fora do critério:** se o gatilho (texto raster mole em gráfica) não disparar, passa à F6 sem reabrir nada; se disparar, sobe para logo depois da etapa em curso.
- Cauda, sem versão: internacionalização (i18n); imprimir direto, sem salvar arquivo (API de impressão do Windows); marcas nos cantos internos (se pedido); nitidez em zoom 125%/150%.

---

## 🚫 Itens descartados desta visão
- **SVG como formato de saída** — sem ganho com arte raster; qualidade vetorial vem da entrada (PDF na 1.4.0). (Entrada SVG segue ativa.)
- **Raia de desenvolvimento no Claude Code como modo padrão** — ver DEC-007 e DEC-010 (virou raia de validação). **Revertido em 2026-11-03 (DEC-012):** o Claude Code passou a implementar o código.
- **Tabs para as configurações** — descartadas na análise da F3: 6 seções com rótulos longos passam do limite prático de 3–5 abas, e as duas mais usadas cairiam em abas diferentes. Ver SPEC-F3-UI §2.
- **Software de prepress completo** (separação de cores, trapping, registro multi-plate, booklet) — fora do escopo (ver CONTEXT §"O que o projeto NÃO é").
