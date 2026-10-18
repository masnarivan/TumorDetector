# Training multi-centro e teste per tessuto — progetto

Stato: **progetto approvato nelle scelte principali**, 18/10/2026. Implementati: manifest (paziente
unificato, `file_format`), specifica della testa e cohort con ruoli e fold (`td task=cohort`),
training della testa senza mitigazioni con temperatura globale, probe e Robustness Index nel gate
(`td task=train_head`, protocollo di E6). Mancano le mitigazioni (E7) e il task del test esterno. I
protocolli degli esperimenti (E6, E7) passano in [esperimenti.md](esperimenti.md) prima di vedere i
risultati, con le soglie di adozione.

## Decisioni (18/10/2026)

| Tema | Decisione |
|---|---|
| Split | Tutto CAMELYON16 (test ufficiale compreso) + CAMELYON17 di Radboud, Utrecht, CWZ, Rijnstate in sviluppo; **LPON esterno bloccato** |
| Mitigazioni da confrontare | `balanced`, `group_dro`, `stat_mix`. L'avversariale (DANN) non entra in questa tornata |
| Teste future | Ricetta di mitigazione dentro ogni testa; nessun adapter condiviso per ora |
| Gruppi | Bilanciamento e DRO sui **domini** (dataset × centro); leave-one-centre-out per centro intero |
| Calibrazione | **Solo globale**: il modello deve reggere su un centro nuovo senza vetrini di quel centro. Nessuna ricalibrazione per centro all'installazione |
| Robustezza nel gate | Soglie subito, primo gradino permissivo: probe sul centro ≤ 0,80, Robustness Index ≥ 0,5; da stringere dopo E7 |
| Test esterno | Bloccato dal codice: una consultazione per versione, solo versioni `validated` |
| Punto cieco della griglia | Non prioritario: griglia invariata, i vetrini noti riportati come sottogruppo |

## Da dove partiamo

- **Il centro è leggibile ovunque** negli embedding Phikon (E2: AUROC 1,000 da una singola tile di
  tessuto normale; i 10 vicini di una tile sono tutti dello stesso centro). È il "foundation model che
  impara il centro": il backbone è congelato, quindi la mitigazione va fatta nelle teste.
- **Il baseline ABMIL non è calibrato su un centro mai visto** (gate fallito sull'ECE e sulla
  specificità del centro escluso). Con due centri il leave-one-centre-out ha due sole rotazioni e
  l'addestramento ne vede uno solo: è il caso peggiore possibile per qualunque mitigazione.
- **La normalizzazione per vetrino non funziona** (E4): sposta l'errore tra i centri e costa 0,05 di
  AUROC dell'attenzione. Non va riproposta.
- **Il dominio non è solo il centro** (E3b): dentro Radboud i casi metastatici del 2015 sono un
  dominio a parte; `normal_144` è una conversione diversa (C17 §4); LPON ha 5 scanner (C17 §2).
- **CAMELYON17 è usabile** (C17): 500 vetrini estratti con Phikon, stessa versione del backbone di
  CAMELYON16 (`phikon__057cc0295895`), annotazioni allineate, nessun duplicato con CAMELYON16.

Dati disponibili per la testa linfonodo (ITC escluse dal binario, come già stabilito):

| Centro | Scanner | CAMELYON16 (neg / pos) | CAMELYON17 (neg / pos, ITC escluse) | Totale |
|---|---|---|---|---|
| Radboud | 3DHistech (C16 riconvertiti) | 150 / 95 | 64 / 25 | 334 |
| Utrecht | Hamamatsu | 89 / 65 | 75 / 23 | 252 |
| CWZ | 3DHistech | — | 58 / 35 | 93 |
| Rijnstate | 3DHistech | — | 60 / 32 | 92 |
| LPON | Philips (5 scanner) | — | 61 / 31 | 92 |

## Principi

