# INSTRUCTION_GUIDE — Como gerar instruções para o Atualizador Automático de Scripts (ASU)

> **Para quem é este documento:** a IA (ou pessoa) que vai GERAR arquivos de
> instrução. Ele é **autocontido** — tudo de que você precisa está aqui, sem
> depender de outros arquivos. Versão do formato: **1.0** · Guia v2, revisado
> em 2026-06-11 (ferramenta v0.4.0).

## 0. Formato da sua resposta (leia primeiro)

Quando pedirem uma "instrução ASU", responda com:
1. **UM único bloco de código `yaml`** contendo a instrução completa (nada de
   XML, nada de JSON, nada de vários blocos, nada de explicação no meio do YAML);
2. depois do bloco, **uma linha** com o comando de aplicação, ex.:
   `Salve como instrucao.yaml e rode: python -m src apply instrucao.yaml --root <RAIZ> --dry-run`

### Anti-padrões (NUNCA faça)
- ❌ Emitir **XML** ou qualquer formato que não seja YAML (JSON só se pedirem).
- ❌ Inventar campos (`location.type`, `file`, `target`, `line`…) — use SÓ os
  campos deste guia; o validador rejeita campos desconhecidos.
- ❌ Usar **número de linha** como localizador (não existe no formato).
- ❌ Repetir as âncoras `before`/`after` dentro do `new_content` (§4.1).
- ❌ Digitar a âncora "de memória": copie-a **caractere a caractere do arquivo
  real**, incluindo a indentação (§4.2).
- ❌ Repetir uma chave YAML no mesmo nível (dois `files:`) — o parser rejeita.
- ❌ Repetir `id` (de arquivo ou de modificação) — o validador rejeita.

## 1. O que é uma instrução

Um arquivo **YAML** que descreve modificações em arquivos de um projeto. A
ferramenta valida contra schema, mostra diff, cria backup e aplica com rollback
automático em falha. Fluxo do usuário:

```
python -m src validate instrucao.yaml
python -m src apply instrucao.yaml --root C:\projeto --dry-run   (revisão)
python -m src apply instrucao.yaml --root C:\projeto             (aplicação)
python -m src rollback <TIMESTAMP> --root C:\projeto             (desfazer)
```

## 2. EXEMPLO COMPLETO (use como gabarito de estrutura e estilo)

```yaml
format_version: "1.0"
generated_by: "claude"
generated_at: "2026-06-11T12:00:00"
description: "Trata divisão por zero (Python), ajusta config (JSON), reescreve seção (MD) e corrige função JS por contexto"

settings:            # opcional — estes já são os padrões
  backup: true
  dry_run: false
  stop_on_error: true
  encoding: "utf-8"

files:
  - id: "f_calc"
    path_mode: "relative"
    relative_path: "src/calculator.py"
    type: "python"
    modifications:
      - id: "m1"
        description: "divide() passa a rejeitar divisor zero"
        strategy: "replace_method"
        location:
          class_name: "Calculator"
          name: "divide"
        new_content: |
          def divide(self, a, b):
              """Divide a por b, com proteção contra divisão por zero."""
              if b == 0:
                  raise ValueError("Divisão por zero não é permitida")
              return a / b

  - id: "f_cfg"
    path_mode: "relative"
    relative_path: "config.json"
    type: "json"
    modifications:
      - id: "m1"
        description: "Sobe a versão"
        strategy: "set_json_path"
        location: { path: "app.version" }
        value: "2.0.0"
      - id: "m2"
        description: "Registra a feature nova"
        strategy: "append_json_array"
        location: { path: "features" }
        value: "logging"

  - id: "f_readme"
    path_mode: "relative"
    relative_path: "README.md"
    type: "markdown"
    modifications:
      - id: "m1"
        description: "Atualiza a seção de configuração"
        strategy: "replace_section"
        location: { heading: "## Configuração", include_heading: true }
        new_content: |
          ## Configuração

          Defina `LOG_LEVEL` e `SECRET_KEY` no arquivo `.env`.

  - id: "f_js"
    path_mode: "relative"
    relative_path: "web/app.js"
    type: "text"
    language: "javascript"
    modifications:
      - id: "m1"
        description: "Reescreve o corpo de initApp (só o miolo entre as âncoras)"
        strategy: "replace_context_block"
        location:
          before: "function initApp() {"
          after: "\n}"
        new_content: |2
            console.log("App iniciado");
            setupRoutes();
```

