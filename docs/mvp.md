# MVP — piano per il 31/10/2026: TCGA, controllore (M3), seconda testa e web app

Stato: **approvato con modifiche**, 25/10/2026. Il piano definisce l'MVP come QC, embedding H-optimus-0,
controllore e OOD su 3–4 tessuti, un modulo tumore, casi simili e una prima web app con viewer, overlay e
report. Oggi ci sono il modulo linfonodo (`ln_metastasis`, H-optimus-0 `candidate`), il controllo di
dominio della testa (E15, V) e `td task=predict`. Mancano un secondo tessuto, il controllore, un secondo
modulo tumore e la web app: questo documento li pianifica.

Principio per questa settimana: **prima un MVP che funziona da capo a fondo, poi l'ottimizzazione.** I
protocolli si fissano comunque prima dei risultati, come sempre, ma con criteri da MVP: dicono se il pezzo
è abbastanza buono da mostrare, non se è pronto per un centro.

Vincolo della settimana: E14b occupa la CPU del Mac fino a lunedì 26 (circa 24 h). Fino ad allora si scrive
codice e si lavora su Colab; niente training in locale.

## Riassunto

| Parte | Che cosa | Esito a sabato |
|---|---|---|
| A. TCGA | 392 vetrini diagnostici: seno, colon, prostata, polmone (adenocarcinoma e squamoso), rene. Download su Drive prima, embedding H-optimus-0 dopo | Embedding e QC in `data/tcga/`, manifest in git |
| B. Controllore M3 | Tessuto del vetrino e coerenza con la sede dichiarata; OOD rispetto ai tessuti noti, per vetrino e per regione | `td task=train_controller`, E18 |
| C. Seconda testa (M5) | Polmone: adenocarcinoma contro carcinoma squamoso (`nsclc_subtype`) | Testa `candidate` registrata, E19 |
| D. Web app | Lista dei casi, viewer con overlay (QC, attenzione, OOD), report instradato dal controllore alla testa, casi simili, feedback | `td task=app` sui vetrini presenti in locale |

Tessuti noti all'MVP: **linfonodo** (CAMELYON), **seno, colon, prostata, polmone** (TCGA). Il **rene**
(TCGA, carcinoma a cellule chiare) non entra mai nel riferimento: è il tessuto mai visto con cui si misura
l'OOD. Teste: `ln_metastasis` (linfonodo) e `nsclc_subtype` (polmone).

## A. TCGA

### Perché TCGA, e il problema del confondimento

TCGA è open access su GDC (nessun accordo d'uso per i dati open; citazione secondo le linee guida TCGA;
i termini vanno riverificati prima di un uso in prodotto). Ogni organo ha centinaia di vetrini
diagnostici (`DX`, FFPE, Aperio, in genere 40x) da decine di siti di prelievo.

Il rischio è quello di E2: il centro si legge dagli embedding con AUROC 1,000. Se ogni organo venisse da
siti diversi, il controllore imparerebbe il sito invece del tessuto. In TCGA però **4 siti hanno vetrini
di tutti e 4 gli organi** (GDC, interrogato il 25/10/2026):

| Sito di prelievo | Seno (BRCA) | Colon (COAD) | Prostata (PRAD) | Polmone (LUAD) |
|---|---|---|---|---|
| Indivumed | 83 | 173 | 24 | 34 |
| University of Pittsburgh | 142 | 20 | 63 | 22 |
| International Genomics Consortium | 48 | 13 | 65 | 91 |
| Roswell Park | 90 | 27 | 44 | 12 |

### Campione

