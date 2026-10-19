# Report di validazione — head-ln_metastasis-phikon

**Esito della batteria: NON SUPERATA** (media su 3 semi)

- ECE calibrata peggiore in leave-one-center-out 0.277, richiesto <= 0.1
- Specificità peggiore in leave-one-center-out 0.541, richiesto >= 0.8
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
| Ricetta | `balanced, group_dro` |
| Calibrazione | `temperature, 3 fold interni nel LOCO` |
| Semi | `[0, 1, 2] (modello e temperatura salvati: seme 0)` |
| Versione codice | `b350cfd35018b0c7586f46b4b25d849b0042129e+dirty` |
| Vetrini di sviluppo con embedding | 771 |
| Vetrini del cohort lasciati fuori | 0 |

## Risultati

Media su 3 semi (0, 1, 2). Probabilità calibrate con la temperatura (in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della rotazione, stimata senza il centro escluso).

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, calibrata | 771 | 275 | 0.988 | 0.970 | 0.959 | 0.964 | 0.031 | 0.040 |
| Cross-validation, grezza | 771 | 275 | 0.988 | 0.970 | 0.959 | 0.964 | 0.031 | 0.031 |
| Leave-one-center-out, held-out cwz | 93 | 35 | 0.979 | 0.990 | 0.569 | 0.780 | 0.182 | 0.265 |
| Leave-one-center-out, held-out radboud | 334 | 120 | 0.980 | 0.961 | 0.933 | 0.947 | 0.052 | 0.088 |
| Leave-one-center-out, held-out rijnstate | 92 | 32 | 0.970 | 0.938 | 0.983 | 0.960 | 0.036 | 0.049 |
| Leave-one-center-out, held-out utrecht | 252 | 88 | 0.984 | 0.970 | 0.713 | 0.842 | 0.119 | 0.201 |

Centro escluso peggiore (per seme, poi media): AUROC **0.970**, ECE calibrata **0.277** (grezza 0.278), specificità **0.541**.

Temperature (media sui semi): global 1.612, held-out cwz 1.885, held-out radboud 1.900, held-out rijnstate 1.590, held-out utrecht 1.917.

### Per centro e per dominio

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, cwz | 93 | 35 | 0.980 | 0.933 | 0.925 | 0.929 | 0.050 | 0.057 |
| Cross-validation, radboud | 334 | 120 | 0.989 | 0.981 | 0.958 | 0.969 | 0.032 | 0.054 |
| Cross-validation, rijnstate | 92 | 32 | 0.973 | 0.938 | 0.956 | 0.947 | 0.043 | 0.042 |
| Cross-validation, utrecht | 252 | 88 | 0.996 | 0.981 | 0.974 | 0.977 | 0.018 | 0.034 |
| Cross-validation, camelyon16:radboud | 245 | 95 | 0.984 | 0.975 | 0.944 | 0.960 | 0.041 | 0.064 |
| Cross-validation, camelyon16:utrecht | 154 | 65 | 0.995 | 0.979 | 0.963 | 0.971 | 0.020 | 0.038 |
| Cross-validation, camelyon17:cwz | 93 | 35 | 0.980 | 0.933 | 0.925 | 0.929 | 0.050 | 0.057 |
| Cross-validation, camelyon17:radboud | 89 | 25 | 1.000 | 1.000 | 0.990 | 0.995 | 0.008 | 0.027 |
| Cross-validation, camelyon17:rijnstate | 92 | 32 | 0.973 | 0.938 | 0.956 | 0.947 | 0.043 | 0.042 |
| Cross-validation, camelyon17:utrecht | 98 | 23 | 0.999 | 0.986 | 0.987 | 0.986 | 0.015 | 0.039 |
| held-out cwz, camelyon17:cwz | 93 | 35 | 0.979 | 0.990 | 0.569 | 0.780 | 0.182 | 0.265 |
| held-out radboud, camelyon16:radboud | 245 | 95 | 0.971 | 0.954 | 0.907 | 0.931 | 0.068 | 0.120 |
| held-out radboud, camelyon17:radboud | 89 | 25 | 0.999 | 0.987 | 0.995 | 0.991 | 0.008 | 0.028 |
| held-out rijnstate, camelyon17:rijnstate | 92 | 32 | 0.970 | 0.938 | 0.983 | 0.960 | 0.036 | 0.049 |
| held-out utrecht, camelyon16:utrecht | 154 | 65 | 0.992 | 0.979 | 0.693 | 0.836 | 0.110 | 0.184 |
| held-out utrecht, camelyon17:utrecht | 98 | 23 | 0.966 | 0.942 | 0.738 | 0.840 | 0.132 | 0.231 |

