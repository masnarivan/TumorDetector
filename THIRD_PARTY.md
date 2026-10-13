# Dipendenze di terze parti

Registro di modelli, dataset e strumenti usati dal progetto. Regola: niente entra nella pipeline
senza una riga qui. Le librerie Python sono bloccate in `uv.lock`; le loro licenze sono controllate
in CI da `scripts/check_licenses.py` (`--list` per l'elenco completo).

Stato: **verificata** = licenza letta alla fonte da noi; **da verificare** = riportata da memoria o
da fonti secondarie, da confermare sulla pagina ufficiale prima dell'uso indicato.

## Modelli

| Modello | Versione usata | Licenza | Uso consentito qui | Stato | Fonte |
|---|---|---|---|---|---|
| H-optimus-0 (Bioptimus) | commit `b145cc1e6c6b` | Apache 2.0, accesso controllato | Backbone dell'MVP, anche binario prodotto | verificata il 2026-10-13 sui metadati della scheda Hugging Face (`license: apache-2.0`) | https://huggingface.co/bioptimus/H-optimus-0 |
| Phikon (Owkin) | commit `057cc0295895` | Owkin non-commercial (su Hugging Face: `license: other`) | Solo sviluppo locale e test della pipeline; mai nel binario prodotto | da verificare: leggere il testo della licenza | https://huggingface.co/owkin/phikon |

## Dataset

| Dataset | Licenza | Uso | Stato | Fonte |
|---|---|---|---|---|
| CAMELYON16 | CC0 | Sviluppo e baseline; 399 vetrini, 2 centri | da verificare | https://camelyon17.grand-challenge.org/Data/ |

## Strumenti candidati, non ancora integrati

| Strumento | Ruolo previsto | Licenza | Stato | Nota |
|---|---|---|---|---|
| GrandQC | Backend QC con artefatti (M1) | da verificare | da verificare | Verificare se la licenza di codice e pesi ammette l'uso non di ricerca prima di integrarlo |
| Trident | Tiling / estrazione | da verificare | da verificare | Non usato: tiling ed estrazione sono codice nostro (`tumordetector.wsi`, `tumordetector.embed`) |

## Librerie con licenza da tenere d'occhio

| Libreria | Licenza | Nota |
|---|---|---|
| openslide-python, openslide-bin | LGPL-2.1 | Usata come libreria, non modificata |
| psycopg | LGPL-3.0 | Usata come libreria, non modificata |
| dvc (solo sviluppo) | Apache 2.0, con dipendenze GPL (grandalf, pygit2) | Strumento di sviluppo, non distribuito con il sistema |

## Codice riusato

I moduli portati dai prototipi dello stesso autore (`wsi-embeddings`, `mil-camelyon16`) riportano la
provenienza nell'intestazione del file. Nessun codice di terzi è stato copiato.
