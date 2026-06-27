# GLOSSARY.md — Termos do Projeto

> **Opcional.** Use quando o projeto tem vocabulário próprio (nomes de módulos, conceitos, identificadores) que o assistente reexplicaria a cada sessão sem isto.
> Mantenha curto: só o que não é óbvio para alguém de fora.

---

## Conceitos de imposição / prepress
- **Imposição (imposition)** — posicionar várias páginas/artes numa folha maior para imprimir e cortar com eficiência. É o que a ferramenta faz.
- **N-up** — quantas imagens por folha. "4-up" = 4 por folha; aqui sempre num grid `cols×rows`.
- **DPI** — pontos por polegada na impressão. 300 DPI é o padrão profissional. Tamanho em px = `mm × DPI / 25.4`.
- **fit / fill / stretch** — modos de ajuste da imagem ao slot: *fit* cabe inteira (sobra fundo), *fill* preenche e recorta, *stretch* força o tamanho (distorce).
- **Auto-Rotate** — girar a imagem 90° quando sua orientação (retrato/paisagem) não bate com a do slot.
- **Slot / célula (cell)** — o retângulo onde uma imagem é colocada dentro do grid da folha.
- **Margem externa** — espaço ao redor de toda a folha (bordas).
- **Margem entre imagens / gutter** — espaço entre os slots. Em prepress, o **gutter** é a folga entre artes que também acomoda marcas de corte e tolerância de corte.
- **Sangria (bleed)** — arte que transborda o limite de corte (tipicamente ~3 mm) para que não apareça borda branca após o corte. *(planejado, F3)*
- **Marca de corte (crop mark)** — guia de onde cortar. Padrão de indústria: ticks curtos nos cantos, no gutter (não atravessam a arte). v1 usa linhas atravessando a folha. *(canto: F3)*
- **Marca de registro (registration mark)** — alinhamento entre plates de cores diferentes na impressão offset. Fora do escopo deste projeto.
- **Step-and-repeat** — repetir a mesma arte N vezes na folha. O campo "quantidade" por imagem faz uma versão básica.
- **Cut & stack** — ordenar cópias para que, após cortar e empilhar, a sequência fique correta. Fora do escopo atual.
- **Compressão (lossless × lossy)** — *lossless* (PNG/Flate) preserva tudo, arquivo maior; *lossy* (JPEG) reduz tamanho com perda. Reamostrar para um DPI menor também perde qualidade. Ver HISTORICO §2.

## Arquiteturas / módulos (no código)
- **ImpositionEngine** — núcleo de composição; não depende de Tkinter. Métodos-chave: `compose_page`, `generate_all`, `preview_page`, `save`. Ver DEC-004.
- **LayoutConfig** — estado de configuração (papel, DPI, margens, corte, saída). Tem `to_dict`/`from_dict` (base para presets).
- **ImageEntry** — uma imagem + quantidade + miniatura.
- **PrintImposerApp** — janela principal (CTk) que orquestra os painéis.
- **ImageListPanel / ConfigPanel / PreviewPanel** — os três painéis da UI (lista, configurações, preview).
- **ImageRow** — uma linha da lista (miniatura, nome, quantidade, botões).

## Comandos / artefatos
- **`print_imposer.py`** — o app inteiro; rodar com `python print_imposer.py`.
- **`compose_page(page_idx, paths, override_dpi=None)`** — monta uma folha; com `override_dpi=72` é o caminho do preview.

## Identificadores
- **DEC-N** — decisão de arquitetura/design em DECISIONS.md.
- **FIX-N** — bug grave resolvido em DECISIONS.md.
- **F1…F4** — fases do ROADMAP.