## 3. Tabela de estratégias

| Alvo | Estratégia | `location` | Conteúdo |
|---|---|---|---|
| Função Python (módulo) | `replace_function` | `{name}` (+`class_name` se aninhada em classe) | `new_content` |
| Método Python | `replace_method` | `{class_name, name}` — class_name **obrigatório** | `new_content` |
| Classe Python inteira | `replace_class` | `{name}` | `new_content` |
| Inserir após um ponto | `insert_after_pattern` | `{pattern, occurrence?}` (regex de linha) | `content` |
| Inserir antes de um ponto | `insert_before_pattern` | `{pattern, occurrence?}` | `content` |
| Trocar UMA linha | `replace_line_pattern` | `{pattern, occurrence?}` | `new_content` |
| Trocar um BLOCO (qualquer linguagem) | `replace_context_block` | `{before, after, occurrence?}` (literais) | `new_content` (só o miolo!) |
| Seção Markdown | `replace_section` | `{heading, include_heading?}` | `new_content` |
| Valor em JSON | `set_json_path` | `{path}` (`api.version`, `a.b[0].c`) | `value` |
| Acrescentar a array JSON | `append_json_array` | `{path}` | `value` |
| Remover nó JSON | `delete_json_path` | `{path}` | — |
| Substituir arquivo INTEIRO | `replace_file` | — | `new_content` |
| Criar arquivo NOVO | `create_file` | — | `content` |

Preferências: `.py` → estratégias Python (precisão semântica); `.json` →
estratégias JSON; **qualquer outra linguagem** (C#, C++, Java, JS/JSX/TSX,
GDScript, Rust, Go…) → `type: "text"` + `replace_context_block`/patterns, com
`language:` preenchido (informativo). Arquivo novo → `create_file`; reescrever
um inteiro → `replace_file` (prefira o cirúrgico quando possível).

## 4. ⚠️ As seis regras de ouro

### 4.1 `replace_context_block`: o `new_content` é SÓ O MIOLO
As âncoras `before` e `after` **permanecem no arquivo**. Repeti-las no
`new_content` é rejeitado pela ferramenta (duplicaria as linhas).

**Não use na borda do arquivo:** se o bloco-alvo começa na 1ª linha ou termina
na última, não há linha estável para `before`/`after`, e uma âncora vazia é
rejeitada pelo schema (`location.after: '' should be non-empty`). Nesse caso
ancore numa linha existente (`insert_before_pattern`/`replace_line_pattern`) ou
use a estratégia do tipo (`replace_section` p/ Markdown, `replace_function` p/
Python).

### 4.2 Copie as âncoras EXATAS do arquivo (indentação incluída)
A falha nº 1 de geração é âncora com espaços/indentação diferentes do arquivo
real (espaços onde o arquivo usa TAB, 4 espaços onde são 8…). A âncora é um
**literal**: copie do arquivo caractere a caractere. Se errar, a ferramenta
responde com a linha onde achou um trecho parecido e a forma exata — corrija a
âncora com o texto indicado.

