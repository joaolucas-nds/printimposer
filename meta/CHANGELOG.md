# CHANGELOG

> Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).
> **Cresce**: entradas novas no topo. Registra só o que foi de fato concluído/entregue.

## [Não lançado]
### Corrigido
- Crash ao abrir no Windows por incompatibilidade entre `tk.PanedWindow` e `CTkScrollableFrame`: os três painéis (lista, configurações, preview) passaram a ser envolvidos em `tk.Frame` neutro antes de entrar no PanedWindow. Ver FIX-001.

### Adicionado
- Kit de documentação de contexto do projeto (CONTEXT, STATUS, DECISIONS, CHANGELOG, IDEAS, ROADMAP, GLOSSARY, HISTORICO, LOG-TEMPLATE, log da sessão).

---

## [1.0.0] — 2026-06-02
### Adicionado
- Seleção em massa de imagens (PNG, JPG, JPEG, TIFF, BMP, WebP) com lista de miniaturas.
- Quantidade por imagem (duplicação para impressão) e reordenação por botões ↑↓.
- Layouts N-up: 1×1, 2×1, 1×2, 2×2, 3×2, 2×3, 4×2, 2×4, 3×3, 4×3, 4×4.
- Modos de ajuste por slot: fit / fill / stretch, com Auto-Rotate.
- Papéis A3/A4/A5/A6/Letter/Legal/Tabloid/Custom e DPI configurável (72–1200).
- Margem externa e entre imagens (mm); cor de fundo configurável.
- Linhas de corte opcionais: estilos sólida/tracejada/pontilhada, espessura, comprimento de traço e cor.
- Saída em PDF (multipágina), PNG, JPEG e TIFF, com prefixo/sufixo/contador automático e proteção contra sobrescrita.
- Preview em tempo real (72 DPI) com navegação entre folhas e atualização com debounce.
- Geração em thread separada com barra de progresso em duas fases e atalho para abrir a pasta de saída.
- README com guia de uso completo, fluxo Figma → PrintImposer e FAQ.
