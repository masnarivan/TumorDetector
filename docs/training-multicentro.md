# Training multi-centro e teste per tessuto — progetto

Stato: **progetto approvato nelle scelte principali**, 18/10/2026. Implementati: manifest (paziente
unificato, `file_format`), specifica della testa e cohort con ruoli e fold (`td task=cohort`),
training della testa senza mitigazioni con temperatura globale, probe e Robustness Index nel gate
(`td task=train_head`, protocollo di E6). Mancano le mitigazioni (E7) e il task del test esterno. I
protocolli degli esperimenti (E6, E7) passano in [esperimenti.md](esperimenti.md) prima di vedere i
risultati, con le soglie di adozione.

*Aggiornamento del 22/10/2026.* Fatti E6–E12; implementate anche le ricette `balanced`, `group_dro`,
`stat_mix` e `adversarial`. **Nessuna versione supera il gate**: il centro mai visto resta il problema, e
nessuna ricetta di training o correzione a valle lo risolve senza vetrini del centro (*Stato dopo
E6–E12*, sotto). Proposta nuova: un centro entra nella pipeline con i propri vetrini diagnosticati
(*Ingresso di un centro nuovo*), con il costo d'ingresso misurato da E14. Il test esterno su LPON non è
stato consultato.

*Aggiornamento del 22/10/2026, pomeriggio.* Implementati, senza ancora una versione che li usi (la v1
registrata è di prima): insiemi conformal per classe nella testa (`conformal.json`, tag del registry) con la
copertura dei positivi sul centro escluso peggiore nel gate (≥ 0,90; su E6 sarebbe 0,91–0,94); centri e
scanner visti come tag della versione; `td task=predict` (probabilità, insieme, decisione con tutti i motivi
di rinvio, tile con più attenzione; rinvia centri e scanner non visti e versioni non validate; rifiuta il
test esterno); `td task=external` (solo la versione `validated`, una volta, riga nel registro
`data/reports/external_log.csv` scritta prima di leggere gli embedding; rinvio come centro non visto e
risposte "al giorno zero", per scanner).

## Decisioni (18/10/2026)

| Tema | Decisione |
|---|---|
| Split | Tutto CAMELYON16 (test ufficiale compreso) + CAMELYON17 di Radboud, Utrecht, CWZ, Rijnstate in sviluppo; **LPON esterno bloccato** |
| Mitigazioni da confrontare | `balanced`, `group_dro`, `stat_mix`. L'avversariale (DANN) non entra in questa tornata |
| Teste future | Ricetta di mitigazione dentro ogni testa; nessun adapter condiviso per ora |
| Gruppi | Bilanciamento e DRO sui **domini** (dataset × centro); leave-one-centre-out per centro intero |
| Calibrazione | **Solo globale**: il modello deve reggere su un centro nuovo senza vetrini di quel centro. Nessuna ricalibrazione per centro all'installazione |
| Robustezza nel gate | Robustness Index ≥ 0,5. Probe sul centro: soglia ≤ 0,80 fino a E8, poi (19/10) solo riportato, con la regola di non superare il probe del modello `validated` di oltre 0,01 |
| Test esterno | Bloccato dal codice: una consultazione per versione, solo versioni `validated` |
| Punto cieco della griglia | Non prioritario: griglia invariata, i vetrini noti riportati come sottogruppo |

Revisione proposta il 22/10/2026, da decidere (non ancora una decisione): la riga *Calibrazione* resta
com'è per la temperatura, ma il requisito "il modello deve reggere su un centro nuovo senza vetrini di
quel centro" non è raggiungibile con Phikon (E6–E12). La proposta è sostituirlo con: **un centro riceve
risposte diagnostiche solo dopo essere entrato nello sviluppo con i propri vetrini**; fino ad allora i
suoi vetrini vanno in rinvio. Dettagli in *Ingresso di un centro nuovo*.

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

## Stato dopo E6–E12 (22/10/2026)

Dettagli e numeri in [esperimenti.md](esperimenti.md).