| Gruppo | Uso | Disegno | Vetrini |
|---|---|---|---|
| Controllore | B | Seno, colon, prostata, adenocarcinoma polmonare: 12 pazienti per organo per ciascuno dei 4 siti sopra | 192 |
| Testa polmone | C | Adenocarcinoma (LUAD) e squamoso (LUSC): 25 pazienti per classe per sito, 4 siti con entrambi (sotto) | 200, di cui 24 LUAD già nel gruppo del controllore (IGC e Indivumed) |
| Tessuto mai visto | B | Rene, carcinoma a cellule chiare (KIRC), 24 pazienti da siti qualsiasi | 24 |
| **Totale** | | Un vetrino `DX1` per paziente, seme fisso | **392** (`data/manifests/tcga.csv`) |

Siti della testa polmone (pazienti LUAD / LUSC con un vetrino `DX1`): International Genomics Consortium
91 / 41, Asterand 34 / 50, Indivumed 34 / 38, Prince Charles Hospital 31 / 44. Johns Hopkins, proposto
all'inizio, ha solo 17 pazienti LUSC con `DX1` (i 50 vetrini contano più blocchi per paziente). LUAD contro LUSC è il compito di sottotipo più
studiato su TCGA e il più probabile da far funzionare entro sabato; l'alternativa, seno duttale contro
lobulare (176 pazienti lobulari), costerebbe circa il doppio di download (vetrini da ~1 GB) e resta per
dopo l'MVP.

Limiti che restano, da dichiarare:

- **Linfonodo contro TCGA è confuso con il dataset.** Il linfonodo viene solo da CAMELYON (Paesi Bassi,
  3DHistech/Hamamatsu), gli altri organi solo da TCGA (USA/Germania, Aperio). Nessun disegno lo
  risolve con questi dati; E18 lo riporta come limite.
- **I vetrini TCGA diagnostici sono tutti tumore primario.** "Seno" vuol dire carcinoma della mammella con
  il suo stroma, non mammella normale. Per il controllore va bene (sede del vetrino) e la testa polmone è
  di sottotipo (M5: dato un tumore, quale), quindi non servono negativi.
- **La diagnosi di riferimento è il progetto TCGA**, non `primary_diagnosis` di GDC: quest'ultimo è
  rumoroso (nel campione, un linfoma di Hodgkin e un melanoma tra i vetrini di colon) e resta come
  colonna a parte.
- **Marcatori a penna e artefatti** sono frequenti in TCGA e GrandQC non è ancora integrato: la maschera
  del tessuto li può includere. Il QC li riporta.

### Download su Drive, poi embedding

Su Colab il tempo di download è tempo di GPU pagato e fermo. Si separano le due fasi:

1. **`td task=fetch`** (nuovo): scarica i vetrini del manifest in `data.raw_dir`, verifica l'md5, è
   riprendibile e fa più download in parallelo (`fetch.workers`, default 4). Gira su un **runtime Colab
   solo CPU** (consuma poche unità di calcolo) con `raw_dir` su Drive, e si può lasciare andare anche di
   notte.
2. **`td task=stream`** su runtime GPU, con `raw_dir` sulla stessa cartella di Drive: `download` riusa già
   oggi i file presenti. Due aggiunte: `stream.stage_dir` copia il vetrino sul disco locale della VM prima
   del tiling (openslide legge a salti, e su Drive sarebbe lento); `stream.delete_raw` cancella il vetrino
   da Drive dopo l'embedding, tranne quelli della demo.

Si lavora **a lotti**, così il secondo lotto si scarica mentre il primo si embedda e Drive non tiene mai
tutto:

| Lotto | Vetrini | Download (stima) |
|---|---|---|
| 1 | Controllore + rene | 216, ~150 GB |
| 2 | Testa polmone (i 176 non già nel lotto 1) | ~176, ~130 GB |

Vincoli: lo spazio libero su Drive deve contenere un lotto (~150 GB) più gli embedding; Drive accetta al
massimo 750 GB caricati al giorno per utente, qui non è un limite. Velocità misurata dal Mac il
25/10/2026 su 4 vetrini: **~4 MB/s per connessione**, che si sommano (14 MB/s con 4 download in
parallelo). Il notebook usa 16 download: a ~50 MB/s un lotto richiede ~1 h, a 4 MB/s un solo download ne
richiederebbe 10. Da Colab va rimisurato.