1. **Più centri prima di qualunque trucco.** La prima misura è il baseline invariato addestrato su
   tutti i centri: spesso la diversità dei dati da sola fa più delle mitigazioni. Ogni mitigazione
   si giudica contro quel baseline, non contro quello su CAMELYON16.
2. **La mitigazione è una ricetta di training, non un pezzo del modello in esercizio.** Il modello
   registrato resta "tile → logit + attenzione" come oggi; discriminatori, pesi per gruppo e
   aumentazioni restano nel training. Il contratto di inferenza non cambia al variare della ricetta.
3. **Ogni testa è autonoma** (piano: moduli aggiornabili e validabili in modo indipendente). Le
   mitigazioni sono una libreria condivisa; ogni testa le istanzia per sé e ha la propria batteria.
   Niente strato condiviso tra teste per ora (vedi *Adapter condiviso*, sotto).
4. **Il centro peggiore decide**, come nel gate di oggi. Le mitigazioni che ottimizzano il caso
   peggiore (Group DRO) sono coerenti con il criterio di promozione.
5. **Il test esterno si consulta una volta per candidato**, e il codice lo impedisce altrimenti.

## Architettura

```
                      backbone congelato (Phikon ora, H-optimus-0 per l'MVP)
                                     │  embedding per tile, una collezione per versione
              ┌──────────────────────┼──────────────────────────┐
              ▼                      ▼                          ▼
        cohort: unione dei     M3 controllore (dopo)      vector DB (com'è)
        manifest filtrati      tessuti presenti, OOD
        per sede della testa         │ regioni del tessuto atteso (dopo; ora tutte le tile)
              │                      ▼
              └─────────────►  HEAD = spec versionata ───────────────────────────────┐
                               ├─ etichette: mappa da reference_diagnosis            │
                               ├─ aggregatore: ABMIL (poi CLAM / TransMIL)           │ training
                               ├─ ricetta: mitigazioni [bilanciamento, DRO, ...]  ◄──┘ solo qui
                               ├─ calibratore: temperatura globale (fuori fold)
                               └─ batteria e soglie del gate proprie
                                     │
                                     ▼  registry: head-<id>-<backbone>, alias candidate/validated
                          probabilità calibrata, attenzione, motivo di rinvio (contratto M4)
```

### La specifica di una testa

Una testa è un file di configurazione Hydra (`conf/head/<id>.yaml`), validato da un modello pydantic
come `SlideRecord`. Per la testa di oggi:

```yaml
id: ln_metastasis                 # M4, linfonodo: metastasi sì/no
version: 1                        # cambia se cambiano etichette, input o batteria
module: M4
sites: [C77.3]                    # ICD-O: quali vetrini del manifest la riguardano
datasets: [camelyon16, camelyon17]
labels:                           # reference_diagnosis -> etichetta; assente = escluso, con motivo
  negative: 0
  micro: 1
  macro: 1
  # itc: esclusa (sotto la risoluzione di una tile, C17 §1)
  # CAMELYON16 'tumor' / 'normal': mappati dal manifest esistente
task: binary                      # binary | multiclass | hierarchical (M5)
input: tiles                      # tiles | regions:<tessuto> quando esisterà M3
aggregator: abmil
domain: [dataset, center]         # cosa conta come dominio per bilanciamento e DRO (vedi sotto)
roles:                            # vedi "Split"
  external: {center: [lpon]}
recipe: []                # mitigazioni, in ordine; vuoto = baseline
calibration: temperature        # globale, fuori fold
gate: {...}                       # soglie della testa, oggi in conf/config.yaml
```

Una testa futura (es. prostata con PANDA, sottotipi di sarcoma M5) è un altro file: altre sedi,
altri dataset, altra mappa di etichette, magari `task: hierarchical`. Il codice di training, il
protocollo e le mitigazioni sono gli stessi. Un caso utile per verificare che il disegno regga:
una testa **paziente** `ln_pn_stage` (pN0 / pN0(i+) / pN1mi / pN1 / pN2 dai 5 linfonodi di CAMELYON17),
il cui input sono le uscite per vetrino di `ln_metastasis`: le teste possono dipendere da altre teste,
e la dipendenza (id e versione) è registrata come quella dal backbone.

