# PROMPT_IA — Bloco pronto para colar no contexto de outros projetos (v2)

> **Como usar:** copie o bloco entre as linhas `─────` para as instruções do
> seu projeto (Claude Project, system prompt, CLAUDE.md…), e suba o arquivo
> `INSTRUCTION_GUIDE.md` na base de conhecimento. A partir daí, peça:
> *"emita uma instrução ASU para estas mudanças"*.

─────────────────────────────────────────────────────────────────────────────

## Saída de código via Atualizador Automático de Scripts (ASU)

Este projeto usa o **ASU**: uma ferramenta que aplica modificações de código a
partir de um arquivo de instrução **YAML** (`format_version: "1.0"`). O
documento **`INSTRUCTION_GUIDE.md`** (na base de conhecimento) é a referência
completa e obrigatória: esqueleto, exemplo completo, tabela de estratégias,
seis regras de ouro, tabela de correção de erros e checklist.

Quando eu pedir uma "instrução ASU" (ou ao entregar várias mudanças em
arquivos existentes):

1. **Responda com UM único bloco `yaml`** (nunca XML; nunca JSON salvo pedido;
   nunca trechos soltos) + **uma linha final** com o comando:
   `Salve como instrucao.yaml e rode: python -m src apply instrucao.yaml --root <RAIZ> --dry-run`
2. Siga o guia à risca; **não invente campos** (não existe `location.type` nem
   localização por número de linha).
3. Modificações **cirúrgicas** primeiro (função/método/seção/caminho JSON);
   `create_file` para arquivos novos; `replace_file` só quando reescrever tudo
   for inevitável.
4. Linguagens sem estratégia semântica (C#, C++, Java, JS/JSX/TSX, GDScript…):
   `type: "text"` + `replace_context_block`, lembrando que:
   - `new_content` é **só o miolo** (as âncoras permanecem no arquivo);
   - âncoras são **literais copiados do arquivo real, com a indentação exata**;
   - `after` deve ser **inequívoco** (`"\n}"`, fechamento indentado, ou a
     assinatura do bloco seguinte) — nunca `"}"` solto havendo aninhamento;
   - localizador deve casar **uma única vez**; amplie a âncora (multilinha) em
     vez de recorrer a `occurrence`, que é exceção consciente.
5. Reproduza **decoradores** ao substituir funções/métodos Python decorados.
6. Confira caminhos JSON letra a letra (`set_json_path` cria intermediários).
7. Se eu colar um **erro** do `validate`/`apply`, use a tabela da §6 do guia
   para emitir a instrução corrigida (a ferramenta foi desenhada para esse
   loop de autocorreção).
8. Antes de emitir, percorra o **checklist** da §7 do guia.
9. **Verificação na próxima vez:** se eu já apliquei uma instrução ASU sua na
   conversa anterior e agora os arquivos do projeto estão à vista, **confira no
   disco cada arquivo que a instrução tocou** antes de seguir (§8 do guia) —
   mesmo que eu não reclame. Não confie em "deu certo": olhe o arquivo. Se bateu,
   uma linha confirmando basta; se não bateu, aponte o arquivo/modificação e
   proponha a correção.

Se a mudança for grande demais para uma instrução (refactor amplo, renomeações
em massa), diga isso e proponha dividir em instruções menores.

─────────────────────────────────────────────────────────────────────────────
