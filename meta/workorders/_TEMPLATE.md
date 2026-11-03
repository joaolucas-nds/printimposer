# WO NNNN — [titulo curto e concreto, no que a WO ENTREGA]

> **Este arquivo e o MODELO — nao o preencha aqui.** Copie para `meta/workorders/AAMMDD-woNNNN-desc.md`
> e preencha a copia. No canal de reserva (FlatDrop) o modelo sobe ao Projeto mesmo assim (o `.flatdropignore` ignora `meta/workorders/*` mas
> reinclui `!meta/workorders/_TEMPLATE.md`), para que a primeira conversa depois de uma transferencia
> tenha o formato a mao sem precisar das WOs antigas.
>
> **O que e uma WO:** instrucao de APLICACAO — ancora + texto exato — que o chat autora e o Code posiciona.
> **O que NAO e:** a spec de feature diz **o que** construir e quando esta pronto; a WO diz **como aplicar**.
> Se voce ainda nao sabe o que construir, nao e hora de escrever WO — e hora de analise ou spec.

---

## Cabecalho — preencha as linhas que se aplicam e apague as que nao

> **Tipo:** WO de CODIGO · WO de DOC (registro) · mista.
> **Config sugerida:** modelo e esforco para quem for aplicar.
> **Pre-requisito:** versao/commit em que esta WO foi escrita, e o estado esperado (testes verdes, arvore limpa).
> **Base:** a decisao, a analise ou a conversa que originou.
> **Depende de:** WOs que precisam estar aplicadas antes — ou apague a linha.
> **Arquivos que o chat gravou no disco e esta WO versiona:** um por linha, com o `sha1sum` que o chat mediu
> ao grava-los. A Edicao 0 roda `sha1sum` em cada um ANTES de tudo: hash diferente = outro escritor mexeu
> no arquivo depois do chat — **PARE e reporte**, nao commite por cima. Sem pasta vinculada, apague a linha.
> **Ancora semantica:** se um trecho-ancora nao bater EXATAMENTE, **PARE e reporte** — nunca chute um
> lugar proximo. Os arquivos podem ter mudado entre a escrita desta WO e a aplicacao.
> **Idempotencia:** antes de cada edicao, procure o texto NOVO INTEIRO no arquivo — frase-chave nao basta: na forma
> «trocar» o texto novo repete a ancora, e um trecho dele ja existe antes de aplicar. Ja aplicada = o texto novo INTEIRO esta
> no arquivo **e a ancora nao** — salvo quando a ancora esta DENTRO do texto novo (forma «trocar»). Na REMOCAO o texto novo e
> um pedaco da ancora: sem a segunda condicao, ela seria pulada sem nunca ter sido aplicada. Ja aplicada, **PULE**
> o item e diga no relatorio — nao duplique.
> **Ancoras lidas em:** para CADA edicao, o arquivo e o trecho literal que voce leu NESTE turno para escrever a ancora.
> Campo OBRIGATORIO em WO que edita arquivo existente. **Quem aplica RECUSA a WO se vier vazio** — a conferencia sai de
> quem escreveu (que tem o vies) e vai para quem aplica (que nao tem), que e o mesmo desenho que faz o «PARE e reporte»
> funcionar todas as vezes. O campo pede o TRECHO, nao uma marca de conferido: nao se escreve o trecho sem abrir o arquivo.
> **Afirmacao sobre artefato legivel nao e opiniao, e leitura** — o que uma ferramenta faz, o que um simbolo contem, em que
> estado esta a pasta (ou o mount, no canal de reserva). Nao cite simbolo, caminho ou capacidade de ferramenta que voce nao leu neste turno; declarar «nao li»
> nao autoriza escrever a WO em cima.
> **Numero de checklist e DERIVADO, nunca estimado.** Toda contagem prevista (`grep -c`, quantidade de bullets, de
> arquivos) sai de simular o texto final DESTA WO, incluindo o que ela propria manda inserir — a WO costuma citar as
> frases que insere, na prosa e no checklist, e a contagem ingenua erra por isso. Numero de memoria vira desvio no
> relatorio de quem aplica, que estava certo. **`grep -c` conta LINHAS, nao ocorrencias:** em documento cujo
> paragrafo e uma linha so, duas mencoes no mesmo bullet contam 1 — para ocorrencia use `grep -o ... | wc -l`,
> e diga qual dos dois voce previu. **Byte previsto carrega o fim de linha:** numero tirado de sandbox que grava
> CRLF erra 1 byte por linha nova quando o arquivo do repo e LF. Confira com `git ls-files --eol` antes de prever
> tamanho, ou preveja faixa em vez de numero exato. **E carrega tambem ONDE foi medido:** arvore de
> trabalho e blob do git nao sao a mesma coisa quando `core.autocrlf` esta ligado — a maquina converte
> no checkout arquivos que o `.gitattributes` marca so como `text=auto`, e o `wc -c` da arvore diverge
> do `git cat-file -s` do indice por 1 byte por linha. **Diga qual das duas pontas voce previu**; na
> duvida, preveja o blob, que e o que fica no repositorio. Ja custou um desvio de relatorio em que os
> numeros da WO estavam certos e a conferencia, feita na outra ponta, parecia errada.
> **Onde o numero absoluto e caro de simular, peca o COMANDO — nao o numero.** «Rode isto antes, rode
> depois, diga os dois valores e por que a diferenca e essa.» Transfere a aritmetica de quem ESCREVE, que
> nao tem o repositorio na mao, para quem APLICA, que tem — e produz o dado que a WO queria, em vez de um
> palpite conferido. **Regra de corte:** previsao que depende de somar parcelas de edicoes diferentes, ou
> de contar ocorrencias dentro de texto que a propria WO insere, e **cara** e vai como antes/depois;
> contagem de uma linha unica ancorada em `^` e **barata** e vai como numero. **Medido:** tres WOs
> seguidas erraram um numero absoluto — 4.915 linhas previstas contra 4.917 reais (numero tirado de uma
> medicao feita antes da ultima edicao), uma ocorrencia prevista 10 contra 9 reais (duas parcelas somadas
> de cabeca) e um negativo previsto 0 contra 1 real. So o terceiro e da classe que o `^` resolve. Regra
> por si so nao conserta defeito de POSICAO: a checklist e escrita por ultimo, com o trabalho ja
> mentalmente concluido, e e ali que a aritmetica de quem nao tem o repo falha.
> **Checagem negativa vai ancorada em `^`.** Sem excecao. O texto que uma WO insere quase sempre cita a
> frase que ela manda conferir, e a cita no MEIO de uma linha, dentro de uma explicacao: `grep -c "frase"`
> = 0 falha ai, `grep -c "^frase"` nao. A regra em prosa do paragrafo acima ja existia e foi violada pela
> WO que a leu — forma mecanica nao depende de o autor lembrar, no fim, do que escreveu no meio.
> **Quando o `grep` nao serve, diga que a checagem e DE LEITURA.** Prosa quebra em varias linhas, e uma
> frase que a propria WO escreveu em duas nao e encontrada inteira por padrao nenhum de linha unica —
> **ja derrubou um check deste repositorio**, que exigia uma frase contigua e a recebeu partida. As
> saidas, nesta ordem: escolher como padrao um **trecho curto que caiba numa linha** e que o texto novo
> nao cite; ou, nao havendo, **escrever que aquele item e de leitura** — «abra o arquivo e confira que o
> paragrafo X esta inteiro» —, porque a lista de conferencia tem o direito de mandar abrir o arquivo.
> Inventar um padrao que nao casa e pior que admitir que ali nao cabe `grep`.
> **Padrao de conferencia e RECORTADO, nunca redigitado.** O padrao do `grep` sai por copia do texto da
> ancora citada nesta mesma WO; o comando do par negativo sai do comando que voce de fato rodou. Padrao
> que voce nao consegue recortar de uma ancora e sinal de que a conferencia mede outra coisa. Ja custou
> duas vezes: um `grep` pedido com dois espacos de indentacao tendo a linha certa, com quatro, citada
> tres paragrafos acima; e um par negativo prescrito com uma edicao quando o teste que rodou fizera tres.
> **Valor exigido por uma instrucao declara ONDE NASCE.** Numero: o comando que o produz. Contagem: a
> unidade (linha ou ocorrencia). Carimbo de hora: `date +%y%m%d-%H%M`, rodado na hora. Resultado de
> terceiro: de quem, e em que artefato ele ja esta escrito. Valor exigido sem fonte e preenchido por
> deducao — e saida deduzida e indistinguivel de saida medida no ponto onde e ESCRITA; as duas so se
> separam no ponto onde e USADA, tarde demais.
> **A string contada e EXCLUSIVA do texto que a WO insere.** Se ela aparece tambem noutro ponto do
> arquivo, o numero previsto e da intencao, nao do arquivo — quatro contagens seguidas erraram assim
> num projeto vizinho, todas por uma string generica que ja existia la. O comando antes/depois resolve
> o VALOR; esta regra resolve o ALVO, e os dois defeitos sao diferentes.
> **Comando de conferencia que voce nao rodou no ambiente de quem aplica vai marcado «nao testado».**
> Um `grep` de fim de linha devolveu o oposto do prometido noutra plataforma, e so nao virou ciclo
> perdido porque quem aplicou montou um controle sozinho. Marcado, o vermelho dele e lido como suspeita
> do instrumento, nao da aplicacao.
> **Esperado deduzido nao e condicao de parada.** Valor que voce deduziu e nao mediu (um status HTTP,
> um total) vai rotulado «deduzido — relate o cru, nao pare»; so valor medido pode mandar parar.
> **Quando o numero absoluto e inevitavel, escreva-o como PISO** («se der menos que 126, PARE»): protege
> contra perda sem depender de acertar o total. **E rede ja vermelha nao e rede:** se lint ou build ja
> falham antes da WO, o criterio e o DELTA — meca o baseline (`git stash`, rode, `git stash pop`),
> compare antes e depois, e nomeie cada erro novo.
> **Referencia a outro documento cita o TRECHO literal, nunca numero de linha ou de secao.** Trecho
> falha alto quando o documento muda; numero falha em silencio e parece preciso enquanto esta errado.
> Vale para comportamento de arquivo de terceiro (CSS, configuracao de biblioteca): o conserto cita a
> regra que ele vence, com o seletor ou a chave literal — afirmar cascata sem abrir o arquivo ja
> declarou resolvido o que nao estava.
> **Simule a WO a partir do PROPRIO TEXTO dela.** Aplique as edicoes numa copia do repositorio lendo-as
> do arquivo da WO — nao da lembranca nem do script que as gerou — e compare com o que foi testado. Ja
> pegou uma linha em branco que o bloco cercado perdeu e um saldo que esquecia as linhas da propria WO.
> **O bloco de commit da WO nao traz rodape de coautoria.** Quem commita poe o seu: o modelo e a sessao
> sao de quem aplica, e um rodape escrito por quem redigiu e trocado na aplicacao.
> **Proximo comando:** o comando que o usuario deve rodar quando esta WO fechar em verde — ou apague a linha.
> Ele vai CRU e SOZINHO na ultima linha do relatorio, sem frase de apresentacao: texto em volta esconde o comando.