### Cohort: più dataset in un solo addestramento

Oggi `train` legge un dataset e una cartella di embedding. Il nuovo `cohort`:

- unisce i manifest dei `datasets` della testa, filtra per `sites`, applica la mappa delle etichette
  e scrive gli esclusi con motivo (ITC, diagnosi non mappata, vetrino bloccato) come fa M0;
- carica gli embedding dalla cartella di ogni dataset (`data/embeddings/<backbone>`,
  `data/camelyon17/embeddings/<backbone>`) e **rifiuta di partire se le `collection.json` non hanno la
  stessa versione del backbone**: embedding di versioni diverse non si mescolano mai;
- aggiunge la colonna `domain` (per la testa linfonodo: `camelyon16:radboud`, `camelyon17:radboud`,
  ...), che non coincide con `center`.

Perché `domain` distinto da `center`: Radboud in CAMELYON16 e in CAMELYON17 sono preparati in anni
diversi e convertiti in modo diverso (`normal_144`, E3b). Il **leave-one-centre-out** raggruppa per
centro (si esclude tutto Radboud, perché la sovrapposizione di pazienti tra i due dataset non è
verificabile, C17 §3); bilanciamento, DRO e discriminatore lavorano invece sui domini, che sono più
fini e più vicini a ciò che il backbone vede davvero.

### Split

Un file versionato per testa, `data/manifests/splits/<head_id>.csv` (`slide_id, role, cv_fold`),
scritto da `td task=splits head=<id>` e mai rigenerato in modo implicito, come oggi. I fold di CV sono
raggruppati per paziente (5 linfonodi per paziente in CAMELYON17) e stratificati per etichetta ×
dominio. Il file di CAMELYON16 resta com'è per riprodurre il baseline registrato.

Prima di scriverlo, nel manifest: `test_116` e `tumor_091` con lo stesso `patient_pseudo_id`
(E3b §6); `normal_144` marcato come conversione diversa (C17 §6).

Ruoli (decisi):

| Ruolo | Vetrini | Perché |
|---|---|---|
| sviluppo | tutto CAMELYON16 (train **e** test ufficiale) + CAMELYON17 di Radboud, Utrecht, CWZ, Rijnstate: 771 vetrini, 4 centri | Il test ufficiale di CAMELYON16 è già stato consultato molte volte (E1, E3, E3b): non è più un test pulito. Con 4 centri il leave-one-centre-out è la misura di generalizzazione |
| esterno bloccato | CAMELYON17 di LPON: 92 vetrini | L'unico centro con scanner Philips nativo, 5 scanner e date di scansione: il centro "nuovo" più realistico, e un sottogruppo per scanner già pronto |

Scartata: tenere il test di CAMELYON16 come test in distribuzione. Costava 129 vetrini allo
sviluppo per misurare ciò che la CV già misura.

### Mitigazioni

Interfaccia unica: il ciclo di training chiama, per ogni mitigazione della ricetta, al più quattro
punti — l'ordine dei vetrini in un'epoca, un'aumentazione della borsa di tile, una perdita aggiuntiva
sulle rappresentazioni (tile `h`, vetrino pooled `z`), la riduzione delle perdite per gruppo. Ogni
mitigazione è un modulo piccolo con i suoi iperparametri in `conf/mitigation/<nome>.yaml`.

