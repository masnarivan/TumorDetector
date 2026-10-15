# Report di validazione — abmil-camelyon16-phikon

**Esito della batteria: SUPERATA** (media su 3 semi)


Solo uso di ricerca. Le soglie della batteria sono proposte iniziali, da fissare con i patologi.

## Provenienza

| | |
|---|---|
| Modello | `abmil-camelyon16-phikon` |
| Collezione embedding | `phikon__057cc0295895` |
| Versione backbone | `057cc0295895c2df3dd7681a89680da6015cbefe` |
| Split | `data/manifests/camelyon16_splits.csv (seed 0)` |
| Iperparametri | `{'hidden': 256, 'dropout': 0.25, 'lr': 0.0002, 'weight_decay': 0.0001, 'epochs': 30, 'max_tiles': 4096, 'threshold': 0.5, 'normalize': 'none', 'threads': 1}` |
| Semi | `[0, 1, 2] (modello salvato: seme 0)` |
| Versione codice | `c07c13a14e55610c656635d3b15e6764ce40ac75` |
| Vetrini con embedding | 399 (270 sviluppo, 129 test bloccato) |

## Risultati

Ogni valore è la media su 3 semi (0, 1, 2): stesso protocollo, stessi split, cambiano inizializzazione, ordine dei vetrini e tile campionate. La variabilità è nella sezione «Variabilità tra semi».

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation (predizioni fuori fold, aggregate) | 270 | 111 | 0.989 | 0.964 | 0.941 | 0.953 | 0.036 | 0.040 |
| Leave-one-center-out, held-out radboud | 171 | 71 | 0.973 | 0.930 | 0.883 | 0.906 | 0.073 | 0.079 |
| Leave-one-center-out, held-out utrecht | 99 | 40 | 0.997 | 0.992 | 0.864 | 0.928 | 0.065 | 0.146 |
| Split di test bloccato | 129 | 49 | 0.996 | 0.946 | 0.958 | 0.952 | 0.032 | 0.041 |

AUROC peggiore tra i centri esclusi: **0.973**.

### Per centro

| Valutazione | Vetrini | Positivi | AUROC | Sensibilità | Specificità | Acc. bilanciata | Brier | ECE |
|---|---|---|---|---|---|---|---|---|
| Cross-validation, radboud | 171 | 71 | 0.984 | 0.967 | 0.917 | 0.942 | 0.045 | 0.050 |
| Cross-validation, utrecht | 99 | 40 | 0.998 | 0.958 | 0.983 | 0.971 | 0.019 | 0.025 |
| Test bloccato, radboud | 74 | 24 | 0.993 | 0.917 | 0.947 | 0.932 | 0.042 | 0.060 |
| Test bloccato, utrecht | 55 | 25 | 0.997 | 0.973 | 0.978 | 0.976 | 0.018 | 0.023 |

### Localizzazione

AUROC dell'attenzione nel distinguere tile tumorali da normali, media sui vetrini positivi con annotazione completa (fuori fold): **0.989** su 86 vetrini.

## Variabilità tra semi

| Metrica | Media | DS | Min | Max | Seme 0 | Seme 1 | Seme 2 |
|---|---|---|---|---|---|---|---|
| cv/auroc | 0.989 | 0.003 | 0.987 | 0.993 | 0.987 | 0.989 | 0.993 |
| cv/ece | 0.040 | 0.009 | 0.031 | 0.049 | 0.049 | 0.040 | 0.031 |
| loco_worst_auroc | 0.973 | 0.024 | 0.945 | 0.988 | 0.945 | 0.986 | 0.988 |
| test/auroc | 0.996 | 0.001 | 0.995 | 0.997 | 0.995 | 0.997 | 0.995 |
| test/ece | 0.041 | 0.014 | 0.032 | 0.057 | 0.034 | 0.032 | 0.057 |
| attention_auroc_mean | 0.989 | 0.004 | 0.985 | 0.992 | 0.992 | 0.990 | 0.985 |
| loco/held-out radboud/auroc | 0.973 | 0.024 | 0.945 | 0.988 | 0.945 | 0.986 | 0.988 |
| loco/held-out radboud/sensitivity | 0.930 | 0.049 | 0.901 | 0.986 | 0.901 | 0.901 | 0.986 |
| loco/held-out radboud/specificity | 0.883 | 0.085 | 0.820 | 0.980 | 0.820 | 0.980 | 0.850 |
| loco/held-out radboud/ece | 0.079 | 0.037 | 0.039 | 0.112 | 0.087 | 0.039 | 0.112 |
| loco/held-out utrecht/auroc | 0.997 | 0.006 | 0.990 | 1.000 | 0.990 | 1.000 | 1.000 |
| loco/held-out utrecht/sensitivity | 0.992 | 0.014 | 0.975 | 1.000 | 0.975 | 1.000 | 1.000 |
| loco/held-out utrecht/specificity | 0.864 | 0.090 | 0.763 | 0.932 | 0.898 | 0.763 | 0.932 |
| loco/held-out utrecht/ece | 0.146 | 0.038 | 0.123 | 0.190 | 0.126 | 0.190 | 0.123 |
| test_by_center/radboud/auroc | 0.993 | 0.005 | 0.990 | 0.999 | 0.999 | 0.991 | 0.990 |
| test_by_center/radboud/sensitivity | 0.917 | 0.042 | 0.875 | 0.958 | 0.958 | 0.875 | 0.917 |
| test_by_center/radboud/specificity | 0.947 | 0.058 | 0.880 | 0.980 | 0.980 | 0.980 | 0.880 |
| test_by_center/radboud/ece | 0.060 | 0.037 | 0.026 | 0.100 | 0.026 | 0.055 | 0.100 |
| test_by_center/utrecht/auroc | 0.997 | 0.005 | 0.991 | 1.000 | 0.991 | 1.000 | 1.000 |
| test_by_center/utrecht/sensitivity | 0.973 | 0.023 | 0.960 | 1.000 | 0.960 | 1.000 | 0.960 |
| test_by_center/utrecht/specificity | 0.978 | 0.038 | 0.933 | 1.000 | 0.933 | 1.000 | 1.000 |
| test_by_center/utrecht/ece | 0.023 | 0.025 | 0.004 | 0.052 | 0.052 | 0.004 | 0.013 |

## Esecuzioni (seme 0)

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