Notebook: `notebooks/tcga_fetch_colab.ipynb` (CPU, scarica un lotto su Drive) e
`notebooks/tcga_extract_colab.ipynb` (GPU, prima i 4 vetrini di prova con il confronto della griglia
del Mac, poi il lotto).

### Volumi e tempi (stime)

- Embedding: su A100 un vetrino CAMELYON16 di 7.519 tile richiede ~51 s. I 4 vetrini di prova hanno
  3.949–19.396 tile (media ~13 mila, il doppio di CAMELYON): **~10 h di GPU** per 392 vetrini, una
  sessione per lotto.
- Disco: ~390 × 15.000 × 1536 × 2 byte ≈ **18 GB** di embedding float16 (le tile parquet e il QC a parte).

### Codice

1. `src/tumordetector/data/tcga.py`: manifest dall'API GDC (`/files`, filtro `Diagnostic Slide`, `SVS`,
   `open`). Colonne dello schema comune:

   | Colonna | Valore |
   |---|---|
   | `slide_id` | nome del file senza `.svs` (`TCGA-XX-XXXX-01Z-00-DX1.<uuid>`) |
   | `file_md5` | `md5sum` di GDC |
   | `patient_pseudo_id`, `case_id` | `cases.submitter_id` (`TCGA-XX-XXXX`) |
   | `center` | sito di prelievo (`tissue_source_site.name`) |
   | `scanner` | `Aperio`, verificato al tiling sulle proprietà del file |
   | `site` | C50.9 seno, C18.9 colon, C61.9 prostata, C34.9 polmone, C64.9 rene |
   | `procedure`, `specimen_type` | `resection`, `FFPE diagnostic slide` |
   | `reference_diagnosis` | `diagnoses.primary_diagnosis` |
   | `diagnosis_source` | `histology` |
   | colonne in più | `project_id`, `file_id`, `size_gb`, `file_format = svs`, `group` (controllore, testa polmone, mai visto), `batch` |

   Il campione si sceglie in `build_manifest` e il manifest è versionato in git: non si rigenera in modo
   implicito.
2. `tasks/fetch.py` e, in `tasks/stream.py`, `download` generalizzato a estensione e URL per dataset
   (`https://api.gdc.cancer.gov/data/<file_id>`), più `stage_dir` e `delete_raw`. Controllo md5 invariato.
3. `conf/data/tcga.yaml` (out `data/tcga`), `td task=manifest data=tcga`, test sul parsing di una risposta
   GDC salvata (nessuna rete nei test).
4. Notebook Colab: `notebooks/fetch_colab.ipynb` (CPU) e TCGA come terzo dataset in
   `extract_colab.ipynb` (GPU), con il lotto come parametro.
5. Tiling: i vetrini a 40x (0,25 mpp) si leggono con downsample 2, come CAMELYON16; quelli a 20x
   direttamente. La griglia è salvata con il vetrino, come oggi.
6. **Maschera del tessuto** (trovato nella prova): gli scanner TCGA acquisiscono solo un riquadro intorno
   al tessuto, spesso più tessuto che vetro, e la mediana della saturazione dell'area acquisita (il livello
   del vetro in `qc/tissue.py`) cade nel tessuto chiaro. Sul vetrino di seno della prova la maschera teneva
   solo il tessuto denso (26 mm², stroma escluso). Ora il livello del vetro è un parametro del dataset,
   `data.glass_quantile`: 0,5 (la mediana di prima) per CAMELYON, 0,1 per TCGA (50 mm², stroma
   compreso; gli altri 3 vetrini +2–10% di tessuto). Per CAMELYON identità della griglia e uscite non
   cambiano (`td task=verify`).

