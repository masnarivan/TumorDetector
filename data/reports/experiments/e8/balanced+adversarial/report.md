# Report di validazione — head-ln_metastasis-phikon

**Esito della batteria: NON SUPERATA** (media su 3 semi)

- ECE calibrata peggiore in leave-one-center-out 0.389, richiesto <= 0.1
- Specificità peggiore in leave-one-center-out 0.383, richiesto >= 0.8
- AUROC del probe sul centro (vetrini negativi) 0.991, richiesto <= 0.8

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
| Ricetta | `balanced, adversarial` |
| Calibrazione | `temperature, 3 fold interni nel LOCO` |
| Semi | `[0, 1, 2] (modello e temperatura salvati: seme 0)` |
| Versione codice | `b350cfd35018b0c7586f46b4b25d849b0042129e+dirty` |
| Vetrini di sviluppo con embedding | 771 |
| Vetrini del cohort lasciati fuori | 0 |

## Risultati

Media su 3 semi (0, 1, 2). Probabilità calibrate con la temperatura (in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della rotazione, stimata senza il centro escluso).

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, calibrata | 771 | 275 | 0.986 | 0.970 | 0.933 | 0.951 | 0.046 | 0.076 |
| Cross-validation, grezza | 771 | 275 | 0.986 | 0.970 | 0.933 | 0.951 | 0.046 | 0.051 |
| Leave-one-center-out, held-out cwz | 93 | 35 | 0.975 | 0.971 | 0.414 | 0.693 | 0.288 | 0.342 |
| Leave-one-center-out, held-out radboud | 334 | 120 | 0.980 | 0.969 | 0.896 | 0.933 | 0.069 | 0.119 |
| Leave-one-center-out, held-out rijnstate | 92 | 32 | 0.965 | 0.938 | 0.989 | 0.963 | 0.026 | 0.016 |
| Leave-one-center-out, held-out utrecht | 252 | 88 | 0.989 | 0.985 | 0.870 | 0.927 | 0.092 | 0.203 |

Centro escluso peggiore (per seme, poi media): AUROC **0.962**, ECE calibrata **0.389** (grezza 0.381), specificità **0.383**.

Temperature (media sui semi): global 1.920, held-out cwz 1.911, held-out radboud 2.005, held-out rijnstate 2.062, held-out utrecht 2.416.

### Per centro e per dominio

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, cwz | 93 | 35 | 0.975 | 0.943 | 0.839 | 0.891 | 0.094 | 0.128 |
| Cross-validation, radboud | 334 | 120 | 0.988 | 0.972 | 0.928 | 0.950 | 0.047 | 0.085 |
| Cross-validation, rijnstate | 92 | 32 | 0.964 | 0.938 | 0.956 | 0.947 | 0.047 | 0.055 |
| Cross-validation, utrecht | 252 | 88 | 0.993 | 0.989 | 0.963 | 0.976 | 0.027 | 0.058 |
| Cross-validation, camelyon16:radboud | 245 | 95 | 0.983 | 0.968 | 0.907 | 0.938 | 0.059 | 0.098 |
| Cross-validation, camelyon16:utrecht | 154 | 65 | 0.992 | 0.990 | 0.966 | 0.978 | 0.025 | 0.053 |
| Cross-validation, camelyon17:cwz | 93 | 35 | 0.975 | 0.943 | 0.839 | 0.891 | 0.094 | 0.128 |
| Cross-validation, camelyon17:radboud | 89 | 25 | 1.000 | 0.987 | 0.979 | 0.983 | 0.015 | 0.057 |
| Cross-validation, camelyon17:rijnstate | 92 | 32 | 0.964 | 0.938 | 0.956 | 0.947 | 0.047 | 0.055 |
| Cross-validation, camelyon17:utrecht | 98 | 23 | 0.997 | 0.986 | 0.960 | 0.973 | 0.030 | 0.071 |
| held-out cwz, camelyon17:cwz | 93 | 35 | 0.975 | 0.971 | 0.414 | 0.693 | 0.288 | 0.342 |
| held-out radboud, camelyon16:radboud | 245 | 95 | 0.970 | 0.961 | 0.856 | 0.908 | 0.090 | 0.150 |
| held-out radboud, camelyon17:radboud | 89 | 25 | 1.000 | 1.000 | 0.990 | 0.995 | 0.010 | 0.046 |
| held-out rijnstate, camelyon17:rijnstate | 92 | 32 | 0.965 | 0.938 | 0.989 | 0.963 | 0.026 | 0.016 |
| held-out utrecht, camelyon16:utrecht | 154 | 65 | 0.998 | 1.000 | 0.828 | 0.914 | 0.094 | 0.209 |
| held-out utrecht, camelyon17:utrecht | 98 | 23 | 0.971 | 0.942 | 0.920 | 0.931 | 0.088 | 0.194 |

