# Report di validazione — abmil-camelyon16-phikon

**Esito della batteria: DATI INSUFFICIENTI**

- 10 vetrini, ne servono almeno 100: questa esecuzione verifica solo che il codice funzioni

Solo uso di ricerca. Le soglie della batteria sono proposte iniziali, da fissare con i patologi.

## Provenienza

| | |
|---|---|
| Modello | `abmil-camelyon16-phikon` |
| Collezione embedding | `phikon__057cc0295895` |
| Versione backbone | `057cc0295895c2df3dd7681a89680da6015cbefe` |
| Split | `data/manifests/camelyon16_splits.csv (seed 0)` |
| Iperparametri | `{'hidden': 256, 'dropout': 0.25, 'lr': 0.0002, 'weight_decay': 0.0001, 'epochs': 30, 'max_tiles': 4096, 'threshold': 0.5}` |
| Versione codice | `371ad79075e1e154f1415b42a46b108470f24871+dirty` |
| Vetrini con embedding | 10 (10 sviluppo, 0 test bloccato) |

## Risultati

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation (predizioni fuori fold, aggregate) | 10 | 5 | 0.480 | 0.400 | 0.600 | 0.500 | 0.469 | 0.523 |
| Leave-one-center-out, held-out radboud | 5 | 3 | 0.333 | 0.667 | 0.500 | 0.583 | 0.333 | 0.504 |
| Leave-one-center-out, held-out utrecht | 5 | 2 | 0.333 | 0.000 | 1.000 | 0.500 | 0.351 | 0.432 |
| Split di test bloccato | 0 | | | | | | | |

AUROC peggiore tra i centri esclusi: **0.333**.

### Per centro

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, radboud | 5 | 3 | 0.000 | 0.333 | 0.000 | 0.167 | 0.749 | 0.802 |
| Cross-validation, utrecht | 5 | 2 | 0.833 | 0.500 | 1.000 | 0.750 | 0.190 | 0.243 |

### Localizzazione

AUROC dell'attenzione nel distinguere tile tumorali da normali, media sui vetrini positivi con annotazione completa (fuori fold): **0.717** su 4 vetrini.

## Esecuzioni

| Gruppo | Valutazione | Vetrini di training | Vetrini valutati | Stato | Motivo |
|---|---|---|---|---|---|
| cv | fold0 | 9 | 1 | ok |  |
| cv | fold1 | 7 | 3 | ok |  |
| cv | fold2 | 9 | 1 | ok |  |
| cv | fold3 | 8 | 2 | ok |  |
| cv | fold4 | 7 | 3 | ok |  |
| loco | held-out radboud | 5 | 5 | ok |  |
| loco | held-out utrecht | 5 | 5 | ok |  |
| test | held-out split | 10 | 0 | skipped | no slide to score |

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