Prova sul Mac (25/10/2026), 4 vetrini di mediana grandezza, uno per organo: `fetch` da GDC, poi `stream`
con il backbone `dummy` e `stage_dir`. QC superato su tutti, Aperio, 3 a 40x e 1 a 20x, copie locali
cancellate dopo l'embedding. I 4 vetrini restano in `data/raw/tcga` per la demo.

## B. Controllore M3

Contratto (piano, M3): input embedding e sede dichiarata; output esito di coerenza, tessuti presenti,
punteggio OOD per regione e per vetrino. Criterio di accettazione del piano: rileva scambi di sede
simulati, tasso di falsi allarmi misurato e dichiarato.

```
 embedding del vetrino ──► OOD: lontano da tutti i tessuti noti? ──sì──► rinvio "tessuto non riconosciuto"
                                 │ no
                                 ▼
                     tessuto predetto (insieme conformal)
                                 │
            sede dichiarata nell'insieme? ──no──► rinvio "incoerenza con la sede dichiarata"
                                 │ sì
                                 ▼
          testa della sede: linfonodo → ln_metastasis, polmone → nsclc_subtype, altri → nessuna testa
                                 │
                                 ▼
                     la testa applica il proprio V (E15) e la propria decisione
```

- **Tessuto:** regressione logistica multiclasse sulla media delle tile normalizzate del vetrino
  (lo stesso vettore di V), con insiemi conformal per classe come E10. Piccola, deterministica, in CPU.
- **OOD del vetrino:** distanza media dai k vetrini di riferimento più vicini (metodo V di E15),
  riferimento = tutti i tessuti noti, soglia conformal da un fold di calibrazione.
- **OOD per regione** (per la mappa del viewer): distanza di ogni regione 8×8 dal prototipo più vicino
  del riferimento (E3: i prototipi k-center bastano). Solo visualizzazione nell'MVP, nessuna decisione:
  E3b ha mostrato che a livello di tile la distanza misura la composizione del tessuto (tumore, grasso).
- Specifica in `conf/controller.yaml` (tessuti, sede → testa, riferimento, alpha), modello e soglie
  registrati in MLflow come `controller-<backbone>`, come le teste.

### E18 — protocollo da fissare in esperimenti.md prima di leggere gli embedding TCGA

Da copiare in `docs/esperimenti.md` lunedì 26, prima dell'estrazione:

- **Domande.** (1) Il controllore riconosce il tessuto su un sito mai visto? (2) Rileva una sede
  dichiarata sbagliata? (3) Rinvia un tessuto mai visto (rene)?
- **Dati.** Tessuti noti: linfonodo (sviluppo della testa, LPON escluso come sempre), seno, colon,
  prostata, polmone (i vetrini LUAD del gruppo del controllore). Rene mai nel riferimento né nel training.
- **Rotazioni.** TCGA: leave-one-site-out sui 4 siti. Linfonodo: leave-one-centre-out sui 4 centri di
  sviluppo, accoppiato alle rotazioni TCGA.
- **Misure.** Accuratezza del tessuto sul sito escluso, per tessuto (conta il peggiore); scambi di sede
  simulati (ogni vetrino del sito escluso con ciascuna sede sbagliata), rilevati e falsi allarmi; tasso
  di rinvio del rene e falsi rinvii dei tessuti noti. Nient'altro in questa tornata.
- **Criterio da MVP.** Accuratezza peggiore ≥ 0,90; scambi rilevati ≥ 0,90 con falsi allarmi ≤ 0,10;
  rene rinviato ≥ 0,80 con falsi rinvii ≤ 0,15. Se non passa, il controllore entra comunque nella demo
  con i numeri misurati scritti nel report, come la testa non validata.

## C. Seconda testa: `nsclc_subtype` (M5)

