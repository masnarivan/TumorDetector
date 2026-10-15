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
| M2 Embedding | Backbone scelto da configurazione, estrazione deterministica e riprendibile, store su disco e in pgvector | `tumordetector/backbones`, `embed`, `vectordb` |
| Baseline | ABMIL a livello di vetrino sugli embedding, con protocollo di validazione, report automatico e registry MLflow | `tumordetector/mil` |
| M3–M9 | Non iniziati | |

## Pipeline

```
manifest ──> tile_qc ──> embed ──┬──> index      PostgreSQL + pgvector
  (git)      data/tiles  data/embeddings/<backbone>
             data/qc             └──> baseline   data/reports/<backbone>/abmil
splits (git) ─────────────────────────┘
```

Ogni stadio è `td task=<nome>`, configurato da Hydra (`conf/`) e orchestrato da DVC (`dvc.yaml`).
Ogni vetrino porta con sé hash del file, versione del backbone, parametri di tiling e hash degli
embedding (`data/embeddings/<backbone>/<vetrino>.json`); ogni estrazione è una run MLflow.

## Uso

Servono [uv](https://docs.astral.sh/uv/) e Docker.

```bash
uv sync
```

```bash
docker compose up -d
```

```bash
uv run dvc repro
```

`dvc repro` riesegue solo gli stadi il cui codice, configurazione o input è cambiato. I vetrini da
elaborare sono in `conf/data/camelyon16.yaml` (`slides`); la cartella dei `.tif` è `raw_dir`, o la
variabile `TD_RAW_DIR`.

Singoli stadi e override:

```bash
uv run td task=tile "data.slides=[tumor_031]"
```

```bash
uv run td task=embed backbone=dummy embed.device=cpu
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

## Vector DB

`td task=index` carica in pgvector gli embedding presenti su disco (tutti quelli del manifest, anche
se il `.tif` non c'è più). Carica solo i vetrini nuovi o cambiati, riconosciuti dall'hash degli
embedding; in un caricamento in blocco l'indice HNSW viene costruito una volta sola alla fine. I
vettori sono `halfvec` (float16, come su disco). Dopo un cambio di schema la tabella va ricreata:

```bash
uv run td task=index vectordb.rebuild=true
```

## Licenze e dipendenze

Modelli, dataset e strumenti sono registrati in [THIRD_PARTY.md](THIRD_PARTY.md), con lo stato di
verifica di ogni licenza. Il codice di questo repository è rilasciato con licenza [Apache 2.0](LICENSE).
