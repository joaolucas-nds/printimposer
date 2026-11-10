# SPEC — F5 etapa 1: arrastar (v1.7.0)

> Spec de feature. Escrita em 2026-11-10, depois da decisão da ordem da F5 (`meta/analises/261109-ANALISE-ordem-f5.md`, escada C) e da medição `probe-f5`.
> Alvo: v1.7.0. Estado: aprovada pelo plano da escada C, a implementar — pelo Claude Code, via `meta/workorders/261110-wo0012-f5-arrastar.md`.
> Cobre o item «manipulação por arraste» do critério de conclusão da F5.

## Problema

Para pôr imagens na lista, hoje só existem os diálogos «+ Arquivos» e «+ Pasta». Quem já está com a pasta aberta no Explorer tem de navegar de novo até ela no diálogo. O dono sentiu falta de arrastar direto (nota de 07/11). Reordenar também é lento: com 20 itens, levar o último para o topo custa 19 cliques em ▲.

E há uma pendência pequena da 1.6.0. Quando a margem externa é maior que zero mas menor que a sangria, a sangria da borda da folha é recortada **sem aviso** (achado da sonda da wo0010).

## Fundamento (medido em 10/11)

| Achado | Fonte | Aplicação |
|---|---|---|
| `class Win(ctk.CTk, TkinterDnD.DnDWrapper)` + `TkinterDnD._require(win)` carrega o tkDnD 2.10.3 no Python 3.13.13 do dono, e um `CTkFrame` filho registra `DND_FILES` sem erro | relatório `261110-1206-code-printimposer-probe-f5.txt` | mixin na janela principal (DEC-016) |
| O tkDnD entrega os caminhos numa lista Tcl, com chaves em volta dos que têm espaço (`{C:/minha pasta/a.png}`) | código do `tkinterdnd2` | separar com `self.tk.splitlist(event.data)`, nunca com `split()` |
| A entrada já passa por um funil único: `plan_ingest(paths, confirm_many)` | `print_imposer.py` | o arrastar só produz a lista de caminhos; ingestão, PDF e pulados ficam como estão |

## Critérios de aceite (verificáveis)

### Soltar arquivos e pastas
- [ ] Com o `tkinterdnd2` instalado, arrastar arquivos ou pastas do Explorer e soltar **em qualquer ponto da janela** adiciona-os ao fim da lista, pelo mesmo caminho do «+ Arquivos» (PDF vira uma página por item; mais de 50 páginas pedem confirmação; PDF ilegível é pulado com aviso).
- [ ] Pasta solta entra como no «+ Pasta»: só os arquivos de formato suportado do primeiro nível, **sem subpastas**.
- [ ] Ordem: os itens soltos são ordenados pelo nome, sem diferenciar maiúscula (a mesma regra do «+ Pasta»). Cada pasta é expandida no lugar dela.
- [ ] Arquivo de formato não suportado entra na mensagem «Arquivos pulados», que já existe, com o motivo `formato não suportado`. Ele não some em silêncio.
- [ ] Se nada do que foi solto puder entrar, nem pular com motivo (ex.: uma pasta vazia), aparece a mensagem «Nada encontrado», como no «+ Pasta».
- [ ] Soltar **não muda** a pasta de entrada lembrada (`input_dir`) nem a de saída.
- [ ] Enquanto o arraste passa sobre a janela, a lista dá retorno: a moldura da lista acende na cor de destaque e o texto de rodapé dela vira «Solte para adicionar à lista». Ao soltar ou ao sair da janela, tudo volta ao normal.
- [ ] Soltar durante uma geração é permitido: a geração trabalha sobre cópias congeladas (1.4.1) e não é afetada.
- [ ] **Sem o `tkinterdnd2`, ou se o tkDnD não carregar**, o app abre e funciona igual à 1.6.0. O cabeçalho mostra `Arrastar: indisponível` e o rodapé da lista vazia mantém o texto de hoje.
- [ ] Com ele, o cabeçalho mostra `Arrastar: tkinterdnd2` e a lista vazia diz «Nenhuma imagem — arraste arquivos ou pastas para cá». `Ajuda › Sobre` ganha a linha «Arrastar e soltar: sim/não».