| Nome | Cosa fa | Costo | Ipotesi da verificare |
|---|---|---|---|
| `balanced` | Ogni epoca pesa ugualmente i domini e, dentro ogni dominio, le classi (sostituisce il `pos_weight` globale) | Nullo | Oggi Radboud C16 pesa un terzo dei dati: il modello impara la sua scala di punteggi |
| `group_dro` | Minimizza la perdita del dominio peggiore (Sagawa et al., 2020, versione online: un peso per dominio aggiornato a ogni passo, va bene con un vetrino per passo) | Basso | Il gate guarda il centro peggiore: allineare l'obiettivo al criterio |
| `stat_mix` | Aumentazione nello spazio degli embedding: per un vetrino si sostituiscono media e deviazione standard delle sue tile con una miscela di quelle di un vetrino di un altro dominio (MixStyle / DSU sulle statistiche per vetrino) | Basso | E2: dopo aver tolto la media il centro resta nella struttura locale (varianza): la media da sola non basta, media + varianza forse sì. A differenza di E4 non cambia l'inferenza |

Non in questa tornata: discriminatore avversariale del dominio (DANN: instabile, un iperparametro in
più da tarare; si riprende solo se le tre sopra non portano il probe sotto soglia); aumentazione di colore sulle immagini (richiede una seconda estrazione su
Colab per ogni vista: da valutare con H-optimus-0 solo se le mitigazioni sugli embedding non
bastano); supervisione delle tile con le annotazioni (utile per la localizzazione, non per il centro).

### Calibrazione

Solo **globale** (decisione): un centro nuovo non deve fornire vetrini con diagnosi perché il
modello sia calibrato. È il requisito più severo: se le mitigazioni non bastano, la risposta è il
rinvio OOD, non una ricalibrazione locale.

- Temperatura unica, stimata sulle predizioni fuori fold della CV di sviluppo (mai sul centro escluso
  né sull'esterno). È un artefatto separato dal modello, con la sua provenienza (vetrini usati).
- Nel leave-one-centre-out la temperatura si stima dentro i centri di addestramento della rotazione,
  così l'ECE del centro escluso misura davvero un centro mai visto.

E4 suggeriva la ricalibrazione per centro: scartata qui. Resta possibile come esperimento solo
diagnostico, per capire quanta parte dell'errore è una scala dei punteggi.

### Protocollo e batteria

Il protocollo di oggi resta (CV, leave-one-centre-out, più semi, gate sulla media) con queste
modifiche:

- leave-one-centre-out su 4 centri di sviluppo, con la temperatura globale stimata dentro la
  rotazione;
- due nuove voci **nel gate**, con soglie permissive da stringere dopo E7: probe lineare sul centro
  dalla rappresentazione `z` della testa, AUROC macro one-vs-rest con fold per paziente, **≤ 0,80**;
  Robustness Index sulle `h` delle tile (k = 10, vicini da altri vetrini, tile delle slide con
  annotazione completa), **≥ 0,5**. Riferimento: sugli embedding grezzi Phikon probe 1,000 e RI 0,09
  (E2), quindi è probabile che E6 non passi: è atteso, e misura la distanza da coprire;
- metriche per scanner e per dominio nel report, senza soglia;
- il **test esterno** è un task a parte, `td task=external head=<id> version=<n>`: accetta solo una
  versione registrata con alias `validated`, scrive ogni consultazione in un registro versionato in
  git (`data/reports/external_log.csv`: data, testa, versione, risultato) e rifiuta una seconda
  consultazione per la stessa versione;
- iperparametri delle mitigazioni (λ, tasso di DRO) scelti solo dentro lo sviluppo, con il
  leave-one-centre-out: mai con l'esterno.

Le soglie del gate passano da `conf/config.yaml` alla specifica della testa: una testa sui sottotipi
non avrà le stesse soglie di quella sui linfonodi.

### Registry e tracciabilità

- Nome del modello: `head-<id>-<backbone>` (es. `head-ln_metastasis-phikon`); il vecchio
  `abmil-camelyon16-phikon` resta per il baseline.
- Tag della versione: id e versione della testa, versione del backbone, ricetta, domini visti in
  training, file degli split (hash), calibratore (hash, vetrini usati), dipendenze da altre teste.

### Adapter condiviso: perché no, per ora

L'alternativa è uno strato condiviso (backbone → adapter invariante al centro → teste) addestrato una
volta con le mitigazioni su tutti i dataset. Vantaggio: le teste future ne ereditano la robustezza.
Svantaggio: l'adapter diventa una dipendenza di ogni testa come il backbone: cambiarlo rivalida
tutto, e un adapter appreso sui linfonodi non ha motivo di valere per la prostata. Si riconsidera
quando ci sarà una seconda testa, con un esperimento che lo confronti con le ricette per testa. Se
adottato, avrebbe una collezione di embedding propria, come uno studente distillato.

## Esperimenti (bozze di protocollo)

Tutti con Phikon (embedding già estratti per 899 vetrini), tre semi, stessi split. La ricetta scelta
va **rivalidata con H-optimus-0**: quanto il centro è codificato dipende dal backbone.

- **E6 — Più centri, nessuna mitigazione.** Baseline ABMIL invariato sulla cohort di sviluppo.
  Domande: il leave-one-centre-out su 4 centri passa il gate? Di quanto migliora rispetto al
  baseline su CAMELYON16 sul centro comune (Utrecht escluso)? È il riferimento per E7.
- **E7 — Mitigazioni.** `balanced`, `balanced + group_dro`, `balanced + stat_mix` contro E6. Esito primario: ECE peggiore in leave-one-centre-out (grezza).
  Co-primari: AUROC peggiore in leave-one-centre-out; AUROC in CV (non deve scendere più di 0,01).
  Secondari: specificità peggiore, probe sul centro da `z` e Robustness Index (le voci del gate), AUROC dell'attenzione (non deve
  scendere come in E4). Criterio di adozione nella forma di E4, soglie da fissare insieme.
