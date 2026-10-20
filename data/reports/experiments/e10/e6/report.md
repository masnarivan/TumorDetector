# Report di validazione — head-ln_metastasis-phikon

**Esito della batteria: NON SUPERATA** (media su 3 semi)

- ECE calibrata peggiore in leave-one-center-out 0.293, richiesto <= 0.1
- Specificità peggiore in leave-one-center-out 0.430, richiesto >= 0.8
- *Probe sul centro 0.999: riportato, senza soglia*
- *Non regressione del probe: nessun modello validato con cui confrontare*

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
| Ricetta | `nessuna mitigazione` |
| Calibrazione | `temperature, 3 fold interni nel LOCO` |
| Semi | `[0, 1, 2] (modello e temperatura salvati: seme 0)` |
| Versione codice | `7595dbb342be0b86db63801db84fd025af4daefa+dirty` |
| Vetrini di sviluppo con embedding | 771 |
| Vetrini del cohort lasciati fuori | 0 |

## Risultati

Media su 3 semi (0, 1, 2). Probabilità calibrate con la temperatura (in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della rotazione, stimata senza il centro escluso).

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, calibrata | 771 | 275 | 0.989 | 0.970 | 0.962 | 0.966 | 0.029 | 0.033 |
| Cross-validation, grezza | 771 | 275 | 0.989 | 0.970 | 0.962 | 0.966 | 0.030 | 0.030 |
| Leave-one-center-out, held-out cwz | 93 | 35 | 0.976 | 0.962 | 0.770 | 0.866 | 0.115 | 0.186 |
| Leave-one-center-out, held-out radboud | 334 | 120 | 0.984 | 0.978 | 0.911 | 0.944 | 0.057 | 0.105 |
| Leave-one-center-out, held-out rijnstate | 92 | 32 | 0.978 | 0.938 | 0.972 | 0.955 | 0.032 | 0.033 |
| Leave-one-center-out, held-out utrecht | 252 | 88 | 0.980 | 0.981 | 0.492 | 0.736 | 0.182 | 0.273 |

Centro escluso peggiore (per seme, poi media): AUROC **0.974**, ECE calibrata **0.293** (grezza 0.320), specificità **0.430**.

Temperature (media sui semi): global 1.694, held-out cwz 2.053, held-out radboud 1.757, held-out rijnstate 1.749, held-out utrecht 1.863.

### Per centro e per dominio

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, cwz | 93 | 35 | 0.960 | 0.924 | 0.943 | 0.933 | 0.052 | 0.063 |
| Cross-validation, radboud | 334 | 120 | 0.991 | 0.975 | 0.956 | 0.966 | 0.033 | 0.049 |
| Cross-validation, rijnstate | 92 | 32 | 0.984 | 0.938 | 0.956 | 0.947 | 0.038 | 0.044 |
| Cross-validation, utrecht | 252 | 88 | 0.999 | 0.992 | 0.980 | 0.986 | 0.014 | 0.028 |
| Cross-validation, camelyon16:radboud | 245 | 95 | 0.987 | 0.975 | 0.938 | 0.957 | 0.042 | 0.064 |
| Cross-validation, camelyon16:utrecht | 154 | 65 | 0.999 | 0.995 | 0.970 | 0.982 | 0.015 | 0.031 |
| Cross-validation, camelyon17:cwz | 93 | 35 | 0.960 | 0.924 | 0.943 | 0.933 | 0.052 | 0.063 |
| Cross-validation, camelyon17:radboud | 89 | 25 | 0.999 | 0.973 | 1.000 | 0.987 | 0.008 | 0.016 |
| Cross-validation, camelyon17:rijnstate | 92 | 32 | 0.984 | 0.938 | 0.956 | 0.947 | 0.038 | 0.044 |
| Cross-validation, camelyon17:utrecht | 98 | 23 | 0.999 | 0.986 | 0.991 | 0.988 | 0.011 | 0.030 |
| held-out cwz, camelyon17:cwz | 93 | 35 | 0.976 | 0.962 | 0.770 | 0.866 | 0.115 | 0.186 |
| held-out radboud, camelyon16:radboud | 245 | 95 | 0.977 | 0.972 | 0.878 | 0.925 | 0.076 | 0.138 |
| held-out radboud, camelyon17:radboud | 89 | 25 | 1.000 | 1.000 | 0.990 | 0.995 | 0.007 | 0.029 |
| held-out rijnstate, camelyon17:rijnstate | 92 | 32 | 0.978 | 0.938 | 0.972 | 0.955 | 0.032 | 0.033 |
| held-out utrecht, camelyon16:utrecht | 154 | 65 | 0.997 | 1.000 | 0.427 | 0.713 | 0.181 | 0.275 |
| held-out utrecht, camelyon17:utrecht | 98 | 23 | 0.941 | 0.928 | 0.569 | 0.748 | 0.182 | 0.280 |