### Reordenar arrastando
- [ ] Cada linha da lista ganha uma **alça** `≡` à esquerda da miniatura, com cursor de mover (`fleur`).
- [ ] Apertar na alça e arrastar leva a imagem para a posição da linha sob o ponteiro; durante o arraste, essa linha fica com a borda acesa na cor de destaque. Soltar fora da lista, ou na própria linha, não muda nada.
- [ ] Só a alça inicia o arraste: clicar no campo «Qtd», nos botões ou na miniatura continua fazendo o que faz hoje.
- [ ] ▲ ▼ e ✕ continuam.
- [ ] Depois de soltar, a lista, a quantidade total, o preview e o contador de folhas refletem a nova ordem (o mesmo `on_change` das setas).
- [ ] Não depende do `tkinterdnd2`: funciona com ele ou sem ele.

### Aviso de sangria externa
- [ ] Com sangria > 0 e margem externa **maior que 0 e menor que a sangria**, `sheet_geometry` devolve um aviso âmbar: «A margem externa (X mm) é menor que a sangria (Y mm): na borda da folha, a sangria vai só até X mm.» Como os outros avisos âmbar, ele aparece na seção e pede confirmação antes de gerar.
- [ ] Com margem externa **0** não há aviso: a célula encosta na borda do papel e não há corte externo a proteger.

### Geral
- [ ] Suíte verde com os testes novos; `/smoke` sem FALHOU.

## Decisões de design

### 1. Alvo do soltar: a janela inteira
O tkDnD entrega o evento ao widget sob o ponteiro, se ele estiver registrado. As linhas da lista são destruídas e recriadas a cada mudança. Registrar só a lista obrigaria cada linha nova a se registrar também, o que é mais superfície para errar sem ganho para o usuário. **Registra-se a janela principal** (DEC-016). Soltar sobre o preview ou sobre o painel de configuração também adiciona à lista, e a lista acende para mostrar onde os arquivos vão.

### 2. Capacidade provada, não importada
Seguindo a FIX-002: importar o `tkinterdnd2` não basta. O app só liga o recurso depois que `TkinterDnD._require(self)` devolve uma versão, dentro de `try`. Se falhar, o recurso fica desligado e nada mais muda. A classe da janela usa `DnDWrapper` como base só quando o import funcionou; sem o pacote, a base é `object` (ou nenhuma extra).

### 3. Funções puras para o que dá para testar sem tela
- `expand_dropped(paths) -> (arquivos, pulados)`: expande pastas (primeiro nível, formatos suportados), ordena pelo nome, separa os não suportados com o motivo `formato não suportado` e ignora caminho que não existe. Sem Tk.
- `move_item(lista, origem, destino)`: tira o item da origem e o insere no destino; índices fora da faixa, ou origem igual ao destino, não mudam nada. Sem Tk.
- A conversão do `event.data` em lista usa `self.tk.splitlist` dentro do handler, porque precisa do Tcl.

### 4. Reordenar em Tk puro
`<ButtonPress-1>`, `<B1-Motion>` e `<ButtonRelease-1>` na alça. A linha de destino sai de `winfo_containing(x_root, y_root)`, subindo pelos pais até achar uma `ImageRow`. **Sem autorrolagem** nesta versão: para trajetos longos, as setas continuam. Se a roda do mouse rolar a lista durante o arraste, ótimo, mas não é critério.

### 5. Nomes do Tkinter
A janela passa a misturar `DnDWrapper`, que usa `self._w` legitimamente. Nada novo do app grava em nome reservado do Tk (FIX-003, armadilha 3). Atributos novos levam prefixo (`_dnd_ok`, `_drag_src`…).

## Fora de escopo
- Arrastar da lista **para fora** (exportar arrastando).
- Autorrolagem durante a reordenação.
- Seleção múltipla na lista.
- Soltar texto ou URL (só arquivos e pastas).
- Subpastas ao soltar uma pasta.
- Empacotamento (`.exe`) — vai para a 1.10.0.

## Passos
1. `expand_dropped`, `move_item` e o aviso novo em `sheet_geometry`, com testes.
2. Probe do `tkinterdnd2` no topo do módulo (import guardado) e mixin condicional na `PrintImposerApp`; `_require` no `__init__`.
3. Registro da janela, handlers `<<DropEnter>>`/`<<DropLeave>>`/`<<Drop>>`, retorno visual na lista, ingestão por `_ingest`.
4. Alça e reordenação na `ImageRow` / `ImageListPanel`.
5. Cabeçalho, Sobre e texto da lista vazia.
6. README, `/smoke` e roteiro do dono.
