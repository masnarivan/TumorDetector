# Report di validazione — head-ln_metastasis-phikon

**Esito della batteria: NON SUPERATA** (media su 3 semi)

- ECE calibrata peggiore in leave-one-center-out 0.313, richiesto <= 0.1
- Specificità peggiore in leave-one-center-out 0.485, richiesto >= 0.8
- AUROC del probe sul centro (vetrini negativi) 0.995, richiesto <= 0.8

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
| Ricetta | `balanced` |
| Calibrazione | `temperature, 3 fold interni nel LOCO` |
| Semi | `[0, 1, 2] (modello e temperatura salvati: seme 0)` |
| Versione codice | `b350cfd35018b0c7586f46b4b25d849b0042129e` |
| Vetrini di sviluppo con embedding | 771 |
| Vetrini del cohort lasciati fuori | 0 |

## Risultati

Media su 3 semi (0, 1, 2). Probabilità calibrate con la temperatura (in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della rotazione, stimata senza il centro escluso).

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, calibrata | 771 | 275 | 0.985 | 0.962 | 0.961 | 0.962 | 0.033 | 0.037 |
| Cross-validation, grezza | 771 | 275 | 0.985 | 0.962 | 0.961 | 0.962 | 0.032 | 0.031 |
| Leave-one-center-out, held-out cwz | 93 | 35 | 0.978 | 0.962 | 0.759 | 0.860 | 0.106 | 0.156 |
| Leave-one-center-out, held-out radboud | 334 | 120 | 0.978 | 0.961 | 0.964 | 0.963 | 0.037 | 0.062 |
| Leave-one-center-out, held-out rijnstate | 92 | 32 | 0.972 | 0.938 | 0.994 | 0.966 | 0.025 | 0.019 |
| Leave-one-center-out, held-out utrecht | 252 | 88 | 0.986 | 0.989 | 0.490 | 0.739 | 0.194 | 0.313 |

Centro escluso peggiore (per seme, poi media): AUROC **0.967**, ECE calibrata **0.313** (grezza 0.318), specificità **0.485**.

Temperature (media sui semi): global 1.773, held-out cwz 1.798, held-out radboud 1.918, held-out rijnstate 1.620, held-out utrecht 1.793.

### Per centro e per dominio

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, cwz | 93 | 35 | 0.961 | 0.886 | 0.954 | 0.920 | 0.057 | 0.064 |
| Cross-validation, radboud | 334 | 120 | 0.990 | 0.972 | 0.944 | 0.958 | 0.038 | 0.059 |
| Cross-validation, rijnstate | 92 | 32 | 0.968 | 0.927 | 0.978 | 0.952 | 0.036 | 0.040 |
| Cross-validation, utrecht | 252 | 88 | 0.998 | 0.992 | 0.980 | 0.986 | 0.017 | 0.038 |
| Cross-validation, camelyon16:radboud | 245 | 95 | 0.987 | 0.972 | 0.924 | 0.948 | 0.048 | 0.075 |
| Cross-validation, camelyon16:utrecht | 154 | 65 | 0.997 | 0.990 | 0.981 | 0.986 | 0.017 | 0.037 |
| Cross-validation, camelyon17:cwz | 93 | 35 | 0.961 | 0.886 | 0.954 | 0.920 | 0.057 | 0.064 |
| Cross-validation, camelyon17:radboud | 89 | 25 | 0.997 | 0.973 | 0.990 | 0.981 | 0.010 | 0.024 |
| Cross-validation, camelyon17:rijnstate | 92 | 32 | 0.968 | 0.927 | 0.978 | 0.952 | 0.036 | 0.040 |
| Cross-validation, camelyon17:utrecht | 98 | 23 | 0.998 | 1.000 | 0.978 | 0.989 | 0.017 | 0.044 |
| held-out cwz, camelyon17:cwz | 93 | 35 | 0.978 | 0.962 | 0.759 | 0.860 | 0.106 | 0.156 |
| held-out radboud, camelyon16:radboud | 245 | 95 | 0.968 | 0.951 | 0.949 | 0.950 | 0.049 | 0.079 |
| held-out radboud, camelyon17:radboud | 89 | 25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.003 | 0.023 |
| held-out rijnstate, camelyon17:rijnstate | 92 | 32 | 0.972 | 0.938 | 0.994 | 0.966 | 0.025 | 0.019 |
| held-out utrecht, camelyon16:utrecht | 154 | 65 | 0.996 | 1.000 | 0.348 | 0.674 | 0.210 | 0.330 |
| held-out utrecht, camelyon17:utrecht | 98 | 23 | 0.962 | 0.957 | 0.658 | 0.807 | 0.170 | 0.289 |

### Robustezza al centro (modello finale)

- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: **0.995** sui vetrini negativi, 0.995 su tutti (0,5 = centro non leggibile).
- Robustness Index sulle tile: **2.704** (> 1: domina la biologia); vicini dallo stesso centro 0.971, su 75391 tile.

### Localizzazione

AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori fold): **0.988**.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.985 | 0.001 | 0.984 | 0.986 | 0.986 | 0.986 | 0.984 |
| cv/ece | 0.037 | 0.023 | 0.021 | 0.064 | 0.021 | 0.064 | 0.027 |
| loco_worst_auroc | 0.967 | 0.008 | 0.958 | 0.974 | 0.974 | 0.958 | 0.967 |
| loco_worst_ece | 0.313 | 0.061 | 0.271 | 0.384 | 0.384 | 0.271 | 0.286 |
| loco_worst_ece_raw | 0.318 | 0.086 | 0.255 | 0.416 | 0.416 | 0.255 | 0.284 |
| loco_worst_specificity | 0.485 | 0.202 | 0.256 | 0.638 | 0.256 | 0.638 | 0.561 |
| robustness/center_probe_auroc | 0.995 | 0.006 | 0.989 | 0.999 | 0.998 | 0.989 | 0.999 |
| robustness/center_probe_auroc_all | 0.995 | 0.003 | 0.992 | 0.997 | 0.992 | 0.997 | 0.995 |
| robustness/robustness_index | 2.704 | 0.290 | 2.374 | 2.915 | 2.824 | 2.374 | 2.915 |
| temperature/global | 1.773 | 0.055 | 1.710 | 1.808 | 1.710 | 1.808 | 1.802 |
| attention_auroc_mean | 0.988 | 0.002 | 0.986 | 0.990 | 0.986 | 0.987 | 0.990 |
| loco/held-out cwz/auroc | 0.978 | 0.012 | 0.967 | 0.991 | 0.974 | 0.991 | 0.967 |
| loco/held-out cwz/sensitivity | 0.962 | 0.044 | 0.914 | 1.000 | 0.971 | 1.000 | 0.914 |
| loco/held-out cwz/specificity | 0.759 | 0.130 | 0.638 | 0.897 | 0.741 | 0.638 | 0.897 |
| loco/held-out cwz/ece | 0.156 | 0.072 | 0.081 | 0.224 | 0.164 | 0.224 | 0.081 |
| loco/held-out radboud/auroc | 0.978 | 0.005 | 0.974 | 0.984 | 0.984 | 0.974 | 0.977 |
| loco/held-out radboud/sensitivity | 0.961 | 0.017 | 0.942 | 0.975 | 0.975 | 0.942 | 0.967 |
| loco/held-out radboud/specificity | 0.964 | 0.027 | 0.944 | 0.995 | 0.944 | 0.995 | 0.953 |
| loco/held-out radboud/ece | 0.062 | 0.025 | 0.045 | 0.090 | 0.090 | 0.045 | 0.050 |
| loco/held-out rijnstate/auroc | 0.972 | 0.012 | 0.958 | 0.981 | 0.981 | 0.958 | 0.978 |
| loco/held-out rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco/held-out rijnstate/specificity | 0.994 | 0.010 | 0.983 | 1.000 | 1.000 | 0.983 | 1.000 |
| loco/held-out rijnstate/ece | 0.019 | 0.008 | 0.013 | 0.029 | 0.016 | 0.029 | 0.013 |
| loco/held-out utrecht/auroc | 0.986 | 0.011 | 0.974 | 0.997 | 0.997 | 0.974 | 0.986 |
| loco/held-out utrecht/sensitivity | 0.989 | 0.011 | 0.977 | 1.000 | 1.000 | 0.977 | 0.989 |
| loco/held-out utrecht/specificity | 0.490 | 0.208 | 0.256 | 0.652 | 0.256 | 0.652 | 0.561 |
| loco/held-out utrecht/ece | 0.313 | 0.061 | 0.271 | 0.384 | 0.384 | 0.271 | 0.286 |
| loco_by_domain/held-out cwz/camelyon17:cwz/auroc | 0.978 | 0.012 | 0.967 | 0.991 | 0.974 | 0.991 | 0.967 |
| loco_by_domain/held-out cwz/camelyon17:cwz/sensitivity | 0.962 | 0.044 | 0.914 | 1.000 | 0.971 | 1.000 | 0.914 |
| loco_by_domain/held-out cwz/camelyon17:cwz/specificity | 0.759 | 0.130 | 0.638 | 0.897 | 0.741 | 0.638 | 0.897 |
| loco_by_domain/held-out cwz/camelyon17:cwz/ece | 0.156 | 0.072 | 0.081 | 0.224 | 0.164 | 0.224 | 0.081 |
| loco_by_domain/held-out radboud/camelyon16:radboud/auroc | 0.968 | 0.008 | 0.960 | 0.975 | 0.975 | 0.960 | 0.969 |
| loco_by_domain/held-out radboud/camelyon16:radboud/sensitivity | 0.951 | 0.022 | 0.926 | 0.968 | 0.968 | 0.926 | 0.958 |
| loco_by_domain/held-out radboud/camelyon16:radboud/specificity | 0.949 | 0.039 | 0.920 | 0.993 | 0.920 | 0.993 | 0.933 |
| loco_by_domain/held-out radboud/camelyon16:radboud/ece | 0.079 | 0.032 | 0.055 | 0.115 | 0.115 | 0.055 | 0.065 |
| loco_by_domain/held-out radboud/camelyon17:radboud/auroc | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/specificity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/ece | 0.023 | 0.004 | 0.019 | 0.026 | 0.026 | 0.019 | 0.024 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/auroc | 0.972 | 0.012 | 0.958 | 0.981 | 0.981 | 0.958 | 0.978 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/specificity | 0.994 | 0.010 | 0.983 | 1.000 | 1.000 | 0.983 | 1.000 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/ece | 0.019 | 0.008 | 0.013 | 0.029 | 0.016 | 0.029 | 0.013 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/auroc | 0.996 | 0.002 | 0.994 | 0.998 | 0.997 | 0.994 | 0.998 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/specificity | 0.348 | 0.213 | 0.135 | 0.562 | 0.135 | 0.562 | 0.348 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/ece | 0.330 | 0.050 | 0.278 | 0.378 | 0.378 | 0.278 | 0.334 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/auroc | 0.962 | 0.035 | 0.926 | 0.996 | 0.996 | 0.926 | 0.964 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/sensitivity | 0.957 | 0.043 | 0.913 | 1.000 | 1.000 | 0.913 | 0.957 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/specificity | 0.658 | 0.225 | 0.400 | 0.813 | 0.400 | 0.760 | 0.813 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/ece | 0.289 | 0.093 | 0.210 | 0.392 | 0.392 | 0.265 | 0.210 |

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
