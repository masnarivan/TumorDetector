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
| Iperparametri | `{'hidden': 256, 'dropout': 0.25, 'lr': 0.0002, 'weight_decay': 0.0001, 'epochs': 30, 'max_tiles': 4096, 'threshold': 0.5}` |
| Versione codice | `70fa3d904cc7ccb8eab29e92f998636e5376bdb0` |
| Vetrini con embedding | 399 (270 sviluppo, 129 test bloccato) |

## Risultati

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation (predizioni fuori fold, aggregate) | 270 | 111 | 0.991 | 0.964 | 0.943 | 0.954 | 0.036 | 0.032 |
| Leave-one-center-out, held-out radboud | 171 | 71 | 0.947 | 0.789 | 1.000 | 0.894 | 0.075 | 0.083 |
| Leave-one-center-out, held-out utrecht | 99 | 40 | 0.999 | 1.000 | 0.780 | 0.890 | 0.107 | 0.235 |
| Split di test bloccato | 129 | 49 | 0.993 | 1.000 | 0.838 | 0.919 | 0.067 | 0.086 |

AUROC peggiore tra i centri esclusi: **0.947**.

### Per centro

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, radboud | 171 | 71 | 0.994 | 0.972 | 0.930 | 0.951 | 0.041 | 0.054 |
| Cross-validation, utrecht | 99 | 40 | 0.997 | 0.950 | 0.966 | 0.958 | 0.028 | 0.035 |
| Test bloccato, radboud | 74 | 24 | 0.995 | 1.000 | 0.920 | 0.960 | 0.037 | 0.058 |
| Test bloccato, utrecht | 55 | 25 | 0.996 | 1.000 | 0.700 | 0.850 | 0.106 | 0.137 |

### Localizzazione

AUROC dell'attenzione nel distinguere tile tumorali da normali, media sui vetrini positivi con annotazione completa (fuori fold): **0.990** su 86 vetrini.

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
