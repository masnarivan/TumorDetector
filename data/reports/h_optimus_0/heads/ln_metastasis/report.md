# Report di validazione — head-ln_metastasis-h_optimus_0

**Esito della batteria: NON SUPERATA** (media su 3 semi)

- ECE calibrata peggiore in leave-one-center-out 0.236, richiesto <= 0.1
- Specificità peggiore in leave-one-center-out 0.681, richiesto >= 0.8
- Copertura conformal dei positivi, centro escluso peggiore 0.875, richiesto >= 0.9
- *Probe sul centro 0.998: riportato, senza soglia*
- *Non regressione del probe: nessun modello validato con cui confrontare*

Solo uso di ricerca. Le soglie della batteria sono proposte iniziali, da fissare con i patologi.

## Provenienza

| | |
|---|---|
| Modello | `head-ln_metastasis-h_optimus_0` |
| Testa | `ln_metastasis v1 (M4)` |
| Cohort | `data/manifests/heads/ln_metastasis.csv (sha256 d28e4c48b675)` |
| Collezione embedding | `h_optimus_0__b145cc1e6c6b` |
| Versione backbone | `b145cc1e6c6b30d3251aa8b1f844e6974188a743` |
| Iperparametri | `{'hidden': 256, 'dropout': 0.25, 'lr': 0.0002, 'weight_decay': 0.0001, 'epochs': 30, 'max_tiles': 4096, 'threshold': 0.5, 'normalize': 'none', 'threads': 1}` |
| Ricetta | `nessuna mitigazione` |
| Calibrazione | `temperature, 3 fold interni nel LOCO` |
| Insiemi conformal | `per_class, alpha 0.05` |
| Controllo del dominio | `slide_mean_knn, k 5, alpha 0.05, fold di calibrazione 3` |
| Semi | `[0, 1, 2] (modello e temperatura salvati: seme 0)` |
| Versione codice | `2dca7810240874d7aafed1cb24cbe2f61ab0cce7+dirty` |
| Vetrini di sviluppo con embedding | 771 |
| Vetrini del cohort lasciati fuori | 0 |

## Risultati

Media su 3 semi (0, 1, 2). Probabilità calibrate con la temperatura (in CV quella globale, stimata sulle stesse predizioni: ottimista; in leave-one-center-out quella della rotazione, stimata senza il centro escluso).

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, calibrata | 771 | 275 | 0.994 | 0.979 | 0.990 | 0.985 | 0.011 | 0.009 |
| Cross-validation, grezza | 771 | 275 | 0.994 | 0.979 | 0.990 | 0.985 | 0.012 | 0.011 |
| Leave-one-center-out, held-out cwz | 93 | 35 | 1.000 | 1.000 | 0.914 | 0.957 | 0.044 | 0.089 |
| Leave-one-center-out, held-out radboud | 334 | 120 | 0.997 | 0.994 | 0.922 | 0.958 | 0.037 | 0.075 |
| Leave-one-center-out, held-out rijnstate | 92 | 32 | 0.968 | 0.938 | 1.000 | 0.969 | 0.022 | 0.018 |
| Leave-one-center-out, held-out utrecht | 252 | 88 | 0.992 | 0.992 | 0.681 | 0.837 | 0.134 | 0.236 |

Centro escluso peggiore (per seme, poi media): AUROC **0.968**, ECE calibrata **0.236** (grezza 0.214), specificità **0.681**.

Temperature (media sui semi): global 1.485, held-out cwz 1.576, held-out radboud 1.864, held-out rijnstate 1.219, held-out utrecht 1.638.

### Insiemi conformal per classe

Quantili del modello finale (CV fuori fold): q0 0.088, q1 0.019. Insieme {0} o {1}: risposta; {0, 1} o vuoto: rinvio. In leave-one-center-out i quantili vengono dai fold interni della rotazione. Copertura dei positivi sul centro escluso peggiore: **0.875**.

| Rotazione | q0 | q1 | Copertura positivi | Copertura negativi | Rinvii |
|---|---|---|---|---|---|
| held-out cwz | 0.213 | 0.044 | 0.943 | 0.828 | 0.118 |
| held-out radboud | 0.060 | 0.183 | 0.989 | 0.545 | 0.278 |
| held-out rijnstate | 0.062 | 0.008 | 0.875 | 0.994 | 0.025 |
| held-out utrecht | 0.225 | 0.051 | 0.981 | 0.478 | 0.343 |

