# printimposer — guia para o Claude Code

> Arquivo-raiz lido pelo Claude Code em todo turno. Mantenha CURTO (< 200 linhas — custa token em todo turno).
> Regra prática: se remover uma linha e o Claude ainda acerta, ela não pertence aqui. Procedural detalhado → vira skill em `.claude/skills/`.
> O comportamento detalhado do assistente está em `meta/CEREBRO.md` — leia sob demanda, não decore.

## O que é este projeto
Ferramenta desktop (Python + CustomTkinter) que agrupa várias imagens em folhas para impressão —
ex.: 4 cards A6 numa folha A4, prontos para imprimir e cortar. Arquivo único: `print_imposer.py`.

## Seu papel aqui (DEC-012, que substitui a DEC-007 e a DEC-010)
- **O chat** planeja: decide arquitetura, escreve spec (`meta/specs/`), análise e WO (`meta/workorders/`),
  e cura CEREBRO, CONTEXT, GLOSSARY, Instruções e LOG-TEMPLATE. Ele lê e grava na pasta, mas **não abre a GUI**.
- **Você** implementa: escreve o código a partir da spec ou da WO, roda a suíte e a GUI, faz o smoke,
  edita STATUS / DECISIONS / CHANGELOG (append) e a sua seção do log do dia, commita e empurra.

Por isso: **prefira o menor diff que resolve.** Não refatore o que não foi pedido. Se um problema for de
arquitetura e a spec/WO não decidir, **relate em vez de resolver** — essa decisão é do chat com o dono, e
resolver por conta cria duas fontes de verdade.

## Ritual de início
Leia `meta/CEREBRO.md` → `meta/CONTEXT.md` (**as Armadilhas Conhecidas não são opcionais**) →
`meta/STATUS.md` → em `meta/ROADMAP.md`, só a fase marcada 🟡. Confirme em uma frase o que entendeu.

## Os arquivos meta/ (sistema KCM)
Cada um tem UM papel — não duplique informação entre eles:

| Arquivo | Papel | Como você escreve nele |
|---|---|---|
| `CONTEXT.md` | O que o projeto É. Estável. | Não escreve: armadilha nova vai no relatório, o chat registra. |
| `STATUS.md` | O agora. Rolante. | **Append**: mova o resolvido para fora, registre o que quebrou. |
| `DECISIONS.md` | Por quê. `DEC-` e `FIX-`. | **Append**: novo `FIX-N` se corrigir bug grave. Nunca reescreva entrada antiga. |
| `CHANGELOG.md` | Versões entregues. | Só quando algo for de fato concluído. |
| `IDEAS.md` | Ideias. Nunca perde nada. | Por WO. Esbarrou numa ideia? Ponha no relatório; não decida por ela. |
| `ROADMAP.md` | Fases. | Marque estado de fase (🟢🟡🔵); não invente fase. |
| `GLOSSARY.md` | Termos do projeto. | Não escreve: termo novo vai no relatório. |
| `HISTORY.md` | Conhecimento consolidado. Sob demanda. | Raramente; seção nova entra no FIM (o código cita §6 e §8). |

**Regra de ouro:** o STATUS é o AGORA (o resolvido sai), o DECISIONS é o PORQUÊ (cresce, nunca
reescreve), o IDEAS nunca perde nada. Curadoria que reescreve um doc inteiro é do chat, não sua.

## Build / validação
```bash
python print_imposer.py          # abre a GUI
python tests/test_engine.py      # suite headless (~15s) — rode SEMPRE antes de commitar codigo
```
- Não há build. Mudança só de doc (`meta/`) NÃO precisa de teste; a rede é o `git diff`.
- **Suíte verde não prova que o app abre** (FIX-003). Mudança de interface → `/smoke`.

## Skills
- `/apply-wo <arquivo>` — aplica uma WO de `meta/workorders/` (âncora exata ou PARA e reporta).
- `/smoke` — smoke test da GUI, os 9 itens abaixo.
- `/wrap` — fecha a tarefa: append em STATUS/DECISIONS, `git diff`, commit e push.
- `/sondar` — passada exploratória: devolve candidatos a checagem, nunca veredito.

## Smoke test da GUI (o que o chat não consegue verificar)
Depois de qualquer mudança de interface, abra o app e confira:

1. **Abertura** — janela centralizada, inteira na tela, nada cortado. Em monitor com zoom
   (125%/150%) o texto sai nítido, não borrado.
2. **Divisórias** — os três painéis (lista / configurações / preview) aparecem com largura
   utilizável; nenhum foi engolido pelo vizinho.