### Robustezza al centro (modello finale)

- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: **0.995** sui vetrini negativi, 0.997 su tutti (0,5 = centro non leggibile).
- Robustness Index sulle tile: **2.941** (> 1: domina la biologia); vicini dallo stesso centro 0.969, su 75391 tile.

### Localizzazione

AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori fold): **0.989**.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.988 | 0.003 | 0.987 | 0.991 | 0.991 | 0.987 | 0.987 |
| cv/ece | 0.040 | 0.015 | 0.024 | 0.053 | 0.045 | 0.053 | 0.024 |
| loco_worst_auroc | 0.970 | 0.013 | 0.956 | 0.980 | 0.980 | 0.956 | 0.976 |
| loco_worst_ece | 0.277 | 0.107 | 0.155 | 0.352 | 0.324 | 0.352 | 0.155 |
| loco_worst_ece_raw | 0.278 | 0.122 | 0.139 | 0.363 | 0.333 | 0.363 | 0.139 |
| loco_worst_specificity | 0.541 | 0.205 | 0.397 | 0.776 | 0.451 | 0.397 | 0.776 |
| robustness/center_probe_auroc | 0.995 | 0.003 | 0.992 | 0.998 | 0.992 | 0.998 | 0.995 |
| robustness/center_probe_auroc_all | 0.997 | 0.001 | 0.996 | 0.999 | 0.996 | 0.999 | 0.996 |
| robustness/robustness_index | 2.941 | 0.307 | 2.633 | 3.247 | 3.247 | 2.633 | 2.944 |
| temperature/global | 1.612 | 0.116 | 1.522 | 1.743 | 1.522 | 1.743 | 1.571 |
| attention_auroc_mean | 0.989 | 0.001 | 0.988 | 0.990 | 0.988 | 0.990 | 0.988 |
| loco/held-out cwz/auroc | 0.979 | 0.009 | 0.969 | 0.985 | 0.984 | 0.969 | 0.985 |
| loco/held-out cwz/sensitivity | 0.990 | 0.016 | 0.971 | 1.000 | 1.000 | 1.000 | 0.971 |
| loco/held-out cwz/specificity | 0.569 | 0.192 | 0.397 | 0.776 | 0.534 | 0.397 | 0.776 |
| loco/held-out cwz/ece | 0.265 | 0.101 | 0.155 | 0.352 | 0.289 | 0.352 | 0.155 |
| loco/held-out radboud/auroc | 0.980 | 0.004 | 0.976 | 0.984 | 0.984 | 0.979 | 0.976 |
| loco/held-out radboud/sensitivity | 0.961 | 0.024 | 0.933 | 0.975 | 0.975 | 0.975 | 0.933 |
| loco/held-out radboud/specificity | 0.933 | 0.035 | 0.893 | 0.953 | 0.893 | 0.953 | 0.953 |
| loco/held-out radboud/ece | 0.088 | 0.040 | 0.060 | 0.134 | 0.134 | 0.069 | 0.060 |
| loco/held-out rijnstate/auroc | 0.970 | 0.013 | 0.956 | 0.980 | 0.980 | 0.956 | 0.976 |
| loco/held-out rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco/held-out rijnstate/specificity | 0.983 | 0.000 | 0.983 | 0.983 | 0.983 | 0.983 | 0.983 |
| loco/held-out rijnstate/ece | 0.049 | 0.028 | 0.028 | 0.081 | 0.038 | 0.081 | 0.028 |
| loco/held-out utrecht/auroc | 0.984 | 0.009 | 0.974 | 0.992 | 0.986 | 0.974 | 0.992 |
| loco/held-out utrecht/sensitivity | 0.970 | 0.017 | 0.955 | 0.989 | 0.989 | 0.955 | 0.966 |
| loco/held-out utrecht/specificity | 0.713 | 0.232 | 0.451 | 0.890 | 0.451 | 0.799 | 0.890 |
| loco/held-out utrecht/ece | 0.201 | 0.112 | 0.105 | 0.324 | 0.324 | 0.174 | 0.105 |
| loco_by_domain/held-out cwz/camelyon17:cwz/auroc | 0.979 | 0.009 | 0.969 | 0.985 | 0.984 | 0.969 | 0.985 |
| loco_by_domain/held-out cwz/camelyon17:cwz/sensitivity | 0.990 | 0.016 | 0.971 | 1.000 | 1.000 | 1.000 | 0.971 |
| loco_by_domain/held-out cwz/camelyon17:cwz/specificity | 0.569 | 0.192 | 0.397 | 0.776 | 0.534 | 0.397 | 0.776 |
| loco_by_domain/held-out cwz/camelyon17:cwz/ece | 0.265 | 0.101 | 0.155 | 0.352 | 0.289 | 0.352 | 0.155 |
| loco_by_domain/held-out radboud/camelyon16:radboud/auroc | 0.971 | 0.004 | 0.966 | 0.975 | 0.975 | 0.971 | 0.966 |
| loco_by_domain/held-out radboud/camelyon16:radboud/sensitivity | 0.954 | 0.024 | 0.926 | 0.968 | 0.968 | 0.968 | 0.926 |
| loco_by_domain/held-out radboud/camelyon16:radboud/specificity | 0.907 | 0.052 | 0.847 | 0.940 | 0.847 | 0.933 | 0.940 |
| loco_by_domain/held-out radboud/camelyon16:radboud/ece | 0.120 | 0.051 | 0.089 | 0.178 | 0.178 | 0.092 | 0.089 |
| loco_by_domain/held-out radboud/camelyon17:radboud/auroc | 0.999 | 0.002 | 0.996 | 1.000 | 1.000 | 1.000 | 0.996 |
| loco_by_domain/held-out radboud/camelyon17:radboud/sensitivity | 0.987 | 0.023 | 0.960 | 1.000 | 1.000 | 1.000 | 0.960 |
| loco_by_domain/held-out radboud/camelyon17:radboud/specificity | 0.995 | 0.009 | 0.984 | 1.000 | 1.000 | 1.000 | 0.984 |
| loco_by_domain/held-out radboud/camelyon17:radboud/ece | 0.028 | 0.016 | 0.010 | 0.042 | 0.033 | 0.010 | 0.042 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/auroc | 0.970 | 0.013 | 0.956 | 0.980 | 0.980 | 0.956 | 0.976 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/specificity | 0.983 | 0.000 | 0.983 | 0.983 | 0.983 | 0.983 | 0.983 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/ece | 0.049 | 0.028 | 0.028 | 0.081 | 0.038 | 0.081 | 0.028 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/auroc | 0.992 | 0.004 | 0.987 | 0.995 | 0.995 | 0.987 | 0.993 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/sensitivity | 0.979 | 0.018 | 0.969 | 1.000 | 1.000 | 0.969 | 0.969 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/specificity | 0.693 | 0.347 | 0.292 | 0.910 | 0.292 | 0.876 | 0.910 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/ece | 0.184 | 0.130 | 0.094 | 0.333 | 0.333 | 0.124 | 0.094 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/auroc | 0.966 | 0.026 | 0.940 | 0.991 | 0.968 | 0.940 | 0.991 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/sensitivity | 0.942 | 0.025 | 0.913 | 0.957 | 0.957 | 0.913 | 0.957 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/specificity | 0.738 | 0.116 | 0.640 | 0.867 | 0.640 | 0.707 | 0.867 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/ece | 0.231 | 0.096 | 0.124 | 0.310 | 0.310 | 0.259 | 0.124 |

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