> **Canal dos meta neste ciclo = CHAT** *(ou **CODE** — escolha um e apague o outro)*.
> Se **CHAT**: esta WO toca so codigo/config — nao faca append nos `meta/`; o chat entrega os
> documentos depois da validacao. Se **CODE**: esta WO E o registro — aplique os appends previstos
> e nao espere doc do chat. *Uma fonte por doc por ciclo; escolher errado aqui duplica conteudo.*
> **O banner decide quem APLICA, nao quem redige.** WO que traga edicao numerada num documento que o
> banner reserva ao chat e contraditoria: quem aplica PARA e pergunta, em vez de escolher um dos lados
> — escolher em silencio ja deixou o registro de uma WO inteira de fora.

---

## 1. Por que

[Uma a tres frases: a dor concreta, ou a causa raiz se for correcao. Quem aplica precisa saber o que
esta consertando para reconhecer quando o resultado sai errado. Se for correcao de defeito introduzido
por WO anterior, diga qual e assuma — historico honesto e o que impede repetir.]

## 2. Contexto factual *(so em WO de registro — apague em WO de codigo)*

[Os fatos que os textos das edicoes afirmam, na ordem em que aconteceram. Esta secao e a FONTE dos
blocos abaixo: fato que nao esta aqui nao deveria aparecer la. Marque o que foi **medido** e o que e
**deduzido** — inferencia sem rotulo vira fato na leitura seguinte.]

