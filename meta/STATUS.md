# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log da sessão.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.1.1** — 2026-07-19 — F2 com as correções do primeiro smoke test: app volta a abrir (FIX-003), fim da corrida de DPI (FIX-004), janela respeita a barra de tarefas (FIX-005).

## ⚠️ Pendente de re-validação (prioridade da próxima sessão)
O smoke test de 2026-07-19 rodou e **achou três bugs**, todos corrigidos via instrução ASU `260719-asu0001.yaml`. As correções foram validadas em simulação (resultado byte a byte idêntico ao arquivo testado) e por **48 testes headless verdes**, mas **a GUI ainda não foi aberta depois delas**.

Rodar de novo, na íntegra:
```
python tests\test_engine.py     (deve dar 48 OK)
python print_imposer.py          (checklist de 9 itens no CLAUDE.md)
```
No Claude Code: `/smoke`. Itens de maior risco agora:
1. **Abertura** — era o bloqueador; confirmar que o app sobe.
8. **`.bat`** — falhava só por causa do bloqueador; deve funcionar agora.
2. **Barra de ação** — o botão "Gerar Arquivos" precisa estar inteiro, acima da barra de tarefas.
Extra: **gerar com o preview em voo** (mexer numa opção e clicar Gerar na sequência) e conferir que a folha sai no DPI configurado.

**Ainda sem cobertura:** nitidez em monitor com zoom 125%/150% — o monitor do teste está a 100%. A troca para `CTkImage` deve ter resolvido o aviso do CustomTkinter, mas ninguém viu.

## ✅ Funcionando *(48 testes verdes; itens 2–7 e 9 confirmados no smoke de 19/07)*
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
- (nada conhecido) — os três bugs do smoke de 19/07 foram corrigidos na 1.1.1 (FIX-003, FIX-004, FIX-005). Aguardando o segundo smoke para confirmar.

## 📋 Backlog (curto prazo — itens acionáveis)
> Só o que dá para pegar nas próximas sessões. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] Aplicar `260719-asu0001.yaml` e rodar o segundo smoke *(bloqueia o fechamento da F2)*.
- [ ] Conferir nitidez em monitor com zoom 125%/150% — único item do checklist nunca exercitado.
- [ ] Instalar um back-end de SVG no Windows e confirmar que o cabeçalho mostra o nome certo. `cairosvg` precisa de libcairo; `svglib` precisa de `rlPyCairo` — nenhum é 100% Python puro na hora de desenhar (ver FIX-002).
- [ ] Menu de presets: os valores só recarregam ao reabrir o app; fazer o refresh na hora de salvar.
- [ ] Avaliar `Image.draft()` também no caminho de composição (hoje só na miniatura).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `print_imposer.py` — app inteiro (~1960 linhas). Antes de tocar na composição, ler CONTEXT §"Como a imposição funciona". `compose_page` **não muta mais `cfg.dpi`** — o DPI desce por parâmetro (FIX-004). Não reintroduza mutação: preview e geração compartilham o `LayoutConfig` entre threads.
- `tests/test_engine.py` — 48 testes headless; a única rede antes do smoke. Três deles inspecionam o **código-fonte** (colisão com nomes do Tkinter, contrato da área útil), porque o stub headless não consegue reproduzir esses bugs. Rodar antes de qualquer commit.
- `CLAUDE.md` / `.claude/` — contrato da raia de validação (DEC-010). O `settings.json` proíbe de propósito editar CEREBRO, Instruções e LOG-TEMPLATE.
- `meta/CEREBRO.md` — alinhado ao kit v1.73.0; customização volta a divergir dos updates, então registre em «Feedback para o Kit».

## 💬 Última Sessão
**2026-07-19 (noite)** — O primeiro smoke test rodou na raia de validação e provou seu valor: achou **um bloqueador que a suíte de 40 testes não pegava** — a 1.1.0 simplesmente não abria, por colisão de `self._w` com o pathname Tcl do Tkinter. Achou também a corrida de DPI entre preview e geração (folha saindo em 72 DPI silenciosamente) e a janela invadindo a barra de tarefas. Os três viraram FIX-003/004/005 e foram corrigidos por **instrução ASU** — a primeira do projeto —, com 8 testes de regressão novos, cada um provado por reintrodução do bug. Próximo passo óbvio: aplicar o YAML e rodar o segundo smoke.
