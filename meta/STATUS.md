# STATUS.md — Estado Atual

> Arquivo **rolante**: descreve só o AGORA. O assistente lê no início para saber onde retomar.
> Item resolvido SAI daqui — vai para o CHANGELOG (se foi entrega) e/ou para o log da sessão.
> Médio e longo prazo NÃO ficam aqui — ficam no ROADMAP.

---

## Versão Atual
**1.0.0** — 2026-06-02 — Primeira versão funcional: imposição N-up de imagens em folhas, com preview, linhas de corte e saída multi-formato.

## ✅ Funcionando
- Seleção em massa de imagens (PNG, JPG, JPEG, TIFF, BMP, WebP).
- Lista com miniatura, nome, quantidade por imagem (+/−) e reordenação por botões ↑↓.
- Layouts N-up: 1×1, 2×1, 1×2, 2×2, 3×2, 2×3, 4×2, 2×4, 3×3, 4×3, 4×4.
- Ajuste por slot: fit / fill / stretch + Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom; DPI configurável (72–1200).
- Margem externa e entre imagens (mm), cor de fundo.
- Linhas de corte: sólida/tracejada/pontilhada, espessura, comprimento de traço, cor.
- Saída PDF (multipágina), PNG, JPEG, TIFF, com prefixo/sufixo/contador e anti-overwrite.
- Preview em tempo real (72 DPI) com navegação entre folhas e debounce de 300ms.
- Geração em thread com barra de progresso em 2 fases e atalho para abrir a pasta.

## 🔧 Em Progresso
- (vazio) — sessão atual focou em documentação e planejamento; nenhuma implementação aberta.

## ❌ Quebrado / Com Problema
- (nada conhecido) — o único bug grave (PanedWindow + CTkScrollableFrame) foi resolvido. Ver FIX-001.

## 📋 Backlog (curto prazo — itens acionáveis)
> Itens pequenos e concretos. Plano em fases vive no ROADMAP; ideias soltas no IDEAS.
- [ ] Adicionar pasta inteira de uma vez (hoje só multi-seleção de arquivos).
- [ ] Guarda de qualidade: avisar quando a imagem-fonte for menor que a célula (upscale/perda). *(alto valor, baixo custo)*
- [ ] Salvar/carregar perfil de configuração (.json) — presets reutilizáveis.
- [ ] Lembrar última pasta de saída e últimas configurações entre execuções.
- [ ] Escrever 2–3 testes headless do `ImpositionEngine` (contagem de folhas, tamanho de página, ajuste fit/fill).

## 📁 Arquivos Críticos (não mexer sem contexto)
- `print_imposer.py` — app inteiro. Antes de tocar na composição, ler CONTEXT §"Como a imposição funciona". A função `compose_page` troca `cfg.dpi` temporariamente: não remover a restauração.

## 💬 Última Sessão
**2026-06-15** — Sessão de documentação. Montado o kit de contexto completo a partir da realidade do v1.0 + FIX-001. Pesquisa profissional de imposição/prepress consolidada no HISTORICO; melhorias concretas registradas em IDEAS e organizadas em fases no ROADMAP. Próximo passo óbvio: executar a Fase F2 do ROADMAP (quick wins de UX + guarda de qualidade) ou escrever os primeiros testes do engine.