### Alla prevalenza (insiemi conformal, centro escluso)

Rinvii / PPV / NPV delle risposte se la quota di vetrini positivi fosse quella in colonna: tassi del centro escluso per classe, ricombinati (E10). Nessuna soglia: il tasso di rinvio accettabile lo decidono i patologi.

| Rotazione | 5% | 10% | 20% | 30% |
|---|---|---|---|---|
| held-out cwz | 0.150 / 0.742 / 1.000 | 0.145 / 0.859 / 1.000 | 0.136 / 0.932 / 1.000 | 0.126 / 0.959 / 1.000 |
| held-out radboud | 0.409 / 0.676 / 1.000 | 0.388 / 0.815 / 0.999 | 0.346 / 0.908 / 0.999 | 0.303 / 0.944 / 0.998 |
| held-out rijnstate | 0.008 / 1.000 / 0.997 | 0.011 / 1.000 / 0.993 | 0.017 / 1.000 / 0.985 | 0.023 / 1.000 / 0.974 |
| held-out utrecht | 0.495 / 0.962 / 0.999 | 0.469 / 0.982 / 0.998 | 0.419 / 0.992 / 0.996 | 0.368 / 0.995 / 0.993 |

### Positivi per diagnosi

Sensibilità alla soglia 0,5 e, con gli insiemi conformal, quota con risposta «positivo», rinviata e persa (risposta «negativo»). In cross-validation i quantili sono stimati sulle stesse predizioni: ottimista. Sensibilità sul centro escluso peggiore: macro **1.000**, micro **0.846**.

| Valutazione | Diagnosi | Vetrini | Sensibilità | Risposta positivo | Rinviati | Persi |
|---|---|---|---|---|---|---|
| Cross-validation | macro | 141 | 1.000 | 0.991 | 0.009 | 0.000 |
| Cross-validation | micro | 134 | 0.958 | 0.920 | 0.052 | 0.027 |
| held-out cwz | macro | 12 | 1.000 | 0.972 | 0.028 | 0.000 |
| held-out cwz | micro | 23 | 1.000 | 0.928 | 0.072 | 0.000 |
| held-out radboud | macro | 60 | 1.000 | 1.000 | 0.000 | 0.000 |
| held-out radboud | micro | 60 | 0.989 | 0.978 | 0.017 | 0.006 |
| held-out rijnstate | macro | 19 | 1.000 | 0.912 | 0.088 | 0.000 |
| held-out rijnstate | micro | 13 | 0.846 | 0.821 | 0.026 | 0.154 |
| held-out utrecht | macro | 50 | 1.000 | 0.993 | 0.007 | 0.000 |
| held-out utrecht | micro | 38 | 0.982 | 0.965 | 0.018 | 0.018 |

### Per centro e per dominio

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, cwz | 93 | 35 | 0.999 | 0.990 | 0.971 | 0.981 | 0.013 | 0.023 |
| Cross-validation, radboud | 334 | 120 | 0.996 | 0.981 | 0.991 | 0.986 | 0.011 | 0.014 |
| Cross-validation, rijnstate | 92 | 32 | 0.971 | 0.938 | 0.989 | 0.963 | 0.026 | 0.025 |
| Cross-validation, utrecht | 252 | 88 | 0.997 | 0.989 | 0.996 | 0.992 | 0.005 | 0.010 |
| Cross-validation, camelyon16:radboud | 245 | 95 | 0.995 | 0.982 | 0.989 | 0.986 | 0.012 | 0.018 |
| Cross-validation, camelyon16:utrecht | 154 | 65 | 1.000 | 0.990 | 0.993 | 0.991 | 0.006 | 0.013 |
| Cross-validation, camelyon17:cwz | 93 | 35 | 0.999 | 0.990 | 0.971 | 0.981 | 0.013 | 0.023 |
| Cross-validation, camelyon17:radboud | 89 | 25 | 0.999 | 0.973 | 0.995 | 0.984 | 0.010 | 0.013 |
| Cross-validation, camelyon17:rijnstate | 92 | 32 | 0.971 | 0.938 | 0.989 | 0.963 | 0.026 | 0.025 |
| Cross-validation, camelyon17:utrecht | 98 | 23 | 0.992 | 0.986 | 1.000 | 0.993 | 0.005 | 0.009 |
| held-out cwz, camelyon17:cwz | 93 | 35 | 1.000 | 1.000 | 0.914 | 0.957 | 0.044 | 0.089 |
| held-out radboud, camelyon16:radboud | 245 | 95 | 0.997 | 0.993 | 0.891 | 0.942 | 0.048 | 0.089 |
| held-out radboud, camelyon17:radboud | 89 | 25 | 1.000 | 1.000 | 0.995 | 0.997 | 0.009 | 0.041 |
| held-out rijnstate, camelyon17:rijnstate | 92 | 32 | 0.968 | 0.938 | 1.000 | 0.969 | 0.022 | 0.018 |
| held-out utrecht, camelyon16:utrecht | 154 | 65 | 0.989 | 0.990 | 0.734 | 0.862 | 0.101 | 0.191 |
| held-out utrecht, camelyon17:utrecht | 98 | 23 | 1.000 | 1.000 | 0.618 | 0.809 | 0.187 | 0.307 |

