# Report di validazione — head-ln_metastasis-phikon

**Esito della batteria: NON SUPERATA** (media su 3 semi)

- ECE calibrata peggiore in leave-one-center-out 0.296, richiesto <= 0.1
- Specificità peggiore in leave-one-center-out 0.530, richiesto >= 0.8
- AUROC del probe sul centro (vetrini negativi) 0.994, richiesto <= 0.8

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
| Ricetta | `balanced, stat_mix` |
| Calibrazione | `temperature, 3 fold interni nel LOCO` |
| Semi | `[0, 1, 2] (modello e temperatura salvati: seme 0)` |
| Versione codice | `b350cfd35018b0c7586f46b4b25d849b0042129e+dirty` |
| Vetrini di sviluppo con embedding | 771 |
| Vetrini del cohort lasciati fuori | 0 |

## Risultati

Media su 3 semi (0, 1, 2). Probabilità calibrate con la temperatura (in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della rotazione, stimata senza il centro escluso).

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, calibrata | 771 | 275 | 0.986 | 0.962 | 0.976 | 0.969 | 0.025 | 0.021 |
| Cross-validation, grezza | 771 | 275 | 0.986 | 0.962 | 0.976 | 0.969 | 0.025 | 0.022 |
| Leave-one-center-out, held-out cwz | 93 | 35 | 0.971 | 0.867 | 0.920 | 0.893 | 0.067 | 0.084 |
| Leave-one-center-out, held-out radboud | 334 | 120 | 0.981 | 0.961 | 0.874 | 0.917 | 0.075 | 0.140 |
| Leave-one-center-out, held-out rijnstate | 92 | 32 | 0.976 | 0.938 | 0.983 | 0.960 | 0.029 | 0.021 |
| Leave-one-center-out, held-out utrecht | 252 | 88 | 0.978 | 0.973 | 0.530 | 0.752 | 0.177 | 0.296 |

Centro escluso peggiore (per seme, poi media): AUROC **0.959**, ECE calibrata **0.296** (grezza 0.304), specificità **0.530**.

Temperature (media sui semi): global 1.562, held-out cwz 1.655, held-out radboud 1.678, held-out rijnstate 1.438, held-out utrecht 1.835.

### Per centro e per dominio

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, cwz | 93 | 35 | 0.961 | 0.914 | 0.954 | 0.934 | 0.050 | 0.040 |
| Cross-validation, radboud | 334 | 120 | 0.992 | 0.972 | 0.980 | 0.976 | 0.021 | 0.031 |
| Cross-validation, rijnstate | 92 | 32 | 0.968 | 0.927 | 0.983 | 0.955 | 0.035 | 0.033 |
| Cross-validation, utrecht | 252 | 88 | 0.995 | 0.981 | 0.978 | 0.979 | 0.018 | 0.029 |
| Cross-validation, camelyon16:radboud | 245 | 95 | 0.989 | 0.968 | 0.978 | 0.973 | 0.024 | 0.037 |
| Cross-validation, camelyon16:utrecht | 154 | 65 | 0.997 | 0.985 | 0.978 | 0.981 | 0.019 | 0.033 |
| Cross-validation, camelyon17:cwz | 93 | 35 | 0.961 | 0.914 | 0.954 | 0.934 | 0.050 | 0.040 |
| Cross-validation, camelyon17:radboud | 89 | 25 | 0.999 | 0.987 | 0.984 | 0.986 | 0.012 | 0.025 |
| Cross-validation, camelyon17:rijnstate | 92 | 32 | 0.968 | 0.927 | 0.983 | 0.955 | 0.035 | 0.033 |
| Cross-validation, camelyon17:utrecht | 98 | 23 | 0.990 | 0.971 | 0.978 | 0.974 | 0.018 | 0.029 |
| held-out cwz, camelyon17:cwz | 93 | 35 | 0.971 | 0.867 | 0.920 | 0.893 | 0.067 | 0.084 |
| held-out radboud, camelyon16:radboud | 245 | 95 | 0.975 | 0.951 | 0.856 | 0.903 | 0.087 | 0.163 |
| held-out radboud, camelyon17:radboud | 89 | 25 | 1.000 | 1.000 | 0.917 | 0.958 | 0.041 | 0.086 |
| held-out rijnstate, camelyon17:rijnstate | 92 | 32 | 0.976 | 0.938 | 0.983 | 0.960 | 0.029 | 0.021 |
| held-out utrecht, camelyon16:utrecht | 154 | 65 | 0.990 | 0.995 | 0.434 | 0.715 | 0.169 | 0.282 |
| held-out utrecht, camelyon17:utrecht | 98 | 23 | 0.941 | 0.913 | 0.644 | 0.779 | 0.191 | 0.321 |

