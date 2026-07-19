# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log da sessão.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.1.0** — 2026-07-19 — Fase F2 completa: grade livre, persistência, presets, guarda de qualidade, entrada SVG, segundo destino, gerador de `.bat` e janela corrigida.

## ⚠️ Pendente de validação (prioridade da próxima sessão)
A 1.1.0 foi entregue com **40 testes headless verdes**, mas o chat **não executa a GUI** — nenhuma mudança de interface foi vista rodando. Antes de considerar a F2 encerrada, rodar o smoke test:

```
python tests/test_engine.py     (deve dar 40 OK)
python print_imposer.py         (checklist de 9 itens no CLAUDE.md)
```
No Claude Code: `/smoke`. Itens de maior risco, por serem os que só aparecem com janela aberta:
abertura centralizada, nitidez em monitor com zoom, largura das três divisórias, e o botão
"Aplicar valores digitados" da grade.

## ✅ Funcionando *(verde na suíte headless; interface pendente de smoke)*
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
- (vazio) — F2 entregue; aguardando o smoke test para fechar.

## ❌ Quebrado / Com Problema
- (nada conhecido) — os dois problemas do STATUS anterior foram resolvidos na 1.1.0: a janela agora centraliza com clamp + DPI awareness, e a grade livre eliminou a necessidade de editar o código para criar layout.

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nas próximas sessões. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] Rodar o smoke test da GUI e registrar o resultado *(bloqueia o fechamento da F2)*.
- [ ] Instalar um back-end de SVG no Windows e confirmar que o cabeçalho mostra o nome certo. `cairosvg` precisa de libcairo; `svglib` precisa de `rlPyCairo` — nenhum é 100% Python puro na hora de desenhar (ver FIX-002).
- [ ] Menu de presets: os valores só recarregam ao reabrir o app; fazer o refresh na hora de salvar.
- [ ] Avaliar `Image.draft()` também no caminho de composição (hoje só na miniatura).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `print_imposer.py` — app inteiro (~1930 linhas). Antes de tocar na composição, ler CONTEXT §"Como a imposição funciona". `compose_page` troca `cfg.dpi` temporariamente e restaura em `finally`: não remover.
- `tests/test_engine.py` — 40 testes headless; a única rede antes do smoke. Rodar antes de qualquer commit.
- `CLAUDE.md` / `.claude/` — contrato da raia de validação (DEC-010). O `settings.json` proíbe de propósito editar CEREBRO, Instruções e LOG-TEMPLATE.
- `meta/CEREBRO.md` — alinhado ao kit v1.73.0; customização volta a divergir dos updates, então registre em «Feedback para o Kit».

## 💬 Última Sessão
**2026-07-19** — Implementada a F2 inteira (v1.1.0) e criada a suíte headless de 40 testes, que capturou dois bugs antes da entrega (FIX-002: detecção de SVG por import não prova capacidade de render; e referência de módulo perdida no probe). Montados `CLAUDE.md` e `.claude/` com os comandos `/smoke` e `/wrap`, formalizando o Claude Code como raia de validação (DEC-010) — o gatilho previsto na DEC-007 disparou porque a F2 é majoritariamente de interface. Próximo passo óbvio: rodar `/smoke` no Claude Code e fechar a F2.