Una specifica in `conf/head/nsclc_subtype.yaml`, stesso codice di `ln_metastasis` (`td task=cohort`,
`td task=train_head`): `module: M5`, `task: binary`, `sites: [C34.9]`, `datasets: [tcga]`, etichette da
`reference_diagnosis` (adenocarcinoma 0, squamoso 1; diagnosi miste o "Not Reported" escluse con il
motivo), `domain: [dataset, center]`, nessun esterno bloccato in questa tornata (lo si aggiunge quando ci
sarà un secondo dataset polmonare). Il Robustness Index non si calcola (nessuna annotazione di tile) e il
codice lo riporta già come assente.

Il protocollo è quello della testa: CV per paziente, leave-one-centre-out sui 4 siti, temperatura
globale, insiemi conformal per classe, controllo di dominio V. Training sul Mac dopo E14b: 200 vetrini,
stima poche ore.

### E19 — protocollo breve, da fissare con E18

- **Domanda.** La testa distingue adenocarcinoma e squamoso su un sito mai visto?
- **Criterio da MVP.** AUROC in CV ≥ 0,90 e AUROC peggiore in leave-one-centre-out ≥ 0,85. Il gate della
  specifica resta quello di `ln_metastasis` (ECE, specificità, copertura); la versione resta `candidate`
  se non lo supera, come la testa linfonodo.

## D. Web app

Stack del piano, nella versione minima per la prima demo: FastAPI, OpenSeadragon, HTML + JS senza build.
Si avvia con `td task=app` (uvicorn su `127.0.0.1`).

### Che cosa c'è e che cosa no

| Funzione del piano | MVP | Come |
|---|---|---|
| Lista dei casi con stato | Sì | Manifest ∩ vetrini su disco; stato: analizzato, rinviato (motivo), revisionato |
| Viewer con zoom | Sì | `openslide.deepzoom.DeepZoomGenerator` (già dipendenza) → tile DZI |
| Overlay maschera QC | Sì | PNG del QC già in `data/qc/<vetrino>.png`, allineato al vetrino |
| Overlay heatmap | Sì | Attenzione ABMIL di tutte le tile della testa scelta, resa come PNG alla risoluzione della griglia |
| Overlay OOD per regione | Sì | Dal controllore (B) |
| Regioni a supporto, margini | No | Margini sono M6, non nell'MVP; le top tile di attenzione come marcatori |
| Report | Sì | Controllore (tessuto, coerenza, OOD) + testa instradata: probabilità, insieme conformal, decisione con tutti i motivi, versioni di backbone, controllore, testa e codice |
| Casi simili | Sì, semplice | Qdrant, livello regione, sui vetrini di sviluppo dello stesso tessuto; aperti nello stesso viewer se su disco |
| Feedback | Sì, semplice | Accetta / correggi l'etichetta; SQLite in `data/feedback/` con autore, data, versione del modello. Disegno di regioni no |
| "Solo uso di ricerca" | Sì | Banda fissa in ogni pagina |
| Login, ruoli, audit | No | Utente dichiarato a mano; log delle richieste di uvicorn |
| PostgreSQL + pgvector | No | Si resta su Qdrant e file; la migrazione è dopo l'MVP |

Le teste non validate restano come sono: il report mostra il rinvio "versione non validata" con tutti i
motivi, come `predict` oggi.

### Struttura

```
src/tumordetector/app/
  server.py      FastAPI: /api/cases, /api/cases/{id}, /dzi/{id}.dzi, /dzi/{id}_files/{level}/{x}_{y}.jpeg,
                 /api/cases/{id}/overlay/{qc|attention|ood}.png, /api/cases/{id}/report,
                 /api/cases/{id}/similar, POST /api/cases/{id}/feedback
  cases.py       quali vetrini, dove sono (raw_dir dei dataset), stato
  overlays.py    PNG delle tre mappe dalla griglia di tile
  feedback.py    SQLite in sola aggiunta: una correzione non sovrascrive mai la precedente
  static/        index.html, case.html, app.js, style.css; OpenSeadragon da CDN con versione fissa
tasks/app.py     td task=app
```