### 4.3 `after` fecha no PRIMEIRO match — use âncora distintiva
Com `}` aninhado (C#, Java, JS…), um `after: "}"` curto fecha no delimitador
interno. Use o fechamento no nível certo (`"\n}"` = `}` na coluna 0;
`"\n        }"` = fechamento indentado de método C#) ou um trecho do código que
vem DEPOIS do bloco (ex.: a assinatura da próxima função).

### 4.4 Localizador deve ser ÚNICO; `occurrence` é exceção consciente
Se o `pattern`/`before` casa mais de uma vez sem `occurrence`, a ferramenta
REJEITA (evita modificar o lugar errado). Prefira tornar a âncora única
**ampliando o contexto** (âncora multilinha: inclua 1–3 linhas vizinhas) — só
use `occurrence: N` quando a repetição for intencional e você souber qual é.

### 4.5 Decoradores fazem parte da função
`replace_function`/`replace_method` substituem o nó COMPLETO: se a função tem
`@decorator` e o `new_content` não o repete, **o decorador some**. Reproduza os
decoradores que devem permanecer.

### 4.6 JSON: `set_json_path` cria intermediários
Um typo no caminho (`aip.version`) **cria** o galho errado em vez de falhar.
Confira o caminho letra a letra contra o arquivo real. `append_json_array` e
`delete_json_path` exigem caminho existente (valor `null` existe e é removível).

### 4.7 Âncoras em ASCII: não ancore em setas/box-drawing
Caracteres não-ASCII usados como literal na âncora (setas `→ ← ⟶`, traços
longos `— –`, box-drawing `│ ├ └ ─ ┌`, marcadores `• ◦`, aspas curvas `" " ' '`)
são uma fonte recorrente de "casou 0 vezes": variam por encoding, por cópia
entre editores e por normalização. Quando o trecho-alvo CONTÉM esses glifos:

- Em `pattern` (regex): use `.*` para saltar sobre o glifo e ancore em texto
  ASCII estável ao redor — ex.: em vez de `^├── src/` use `^.*src/`.
- Em `before`/`after` (âncora literal): recorte a âncora para começar/terminar
  num ponto ASCII — escolha a linha vizinha (ou o pedaço da linha) que não
  tenha o glifo. A âncora não precisa ser a linha inteira, só ser ÚNICA (§4.4).

Não é proibido casar um caractere Unicode (a ferramenta aceita), mas ancorar em
ASCII estável evita um round-trip de debug por um detalhe invisível.

## 5. Detalhes que evitam fricção

- **Indentação no YAML:** o bloco `|` remove a indentação comum; quando o
  conteúdo precisa começar indentado, use `|2`/`|4` (nº de espaços a
  preservar). Em GDScript use TAB real dentro do bloco.
- **Encoding:** alvos em UTF-8 (BOM ok — preservado) ou CP-1252; UTF-16 e
  binários são rejeitados. A instrução: UTF-8.
- **Caminhos Windows:** com aspas duplas escape `\\` ou use `/`. Prefira
  `path_mode: relative` (o usuário passa `--root`).
- **Regex em `pattern`:** regex Python aplicada **linha a linha** (`^`/`$`
  ancoram a linha); escape metacaracteres (`\.`, `\(`, `\[`).
- **Ordem:** modificações do mesmo arquivo aplicam em sequência, cada uma vendo
  o resultado da anterior.
- **JSON:** o estilo do arquivo (indentação/compacto) é preservado pela
  ferramenta — não reformate por conta própria.

## 6. Se o usuário colar um ERRO da ferramenta, corrija assim

| Erro contém… | Causa | Correção |
|---|---|---|
| `casou 0 vez(es)` + `é SUBSTRING de algo na linha N` | Âncora é parte de um nome maior, OU já aplicada | Use o nome COMPLETO indicado, ou remova a modificação se já aplicada |
| `provavelmente JA FOI APLICADA` | O conteúdo-alvo já está no arquivo | Remova esta modificação da instrução (não repita o que já foi aplicado) |
| `casou N vezes e 'location.occurrence' não foi especificado` | Localizador ambíguo | Amplie a âncora (multilinha) p/ ficar única, OU declare `occurrence` |
| `Encontrei um trecho parecido na linha X… indentação/os espaços diferem` | Âncora digitada com whitespace errado | Substitua a âncora pela linha exata indicada no erro |
| `casou 0 vez(es)` numa âncora que tem seta/box-drawing/aspas curvas | Glifo não-ASCII na âncora não casou (encoding/cópia) | Reescreva a âncora em ASCII: `.*` no `pattern`, ou recorte `before`/`after` p/ texto ASCII vizinho (§4.7) |
| `o new_content inclui as âncoras` | Miolo repetiu `before`/`after` | Remova as âncoras do `new_content` (deixe só o conteúdo entre elas) |
| `location.before`/`after` + `non-empty`/`is too short`/`minLength` | Âncora `before`/`after` vazia (bloco toca a borda do arquivo) | Ancore numa linha existente (`insert_before_pattern`/`replace_line_pattern`) ou use `replace_section`/`replace_function`; `replace_context_block` não serve na borda |
| `Âncora 'after' não encontrada depois de 'before'` | `after` não existe após o ponto, ou está antes | Escolha um `after` que ocorra DEPOIS do `before` no arquivo |
| `Heading '…' não encontrado. Headings encontrados: …` | Heading digitado diferente | Use exatamente um dos headings listados |
| `aparece N vezes no documento — localização ambígua` | Heading duplicado no MD | Peça ao usuário p/ tornar headings únicos, ou use outra estratégia |
| `chave duplicada no YAML` | Mesma chave 2× no mesmo nível | Remova a duplicata (una os conteúdos) |
| `id: "…" repetido` | IDs iguais | Renomeie para ids únicos (f1, f2…/m1, m2…) |
| `Esperava objeto/lista … no caminho` | Caminho JSON não bate com a estrutura | Confira o caminho contra o JSON real |
| `não é Python válido` | `new_content` com sintaxe quebrada | Corrija a sintaxe (indentação consistente, def completo) |
| `parece arquivo binário` | Caminho aponta p/ binário (ou UTF-16 sem BOM) | Confira o caminho; converta o arquivo p/ UTF-8 se for texto |
| `Campo obrigatório ausente` / `não é um dos valores permitidos` | Campo faltando/insuficiente | Compare com o exemplo da §2 e a tabela da §3 |

## 7. Checklist de autovalidação (rode mentalmente antes de emitir)

1. Resposta = 1 bloco `yaml` + 1 linha de comando? (§0)
2. `format_version: "1.0"` e `description` presentes?
3. IDs únicos (arquivos entre si; modificações dentro do arquivo)?
4. Cada `strategy` com o campo certo (`new_content` × `content` × `value`) e o
   `location` no formato da tabela?
5. Âncoras copiadas do arquivo real, com indentação exata?
6. Nenhuma âncora dentro do `new_content`?
7. `after` distintivo onde há `}` aninhado?
8. Localizadores únicos (ou `occurrence` consciente)?
9. Decoradores reproduzidos?
10. Caminhos JSON conferidos letra a letra?
11. `|2`/`|4` onde o conteúdo precisa de indentação inicial?
12. Caminhos de arquivo relativos à raiz do projeto?

## 8. Verificação pós-aplicação (quando o usuário voltar com os arquivos)

Esta seção vale para a IA na sessão **seguinte** — quando o usuário, depois de
aplicar uma instrução ASU, sobe de novo os arquivos do projeto (o fluxo normal
de quem usa o kit de contexto). É uma prática validada na indústria: agentes de
código geram "linguagem de conclusão" ("pronto, apliquei") como padrão de
saída, **independentemente do estado real** dos arquivos — então a verificação
tem de olhar o **arquivo no disco**, nunca confiar no relato. (Pesquisa:
verificação *outcome-based* supera a checagem por transcrição; ver IDEAS.)

**Regra:** se na conversa anterior você emitiu uma instrução ASU e agora tem os
arquivos do projeto à vista (mount/anexo), **confira cada arquivo que a
instrução tocou** antes de seguir — mesmo que o usuário não reclame de nada.
Isso pega discrepâncias silenciosas (a mudança foi aplicada no lugar errado, ou
não foi aplicada) nos primeiros usos, que é exatamente quando a confiança no
fluxo está se formando.

Como verificar (rápido, sem alarde):
1. Para cada `file`/`modification` da instrução anterior, abra o arquivo real e
   confirme que o conteúdo esperado está lá (a função nova, o valor JSON novo, a
   seção reescrita) e que o resto ficou intacto.
2. Se bateu: diga em UMA linha que conferiu e está coerente, e siga a tarefa
   atual. Não encha de relatório quando está tudo certo.
3. Se NÃO bateu (ou o arquivo não mostra a mudança): aponte o arquivo e a
   modificação específicos, mostre o que esperava × o que encontrou, e proponha
   a correção (uma nova instrução, ou o ajuste manual). Trate como possível
   discrepância de aplicação, não como erro do usuário.

> Por que olhar o disco e não perguntar "deu certo?": o usuário pode não ter
> percebido uma mudança sutil aplicada no lugar errado. A verificação no
> arquivo é barata e é a única que pega esse caso.