### Robustezza al centro (modello finale)

- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: **0.999** sui vetrini negativi, 0.999 su tutti (0,5 = centro non leggibile).
- Robustness Index sulle tile: **2.649** (> 1: domina la biologia); vicini dallo stesso centro 0.971, su 75391 tile.

### Localizzazione

AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori fold): **0.988**.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.989 | 0.003 | 0.987 | 0.992 | 0.992 | 0.987 | 0.988 |
| cv/ece | 0.033 | 0.009 | 0.026 | 0.042 | 0.026 | 0.042 | 0.030 |
| loco_worst_auroc | 0.974 | 0.004 | 0.970 | 0.978 | 0.970 | 0.978 | 0.974 |
| loco_worst_ece | 0.293 | 0.106 | 0.214 | 0.414 | 0.252 | 0.414 | 0.214 |
| loco_worst_ece_raw | 0.320 | 0.146 | 0.219 | 0.487 | 0.253 | 0.487 | 0.219 |
| loco_worst_specificity | 0.430 | 0.296 | 0.091 | 0.638 | 0.561 | 0.091 | 0.638 |
| robustness/center_probe_auroc | 0.999 | 0.001 | 0.998 | 0.999 | 0.999 | 0.999 | 0.998 |
| robustness/center_probe_auroc_all | 0.999 | 0.001 | 0.998 | 0.999 | 0.998 | 0.999 | 0.998 |
| robustness/robustness_index | 2.649 | 0.170 | 2.456 | 2.774 | 2.716 | 2.456 | 2.774 |
| temperature/global | 1.694 | 0.105 | 1.576 | 1.780 | 1.576 | 1.725 | 1.780 |
| attention_auroc_mean | 0.988 | 0.003 | 0.986 | 0.991 | 0.991 | 0.986 | 0.987 |
| loco/held-out cwz/auroc | 0.976 | 0.006 | 0.972 | 0.983 | 0.972 | 0.983 | 0.974 |
| loco/held-out cwz/sensitivity | 0.962 | 0.044 | 0.914 | 1.000 | 0.914 | 1.000 | 0.971 |
| loco/held-out cwz/specificity | 0.770 | 0.160 | 0.638 | 0.948 | 0.948 | 0.724 | 0.638 |
| loco/held-out cwz/ece | 0.186 | 0.034 | 0.148 | 0.214 | 0.148 | 0.196 | 0.214 |
| loco/held-out radboud/auroc | 0.984 | 0.004 | 0.981 | 0.989 | 0.989 | 0.982 | 0.981 |
| loco/held-out radboud/sensitivity | 0.978 | 0.005 | 0.975 | 0.983 | 0.975 | 0.983 | 0.975 |
| loco/held-out radboud/specificity | 0.911 | 0.005 | 0.907 | 0.916 | 0.916 | 0.911 | 0.907 |
| loco/held-out radboud/ece | 0.105 | 0.030 | 0.079 | 0.138 | 0.079 | 0.098 | 0.138 |
| loco/held-out rijnstate/auroc | 0.978 | 0.008 | 0.970 | 0.986 | 0.970 | 0.978 | 0.986 |
| loco/held-out rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco/held-out rijnstate/specificity | 0.972 | 0.019 | 0.950 | 0.983 | 0.950 | 0.983 | 0.983 |
| loco/held-out rijnstate/ece | 0.033 | 0.018 | 0.017 | 0.053 | 0.053 | 0.017 | 0.029 |
| loco/held-out utrecht/auroc | 0.980 | 0.012 | 0.970 | 0.993 | 0.970 | 0.993 | 0.978 |
| loco/held-out utrecht/sensitivity | 0.981 | 0.017 | 0.966 | 1.000 | 0.977 | 1.000 | 0.966 |
| loco/held-out utrecht/specificity | 0.492 | 0.371 | 0.091 | 0.823 | 0.561 | 0.091 | 0.823 |
| loco/held-out utrecht/ece | 0.273 | 0.132 | 0.152 | 0.414 | 0.252 | 0.414 | 0.152 |
| loco_by_domain/held-out cwz/camelyon17:cwz/auroc | 0.976 | 0.006 | 0.972 | 0.983 | 0.972 | 0.983 | 0.974 |
| loco_by_domain/held-out cwz/camelyon17:cwz/sensitivity | 0.962 | 0.044 | 0.914 | 1.000 | 0.914 | 1.000 | 0.971 |
| loco_by_domain/held-out cwz/camelyon17:cwz/specificity | 0.770 | 0.160 | 0.638 | 0.948 | 0.948 | 0.724 | 0.638 |
| loco_by_domain/held-out cwz/camelyon17:cwz/ece | 0.186 | 0.034 | 0.148 | 0.214 | 0.148 | 0.196 | 0.214 |
| loco_by_domain/held-out radboud/camelyon16:radboud/auroc | 0.977 | 0.004 | 0.973 | 0.982 | 0.982 | 0.976 | 0.973 |
| loco_by_domain/held-out radboud/camelyon16:radboud/sensitivity | 0.972 | 0.006 | 0.968 | 0.979 | 0.968 | 0.979 | 0.968 |
| loco_by_domain/held-out radboud/camelyon16:radboud/specificity | 0.878 | 0.004 | 0.873 | 0.880 | 0.880 | 0.880 | 0.873 |
| loco_by_domain/held-out radboud/camelyon16:radboud/ece | 0.138 | 0.043 | 0.105 | 0.186 | 0.105 | 0.123 | 0.186 |
| loco_by_domain/held-out radboud/camelyon17:radboud/auroc | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/specificity | 0.990 | 0.009 | 0.984 | 1.000 | 1.000 | 0.984 | 0.984 |
| loco_by_domain/held-out radboud/camelyon17:radboud/ece | 0.029 | 0.015 | 0.014 | 0.045 | 0.014 | 0.028 | 0.045 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/auroc | 0.978 | 0.008 | 0.970 | 0.986 | 0.970 | 0.978 | 0.986 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/specificity | 0.972 | 0.019 | 0.950 | 0.983 | 0.950 | 0.983 | 0.983 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/ece | 0.033 | 0.018 | 0.017 | 0.053 | 0.053 | 0.017 | 0.029 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/auroc | 0.997 | 0.003 | 0.993 | 0.999 | 0.993 | 0.999 | 0.999 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/specificity | 0.427 | 0.371 | 0.022 | 0.753 | 0.506 | 0.022 | 0.753 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/ece | 0.275 | 0.105 | 0.181 | 0.389 | 0.255 | 0.389 | 0.181 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/auroc | 0.941 | 0.038 | 0.907 | 0.983 | 0.907 | 0.983 | 0.934 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/sensitivity | 0.928 | 0.066 | 0.870 | 1.000 | 0.913 | 1.000 | 0.870 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/specificity | 0.569 | 0.370 | 0.173 | 0.907 | 0.627 | 0.173 | 0.907 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/ece | 0.280 | 0.170 | 0.120 | 0.458 | 0.262 | 0.458 | 0.120 |

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