### Robustezza al centro (modello finale)

- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: **0.994** sui vetrini negativi, 0.996 su tutti (0,5 = centro non leggibile).
- Robustness Index sulle tile: **2.901** (> 1: domina la biologia); vicini dallo stesso centro 0.969, su 75391 tile.

### Localizzazione

AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori fold): **0.989**.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.986 | 0.008 | 0.977 | 0.991 | 0.977 | 0.990 | 0.991 |
| cv/ece | 0.021 | 0.009 | 0.012 | 0.030 | 0.030 | 0.022 | 0.012 |
| loco_worst_auroc | 0.959 | 0.015 | 0.947 | 0.977 | 0.954 | 0.977 | 0.947 |
| loco_worst_ece | 0.296 | 0.066 | 0.247 | 0.371 | 0.247 | 0.270 | 0.371 |
| loco_worst_ece_raw | 0.304 | 0.098 | 0.237 | 0.416 | 0.237 | 0.258 | 0.416 |
| loco_worst_specificity | 0.530 | 0.185 | 0.317 | 0.646 | 0.646 | 0.628 | 0.317 |
| robustness/center_probe_auroc | 0.994 | 0.005 | 0.989 | 0.999 | 0.989 | 0.994 | 0.999 |
| robustness/center_probe_auroc_all | 0.996 | 0.002 | 0.995 | 0.999 | 0.995 | 0.999 | 0.996 |
| robustness/robustness_index | 2.901 | 0.318 | 2.585 | 3.220 | 3.220 | 2.585 | 2.898 |
| temperature/global | 1.562 | 0.107 | 1.487 | 1.684 | 1.684 | 1.487 | 1.514 |
| attention_auroc_mean | 0.989 | 0.002 | 0.987 | 0.990 | 0.987 | 0.989 | 0.990 |
| loco/held-out cwz/auroc | 0.971 | 0.025 | 0.947 | 0.997 | 0.970 | 0.997 | 0.947 |
| loco/held-out cwz/sensitivity | 0.867 | 0.135 | 0.714 | 0.971 | 0.914 | 0.971 | 0.714 |
| loco/held-out cwz/specificity | 0.920 | 0.020 | 0.897 | 0.931 | 0.931 | 0.897 | 0.931 |
| loco/held-out cwz/ece | 0.084 | 0.017 | 0.065 | 0.099 | 0.099 | 0.087 | 0.065 |
| loco/held-out radboud/auroc | 0.981 | 0.002 | 0.979 | 0.984 | 0.984 | 0.981 | 0.979 |
| loco/held-out radboud/sensitivity | 0.961 | 0.032 | 0.925 | 0.983 | 0.983 | 0.975 | 0.925 |
| loco/held-out radboud/specificity | 0.874 | 0.108 | 0.790 | 0.995 | 0.790 | 0.836 | 0.995 |
| loco/held-out radboud/ece | 0.140 | 0.066 | 0.071 | 0.202 | 0.202 | 0.147 | 0.071 |
| loco/held-out rijnstate/auroc | 0.976 | 0.010 | 0.966 | 0.985 | 0.985 | 0.977 | 0.966 |
| loco/held-out rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco/held-out rijnstate/specificity | 0.983 | 0.000 | 0.983 | 0.983 | 0.983 | 0.983 | 0.983 |
| loco/held-out rijnstate/ece | 0.021 | 0.005 | 0.015 | 0.025 | 0.023 | 0.015 | 0.025 |
| loco/held-out utrecht/auroc | 0.978 | 0.022 | 0.954 | 0.998 | 0.954 | 0.982 | 0.998 |
| loco/held-out utrecht/sensitivity | 0.973 | 0.029 | 0.943 | 1.000 | 0.943 | 0.977 | 1.000 |
| loco/held-out utrecht/specificity | 0.530 | 0.185 | 0.317 | 0.646 | 0.646 | 0.628 | 0.317 |
| loco/held-out utrecht/ece | 0.296 | 0.066 | 0.247 | 0.371 | 0.247 | 0.270 | 0.371 |
| loco_by_domain/held-out cwz/camelyon17:cwz/auroc | 0.971 | 0.025 | 0.947 | 0.997 | 0.970 | 0.997 | 0.947 |
| loco_by_domain/held-out cwz/camelyon17:cwz/sensitivity | 0.867 | 0.135 | 0.714 | 0.971 | 0.914 | 0.971 | 0.714 |
| loco_by_domain/held-out cwz/camelyon17:cwz/specificity | 0.920 | 0.020 | 0.897 | 0.931 | 0.931 | 0.897 | 0.931 |
| loco_by_domain/held-out cwz/camelyon17:cwz/ece | 0.084 | 0.017 | 0.065 | 0.099 | 0.099 | 0.087 | 0.065 |
| loco_by_domain/held-out radboud/camelyon16:radboud/auroc | 0.975 | 0.003 | 0.972 | 0.977 | 0.977 | 0.974 | 0.972 |
| loco_by_domain/held-out radboud/camelyon16:radboud/sensitivity | 0.951 | 0.040 | 0.905 | 0.979 | 0.979 | 0.968 | 0.905 |
| loco_by_domain/held-out radboud/camelyon16:radboud/specificity | 0.856 | 0.120 | 0.773 | 0.993 | 0.800 | 0.773 | 0.993 |
| loco_by_domain/held-out radboud/camelyon16:radboud/ece | 0.163 | 0.072 | 0.080 | 0.212 | 0.212 | 0.197 | 0.080 |
| loco_by_domain/held-out radboud/camelyon17:radboud/auroc | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/specificity | 0.917 | 0.131 | 0.766 | 1.000 | 0.766 | 0.984 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/ece | 0.086 | 0.078 | 0.036 | 0.176 | 0.176 | 0.036 | 0.047 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/auroc | 0.976 | 0.010 | 0.966 | 0.985 | 0.985 | 0.977 | 0.966 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/specificity | 0.983 | 0.000 | 0.983 | 0.983 | 0.983 | 0.983 | 0.983 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/ece | 0.021 | 0.005 | 0.015 | 0.025 | 0.023 | 0.015 | 0.025 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/auroc | 0.990 | 0.013 | 0.975 | 0.998 | 0.975 | 0.998 | 0.998 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/sensitivity | 0.995 | 0.009 | 0.985 | 1.000 | 0.985 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/specificity | 0.434 | 0.247 | 0.191 | 0.685 | 0.427 | 0.685 | 0.191 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/ece | 0.282 | 0.057 | 0.230 | 0.342 | 0.274 | 0.230 | 0.342 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/auroc | 0.941 | 0.053 | 0.893 | 0.998 | 0.893 | 0.933 | 0.998 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/sensitivity | 0.913 | 0.087 | 0.826 | 1.000 | 0.826 | 0.913 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/specificity | 0.644 | 0.232 | 0.467 | 0.907 | 0.907 | 0.560 | 0.467 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/ece | 0.321 | 0.103 | 0.212 | 0.417 | 0.212 | 0.335 | 0.417 |

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
