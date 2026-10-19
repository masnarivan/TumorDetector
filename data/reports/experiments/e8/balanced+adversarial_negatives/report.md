# Report di validazione — head-ln_metastasis-phikon

**Esito della batteria: NON SUPERATA** (media su 3 semi)

- ECE calibrata peggiore in leave-one-center-out 0.301, richiesto <= 0.1
- Specificità peggiore in leave-one-center-out 0.561, richiesto >= 0.8
- AUROC del probe sul centro (vetrini negativi) 0.997, richiesto <= 0.8

Solo uso di ricerca. Le soglie della batteria sono proposte iniziali, da fissare con i patologi.

## Provenienza

| | |
|---|---|
| Modello | `head-ln_metastasis-phikon` |
| Testa | `ln_metastasis v1 (M4)` |
| Cohort | `data/manifests/heads/ln_metastasis.csv (sha256 d28e4c48b675)` |
| Collezione embedding | `phikon__057cc0295895` |
| Versione backbone | `057cc0295895c2df3dd7681a89680da6015cbefe` |
| Iperparametri | `{'hidden': 256, 'dropout': 0.25, 'lr': 0.0002, 'weight_decay': 0.0001, 'epochs': 30, 'max_tiles': 4096, 'threshold': 0.5, 'normalize': 'none', 'threads': 1}` |
| Ricetta | `balanced, adversarial_negatives` |
| Calibrazione | `temperature, 3 fold interni nel LOCO` |
| Semi | `[0, 1, 2] (modello e temperatura salvati: seme 0)` |
| Versione codice | `b350cfd35018b0c7586f46b4b25d849b0042129e+dirty` |
| Vetrini di sviluppo con embedding | 771 |
| Vetrini del cohort lasciati fuori | 0 |

## Risultati

Media su 3 semi (0, 1, 2). Probabilità calibrate con la temperatura (in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della rotazione, stimata senza il centro escluso).

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, calibrata | 771 | 275 | 0.980 | 0.959 | 0.919 | 0.939 | 0.057 | 0.093 |
| Cross-validation, grezza | 771 | 275 | 0.980 | 0.959 | 0.919 | 0.939 | 0.056 | 0.066 |
| Leave-one-center-out, held-out cwz | 93 | 35 | 0.978 | 0.952 | 0.718 | 0.835 | 0.116 | 0.171 |
| Leave-one-center-out, held-out radboud | 334 | 120 | 0.982 | 0.975 | 0.917 | 0.946 | 0.051 | 0.089 |
| Leave-one-center-out, held-out rijnstate | 92 | 32 | 0.952 | 0.938 | 0.989 | 0.963 | 0.028 | 0.017 |
| Leave-one-center-out, held-out utrecht | 252 | 88 | 0.994 | 0.996 | 0.663 | 0.829 | 0.163 | 0.283 |

Centro escluso peggiore (per seme, poi media): AUROC **0.952**, ECE calibrata **0.301** (grezza 0.284), specificità **0.561**.

Temperature (media sui semi): global 2.117, held-out cwz 2.093, held-out radboud 2.258, held-out rijnstate 1.633, held-out utrecht 2.534.

### Per centro e per dominio

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, cwz | 93 | 35 | 0.931 | 0.905 | 0.816 | 0.860 | 0.120 | 0.165 |
| Cross-validation, radboud | 334 | 120 | 0.986 | 0.978 | 0.910 | 0.944 | 0.057 | 0.105 |
| Cross-validation, rijnstate | 92 | 32 | 0.973 | 0.938 | 0.928 | 0.933 | 0.053 | 0.078 |
| Cross-validation, utrecht | 252 | 88 | 0.994 | 0.962 | 0.965 | 0.964 | 0.036 | 0.071 |
| Cross-validation, camelyon16:radboud | 245 | 95 | 0.981 | 0.975 | 0.896 | 0.935 | 0.065 | 0.111 |
| Cross-validation, camelyon16:utrecht | 154 | 65 | 0.995 | 0.964 | 0.970 | 0.967 | 0.034 | 0.067 |
| Cross-validation, camelyon17:cwz | 93 | 35 | 0.931 | 0.905 | 0.816 | 0.860 | 0.120 | 0.165 |
| Cross-validation, camelyon17:radboud | 89 | 25 | 0.999 | 0.987 | 0.943 | 0.965 | 0.035 | 0.092 |
| Cross-validation, camelyon17:rijnstate | 92 | 32 | 0.973 | 0.938 | 0.928 | 0.933 | 0.053 | 0.078 |
| Cross-validation, camelyon17:utrecht | 98 | 23 | 0.990 | 0.957 | 0.960 | 0.958 | 0.039 | 0.085 |
| held-out cwz, camelyon17:cwz | 93 | 35 | 0.978 | 0.952 | 0.718 | 0.835 | 0.116 | 0.171 |
| held-out radboud, camelyon16:radboud | 245 | 95 | 0.974 | 0.968 | 0.900 | 0.934 | 0.061 | 0.096 |
| held-out radboud, camelyon17:radboud | 89 | 25 | 1.000 | 1.000 | 0.958 | 0.979 | 0.024 | 0.071 |
| held-out rijnstate, camelyon17:rijnstate | 92 | 32 | 0.952 | 0.938 | 0.989 | 0.963 | 0.028 | 0.017 |
| held-out utrecht, camelyon16:utrecht | 154 | 65 | 0.998 | 1.000 | 0.573 | 0.787 | 0.167 | 0.286 |
| held-out utrecht, camelyon17:utrecht | 98 | 23 | 0.984 | 0.986 | 0.769 | 0.877 | 0.157 | 0.279 |

