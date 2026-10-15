# Report di validazione — abmil-camelyon16-phikon

**Esito della batteria: SUPERATA**


Solo uso di ricerca. Le soglie della batteria sono proposte iniziali, da fissare con i patologi.

## Provenienza

| | |
|---|---|
| Modello | `abmil-camelyon16-phikon` |
| Collezione embedding | `phikon__057cc0295895` |
| Versione backbone | `057cc0295895c2df3dd7681a89680da6015cbefe` |
| Split | `data/manifests/camelyon16_splits.csv (seed 0)` |
| Iperparametri | `{'hidden': 256, 'dropout': 0.25, 'lr': 0.0002, 'weight_decay': 0.0001, 'epochs': 30, 'max_tiles': 4096, 'threshold': 0.5, 'normalize': 'none'}` |
| Versione codice | `7712fdb3d827cdcb651ef2d8b5d082389d771eb1+dirty` |
| Vetrini con embedding | 399 (270 sviluppo, 129 test bloccato) |

## Risultati

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation (predizioni fuori fold, aggregate) | 270 | 111 | 0.987 | 0.946 | 0.931 | 0.938 | 0.042 | 0.049 |
| Leave-one-center-out, held-out radboud | 171 | 71 | 0.945 | 0.901 | 0.820 | 0.861 | 0.110 | 0.087 |
| Leave-one-center-out, held-out utrecht | 99 | 40 | 0.990 | 0.975 | 0.898 | 0.937 | 0.058 | 0.126 |
| Split di test bloccato | 129 | 49 | 0.995 | 0.959 | 0.963 | 0.961 | 0.032 | 0.034 |

AUROC peggiore tra i centri esclusi: **0.945**.

### Per centro

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, radboud | 171 | 71 | 0.986 | 0.958 | 0.890 | 0.924 | 0.053 | 0.063 |
| Cross-validation, utrecht | 99 | 40 | 0.996 | 0.925 | 1.000 | 0.963 | 0.023 | 0.029 |
| Test bloccato, radboud | 74 | 24 | 0.999 | 0.958 | 0.980 | 0.969 | 0.020 | 0.026 |
| Test bloccato, utrecht | 55 | 25 | 0.991 | 0.960 | 0.933 | 0.947 | 0.048 | 0.052 |

### Localizzazione

AUROC dell'attenzione nel distinguere tile tumorali da normali, media sui vetrini positivi con annotazione completa (fuori fold): **0.992** su 86 vetrini.

## Esecuzioni

| Gruppo | Valutazione | Vetrini di training | Vetrini valutati | Stato | Motivo |
|---|---|---|---|---|---|
| cv | fold0 | 216 | 54 | ok |  |
| cv | fold1 | 216 | 54 | ok |  |
| cv | fold2 | 216 | 54 | ok |  |
| cv | fold3 | 216 | 54 | ok |  |
| cv | fold4 | 216 | 54 | ok |  |
| loco | held-out radboud | 99 | 171 | ok |  |
| loco | held-out utrecht | 171 | 99 | ok |  |
| test | held-out split | 270 | 129 | ok |  |

## Copertura della batteria di promozione

| Voce del piano | Coperta da questo report |
|---|---|
| Leave-one-center-out, risultato peggiore | sì |
| Test esterno bloccato | sì, quando gli embedding dello split di test sono disponibili |
| Robustezza al centro (Robustness Index, probe lineare sul centro) | no |
| Calibrazione (ECE) | sì, aggregata; per centro nella tabella per centro |
| Copertura conformal | no: il modello non produce ancora insiemi di predizione |
| OOD | no |
| Metriche alla prevalenza reale, tasso di rinvio | no |
| Sottogruppi (scanner, tipo di campione) | solo per centro |
| Regressione sui casi difficili | no |
