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
| M3–M9 | Non iniziati | |

## Pipeline

```
manifest ──> tile_qc ──> embed ──> index
  (git)      data/tiles  data/embeddings/<backbone>   PostgreSQL + pgvector
             data/qc
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

## Backbone

| Nome | Uso | Note |
|---|---|---|
| `h_optimus_0` | Backbone dell'MVP (1536-d) | Accesso controllato su Hugging Face. Troppo pesante per il Mac: si estrae su Colab con `notebooks/extract_colab.ipynb` |
| `phikon` | Sviluppo locale della pipeline (768-d) | Licenza non commerciale: mai nel binario prodotto |
| `dummy` | Test e CI | Proiezione casuale fissa, nessun peso da scaricare |

Le tile sono 224 px a 0,5 µm/px, l'input nativo di entrambi i modelli. Embedding di versioni diverse
non si mescolano mai: una cartella e una tabella per (backbone, versione).

## Estrazione su Colab

`td task=stream` scarica un vetrino alla volta, lo elabora e lo cancella, saltando quelli già fatti.
Il notebook `notebooks/extract_colab.ipynb` lo esegue con gli embedding su Google Drive.

## Licenze e dipendenze

Modelli, dataset e strumenti sono registrati in [THIRD_PARTY.md](THIRD_PARTY.md), con lo stato di
verifica di ogni licenza. Il codice di questo repository è rilasciato con licenza [Apache 2.0](LICENSE).