## Inventario — de onde saiu a lista de edicoes *(apague se a WO tem uma edicao so)*

[Quando as edicoes abaixo sao **todos os lugares** que precisam mudar, diga como voce achou esses lugares.
Lista feita de cabeca, ou herdada do texto de quem apontou o problema, ja custou caro: o que ficou de fora
fica invisivel dos dois lados, porque a correcao e a conferencia saem do mesmo inventario incompleto.]

- **Saiu do artefato, nao da memoria.** A pergunta e sempre "que lugares declaram esta grandeza?", feita ao
  codigo. Grepe o **fato**, nao a frase: o mesmo campo aparece com outro nome de variavel, e a mesma regra
  aparece parafraseada. Procure o termo literal, a parafrase, e as listas de pendencia.
- **Nao truncar.** Nada de `head`, nada de "os principais". Inventario paginado e inventario errado, e o
  item que ficou de fora e justamente o que ninguem vai procurar depois.
- **Declare quantos.** Escreva o numero de pontos encontrados — "onze lugares montam este caminho" — para
  que quem aplica possa **contestar a contagem antes de agir**. Ja foi assim que um inventario truncado foi
  pego: a WO dizia onze, o executor achou doze. A contagem e a rede; a proibicao do `head` sozinha nao pega.
- **E declare de QUE.** Numero de cobertura sem a unidade DENTRO dele nao e contestavel: «20/20
  comparados» media arquivos contra um pacote, e a conclusao «encerrado» falava do repositorio — duas
  coberturas diferentes, e a segunda nunca foi declarada. Escreva «20/20 arquivos do pacote comparados;
  varredura do repo: pendente», nao «20/20». A pergunta «quantos?» so e respondivel junto com «de que?»,
  e **no fim de um trabalho longo a segunda metade e a que se perde**.