3. **Grade livre** — botões `+`/`-` de colunas e linhas mudam a miniatura do grid e o preview.
   Digite `2` e `6`, clique em "Aplicar valores digitados": deve virar 12 por folha.
4. **Guarda de qualidade** — adicione uma imagem pequena (ex.: 300×420) com DPI 300: deve
   aparecer o aviso vermelho. Uma imagem grande deve dar o selo verde.
5. **Presets** — salve um preset, mude tudo, recarregue: os campos voltam.
6. **Pastas** — "+ Arquivos" não altera a pasta de saída. Ligar o segundo destino grava nos dois.
7. **Persistência** — feche e reabra: configuração e tamanho de janela voltam.
8. **.bat** — gere o atalho, dê duplo clique: abre sem janela de console.
9. **SVG** — se o cabeçalho disser `SVG: cairosvg` (ou `svglib`), adicione um `.svg` e gere.
   Se disser `indisponível`, `.svg` não deve nem aparecer no seletor de arquivos.

**Abra o app de teste isolado:** defina `USERPROFILE` **e** `HOME` para uma pasta temporária — no Windows `Path.home()` ignora `HOME`, e só ele não protege o `~/.printimposer` real do dono (CONTEXT, armadilha 11). Confira em `Ajuda › Sobre` o caminho do `settings.json` antes de mexer em campos.

Relate o que falhou com o traceback inteiro. Se tudo passar, diga isso explicitamente.

## Convenções
- Nomes de arquivo/função/variável em **inglês**; comentários em **PT-BR**.
- Comentário explica o **porquê**, não o quê. Docstring em função pública.
- **Preserve** comentários e código existentes; só remova os órfãos.
- Mensagens de commit em PT-BR, imperativo curto, **sem acento**.
- `.bat` e qualquer saída para o CMD: **ASCII puro** — o console do Windows corrompe UTF-8.
- Dependência opcional entra em `try/except` e **degrada com elegância**: a UI nunca quebra por
  falta de um extra. E **sondar a capacidade, não só o import** (ver FIX-002).
- Ao aplicar uma WO: ache cada âncora exatamente; se não achar, PARE e reporte. Não mexa fora das
  edições nomeadas. `git diff` antes do commit.
- **Ao fechar a tarefa, RELATE o trabalho** — o que fez, achados e desvios do que a tarefa pedia, arquivos
  tocados, resultado da validação e o commit. **Não** copie o bloco de fecho do `meta/CEREBRO.md`: aquele é
  da raia de planejamento, e trocar relatório por formulário perde o que só você viu.

## Quando eu pedir medição
- Eu leio a pasta com teto de contexto e de tempo por comando; você lê o repositório inteiro. Se eu pedir para
  **medir**, o pedido não tem âncora nem commit: não edite nada, não conserte nada, não sugira nada.
- Responda com o **número cru e o comando que o produziu**. Sem interpretação — se achar que o número indica
  um problema, diga o número primeiro e a suspeita depois, separada.
- Alvo fora da raiz do repositório depende de `permissions.additionalDirectories`. Se a leitura for negada, DIGA — não estime.

## Push e relatório — nesta ordem, sempre
- **Verde** (suíte passou, ou WO só de doc com o `git diff` conferido) → `add`, `commit` e **`push`, sem perguntar.**
- **Vermelho** (suíte falhou, âncora não encontrada, `git diff` com arquivo fora do previsto) → **não commite e
  não empurre.** Feche com menu de opções pela ferramenta `AskUserQuestion`, a recomendada em primeiro e
  marcada `(Recomendado)` — nunca pergunta em prosa.
- **O relatório é o ÚLTIMO passo**, depois de resolvido o push: empurrado (com o hash), não empurrado (com o
  motivo), ou aguardando a escolha do menu. Se a escolha chegar depois, **reescreva o relatório**.

## Relatório em arquivo (sempre, sem pedir)
- Ao fechar QUALQUER tarefa, grave o MESMO relatório em `../AAMMDD-HHMM-code-printimposer-<ato>-<alvo>.txt`
  (pasta-PAI do repo, fora do versionamento). **`<ato>`** = vocabulário FECHADO: `apply` · `wrap` · `probe` ·
  `explore`. **`<alvo>`** = a WO (`wo0001`) ou duas ou três palavras com hífen. O `AAMMDD-HHMM` sai de
  `date +%y%m%d-%H%M`, rodado na hora.
- Se a escrita for negada, DIGA e siga — o relatório no chat continua sendo a entrega.

## Config (modelo × esforço)
- WO com diff exato já validado → **Sonnet**, esforço proporcional (mecânico = baixo/médio).
- Implementar spec de UI, refator multi-classe, WO que delega decisão → **Opus**, esforço alto.