### Robustezza al centro (modello finale)

- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: **0.997** sui vetrini negativi, 0.990 su tutti (0,5 = centro non leggibile).
- Robustness Index sulle tile: **2.376** (> 1: domina la biologia); vicini dallo stesso centro 0.974, su 75391 tile.

### Localizzazione

AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori fold): **0.990**.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.980 | 0.005 | 0.977 | 0.985 | 0.977 | 0.978 | 0.985 |
| cv/ece | 0.093 | 0.073 | 0.050 | 0.177 | 0.050 | 0.051 | 0.177 |
| loco_worst_auroc | 0.952 | 0.004 | 0.947 | 0.955 | 0.955 | 0.947 | 0.953 |
| loco_worst_ece | 0.301 | 0.009 | 0.293 | 0.310 | 0.310 | 0.300 | 0.293 |
| loco_worst_ece_raw | 0.284 | 0.029 | 0.250 | 0.305 | 0.305 | 0.250 | 0.295 |
| loco_worst_specificity | 0.561 | 0.102 | 0.483 | 0.677 | 0.524 | 0.677 | 0.483 |
| robustness/center_probe_auroc | 0.997 | 0.003 | 0.994 | 0.999 | 0.994 | 0.999 | 0.999 |
| robustness/center_probe_auroc_all | 0.990 | 0.006 | 0.983 | 0.995 | 0.995 | 0.992 | 0.983 |
| robustness/robustness_index | 2.376 | 0.086 | 2.295 | 2.465 | 2.465 | 2.295 | 2.369 |
| temperature/global | 2.117 | 0.207 | 1.928 | 2.338 | 1.928 | 2.086 | 2.338 |
| attention_auroc_mean | 0.990 | 0.002 | 0.988 | 0.992 | 0.990 | 0.988 | 0.992 |
| loco/held-out cwz/auroc | 0.978 | 0.008 | 0.968 | 0.984 | 0.968 | 0.981 | 0.984 |
| loco/held-out cwz/sensitivity | 0.952 | 0.044 | 0.914 | 1.000 | 0.914 | 0.943 | 1.000 |
| loco/held-out cwz/specificity | 0.718 | 0.225 | 0.483 | 0.931 | 0.741 | 0.931 | 0.483 |
| loco/held-out cwz/ece | 0.171 | 0.112 | 0.072 | 0.293 | 0.147 | 0.072 | 0.293 |
| loco/held-out radboud/auroc | 0.982 | 0.001 | 0.981 | 0.983 | 0.981 | 0.983 | 0.981 |
| loco/held-out radboud/sensitivity | 0.975 | 0.000 | 0.975 | 0.975 | 0.975 | 0.975 | 0.975 |
| loco/held-out radboud/specificity | 0.917 | 0.034 | 0.879 | 0.939 | 0.939 | 0.879 | 0.935 |
| loco/held-out radboud/ece | 0.089 | 0.038 | 0.051 | 0.127 | 0.051 | 0.127 | 0.089 |
| loco/held-out rijnstate/auroc | 0.952 | 0.004 | 0.947 | 0.955 | 0.955 | 0.947 | 0.953 |
| loco/held-out rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco/held-out rijnstate/specificity | 0.989 | 0.010 | 0.983 | 1.000 | 0.983 | 0.983 | 1.000 |
| loco/held-out rijnstate/ece | 0.017 | 0.013 | 0.005 | 0.031 | 0.013 | 0.031 | 0.005 |
| loco/held-out utrecht/auroc | 0.994 | 0.004 | 0.989 | 0.997 | 0.989 | 0.994 | 0.997 |
| loco/held-out utrecht/sensitivity | 0.996 | 0.007 | 0.989 | 1.000 | 0.989 | 1.000 | 1.000 |
| loco/held-out utrecht/specificity | 0.663 | 0.132 | 0.524 | 0.787 | 0.524 | 0.677 | 0.787 |
| loco/held-out utrecht/ece | 0.283 | 0.038 | 0.240 | 0.310 | 0.310 | 0.300 | 0.240 |
| loco_by_domain/held-out cwz/camelyon17:cwz/auroc | 0.978 | 0.008 | 0.968 | 0.984 | 0.968 | 0.981 | 0.984 |
| loco_by_domain/held-out cwz/camelyon17:cwz/sensitivity | 0.952 | 0.044 | 0.914 | 1.000 | 0.914 | 0.943 | 1.000 |
| loco_by_domain/held-out cwz/camelyon17:cwz/specificity | 0.718 | 0.225 | 0.483 | 0.931 | 0.741 | 0.931 | 0.483 |
| loco_by_domain/held-out cwz/camelyon17:cwz/ece | 0.171 | 0.112 | 0.072 | 0.293 | 0.147 | 0.072 | 0.293 |
| loco_by_domain/held-out radboud/camelyon16:radboud/auroc | 0.974 | 0.005 | 0.969 | 0.979 | 0.975 | 0.979 | 0.969 |
| loco_by_domain/held-out radboud/camelyon16:radboud/sensitivity | 0.968 | 0.000 | 0.968 | 0.968 | 0.968 | 0.968 | 0.968 |
| loco_by_domain/held-out radboud/camelyon16:radboud/specificity | 0.900 | 0.023 | 0.873 | 0.913 | 0.913 | 0.873 | 0.913 |
| loco_by_domain/held-out radboud/camelyon16:radboud/ece | 0.096 | 0.027 | 0.066 | 0.114 | 0.066 | 0.114 | 0.109 |
| loco_by_domain/held-out radboud/camelyon17:radboud/auroc | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/specificity | 0.958 | 0.059 | 0.891 | 1.000 | 1.000 | 0.891 | 0.984 |
| loco_by_domain/held-out radboud/camelyon17:radboud/ece | 0.071 | 0.082 | 0.010 | 0.164 | 0.010 | 0.164 | 0.038 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/auroc | 0.952 | 0.004 | 0.947 | 0.955 | 0.955 | 0.947 | 0.953 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/specificity | 0.989 | 0.010 | 0.983 | 1.000 | 0.983 | 0.983 | 1.000 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/ece | 0.017 | 0.013 | 0.005 | 0.031 | 0.013 | 0.031 | 0.005 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/auroc | 0.998 | 0.000 | 0.998 | 0.999 | 0.998 | 0.998 | 0.999 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/specificity | 0.573 | 0.254 | 0.292 | 0.787 | 0.292 | 0.640 | 0.787 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/ece | 0.286 | 0.054 | 0.229 | 0.337 | 0.337 | 0.290 | 0.229 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/auroc | 0.984 | 0.009 | 0.974 | 0.993 | 0.974 | 0.983 | 0.993 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/sensitivity | 0.986 | 0.025 | 0.957 | 1.000 | 0.957 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/specificity | 0.769 | 0.043 | 0.720 | 0.800 | 0.800 | 0.720 | 0.787 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/ece | 0.279 | 0.031 | 0.257 | 0.315 | 0.267 | 0.315 | 0.257 |

