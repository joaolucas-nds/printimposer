# SPEC-F3-UI — Reestruturação do painel de configuração

> Spec de implementação. Decisões tomadas em 2026-07-22 com base em pesquisa de UX (ver HISTORY §9).
> Alvo: v1.2.0. Estado: aprovada, a implementar.

---

## 1. Problema

O painel central empilha **7 seções numa rolagem única** (~1400 px de altura). Consequências medidas na v1.1.1:

- O contador (`12 imagens · 4 por folha · 3 folhas`) e a **guarda de qualidade** só aparecem no fim da rolagem. São *feedback*, não configuração — e hoje estão efetivamente escondidos.
- O gerador de `.bat`, usado **uma vez na vida**, ocupa espaço permanente no fim.
- Presets, que são *ação* e não configuração, dividem espaço com os campos.
- No monitor de 1366×768 do usuário, ver "Saída" exige rolar por cima de tudo.

## 2. Fundamento (pesquisa)

| Achado | Fonte | Aplicação |
|---|---|---|
| Não esconder conteúdo essencial em painel colapsado/fora de vista | consenso de accordion/tabs | contador e qualidade viram **zona fixa** |
| Progressive disclosure: deferir o raramente usado para tela secundária | Nielsen, 1995 | `.bat`, presets, sobre → **menubar** |
| Tabs quebram acima de 5 itens e com rótulos longos | pesquisa comparativa | **accordion**, não tabs (6 seções, rótulos longos em PT-BR) |
| Accordion escala de 5 a 20 seções | idem | confirma a escolha |
| Sempre abrir a seção mais importante por padrão | idem | **Saída** nasce aberta |
| Análise de frequência 80/20 define essencial × avançado | prática de design systems | Grade fixa; resto colapsado |

**Frequência observada:** Grade muda a cada trabalho · Saída (prefixo) muda a cada trabalho · Papel/DPI/Ajuste/Margens/Corte se configuram uma vez.

## 3. Decisões aprovadas pelo usuário

1. **Accordion multi-aberto, com estado persistido.** Abrir uma seção não fecha as outras; quais ficaram abertas volta ao reabrir o app.
2. **Menubar clássica:** `Arquivo · Opções · Ajuda`.
3. **Menu recebe os quatro itens:** atalho `.bat` (com explicação), presets, sobre/versão, guia rápido.

## 4. Estrutura alvo

```
┌ TOPBAR ─────────────────────────────────────────────────────┐
│ PrintImposer   Arquivo  Opções  Ajuda      v1.2.0 · SVG: … │
├──────────┬─────────────────────────────┬────────────────────┤
│ Imagens  │ ╔═ FIXO ═══════════════════╗│ Preview            │
│          │ ║ Grade — cols × rows      ║│                    │
│          │ ║ + mini-grid              ║│                    │
│          │ ╚══════════════════════════╝│                    │
│          │ ┌ accordion (rolável) ─────┐│                    │
│          │ │ ▸ Papel e resolução      ││                    │
│          │ │ ▸ Ajuste da imagem       ││                    │
│          │ │ ▸ Margens e espaçamento  ││                    │
│          │ │ ▸ Linhas de corte        ││                    │
│          │ │ ▾ Saída        (aberta)  ││                    │
│          │ └──────────────────────────┘│                    │
│          │ ╔═ FIXO ═══════════════════╗│                    │
│          │ ║ 12 img · 4/folha · 3 fl. ║│                    │
│          │ ║ ✔ Qualidade OK — 153%    ║│                    │
│          │ ║ Célula 105,0 × 148,5 mm  ║│                    │
│          │ ╚══════════════════════════╝│                    │
├──────────┴─────────────────────────────┴────────────────────┤
│ [Gerar arquivos]  ████████████            Pronto            │
└─────────────────────────────────────────────────────────────┘
```

Altura empilhada da coluna central: **~1400 px → ~560 px**. Sem rolagem no uso normal em 768 px.

## 5. Menubar — conteúdo

Implementada como **três `CTkButton` na topbar** disparando `tk.Menu.tk_popup()`.
Motivo: a faixa fica no tema escuro do app (um menubar nativo via `self.config(menu=…)` seria desenhado pelo SO em cinza claro), enquanto o dropdown continua nativo — herda navegação por teclado, dismissal e acessibilidade de graça. Menos código que popups próprios, e evita a classe de bug do FIX-003.

### Arquivo
| Item | Atalho | Ação |
|---|---|---|
| Adicionar arquivos… | `Ctrl+O` | `ImageListPanel._add_files` |
| Adicionar pasta… | `Ctrl+Shift+O` | `ImageListPanel._add_folder` |
| Limpar lista | — | `ImageListPanel._clear` |
| — separador — | | |
| Gerar arquivos | `Ctrl+G` | `_start_generate` |
| Abrir pasta de saída | — | `_open_folder(cfg.output_dir)` |
| — separador — | | |
| Sair | `Alt+F4` | `_on_close` |

### Opções
| Item | Ação |
|---|---|
| Presets ▸ | submenu dinâmico: lista os salvos; `Salvar atual…`, `Excluir…` |
| — separador — | |
| Criar atalho na área de trabalho… | abre o diálogo da §6 |
| — separador — | |
| Restaurar configurações padrão | confirma e reseta `LayoutConfig` |

### Ajuda
| Item | Ação |
|---|---|
| Guia rápido: Figma → impressão | janela de texto rolável (§7) |
| — separador — | |
| Sobre o PrintImposer | versão, back-end de SVG, caminho do `settings.json` |