Il report usa lo stesso codice di `td task=predict` (`serve/answer.py`, `serve/registry.py`) e del
controllore; la web app non ha logica diagnostica propria. Per la heatmap serve l'attenzione di tutte le
tile: `predict` oggi ne salva solo le prime; la funzione condivisa restituirà anche il vettore intero.

### Vetrini della demo

- I 10 vetrini CAMELYON16 in locale (5 normali, 5 tumorali, Radboud e Utrecht). Sono tutti vetrini di
  sviluppo della testa: il report lo dice già (`in_development`), e la demo lo mostra.
- 2 vetrini per tessuto TCGA tenuti dopo l'estrazione (seno, colon, prostata, 2 LUAD, 2 LUSC, rene):
  mostrano il controllore che instrada alla testa polmone, rinvia il rene e segnala uno scambio di sede
  simulato.
- Nessun vetrino LPON: il test esterno resta bloccato.

### Prerequisiti

- `dvc` con `backbone=h_optimus_0` e la testa H-optimus-0 registrata come testa dell'MVP.
- Indice Qdrant H-optimus-0 (`td task=index backbone=h_optimus_0`, oggi c'è solo Phikon). Spazio: ~1,2 GB
  per i 899 vetrini di sviluppo a 1536 dimensioni, più ~0,5 GB per TCGA, sul cluster gratuito da 4 GB di
  disco. Se non basta, si cancella la collezione Phikon (ricostruibile).

## Calendario

| Giorno | A. TCGA (Colab) | B–C. Controllore e testa polmone | D. Web app |
|---|---|---|---|
| Dom 25 | `data/tcga.py`, `fetch`, `stream` con `stage_dir`, test; misura di GDC su 4 vetrini; lotto 1 in download (CPU, notte) | — | — |
| Lun 26 | Lotto 1 in embedding (GPU); lotto 2 in download | Protocolli E18 ed E19 fissati in esperimenti.md | Scheletro: lista dei casi, viewer DZI, overlay QC |
| Mar 27 | Lotto 2 in embedding; copia del lotto 1 sul Mac, `verify` | E18 e controllore; E14b finito: dvc su H-optimus-0, indice Qdrant | Report della testa linfonodo, heatmap di attenzione |
| Mer 28 | Copia del lotto 2, `verify` | `train_head head=nsclc_subtype` (E19) | Report del controllore, overlay OOD |
| Gio 29 | — | Risultati di E19, testa registrata | Instradamento alla testa polmone, casi simili |
| Ven 30 | — | — | Feedback, banda "solo ricerca", prova completa sui vetrini della demo |
| Sab 31 | README, stato nel piano, memoria dei risultati | | Demo |

Il margine è il venerdì. Le parti si toccano solo nel report: se il lotto 2 slitta, la demo va con
linfonodo e controllore e la testa polmone entra appena arrivano gli embedding; se slitta il lotto 1, la
demo va con il solo linfonodo.

## Decisioni (25/10/2026)

| Tema | Decisione |
|---|---|
| Moduli tumore | Almeno due: `ln_metastasis` (M4) e un secondo; proposto `nsclc_subtype` (M5, polmone) |
| Download | Prima su Drive (runtime CPU), poi embedding (runtime GPU), a lotti |
| Criteri | Da MVP, più permissivi; un pezzo sotto criterio entra comunque nella demo con i suoi numeri |
| Testa non validata | Resta come oggi: rinvio "versione non validata" con tutti i motivi |
| Campione TCGA del controllore | 12 pazienti per organo per sito, 4 siti comuni |

Ancora aperti: la scelta del secondo modulo (polmone proposto, seno duttale/lobulare in alternativa); il
piano generale va aggiornato ("controllore su 5 tessuti noti più un tessuto mai visto, due teste");
E10 su H-optimus-0 e ITC dopo l'MVP.