### Robustezza al centro (modello finale)

- Probe lineare sul centro dalla rappresentazione del vetrino, AUROC macro one-vs-rest: **0.998** sui vetrini negativi, 0.999 su tutti (0,5 = centro non leggibile).
- Robustness Index sulle tile: **10.825** (> 1: domina la biologia); vicini dallo stesso centro 0.945, su 75391 tile.

### Localizzazione

AUROC dell'attenzione (tile tumorali contro normali, vetrini positivi con annotazione completa, fuori fold): **0.987**.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.994 | 0.002 | 0.992 | 0.995 | 0.992 | 0.995 | 0.994 |
| cv/ece | 0.009 | 0.003 | 0.008 | 0.012 | 0.008 | 0.012 | 0.008 |
| loco_worst_auroc | 0.968 | 0.009 | 0.963 | 0.979 | 0.963 | 0.964 | 0.979 |
| loco_worst_ece | 0.236 | 0.143 | 0.108 | 0.390 | 0.390 | 0.108 | 0.210 |
| loco_worst_ece_raw | 0.214 | 0.177 | 0.064 | 0.410 | 0.410 | 0.064 | 0.169 |
| loco_worst_specificity | 0.681 | 0.332 | 0.305 | 0.933 | 0.305 | 0.933 | 0.805 |
| robustness/center_probe_auroc | 0.998 | 0.001 | 0.997 | 0.998 | 0.998 | 0.998 | 0.997 |
| robustness/center_probe_auroc_all | 0.999 | 0.000 | 0.998 | 0.999 | 0.998 | 0.999 | 0.999 |
| robustness/robustness_index | 10.825 | 0.400 | 10.423 | 11.223 | 11.223 | 10.423 | 10.830 |
| temperature/global | 1.485 | 0.131 | 1.336 | 1.584 | 1.535 | 1.336 | 1.584 |
| attention_auroc_mean | 0.987 | 0.004 | 0.984 | 0.991 | 0.991 | 0.984 | 0.985 |
| loco_worst_positive_coverage | 0.875 | 0.054 | 0.844 | 0.938 | 0.844 | 0.938 | 0.844 |
| loco/held-out cwz/auroc | 1.000 | 0.001 | 0.999 | 1.000 | 1.000 | 1.000 | 0.999 |
| loco/held-out cwz/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco/held-out cwz/specificity | 0.914 | 0.091 | 0.810 | 0.983 | 0.810 | 0.948 | 0.983 |
| loco/held-out cwz/ece | 0.089 | 0.069 | 0.043 | 0.168 | 0.168 | 0.043 | 0.056 |
| loco/held-out radboud/auroc | 0.997 | 0.003 | 0.994 | 0.999 | 0.999 | 0.994 | 0.999 |
| loco/held-out radboud/sensitivity | 0.994 | 0.005 | 0.992 | 1.000 | 0.992 | 0.992 | 1.000 |
| loco/held-out radboud/specificity | 0.922 | 0.077 | 0.836 | 0.986 | 0.944 | 0.986 | 0.836 |
| loco/held-out radboud/ece | 0.075 | 0.056 | 0.017 | 0.129 | 0.081 | 0.017 | 0.129 |
| loco/held-out rijnstate/auroc | 0.968 | 0.009 | 0.963 | 0.979 | 0.963 | 0.964 | 0.979 |
| loco/held-out rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco/held-out rijnstate/specificity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco/held-out rijnstate/ece | 0.018 | 0.005 | 0.012 | 0.021 | 0.021 | 0.012 | 0.020 |
| loco/held-out utrecht/auroc | 0.992 | 0.001 | 0.991 | 0.993 | 0.993 | 0.991 | 0.992 |
| loco/held-out utrecht/sensitivity | 0.992 | 0.007 | 0.989 | 1.000 | 1.000 | 0.989 | 0.989 |
| loco/held-out utrecht/specificity | 0.681 | 0.332 | 0.305 | 0.933 | 0.305 | 0.933 | 0.805 |
| loco/held-out utrecht/ece | 0.236 | 0.143 | 0.108 | 0.390 | 0.390 | 0.108 | 0.210 |
| loco_by_domain/held-out cwz/camelyon17:cwz/auroc | 1.000 | 0.001 | 0.999 | 1.000 | 1.000 | 1.000 | 0.999 |
| loco_by_domain/held-out cwz/camelyon17:cwz/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out cwz/camelyon17:cwz/specificity | 0.914 | 0.091 | 0.810 | 0.983 | 0.810 | 0.948 | 0.983 |
| loco_by_domain/held-out cwz/camelyon17:cwz/ece | 0.089 | 0.069 | 0.043 | 0.168 | 0.168 | 0.043 | 0.056 |
| loco_by_domain/held-out radboud/camelyon16:radboud/auroc | 0.997 | 0.003 | 0.993 | 0.999 | 0.999 | 0.993 | 0.999 |
| loco_by_domain/held-out radboud/camelyon16:radboud/sensitivity | 0.993 | 0.006 | 0.989 | 1.000 | 0.989 | 0.989 | 1.000 |
| loco_by_domain/held-out radboud/camelyon16:radboud/specificity | 0.891 | 0.106 | 0.773 | 0.980 | 0.920 | 0.980 | 0.773 |
| loco_by_domain/held-out radboud/camelyon16:radboud/ece | 0.089 | 0.069 | 0.021 | 0.160 | 0.087 | 0.021 | 0.160 |
| loco_by_domain/held-out radboud/camelyon17:radboud/auroc | 1.000 | 0.000 | 0.999 | 1.000 | 1.000 | 1.000 | 0.999 |
| loco_by_domain/held-out radboud/camelyon17:radboud/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out radboud/camelyon17:radboud/specificity | 0.995 | 0.009 | 0.984 | 1.000 | 1.000 | 1.000 | 0.984 |
| loco_by_domain/held-out radboud/camelyon17:radboud/ece | 0.041 | 0.033 | 0.007 | 0.071 | 0.071 | 0.007 | 0.047 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/auroc | 0.968 | 0.009 | 0.963 | 0.979 | 0.963 | 0.964 | 0.979 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/sensitivity | 0.938 | 0.000 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/specificity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out rijnstate/camelyon17:rijnstate/ece | 0.018 | 0.005 | 0.012 | 0.021 | 0.021 | 0.012 | 0.020 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/auroc | 0.989 | 0.003 | 0.987 | 0.993 | 0.993 | 0.987 | 0.989 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/sensitivity | 0.990 | 0.009 | 0.985 | 1.000 | 1.000 | 0.985 | 0.985 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/specificity | 0.734 | 0.291 | 0.404 | 0.955 | 0.404 | 0.955 | 0.843 |
| loco_by_domain/held-out utrecht/camelyon16:utrecht/ece | 0.191 | 0.115 | 0.086 | 0.313 | 0.313 | 0.086 | 0.175 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/auroc | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/sensitivity | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/specificity | 0.618 | 0.380 | 0.187 | 0.907 | 0.187 | 0.907 | 0.760 |
| loco_by_domain/held-out utrecht/camelyon17:utrecht/ece | 0.307 | 0.186 | 0.144 | 0.510 | 0.510 | 0.144 | 0.269 |

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
| Copertura conformal | sì: insiemi per classe (E10); copertura dei positivi sul centro escluso peggiore |
| OOD | no |
| Metriche alla prevalenza reale, tasso di rinvio | sì: rinvii, PPV e NPV degli insiemi sul centro escluso, prevalenza 5–30%; senza soglia |
| Sottogruppi (scanner, tipo di campione) | per centro, per dominio (dataset × centro) e per diagnosi (micro e macrometastasi) |
| Regressione sui casi difficili | no |