---

## Edicao 1 — `caminho/real/do/arquivo.ext` · [o que muda, em cinco palavras]

**Ancora** *(diga ONDE fica: secao, funcao, item — nunca numero de linha)*:

```
[trecho literal e unico do arquivo vivo, copiado sem reformatar]
```

**Substituir por:**

```
[texto exato que entra]
```

> Variantes — use a que couber, sempre com a ancora acima: **Inserir IMEDIATAMENTE APOS** ·
> **Inserir IMEDIATAMENTE ANTES** · **Remover o bloco inteiro** · **Criar arquivo novo** (sem ancora;
> diga o que fazer se ele ja existir) · **MOVER**.
> **Mover e a edicao mais fragil que existe numa WO de doc, porque tem DUAS METADES:** a que escreve no
> destino e a que remove a estrutura na origem. A ancora precisa conter **as duas**, e a que falta e
> sempre a de apagar — ancorar so no ponto de insercao descreve metade da operacao e, ao pe da letra,
> produz conteudo duplicado ou duas estruturas aninhadas com o texto antigo preso entre elas. Se voce
> nao consegue ancorar a remocao, **quebre em duas edicoes numeradas** — remover primeiro, inserir
> depois — e diga na WO que sao as duas metades da mesma operacao.
> **Inserir so com ancora de LINHA INTEIRA.** Ancora que e so o comeco de uma linha longa pede a quem
> aplica que ache o fim de uma linha que ele nao ve inteira, e ja virou insercao do lado errado. Prefira
> **Substituir** com a ancora repetida dentro do texto novo: substituir nao tem lado. Linha em branco na
> BORDA do texto novo nao sobrevive ao bloco cercado — ponha-a no MEIO, entre a ancora e o texto.
> **Caso medido:** um script de aplicacao tratou «inserir apos» como «substituir» em tres edicoes; o
> saldo de linhas previsto pela WO acusou, e quem aplicou corrigiu antes do commit.
> **Ancora e texto novo sem linha em branco nas BORDAS.** A borda em branco casa uma linha a menos (ou a mais), o saldo
> «quase bate» e quem aplica racionaliza a diferenca. Recorte sem borda; saldo de linhas diferente do previsto e VERMELHO.

## Edicao 2 — `caminho/real/do/arquivo.ext` · [...]

[Repita. Uma edicao por bloco. Se um arquivo recebe mudancas distantes entre si, numere 2a/2b/2c em
vez de empilhar num bloco so — cada uma com a propria ancora.]

---

## Fora de escopo

[O que esta WO deliberadamente NAO faz, para que quem aplica nao "aproveite a viagem". Melhoria que
voce enxergou no caminho vira ideia no IDEAS ou outra WO — nao entra aqui.]

## Medicao previa *(so quando houver; nao e edicao)*

[So quando esta WO depender de um numero que a raia de planejamento nao pode ler. Diga O QUE contar e o
comando sugerido; peca de volta o valor e o comando que o produziu, sem interpretacao. Isto NAO tem ancora,
NAO tem commit e NAO muda arquivo — se a medicao contrariar o que a WO assume, PARE antes de editar e relate.]

## Armadilhas desta WO

