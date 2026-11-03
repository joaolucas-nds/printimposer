---
name: sondar
description: Passada exploratoria sobre o material do projeto — le sem hipotese previa e devolve CANDIDATOS a checagem, nunca veredito. Use quando o usuario pedir /sondar.
disable-model-invocation: true
---
Voce vai LER o material do projeto e devolver um relatorio de EXPLORACAO.

Isto nao e uma verificacao. A verificacao e determinista, mora no instrumento do projeto e responde perguntas que alguem ja sabia fazer. Sua funcao e a oposta: descobrir as perguntas que ninguem fez ainda. **Exploracao produz HIPOTESE; instrumento produz EVIDENCIA.**

## Regras duras

1. **NAO conclua e NAO use a palavra «verificado».** Voce produz candidatos, nao veredito. Quem decide e a raia de planejamento, com o dono.
2. **Todo achado vem com o comando ou o trecho exato que o reproduz.** Achado sem forma de reproduzir NAO entra: vai para «observacoes descartadas», com o motivo.
3. **Numero que voce contar de cabeca nao vale.** Conte com comando, e cole o comando ao lado do numero.
4. **NAO escreva nada no material explorado.** Nao renomeie, nao apague, nao conserte de passagem. Nao edite `meta/` nem o codigo. O relatorio e a sua UNICA saida.
5. **NAO parta da lista de checagens que ja existe.** Se voce so olhar onde o instrumento ja olha, voce so acha o que ele ja acharia — e o defeito que ele nao cobre sobrevive a mais uma rodada. Comece pelo material, nao pela lista.
6. **NAO abra ordem de trabalho e NAO mova ideia.** O destino de um candidato e o `IDEAS.md`, e quem o move para la e a raia de planejamento, depois que ele virar checagem determinista.

## O que fazer

Os quatro primeiros valem para qualquer projeto; o quinto so existe a partir da segunda vez.

1. **Inventario bruto do que existe.** Que arquivos existem, por pasta e por extensao, com contagem tirada de comando. Inclua as pastas que ninguem abre — e as que o `.gitignore` esconde, se forem legiveis.
2. **O que os documentos DECLARAM contra o que existe.** Numero repetido em dois documentos que deveriam concordar (versao, contagem de testes, «funciona ate X»); caminho citado que nao existe no disco; arquivo no disco que documento nenhum cita; item marcado como pendente que ja esta feito, e o contrario.
3. **O instalado contra o gerado.** O que veio de fora (kit, template, biblioteca) e ficou para tras da fonte, e o que foi editado a mao e vai se perder na proxima atualizacao.
4. **Cruzamentos que a validacao NAO faz.** Procure ativamente: a mesma informacao declarada em dois lugares (elas concordam?); id referenciado que nao existe no indice correspondente; unidade, escala ou formato trocado entre campos irmaos; valor que parece caminho, data ou versao dentro de campo que ninguem confere.
5. **O que mudou desde a exploracao anterior**, se houver relatorio anterior.

## O relatorio

Grave em `../AAMMDD-HHMM-code-<slug>-explore-<alvo>.txt` (pasta-pai do repo, mesmo lugar e mesmo padrao dos outros relatorios; o ato e sempre `explore`). Use estas quatro secoes:
O `HHMM` sai de `date +%y%m%d-%H%M`, rodado na hora — nunca de cabeça.

- **O que eu olhei** — as pastas e os arquivos, com as contagens e os comandos usados.
- **O que eu olhei e NAO achei nada** — explicito, e nao e formalidade. Passada exploratoria que sempre acha algo e passada que inventa; dizer «olhei X e esta consistente» e RESULTADO, e e o que permite a proxima passada pular X. Sem esta secao, a exploracao seguinte recomeca do zero.
- **Candidatos a checagem** — um por bloco, cada um com: o fato observado, como reproduzir, e qual checagem determinista o capturaria. Voce PROPOE a checagem; nao a implementa.
- **Observacoes descartadas** — o que voce viu e nao conseguiu reproduzir, com o motivo. Descartar em silencio e perder o rastro de uma pergunta boa.

Ao terminar, imprima o caminho do relatorio e um resumo de tres linhas. Se a passada nao produziu nenhum candidato, diga isso — e a secao «o que eu olhei e nao achei nada» passa a ser o corpo do relatorio, o que e um resultado util e nao um fracasso.

Material a explorar: $ARGUMENTS


*Gerado pelo Kit de Contexto Universal v1.133.0 — 2026-11-03 — esta linha e do KIT: nao funda, substitua pela do pacote mais recente.*