| Esperimento | Che cosa ha provato | Esito |
|---|---|---|
| E6 | Quattro centri, ricetta vuota, temperatura globale | Gate non superato. Sul centro escluso i **negativi** salgono verso il tumore (Utrecht: logit mediana +0,1 contro −8 in CV, specificità 0,49); i positivi restano dove sono |
| E7 | `balanced`, `group_dro`, `stat_mix` | Nessuna adottata: l'errore si sposta tra centri |
| E8 | Discriminatore avversariale (DANN) | Nessuna adottata: corregge Utrecht, rompe CWZ |
| E9 | Offset dai negativi del centro nuovo | Specificità recuperata da 3 negativi (Utrecht 0,49 → 0,97), ma si perdono micrometastasi (sensibilità −0,08 rispetto al centro visto) |
| E10 | Insiemi conformal e rinvio | Scelta «per classe»: le risposte «negativo» reggono su ogni centro, i falsi positivi di Utrecht restano positivi sicuri |
| E11 | Offset + conformal | Non proponibile: dopo l'offset le micrometastasi perse sono negativi chiari, non incerti |
| E12 | Punteggi dalle tile (istanze ABMIL, classificatore di tile) | Nessun candidato: anche le tile portano lo spostamento di centro |
| E13 | Normalizzazione del colore prima dell'embedding (pilota) | Protocollo fissato, in pausa dopo E14 |
| E14 | Vetrini del centro nuovo aggiunti al training | Protocollo fissato |

Che cosa se ne ricava:

- **Un centro visto funziona.** In CV di E6, dove ogni centro contribuisce l'80% dei suoi vetrini al
  training: specificità 0,94–0,98, sensibilità 0,92–0,99, su ogni centro. Il problema non è un modello
  debole ma un modello che non ha mai visto quello scanner.
- **Senza vetrini del centro le leve sono esaurite**: ricette di training, temperatura, offset,
  conformal, punteggi dalle tile si fermano tutti sullo stesso spostamento del tessuto normale.
- **Restano due strade, complementari**: cambiare il segnale a monte (normalizzazione del colore, E13;
  H-optimus-0, che non gira in locale) o far vedere il centro al modello (E14). La prima riduce il costo
  della seconda, non la sostituisce: anche con un backbone migliore un centro nuovo resta un dominio
  nuovo da verificare.
- **Le micrometastasi sono il punto debole** di ogni correzione: vanno nella batteria come sottogruppo.
- **Riconoscere un centro mai visto è facile** (E2: il centro si legge dagli embedding con AUROC 1,000):
  il sistema può accorgersene e rinviare invece di sbagliare.

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
6. *(Proposto il 22/10/2026.)* **Un centro mai visto non riceve risposte diagnostiche.** Una versione è
   `validated` per i centri e gli scanner del suo sviluppo; per gli altri il risultato è un rinvio.

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

