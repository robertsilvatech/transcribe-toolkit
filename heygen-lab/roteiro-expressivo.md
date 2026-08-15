# Roteiro orientado à expressão — como escrever pro TTS falar bem

> Guia pro pipeline `heygen-lab generate --el` (ElevenLabs **eleven_multilingual_v2**,
> voz profissional do Robert). O insight que originou isto: o mesmo texto, corrido
> numa linha só, sai apressado; separado em blocos, sai com respiração. **A
> formatação do texto é a partitura da fala.**
>
> Pra copiar pro course-studio quando estabilizar.

---

## A regra de ouro

O modelo lê a **estrutura**, não só as palavras. Ele decide ritmo, pausa e
entonação a partir de pontuação, quebras de linha e contexto. Escrever pra TTS
é escrever a *performance*, não o *conteúdo*.

## Técnicas que funcionam no nosso modelo (validadas na doc oficial)

| Técnica | Efeito | Exemplo |
|---|---|---|
| **Um bloco por ideia** (linha em branco entre frases) | respiração natural entre blocos — a descoberta do Robert | ver antes/depois abaixo |
| **Ponto final** em vez de vírgula | pausa de verdade; vírgula é só meio-fôlego | "Já comemos. Já dormimos." > "já comemos, já dormimos" |
| **Reticências `...`** | hesitação, suspense, beat cômico | "Você vira de lado... e mudamos de canal" |
| **Travessão `—`** | pausa curta, quebra de expectativa | "Espera — que barulho é esse?" |
| **`<break time="1.0s" />`** | pausa explícita e controlada (até 3s) | entre o gancho e a cena de um reel |
| **`?` e `!`** | entonação sobe / energia | "Por aí também acontece?" |
| **UMA quebra de linha depois de `?`** | a entonação da pergunta aterrissa antes da próxima frase; inline fica estranho, e quebra DUPLA vira pausa demais (regra do Robert, validada de ouvido) | "Beleza?\nPronto pra curtir...?" |
| **Número por extenso** | evita leitura imprevisível | "às nove da noite", "Bar Setenta e Cinco" |
| **`speed` na API** (0.7–1.2) | andamento global sem reescrever | 0.95 pra narração didática |

### ⚠️ Cuidados

- **Não abusar do `<break>`**: a doc avisa que muitos numa geração só causam
  instabilidade — "the AI might speed up, or introduce additional noises".
  Regra prática: pontuação e blocos primeiro; `<break>` só onde precisar de
  pausa cirúrgica (1 ou 2 por reel).
- **Contexto narrativo** ("— disse animado") influencia a entrega, mas o modelo
  pode LER a rubrica em voz alta. No nosso pipeline (áudio vai direto pro
  avatar, sem edição), **evitar**.
- **O que NÃO funciona no multilingual v2**: audio tags `[excited]`,
  `[whispers]`, `[pause]` — isso é do **eleven v3**, outro modelo (a voz
  profissional ainda não roda nele). Se um dia migrar, este guia ganha um
  capítulo novo.

## Settings da voz (o que o `--el` manda hoje)

```json
{"stability": 0.5, "similarity_boost": 0.8, "style": 0.3}
```

Guia de ajuste por tipo de conteúdo (fonte: práticas da comunidade + doc):

| Conteúdo | stability | style | Racional |
|---|---|---|---|
| Reel energético (hook forte) | 0.35–0.45 | 0.3–0.45 | mais variação = mais humano |
| Narração didática (curso) | 0.6–0.8 | 0.1–0.2 | consistência > emoção |
| Institucional CdP | 0.5 | 0.2–0.3 | meio-termo |

`style` acima de ~0.6 distorce fonética — não subir.

## Antes / depois (o exemplo do Robert)

**Antes — corrido, sai apressado:**

```
Esse é mais um teste de Avatar, hoje meu amor foi na nutricionista, bora ficar fitness.
```

**Depois — blocos + pontuação, sai com respiração:**

```
Esse é mais um teste do Avatar.

Hoje meu amor foi na nutricionista... já vai vir com a dieta pra gente.

Bora ficar fitness!
```

O que mudou: 1 ideia por bloco · vírgulas viraram pontos · reticências criam o
beat antes da piada · exclamação dá a energia do fecho.

## Template de reel (estrutura T01 como referência)

```
[gancho — frases curtas, pontos finais]
Meu Pod não subia de jeito nenhum. E o problema não era o Kubernetes. Era o meu dedo.

<break time="0.8s" />

[cena — ritmo de história]
Eu tinha escrito o nome da imagem errado. Em vez de nginx com i, eu digitei com e.

Uma letra.

[método — didático, sem pressa]
Olha só o que resolve: kubectl describe no Pod... e desce até os eventos.

[payoff — devolve a responsabilidade]
Antes de investigar cluster, lê o evento.
```

Repare: "Uma letra." sozinho num bloco É a pausa que a nota de gravação pedia.

## Checklist antes de gerar

- [ ] Uma ideia por bloco, linha em branco entre eles
- [ ] Vírgula só onde tem meio-fôlego real; resto vira ponto
- [ ] Números e siglas por extenso ("cê i", "nove da noite")
- [ ] Termos técnicos: conferir se estão no `pronuncia.yaml`
- [ ] Máx 1–2 `<break>` por peça, só onde a pontuação não resolve
- [ ] Sem rubrica narrativa ("disse sorrindo") — o modelo pode ler
- [ ] Ouvir antes de mandar pro HeyGen — áudio é centavos, vídeo é caro

## Fontes

- [ElevenLabs — Best practices (doc oficial)](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices) — break tags, pontuação, contexto narrativo, aviso de instabilidade
- [Audio tags 101 (v3)](https://elevenlabs.io/blog/v3-audiotags) — só pra saber o que NÃO se aplica ao v2
- [ElevenLabs voice settings deep dive](https://www.nassamn.dev/blog/elevenlabs-voice-settings-deep-dive) e [guia NeuraPulse 2026](https://neuraplus-ai.github.io/blog/best-settings-for-elevenlabs-ai-voice-quality-improvement-2026.html) — faixas de stability/style por tipo de conteúdo
- Medição própria: pacing também herda do **material de treino** da voz (a doc confirma: "voice pacing depends heavily on the audio used to create the voice") — a nossa foi treinada em aula, então puxa pro didático; hooks pedem style um pouco mais alto