[So quando houver. O que ja deu errado antes neste mesmo lugar e o que quem aplica pode quebrar sem
perceber: ancora que aparece duas vezes, arquivo com fim de linha CRLF (ancora multi-linha colada com
\\n nao casa), bloco gerado que sera reescrito, numero de check ja usado. Contra o CRLF a saida e
sempre a mesma: ancora de UMA linha nao tem quebra dentro, entao o fim de linha nao morde — para
inserir varias linhas, ancore em UMA so e diga se o texto novo entra antes ou depois dela.]

**Aviso e divida do autor, nao protecao do leitor.** Quando voce consegue descrever o modo de falha com
precisao suficiente para avisar, voce tem informacao suficiente para **eliminar** a falha — o aviso e a
prova de que o conserto era possivel. Antes de escrever «⚠ cuidado com X», responda: por que X nao foi
resolvido na ancora, no padrao do grep ou na ordem das edicoes? Se a resposta existir, conserte e apague o
aviso. So sobra aqui o que e **propriedade do arquivo ou do ambiente** e nao esta ao seu alcance: fim de
linha CRLF, bloco que sera regenerado, numero de check ja usado por outra WO em voo. **Caso medido:** uma
WO avisou que certa frase «nao e citada por nenhum texto inserido — conferido», e era falsa; o conserto
(ancorar o padrao em `^`) estava ao alcance de quem escreveu o aviso.

---

## Depois de aplicar — conferencia antes do commit

- [ ] `git diff` mostra **exatamente** os arquivos previstos, e nada alem.
- [ ] [Conferencia de forma especifica desta WO — ex.: "a entrada nova ficou dentro da secao certa".]
- [ ] **Se algum passo mede um termo com `grep -c`, o numero esperado foi simulado contra o texto FINAL
      de TODAS as edicoes desta WO?** Termo citado por duas edicoes conta 2, nao 1 — e o checklist que
      olha cada edicao isolada produz um VERMELHO falso, que para a aplicacao e gasta um ciclo. Quando um
      termo aparece em mais de uma edicao, declare: «esta frase e citada por duas edicoes; esperado = 2».
      E lembre que `grep -c` conta LINHAS: duas ocorrencias na mesma linha valem 1.
- [ ] **Se a WO declarou um inventario** ("onze lugares"), refaca a contagem no repo. Numero diferente:
      **PARE e reporte antes de editar** — a divergencia e o achado, nao um detalhe a acomodar.
- [ ] **O que esta tarefa criou FORA do repositorio ja foi fechado?** Processo, porta, servidor de
      desenvolvimento, arquivo temporario, download de teste. O que nao deu para fechar entra no
      relatorio **com o caminho** — nao como nota vaga.
- [ ] **WO de codigo:** o comando de validacao do projeto passa com **0 erros**. Se acusar erro,
      **PARE e reporte antes de commitar**.
