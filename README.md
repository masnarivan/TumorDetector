# TumorDetector

Sistema di supporto diagnostico in istopatologia: analizza vetrini H&E, segnala cosa vede con una
confidenza esplicita e rinvia al patologo i casi che non riconosce. **Solo uso di ricerca.**

Piano e specifiche: [Sistema di supporto diagnostico in istopatologia](https://claude.ai/artifact/ULdentTCEKNDVvEn354wo9).
Questo repository è alla fase F0: lo scheletro riproducibile su cui si innestano i moduli.

## Cosa c'è oggi

| Modulo del piano | Stato | Codice |
|---|---|---|
| M0 Ingestione | Manifest CAMELYON16 nello schema comune; i vetrini con metadati mancanti sono bloccati con motivo | `tumordetector/data` |
| M1 Controllo qualità | Maschera del tessuto ed esito `pass` / `refer` con motivo. Gli artefatti (GrandQC) non sono ancora rilevati | `tumordetector/qc` |
| M2 Embedding | Backbone scelto da configurazione, estrazione deterministica e riprendibile, store su disco; nel vector DB (Qdrant) regioni e prototipi per vetrino | `tumordetector/backbones`, `embed`, `vectordb` |
| Baseline | ABMIL a livello di vetrino sugli embedding, con protocollo di validazione, report automatico e registry MLflow | `tumordetector/mil` |
| M3–M9 | Non iniziati | |

## Pipeline

```
manifest ──> stream ──────────────────────┬──> index      Qdrant: regioni + prototipi
  (git)      data/tiles, data/qc,         │
             data/embeddings/<backbone>   └──> baseline   data/reports/<backbone>/abmil
splits (git) ─────────────────────────────────┘
```

Ogni stadio è `td task=<nome>` (un modulo in `tumordetector/tasks/`), configurato da Hydra (`conf/`)
e orchestrato da DVC (`dvc.yaml`). Ogni stadio dipende solo dal codice che esegue e dalla
configurazione che legge: lo controlla `tests/test_dvc.py`.
Ogni vetrino porta con sé hash del file, versione del backbone, parametri di tiling e hash degli
embedding (`data/embeddings/<backbone>/<vetrino>.json`); ogni estrazione è una run MLflow.

## Uso

Serve [uv](https://docs.astral.sh/uv/). Il vector DB è un cluster Qdrant: URL e API key vanno in
`.env` (escluso da git), letto da `td` all'avvio:

```
TD_QDRANT_URL=https://<cluster>.cloud.qdrant.io
TD_QDRANT_API_KEY=<chiave>
```

```bash
uv sync
```

```bash
uv run dvc repro
```

`dvc repro` riesegue solo gli stadi il cui codice, configurazione o input è cambiato. `stream`
elabora tutto il manifest: scarica un vetrino alla volta e rifà solo quelli il cui file, tiling,
soglie di QC o griglia di tile sono cambiati. I suoi output sono `persist`, quindi DVC non li
cancella mai prima di rieseguirlo (ricostruirli vorrebbe dire riscaricare ~700 GB). Se cambia il
*codice* di tiling o di embedding, DVC riesegue lo stadio, ma lo stream non ricalcola i vetrini già
aggiornati secondo quei criteri: se la modifica deve cambiare gli output, vanno cancellati prima.

Per lo sviluppo sui pochi vetrini presenti in locale (`raw_dir`, o la variabile `TD_RAW_DIR`) ci
sono `td task=tile` e `td task=embed`, fuori da DVC:

```bash
uv run td task=tile "data.slides=[tumor_031]"
```

```bash
uv run td task=embed backbone=dummy embed.device=cpu
```

Scrivono nelle stesse cartelle di `stream`: dopo averli usati, prima di `dvc commit`, controlla che
gli output corrispondano alla provenienza registrata per ogni vetrino:

```bash
uv run td task=verify backbone=phikon
```

Esperimenti:

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Test, lint e controllo licenze (gli stessi della CI):

```bash
uv run pytest -q && uv run ruff check && uv run scripts/check_licenses.py
```

## Baseline e validazione

`td task=train` addestra un ABMIL sugli embedding ed esegue sempre lo stesso protocollo:

1. cross-validation a 5 fold dentro lo split di sviluppo, con i fold letti da
   `data/manifests/camelyon16_splits.csv` (stratificati per etichetta e centro, mai rigenerati in
   modo implicito);
2. leave-one-center-out: conta il centro peggiore, non la media;
3. un modello addestrato su tutto lo sviluppo e valutato una volta sullo split di test ufficiale.

Il protocollo gira una volta per seme (`mil.seeds`, default 0, 1, 2, in processi paralleli) e la
batteria legge la media: con un solo seme la variabilità è grande quanto le differenze da giudicare
(esperimento E4). Il report riporta media, deviazione standard e valore di ogni seme; il modello
salvato è quello del primo seme. Ogni addestramento usa `mil.threads` thread (default 1): con lo
stesso seme e lo stesso numero di thread il modello è identico, con un numero diverso no.

Il risultato è `data/reports/<backbone>/abmil/report.md` (versionato in git), allegato alla run
MLflow insieme al modello. Nel registry ogni modello addestrato riceve l'alias `candidate`;
`validated` solo se supera le soglie di `gate` in `conf/config.yaml`; `production` non viene mai
assegnato dal codice. Sotto `gate.min_slides` vetrini l'esito è "dati insufficienti": la run serve
solo a verificare che il codice funzioni. Il report elenca anche le voci della batteria del piano
non ancora coperte.

Gli esperimenti sugli embedding, con protocollo fissato prima dei risultati, sono in
[docs/esperimenti.md](docs/esperimenti.md).

## TCGA: altri tessuti per l'MVP

Un campione fisso di 392 vetrini diagnostici TCGA (seno, colon, prostata, polmone, rene) per il
controllore e la testa del polmone: [docs/mvp.md](docs/mvp.md). Il manifest (`td task=manifest data=tcga`,
dall'API GDC) è in git e non si rigenera in modo implicito. I vetrini si scaricano prima e si embeddano dopo:

```bash
uv run td task=fetch data=tcga fetch.batch=1 fetch.workers=16
```

`fetch` scarica solo, con più download in parallelo (GDC dà ~4 MB/s per connessione) e l'md5 controllato.
`stream` usa poi i file già in `raw_dir`; con `stream.stage_dir` li copia su un disco locale prima del
tiling e con `stream.delete_raw=true` li cancella dopo l'embedding. Su Colab:
`notebooks/tcga_fetch_colab.ipynb` (CPU, verso Drive) e `notebooks/tcga_extract_colab.ipynb` (GPU).

## Teste e cohort multi-centro

Progetto del training multi-centro con CAMELYON17 e delle teste per tessuto:
[docs/training-multicentro.md](docs/training-multicentro.md). Una testa è un file in `conf/head/`
(sedi, dataset, mappa diagnosi → etichetta, dominio, centri esterni). Il suo cohort unisce i manifest
dei dataset e assegna ruolo (sviluppo o esterno bloccato) e fold di CV, raggruppati per paziente:

```bash
uv run td task=cohort head=ln_metastasis
```

Scrive `data/manifests/heads/<testa>.csv` e `<testa>_excluded.csv` (con il motivo di ogni esclusione),
versionati in git e mai riscritti in modo implicito (`head.overwrite=true`). Un test verifica che il
cohort salvato corrisponda ancora ai manifest. Per `ln_metastasis`: 771 vetrini di sviluppo in 6
domini (dataset × centro), 92 esterni (LPON), 36 ITC escluse.

`td task=train_head head=<testa>` (stadio DVC `head-<testa>`) addestra la testa sui soli vetrini di
sviluppo del cohort; quelli esterni non vengono mai letti. Protocollo (esperimento E6):

1. cross-validation sui fold del cohort; le sue logit fuori fold danno **una temperatura globale**;
2. leave-one-centre-out su tutti i centri di sviluppo, con la temperatura stimata su fold interni
   dei soli centri di training;
3. modello finale su tutto lo sviluppo; sul modello finale, **probe lineare sul centro** dalla
   rappresentazione del vetrino e **Robustness Index** sulle tile.

Il gate è nella specifica della testa e comprende probe e Robustness Index. Il modello registrato
(`head-<testa>-<backbone>`) restituisce una logit; la temperatura è in `calibration.json` e nei tag
della versione. Report in `data/reports/<backbone>/heads/<testa>/`.

## Backbone

| Nome | Uso | Note |
|---|---|---|
| `h_optimus_0` | Backbone dell'MVP (1536-d) | Accesso controllato su Hugging Face. Troppo pesante per il Mac: si estrae su Colab con `notebooks/extract_colab.ipynb` |
| `phikon` | Sviluppo locale della pipeline (768-d) | Licenza non commerciale: mai nel binario prodotto |
| `dummy` | Test e CI | Proiezione casuale fissa, nessun peso da scaricare |

Le tile sono 224 px a 0,5 µm/px, l'input nativo di entrambi i modelli. Embedding di versioni diverse
non si mescolano mai: una cartella e una tabella per (backbone, versione).

## Estrazione su Colab

`td task=stream` scarica un vetrino alla volta, lo elabora e lo cancella, saltando quelli già fatti
e quelli già respinti dal QC con le stesse soglie.
Il notebook `notebooks/extract_colab.ipynb` lo esegue con gli embedding su Google Drive.
`extract_log.csv` registra per vetrino i secondi di download, attesa del download, tiling + QC ed
embedding.

Prima dell'estrazione completa, `notebooks/hoptimus_timing.ipynb` (Colab o Kaggle) misura su 7 vetrini
il modello da solo, la pipeline e la lettura delle tile, e proietta ore di GPU e spazio su tutti gli
899 vetrini dai conteggi di `notebooks/tile_counts.csv` (`uv run python scripts/tile_counts.py`).

## Vector DB

Le tile restano su disco (`data/embeddings`). `td task=index` carica in Qdrant, per ogni vetrino,
due livelli (`tumordetector/vectordb/reduce.py`), circa 400 vettori invece di ~10 mila:

- regioni: media degli embedding di ogni quadrato di 8 × 8 tile (~0,9 mm) con almeno 16 tile, per
  cercare casi simili su aree più grandi di una tile;
- prototipi: 256 tile scelte con k-center (ognuna è la più lontana da quelle già scelte), così
  anche il tessuto raro, tumore compreso, è rappresentato. In E3 sono un riferimento OOD buono
  quanto tutte le tile (`docs/esperimenti.md`).

Una collection per versione del backbone; ogni punto ha come payload vetrino, dataset, centro,
diagnosi, livello e posizione. Carica solo i vetrini nuovi, cambiati o caricati a metà, confrontando
l'hash degli embedding e il numero di punti sul server con `data/index/<backbone>.json`. Per
ricaricare tutto:

```bash
uv run td task=index vectordb.rebuild=true
```

Su una rete che ispeziona il TLS il certificato è firmato da una CA aziendale installata nel
sistema: il client verifica il TLS con il trust store del sistema operativo (`truststore`).

Il PostgreSQL + pgvector di `docker-compose.yml` serve solo a riprodurre E3
(`experiments/e3_ood.py`).

## Licenze e dipendenze

Modelli, dataset e strumenti sono registrati in [THIRD_PARTY.md](THIRD_PARTY.md), con lo stato di
verifica di ogni licenza. Il codice di questo repository è rilasciato con licenza [Apache 2.0](LICENSE).