- **Esterno** (una volta): la ricetta adottata, addestrata su tutto lo sviluppo, valutata su LPON,
  per centro e per scanner.

## Dipendenze aperte

- **Punto cieco della griglia** (C17 §1): tumore nella capsula e nel seno sottocapsulare fuori dalle
  tile. Per il training a livello di vetrino è rumore di etichetta (`patient_068_node_1`: vetrino
  positivo senza tumore nelle tile). Deciso: non prioritario. Griglia invariata, i 6 vetrini noti
  riportati come sottogruppo. Se un giorno cambia, cambia gli embedding e quindi ogni training: il
  momento meno costoso resta l'estrazione con H-optimus-0.
- **DVC**: lo stadio `stream` copre solo CAMELYON16; serve lo stesso per CAMELYON17 (o un `foreach`
  sui dataset) e uno stadio `train-<head>` che dipende da entrambi i manifest, entrambe le cartelle
  di embedding, il file degli split e la specifica della testa.

## Codice (bozza della struttura)

```
src/tumordetector/
  heads/spec.py          HeadSpec (pydantic): validazione della configurazione della testa
  heads/cohort.py        unione dei manifest, mappa delle etichette, esclusi con motivo,
                         controllo della versione del backbone, colonna domain
  mil/abmil.py           invariato nel contratto; forward espone anche z (pooled) per le mitigazioni
  heads/mitigations.py   balanced, group_dro, stat_mix (fuori da mil/: il baseline non cambia)
  mil/train_loop.py      fit generico sulla ricetta (sostituisce abmil.fit)
  mil/calibrate.py       temperatura globale (fuori fold)
  mil/evaluate.py        protocollo: + temperatura nella rotazione, + probe sul centro e RI nel gate
  tasks/train.py         td task=train head=<id>
  tasks/splits.py        td task=splits head=<id>
  tasks/external.py      td task=external head=<id> version=<n>
conf/
  head/ln_metastasis.yaml
  mitigation/{balanced,group_dro,stat_mix}.yaml
```

Ordine di lavoro: manifest (paziente unificato, `normal_144`) → cohort e split → calibrazione
globale, probe e RI nel protocollo → E6 → mitigazioni ed E7 → esterno su LPON.