### Robustezza al centro (modello finale)

- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: **0.991** sui vetrini negativi, 0.989 su tutti (0,5 = centro non leggibile).
- Robustness Index sulle tile: **3.086** (> 1: domina la biologia); vicini dallo stesso centro 0.970, su 75391 tile.

### Localizzazione

AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori fold): **0.992**.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.986 | 0.002 | 0.983 | 0.988 | 0.983 | 0.987 | 0.988 |
| cv/ece | 0.076 | 0.016 | 0.066 | 0.094 | 0.067 | 0.066 | 0.094 |
| loco_worst_auroc | 0.962 | 0.010 | 0.955 | 0.974 | 0.974 | 0.955 | 0.957 |
| loco_worst_ece | 0.389 | 0.168 | 0.200 | 0.522 | 0.200 | 0.522 | 0.446 |
| loco_worst_ece_raw | 0.381 | 0.235 | 0.115 | 0.561 | 0.115 | 0.561 | 0.468 |
| loco_worst_specificity | 0.383 | 0.432 | 0.052 | 0.872 | 0.872 | 0.052 | 0.224 |
| robustness/center_probe_auroc | 0.991 | 0.000 | 0.990 | 0.991 | 0.991 | 0.990 | 0.991 |
| robustness/center_probe_auroc_all | 0.989 | 0.003 | 0.986 | 0.992 | 0.986 | 0.989 | 0.992 |
| robustness/robustness_index | 3.086 | 0.130 | 3.002 | 3.236 | 3.002 | 3.236 | 3.021 |
| temperature/global | 1.920 | 0.201 | 1.751 | 2.142 | 2.142 | 1.751 | 1.865 |
| attention_auroc_mean | 0.992 | 0.001 | 0.991 | 0.993 | 0.991 | 0.993 | 0.991 |
| loco/held-out cwz/auroc | 0.975 | 0.006 | 0.969 | 0.982 | 0.974 | 0.969 | 0.982 |
| loco/held-out cwz/sensitivity | 0.971 | 0.049 | 0.914 | 1.000 | 0.914 | 1.000 | 1.000 |
| loco/held-out cwz/specificity | 0.414 | 0.486 | 0.052 | 0.966 | 0.966 | 0.052 | 0.224 |
| loco/held-out cwz/ece | 0.342 | 0.248 | 0.059 | 0.522 | 0.059 | 0.522 | 0.446 |
| loco/held-out radboud/auroc | 0.980 | 0.002 | 0.978 | 0.982 | 0.978 | 0.982 | 0.980 |
| loco/held-out radboud/sensitivity | 0.969 | 0.005 | 0.967 | 0.975 | 0.967 | 0.975 | 0.967 |
| loco/held-out radboud/specificity | 0.896 | 0.054 | 0.864 | 0.958 | 0.958 | 0.864 | 0.864 |
| loco/held-out radboud/ece | 0.119 | 0.066 | 0.049 | 0.181 | 0.049 | 0.181 | 0.126 |
| loco/held-out rijnstate/auroc | 0.965 | 0.016 | 0.955 | 0.984 | 0.984 | 0.955 | 0.957 |
| loco/held-out rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco/held-out rijnstate/specificity | 0.989 | 0.010 | 0.983 | 1.000 | 0.983 | 1.000 | 0.983 |
| loco/held-out rijnstate/ece | 0.016 | 0.010 | 0.006 | 0.027 | 0.014 | 0.006 | 0.027 |
| loco/held-out utrecht/auroc | 0.989 | 0.014 | 0.973 | 0.997 | 0.997 | 0.973 | 0.997 |
| loco/held-out utrecht/sensitivity | 0.985 | 0.017 | 0.966 | 1.000 | 0.989 | 0.966 | 1.000 |
| loco/held-out utrecht/specificity | 0.870 | 0.021 | 0.848 | 0.890 | 0.872 | 0.848 | 0.890 |
| loco/held-out utrecht/ece | 0.203 | 0.016 | 0.188 | 0.220 | 0.200 | 0.220 | 0.188 |
| loco_by_domain/held-out cwz/camelyon17:cwz/auroc | 0.975 | 0.006 | 0.969 | 0.982 | 0.974 | 0.969 | 0.982 |
| loco_by_domain/held-out cwz/camelyon17:cwz/sensitivity | 0.971 | 0.049 | 0.914 | 1.000 | 0.914 | 1.000 | 1.000 |
| loco_by_domain/held-out cwz/camelyon17:cwz/specificity | 0.414 | 0.486 | 0.052 | 0.966 | 0.966 | 0.052 | 0.224 |
| loco_by_domain/held-out cwz/camelyon17:cwz/ece | 0.342 | 0.248 | 0.059 | 0.522 | 0.059 | 0.522 | 0.446 |
| loco_by_domain/held-out radboud/camelyon16:radboud/auroc | 0.970 | 0.004 | 0.966 | 0.973 | 0.966 | 0.973 | 0.970 |
| loco_by_domain/held-out radboud/camelyon16:radboud/sensitivity | 0.961 | 0.006 | 0.958 | 0.968 | 0.958 | 0.968 | 0.958 |
| loco_by_domain/held-out radboud/camelyon16:radboud/specificity | 0.856 | 0.073 | 0.807 | 0.940 | 0.940 | 0.807 | 0.820 |
| loco_by_domain/held-out radboud/camelyon16:radboud/ece | 0.150 | 0.093 | 0.061 | 0.246 | 0.061 | 0.246 | 0.142 |
| loco_by_domain/held-out radboud/camelyon17:radboud/auroc | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/specificity | 0.990 | 0.018 | 0.969 | 1.000 | 1.000 | 1.000 | 0.969 |
| loco_by_domain/held-out radboud/camelyon17:radboud/ece | 0.046 | 0.034 | 0.015 | 0.083 | 0.015 | 0.040 | 0.083 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/auroc | 0.965 | 0.016 | 0.955 | 0.984 | 0.984 | 0.955 | 0.957 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/specificity | 0.989 | 0.010 | 0.983 | 1.000 | 0.983 | 1.000 | 0.983 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/ece | 0.016 | 0.010 | 0.006 | 0.027 | 0.014 | 0.006 | 0.027 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/auroc | 0.998 | 0.001 | 0.997 | 0.999 | 0.999 | 0.997 | 0.998 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/specificity | 0.828 | 0.023 | 0.809 | 0.854 | 0.809 | 0.820 | 0.854 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/ece | 0.209 | 0.019 | 0.187 | 0.224 | 0.215 | 0.224 | 0.187 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/auroc | 0.971 | 0.042 | 0.922 | 0.995 | 0.995 | 0.922 | 0.995 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/sensitivity | 0.942 | 0.066 | 0.870 | 1.000 | 0.957 | 0.870 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/specificity | 0.920 | 0.035 | 0.880 | 0.947 | 0.947 | 0.880 | 0.933 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/ece | 0.194 | 0.019 | 0.178 | 0.215 | 0.178 | 0.215 | 0.189 |

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