- [ ] **WO so de doc:** nao precisa de build — a rede e o `git diff`.
- [ ] **Teste manual que a validacao NAO cobre** (obrigatorio quando a WO toca dado carregado ou UI).
      Cada passo de verificacao — nao cada item deste checklist — traz os tres campos abaixo. Passo
      sem os tres nao esta pronto para ser escrito:
      - **Quem roda:** por padrao, **quem aplica**. Vai ao dono o passo que toca **rede de terceiro**, o
        que **destroi algo fora do repositorio**, e o que exige **olho humano num renderizador** — abrir a
        tela e dizer o que aparece. O terceiro caso e excecao MEDIDA, nao preferencia: tres WOs adiaram
        conferencia de interface esperando que quem aplica a fizesse, e as tres falharam **por motivos
        diferentes** — extensao do navegador devolvendo a aba, depois captura de tela em branco por
        timeout. Saldo: zero conferencias. No mesmo periodo, dois roteiros escritos para o dono devolveram
        27 itens respondidos, e **o que decidiu foi esse contraste, nao o diagnostico de cada falha** — nao
        e preciso saber por que a ferramenta falha para parar de depender dela. Fora esses tres casos,
        leitura e operacao reversivel na mesma maquina nunca sao dele. E quando for dele, o passo chega com
        o comando exato, o que esperar ver, e o que fazer se vier diferente —
        **nunca peca um resultado que voce nao ensinou a produzir.**
      - **Quando o passo e do dono, ele nao e item de checklist: e ROTEIRO, e roteiro tem forma.** Sai da
        lista de quem aplica e vai para o fecho do chat, como bloco proprio. **Cinco linhas de
        cabecalho:** **Para** (quem, e com o que aberto) · **Por que** (o que a automacao nao cobriu,
        nomeando a WO) · **Formato** (cada item diz **o que se ve quando esta certo**, com numero quando
        existe numero) · **Tempo** (quanto dura num passe so) · **Estado** (commit, versao instalada e
        **onde esta o rollback vivo** — e a linha que decide se o dono pode mexer sem medo). **Tres
        secoes:** **Preparo** (o que abrir e deixar pronto antes de comecar, para o passe nao parar no
        meio), os itens, e **«o que este roteiro NAO testa»**, que impede «passou tudo» de ser lido como
        «esta tudo certo». **E fecha com «o que me mandar de volta»** — o contrato de retorno, dizendo em
        que forma a resposta volta (numero, sim/nao, print). **Sem ele o dono responde em prosa livre e
        alguem tem de perguntar de novo**, que e o atrito que o roteiro existe para evitar. Forma medida
        em campo: 27 itens respondidos em dois roteiros, contra zero em tres tentativas sem forma.
        **Tres regras de item.** (1) O item descreve o ESTADO FINAL, nao a acao: «deixe o arquivo sem
        a chave X, ainda valido como JSON», nunca «apague a linha» — a acao tem duas leituras, e a
        errada e a mais natural. (2) Estado intermediario so entra se for REPRESENTAVEL no modelo:
        escreva qual valor o representa; se nao houver, o item mede outra coisa. (3) O roteiro vai
        INTEIRO no corpo da resposta do chat, numerado — nunca «ver o fim da WO».
      - **Chega no ramo?** Uma linha nomeando o arquivo e a funcao por onde a execucao passa pelo codigo
        que esta WO mudou. Se voce nao consegue tracar essa linha, o passo nao verifica esta WO: verifica
        que o programa continua rodando. E o unico campo que da trabalho, e e o que separa conferir de
        parecer conferir.
      - **Esta e qual pergunta: «esta la?» ou «presta?»** Contagem, existencia e extensao sao propriedades
        do INVOLUCRO; a aptidao esta no conteudo. Diga qual das duas este passo NAO responde — 45 arquivos
        existindo, com a extensao certa e o indice batendo, ja passaram verdes estando destruidos por dentro,
        porque nenhum instrumento abriu um deles. Fechar a lacuna costuma custar pouco.
      - **Prova de vida:** quando "passou" se parece com "nada aconteceu", o passo precisa do par negativo
        que forca o sinal. Lista vazia so significa alguma coisa depois de voce ter visto a mesma checagem
        devolver um item. Teste novo: rode-o contra o codigo de ANTES — ele tem de falhar, no numero previsto;
        teste que passa antes da mudanca nao testa a mudanca.
      - **`grep` casa por LINHA.** Se a frase que voce mandou conferir esta quebrada em duas linhas — e o
        proprio texto que a WO insere costuma quebra-la —, o `grep` devolve zero e o passo acusa ausencia
        onde ha presenca. Conferir frase que atravessa linha pede `grep -Pzo`, `rg -U` ou uma ancora curta
        que caiba numa linha so. Vale a regra geral: **ausencia relatada por instrumento e uma afirmacao
        e precisa de prova, igual a qualquer outra** — antes de reportar «nao achei», confirme que o
        instrumento saberia achar.

## Relatorio de aplicacao *(quem aplica preenche ao terminar)*

O que foi feito · o que fugiu do texto literal da WO · arquivos tocados · resultado da validacao · o commit e o push. Escreva-o DEPOIS de resolver o push: relatorio anterior a decisao conta so parte da historia.
**Nao** substitua este relatorio pelo bloco de fecho do chat: aquele e da raia de planejamento, e trocar
relatorio por formulario perde justamente o que so quem aplicou viu.
Relatorio e log se gravam pela ferramenta de escrita de arquivo, nunca por `echo -e`/`printf`: o escape come a barra
invertida dos caminhos do Windows e grava byte invalido.

## Commit — blocos separados, mensagem SEM acento

**A propria WO entra no `git add`.** Ela e o registro do que foi feito; se cada WO versionar so a anterior, a ultima fica sempre nao rastreada — ja aconteceu tres vezes seguidas. Se ela ja estiver versionada, o `add` nao faz nada e isso NAO e erro.

```
git add [caminhos] [o caminho DESTA WO]
```

```
git commit -m "tipo(escopo): descricao no imperativo curto" -m "Corpo explicando o porque, sem acento."
```

```
git push
```

*Gerado pelo Kit de Contexto Universal v1.133.0 — 2026-11-03 — esta linha e do KIT: nao funda, substitua pela do pacote mais recente.*
