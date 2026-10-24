# E16b — H-optimus-0 contro Phikon, classificatore di tile top-5 per vetrino

Controllo: il braccio Phikon coincide con E12 (differenza massima 3.81e-06). Media sui semi [0, 1, 2]; τ al 95% dei positivi dei centri di training, fuori fold. LPON non letto.

## Criterio

| Centro escluso peggiore | Phikon | H-optimus-0 | Differenza | Soglia | Rispettato |
|---|---|---|---|---|---|
| Specificità | 0.684 (radboud) | 0.907 (utrecht) | +0.223 | ≥ +0.1 | sì |
| Sensibilità micro | 0.711 (utrecht) | 0.846 (rijnstate) | +0.136 | ≥ −0.05 | sì |
| AUROC | 0.908 | 0.967 | +0.059 | ≥ −0.01 | sì |

**Esito: H-optimus-0 promettente a livello di vetrino.**

## Per centro escluso

| Centro | Backbone | Specificità (semi) | Sens. micro (semi) | Sens. macro | AUROC | AUROC micro | Mediana negativi (training) | Localizzazione |
|---|---|---|---|---|---|---|---|---|
| cwz | phikon | 0.718 (0.759, 0.707, 0.690) | 0.841 (0.826, 0.870, 0.826) | 1.000 | 0.908 | 0.863 | 6.02 (3.83) | 0.750 |
| cwz | h_optimus_0 | 0.948 (0.948, 0.931, 0.966) | 0.928 (0.913, 0.957, 0.913) | 1.000 | 0.994 | 0.991 | 1.95 (0.81) | 1.000 |
| radboud | phikon | 0.684 (0.883, 0.491, 0.678) | 0.883 (0.850, 0.900, 0.900) | 1.000 | 0.958 | 0.917 | 5.10 (3.19) | 0.900 |
| radboud | h_optimus_0 | 0.989 (0.995, 0.977, 0.995) | 0.872 (0.883, 0.883, 0.850) | 1.000 | 0.990 | 0.980 | 1.28 (-0.47) | 0.916 |
| rijnstate | phikon | 0.939 (0.900, 0.950, 0.967) | 0.846 (0.846, 0.846, 0.846) | 1.000 | 0.965 | 0.915 | 3.90 (3.93) | 0.944 |
| rijnstate | h_optimus_0 | 1.000 (1.000, 1.000, 1.000) | 0.846 (0.846, 0.846, 0.846) | 1.000 | 0.967 | 0.918 | -0.04 (1.04) | 0.833 |
| utrecht | phikon | 0.846 (0.878, 0.677, 0.982) | 0.711 (0.711, 0.789, 0.632) | 0.993 | 0.934 | 0.856 | 2.03 (3.16) | 0.912 |
| utrecht | h_optimus_0 | 0.907 (0.878, 0.884, 0.957) | 0.982 (0.974, 1.000, 0.974) | 1.000 | 0.997 | 0.993 | 8.44 (-0.79) | 0.926 |
