# printimposer — guia para o Claude Code

> Arquivo-raiz lido pelo Claude Code em toda sessão. Mantenha CURTO: custa token em todo turno.
> O comportamento completo do assistente está em `meta/CEREBRO.md` — leia sob demanda, não decore.

## O que é este projeto
Ferramenta desktop (Python + CustomTkinter) que agrupa várias imagens em folhas para impressão —
ex.: 4 cards A6 numa folha A4, prontos para imprimir e cortar. Arquivo único: `print_imposer.py`.

## Seu papel aqui (leia com atenção)
Este projeto é **planejado e escrito no chat**; você é a **raia de execução e validação**.
A divisão foi decidida na DEC-007 e refinada na DEC-010:

- **O chat** decide arquitetura, escreve o código, cura os `meta/`. Ele **não consegue abrir a GUI**
  (não tem Tk nem display) — todo bug de interface passa por ele.
- **Você** roda, vê o traceback, faz o smoke test, e corrige o que só aparece com a janela aberta.

Por isso: **prefira o menor diff que resolve.** Não refatore o que não foi pedido, não reescreva o
arquivo inteiro. Se um problema for de arquitetura e não de execução, **relate em vez de resolver** —
essa decisão pertence ao chat, e resolver por conta cria duas fontes de verdade.

## Ritual de início
Leia, nesta ordem, antes de agir:
1. `meta/CONTEXT.md` — o que o projeto é; **as Armadilhas Conhecidas não são opcionais**.
2. `meta/STATUS.md` — o agora: o que funciona, o que está quebrado, o backlog.
3. `meta/ROADMAP.md` — só a fase marcada 🟡, para saber onde a tarefa se encaixa.

Confirme em uma frase o que entendeu antes de executar.

## Os arquivos meta/ (sistema KCM)
Documentação viva que permite trocar de sessão sem perder contexto. Cada um tem UM papel — não
duplique informação entre eles:

| Arquivo | Papel | Como você escreve nele |
|---|---|---|
| `CONTEXT.md` | O que o projeto É. Estável. | Só se descobrir armadilha nova. |
| `STATUS.md` | O agora. Rolante. | **Append**: mova o resolvido para fora, registre o que quebrou. |
| `DECISIONS.md` | Por quê. `DEC-` e `FIX-`. | **Append**: novo `FIX-N` se corrigir bug grave. Nunca reescreva entrada antiga. |
| `CHANGELOG.md` | Versões entregues. | Só quando algo for de fato concluído. |
| `IDEAS.md` | Ideias. Nunca perde nada. | Se esbarrar numa ideia, registre; não decida por ela. |
| `ROADMAP.md` | Fases. | Marque estado de fase (🟢🟡🔵); não invente fase. |
| `GLOSSARY.md` | Termos do projeto. | Termo novo que vai se repetir. |
| `HISTORY.md` | Conhecimento consolidado. Sob demanda. | Raramente; é o baú de análises longas. |

**Regra de ouro:** o STATUS é o AGORA (o resolvido sai), o DECISIONS é o PORQUÊ (cresce, nunca
reescreve), o IDEAS nunca perde nada. Curadoria que reescreve um doc inteiro é do chat, não sua.

## Comandos
```bash
python print_imposer.py          # abre a GUI
python tests/test_engine.py      # suite headless (40 testes, ~2s) — rode SEMPRE antes de commitar
```
Não há build. Mudança só em `meta/` não precisa de teste; a rede é o `git diff`.

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

Relate o que falhou com o traceback inteiro. Se tudo passar, diga isso explicitamente.

## Convenções
- Nomes de arquivo/função/variável em **inglês**; comentários em **PT-BR**.
- Comentário explica o **porquê**, não o quê. Docstring em função pública.
- **Preserve** comentários e código existentes; só remova os órfãos.
- Mensagens de commit em PT-BR, imperativo curto, **sem acento**.
- `.bat` e qualquer saída para o CMD: **ASCII puro** — o console do Windows corrompe UTF-8.
- Dependência opcional entra em `try/except` e **degrada com elegância**: a UI nunca quebra por
  falta de um extra. E **sondar a capacidade, não só o import** (ver FIX-002).

## Antes de commitar
`python tests/test_engine.py` verde → `git diff` conferido → commit sem acento.
Se mexeu em comportamento, acrescente uma linha no `meta/STATUS.md`.