## Esecuzioni (seme 0)

| Gruppo | Valutazione | Vetrini di training | Vetrini valutati | Stato | Motivo |
|---|---|---|---|---|---|
| cv | fold0 | 621 | 150 | ok |  |
| cv | fold1 | 617 | 154 | ok |  |
| cv | fold2 | 617 | 154 | ok |  |
| cv | fold3 | 616 | 155 | ok |  |
| cv | fold4 | 613 | 158 | ok |  |
| loco-calibration | held-out cwz, inner 0 | 410 | 268 | ok |  |
| loco-calibration | held-out cwz, inner 1 | 403 | 275 | ok |  |
| loco-calibration | held-out cwz, inner 2 | 543 | 135 | ok |  |
| loco | held-out cwz | 678 | 93 | ok |  |
| loco-calibration | held-out radboud, inner 0 | 267 | 170 | ok |  |
| loco-calibration | held-out radboud, inner 1 | 258 | 179 | ok |  |
| loco-calibration | held-out radboud, inner 2 | 349 | 88 | ok |  |
| loco | held-out radboud | 437 | 334 | ok |  |
| loco-calibration | held-out rijnstate, inner 0 | 411 | 268 | ok |  |
| loco-calibration | held-out rijnstate, inner 1 | 404 | 275 | ok |  |
| loco-calibration | held-out rijnstate, inner 2 | 543 | 136 | ok |  |
| loco | held-out rijnstate | 679 | 92 | ok |  |
| loco-calibration | held-out utrecht, inner 0 | 310 | 209 | ok |  |
| loco-calibration | held-out utrecht, inner 1 | 312 | 207 | ok |  |
| loco-calibration | held-out utrecht, inner 2 | 416 | 103 | ok |  |
| loco | held-out utrecht | 519 | 252 | ok |  |
| final | all development slides | 771 | 0 | ok |  |

## Copertura della batteria di promozione

| Voce del piano | Coperta da questo report |
|---|---|
| Leave-one-center-out, risultato peggiore | sì, 4 centri, probabilità calibrate |
| Test esterno bloccato | no: è un task a parte, una consultazione per versione |
| Robustezza al centro (Robustness Index, probe lineare sul centro) | sì, sul modello finale |
| Calibrazione (ECE) | sì: temperatura globale; in leave-one-center-out stimata senza il centro escluso |
| Copertura conformal | no |
| OOD | no |
| Metriche alla prevalenza reale, tasso di rinvio | no |
| Sottogruppi (scanner, tipo di campione) | per centro e per dominio (dataset × centro) |
| Regressione sui casi difficili | no |
