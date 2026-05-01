## Context

Hoje `yt_transcribe/` contém 7 arquivos — 4 do módulo de transcrição e 3 do módulo de tradução. O `config.py` e `translator.py` não pertencem a `yt_transcribe`. Cada módulo deve ser uma pasta independente na raiz.

## Goals / Non-Goals

**Goals:**
- Separar `translate/` como pacote independente na raiz
- Cada módulo autônomo — sem dependências cruzadas, sem pasta `shared`
- `config.yaml` é do projeto (raiz), cada módulo lê sua seção
- AGENT.md e README.md refletem a arquitetura modular
- Regra documentada: sempre questionar se feature pertence a módulo existente ou novo

**Non-Goals:**
- Mudar funcionalidade dos CLIs
- Separar em repos diferentes
- Criar abstrações compartilhadas

## Decisions

### 1. Cada módulo é um pacote Python na raiz

**Decisão:** `yt_transcribe/` e `translate/` são pacotes separados, cada um com `__init__.py` e `cli.py`.

**Rationale:** Sem dependências cruzadas. Cada módulo importa apenas suas próprias coisas. O `pyproject.toml` único gerencia ambos com entry points separados.

### 2. config.yaml é do projeto, não de um módulo

**Decisão:** `config.yaml` fica na raiz. Cada módulo que precisa de config tem seu próprio `config.py` que lê a seção relevante (`translate:`, e futuramente `insights:`, etc.).

**Rationale:** Sem pasta `shared/`. Se outro módulo precisar de config, cria seu próprio loader com 20 linhas de código. Evita acoplamento.

### 3. AGENT.md como guia de arquitetura modular

**Decisão:** AGENT.md documenta a regra: "cada módulo é uma pasta na raiz, sempre perguntar se feature é módulo novo ou existente antes de implementar".

## Risks / Trade-offs

- **Duplicação do config loader** → Trade-off aceito. São ~20 linhas de código e cada módulo lê seção diferente. Melhor duplicar do que acoplar.