## 6. Diálogo "Criar atalho" (substitui a seção `.bat`)

O botão atual gera um arquivo sem explicar o que é. O diálogo passa a **ensinar antes de gerar** — decisão do usuário, e alinhada ao princípio de que ação rara deve ser explicada, não só disponível.

Conteúdo (um `CTkToplevel` modal, ~420×280):
- **O que é:** um atalho `.bat` que abre o PrintImposer com dois cliques, sem janela de console.
- **Onde salvar:** sugere a área de trabalho; qualquer pasta serve.
- **Se eu mover a ferramenta?** o atalho para de funcionar — gere outro.
- Mostra o caminho do interpretador e do script que serão gravados.
- Botões: `Criar atalho…` (abre o `asksaveasfilename` atual) · `Fechar`.

Reaproveita `build_launcher_bat()` sem alteração.

## 7. Guia rápido (Ajuda)

`CTkToplevel` com texto rolável, sem dependência externa. Conteúdo enxuto:
1. No Figma: frames A6, exportar PNG com ≥1240×1748 px (ou SVG, se houver back-end).
2. No PrintImposer: adicionar pasta → grade 2×2 → conferir o selo de qualidade → gerar.
3. Na impressora: "Tamanho real"/100%, nunca "ajustar à página".

Fonte: README §"Fluxo de trabalho recomendado". **Uma fonte de verdade:** o guia lê de uma constante única no módulo; o README continua sendo a versão longa.

## 8. Componente `CollapsibleSection`

Novo widget, `ctk.CTkFrame`:

```
CollapsibleSection(master, title, key, expanded=False, on_toggle=None)
  .header  -> CTkButton full-width: "▸ Título" / "▾ Título"
  .body    -> CTkFrame; grid_remove() quando fechado
  .toggle()
```

**Requisitos:**
- `key` é o identificador estável usado na persistência (`"papel"`, `"ajuste"`, …).
- Fechar usa `grid_remove()`, não `destroy()` — preserva os widgets e o estado dos campos.
- Não escrever em nome reservado do Tkinter — prefixo próprio em todo atributo (armadilha nº3 do CONTEXT, FIX-003).
- Cabeçalho é botão de verdade: foco por `Tab`, aciona por `Espaço`/`Enter`.

## 9. Persistência — mudança de esquema

`~/.printimposer/settings.json` ganha uma chave:

```json
{
  "config": { "...": "inalterado" },
  "geometry": "1180x820+93+31",
  "sections_open": { "papel": false, "ajuste": false, "margens": false,
                     "corte": false, "saida": true },
  "version": "1.2.0"
}
```

**Compatibilidade:** arquivo da 1.1.x não tem `sections_open` → cai no padrão (só `saida` aberta). Nenhuma migração necessária; `SettingsStore` já ignora chave ausente.

## 10. O que sai do painel

| Hoje | Vai para |
|---|---|
| Seção "Atalho" (`.bat`) | `Opções › Criar atalho na área de trabalho…` |
| Seção "Presets" | `Opções › Presets ▸` |
| Rodapé `n imagens · n por folha · n folhas` | **zona fixa** inferior |
| Guarda de qualidade (dentro de "Papel") | **zona fixa** inferior |
| Linha "Célula: … mm (… px @ … DPI)" | **zona fixa** inferior |

O bug conhecido do menu de presets (só atualiza ao reabrir o app) **morre junto**: o submenu é reconstruído a cada abertura do menu.

## 11. Riscos e o que testar

| Risco | Mitigação | Verificação |
|---|---|---|
| `tk_popup` mal posicionado em multi-monitor | ancorar nas coordenadas do botão (`winfo_rootx/rooty`) | smoke, item novo |
| `grid_remove()`/`grid()` embaralhar a ordem das seções | `row=` fixo por seção, definido na construção | smoke |
| Zona fixa comer altura demais em 768 px | zona inferior com altura fixa ≤ 84 px | smoke, item 1 |
| Colisão de atributo com Tkinter no widget novo | prefixo próprio + `TkAttributeCollisionTests` já cobre | suíte headless |
| `sections_open` com chave desconhecida | `SettingsStore` ignora; padrão para chave ausente | teste headless novo |

**Testes headless a acrescentar:** contrato do `sections_open` (round-trip, chave ausente, chave desconhecida) e presença dos itens de menu esperados. O resto é smoke.

**Itens novos para o smoke:**
1. Abrir 3 seções, fechar o app, reabrir → as mesmas 3 continuam abertas.
2. `Ctrl+O`, `Ctrl+Shift+O` e `Ctrl+G` funcionam com o foco em qualquer painel.
3. Salvar um preset e abrir `Opções › Presets` **sem reiniciar** → o novo aparece.
4. Em 1366×768, com todas as seções fechadas, nada é cortado e o rodapé fica visível.

## 12. Formato de entrega

**Arquivo inteiro**, não ASU. A mudança reescreve `ConfigPanel` por completo, acrescenta duas classes (`CollapsibleSection`, `MenuBar`), muda o `_build_ui` e o esquema de persistência — é reescrita profunda, o caso que a DEC-007 reserva para arquivo inteiro. O ASU volta para os ajustes localizados que vierem depois do smoke.

## 13. Fora do escopo desta spec

- Redesenho do painel de imagens ou do preview.
- Drag-and-drop (continua na F5).
- Tema claro / alternância de tema.
- Internacionalização dos rótulos de menu.