Non in E7: discriminatore avversariale del dominio (DANN: instabile, un iperparametro in più da
tarare). Implementato il 18/10/2026 come ricetta `adversarial` (discriminatori su *z* e sulle *h*
delle tile, inversione del gradiente con la rampa di Ganin), da usare solo con un protocollo suo; aumentazione di colore sulle immagini (richiede una seconda estrazione su
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

*Nota del 22/10/2026.* E6 ha mostrato che l'errore sul centro nuovo non è di scala ma di livello dei
soli negativi; E9 ha provato la correzione con i vetrini del centro (offset), che perde micrometastasi.
La proposta di *Ingresso di un centro nuovo* non è una ricalibrazione locale: il centro entra nello
sviluppo e la testa si riaddestra; la temperatura resta una e globale.

## Ingresso di un centro nuovo (proposta, 22/10/2026)

Da discutere con i patologi; la parte quantitativa la dà E14. Il backbone congelato e le teste piccole
rendono il riaddestramento economico (ore di CPU), quindi il modello può crescere con i centri che lo
usano.

```
 vetrino ──► M3 / OOD: centro o scanner visto? ──no──► rinvio (nessuna risposta diagnostica)
                    │ sì                                      │
                    ▼                                         ▼
          risposta della versione validated        uso silente: il sistema gira, il patologo
          (probabilità, insiemi per classe E10)    non vede l'output; la sua diagnosi è l'etichetta
                                                              │ raggiunto il costo d'ingresso (E14)
                                                              ▼
                                       il centro entra nel cohort di sviluppo (nuovo dominio, nuovi fold)
                                                              │
                                                              ▼
                                       riaddestramento + protocollo della testa (CV, leave-one-centre-out)
                                                              │ gate superato
                                                              ▼
                                       registry: nuova versione, validated per i centri del suo sviluppo
```

1. **Riconoscere il centro nuovo.** Il centro è nei metadati del vetrino; lo scanner anche, ma un cambio
   di colorazione o di protocollo no. Serve quindi anche un controllo sugli embedding (il centro si legge
   con AUROC 1,000, E2; E3b ha mostrato che un punteggio OOD sulla composizione del tessuto non basta).
2. **Uso silente.** Già previsto dal piano. In istopatologia ogni vetrino è comunque letto dal patologo:
   le etichette del vetrino sono complete, senza bias di selezione, e non servono annotazioni (l'ABMIL
   impara dalle etichette del vetrino). La diagnosi va confermata e registrata con la mappa delle etichette
   della testa (ITC escluse).
3. **Ingresso nel cohort.** I vetrini del centro diventano un dominio di sviluppo: nuovi fold per
   paziente, file degli split versionato rigenerato **esplicitamente** con una nuova versione (mai in modo
   implicito), il resto dei fold invariato.
4. **Riaddestramento e gate.** Il protocollo della testa intero. Il leave-one-centre-out guadagna una
   rotazione per ogni centro: misura ancora la generalizzazione a un centro nuovo, che resta il caso del
   prossimo ingresso.
5. **Registry.** I tag della versione includono già i domini visti; diventano anche la **lista dei centri
   e degli scanner per cui la versione può rispondere**. Il servizio d'inferenza la legge e rinvia gli
   altri.
6. **Monitoraggio.** Un centro non è un dominio fisso (E3b: i casi di Radboud del 2015). Sui centri
   ammessi si confrontano le distribuzioni delle logit dei negativi confermati con quelle dello sviluppo
   (lo spostamento di E6 si vede già da 3 negativi, E9); uno spostamento riporta il centro al punto 1.
7. **Test esterno.** LPON resta bloccato e non entra mai in questo ciclo: misura una sola volta la
   generalizzazione di una versione, non l'ingresso di un centro.

Vincoli da risolvere fuori dal codice:

- **Regolatorio.** Un modello che si aggiorna è un dispositivo che cambia. Il percorso va descritto in
  anticipo come piano di modifica (in USA i *Predetermined Change Control Plan* della FDA; in Europa MDR
  e AI Act): che cosa può cambiare (pesi della testa, centri ammessi), con quale protocollo, con quale
  gate. Il modo di lavorare del progetto (protocollo prima dei risultati, gate automatico, report
  allegato alla versione) è già in quella forma.
- **Dati.** Accordi con i centri, DPIA, GDPR. Gli embedding possono restare nel centro: una testa ABMIL si
  può anche addestrare in modo federato, da valutare quando ci sarà un secondo centro reale.
- **Il primo periodo in un centro nuovo** non dà risposte diagnostiche: va concordato e comunicato.

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

*Nota del 22/10/2026.* E6 ed E7 sono stati fatti con i protocolli in [esperimenti.md](esperimenti.md),
seguiti da E8–E14; le bozze qui sotto restano come scritte il 18/10.

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
  (22/10/2026) heads/conformal.py   insiemi per classe (E10)
  (22/10/2026) serve/answer.py      positivo / negativo / rinvio con i motivi; serve/registry.py: versione dal registry
  (22/10/2026) tasks/predict.py     td task=predict head=<id> predict.slides=[...]
conf/
  head/ln_metastasis.yaml
  mitigation/{balanced,group_dro,stat_mix}.yaml
```

Ordine di lavoro: manifest (paziente unificato, `normal_144`) → cohort e split → calibrazione
globale, probe e RI nel protocollo → E6 → mitigazioni ed E7 → esterno su LPON.

Ordine dal 22/10/2026: E14 → decisione con i patologi sull'ingresso dei centri (e sullo scambio
specificità / micrometastasi di E9–E11) → E13 se E14 lo chiede → insiemi per classe di E10 nell'output
della testa e nel gate → lista dei centri ammessi nel registry e rinvio dei centri non ammessi →
esterno su LPON solo con una versione che passa il gate.
