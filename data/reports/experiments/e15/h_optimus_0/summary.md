# E15 — riconoscere un dominio non visto dagli embedding (h_optimus_0)

α = 0.05; soglia dai vetrini di calibrazione (fold 3) di ogni rotazione; riferimento fold 0, 1, 2; in distribuzione fold 4. V = media del vetrino, 5 vicini; T = 200 tile, distanza dal più vicino dei 256 prototipi k-center per vetrino.

## Primari

| Candidato | Falsi rinvii in distribuzione | sui positivi | Falsi positivi di E17 rinviati (semi) | Utrecht escluso rilevato | Esito |
|---|---|---|---|---|---|
| V | 0.055 (474) | 0.036 | 0.927 (0.971, 0.941, 0.868; 137, 17, 68 FP) | 1.000 | adottabile |
| T | 0.023 (474) | 0.065 | 0.902 (0.927, 1.000, 0.779; 137, 17, 68 FP) | 0.984 | adottabile |

## Per rotazione (secondari)

| Rotazione | Candidato | Falsi rinvii in distribuzione | Rilevamento fuori distribuzione | AUROC | Falsi negativi di E17 rinviati | Positivi fuori distribuzione rinviati: micro / macro |
|---|---|---|---|---|---|---|
| held-out cwz | V | 0.050 | 0.871 | 0.972 | — | 1.000 / 0.833 |
| held-out cwz | T | 0.022 | 0.699 | 0.969 | — | 0.783 / 0.833 |
| held-out radboud | V | 0.077 | 0.749 | 0.959 | 0.000 | 0.767 / 0.700 |
| held-out radboud | T | 0.011 | 0.524 | 0.957 | 0.000 | 0.500 / 0.717 |
| held-out rijnstate | V | 0.029 | 0.446 | 0.948 | 0.000 | 0.308 / 0.579 |
| held-out rijnstate | T | 0.014 | 0.152 | 0.829 | 0.000 | 0.077 / 0.684 |
| held-out utrecht | V | 0.077 | 1.000 | 0.991 | 1.000 | 1.000 / 1.000 |
| held-out utrecht | T | 0.048 | 0.984 | 0.994 | 1.000 | 0.974 / 0.980 |
| held-out radboud camelyon16 | V | 0.055 | 0.784 | 0.966 | — | 0.820 / 0.778 |
| held-out radboud camelyon16 | T | 0.028 | 0.604 | 0.965 | — | 0.520 / 0.756 |
| held-out utrecht camelyon16 | V | 0.055 | 0.474 | 0.941 | — | 0.400 / 0.600 |
| held-out utrecht camelyon16 | T | 0.031 | 0.649 | 0.951 | — | 0.633 / 0.743 |

## Falsi rinvii in distribuzione per dominio e per diagnosi (rotazioni principali)

| Gruppo | Vetrini | V | T |
|---|---|---|---|
| camelyon16:radboud | 147 | 0.020 | 0.007 |
| camelyon16:utrecht | 90 | 0.033 | 0.000 |
| camelyon17:cwz | 57 | 0.053 | 0.018 |
| camelyon17:radboud | 54 | 0.037 | 0.111 |
| camelyon17:rijnstate | 54 | 0.222 | 0.056 |
| camelyon17:utrecht | 72 | 0.042 | 0.000 |
| macro | 75 | 0.040 | 0.133 |
| micro | 93 | 0.032 | 0.011 |
| negative | 306 | 0.065 | 0.000 |

## Radboud, casi del 2015 (secondario, E3b)

| Valutazione | Positivi del 2015 | Positivi di altri anni | Negativi del 2015 | Negativi di altri anni |
|---|---|---|---|---|
| held-out cwz, in distribuzione, V | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out cwz, in distribuzione, T | 0.000 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out radboud, fuori distribuzione, V | 0.357 (14) | 0.840 (81) | 0.333 (18) | 0.832 (131) |
| held-out radboud, fuori distribuzione, T | 0.571 (14) | 0.642 (81) | 0.222 (18) | 0.649 (131) |
| held-out rijnstate, in distribuzione, V | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out rijnstate, in distribuzione, T | 0.000 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out utrecht, in distribuzione, V | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out utrecht, in distribuzione, T | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out radboud camelyon16, fuori distribuzione, V | 0.357 (14) | 0.877 (81) | 0.389 (18) | 0.832 (131) |
| held-out radboud camelyon16, fuori distribuzione, T | 0.571 (14) | 0.642 (81) | 0.222 (18) | 0.641 (131) |
| held-out utrecht camelyon16, in distribuzione, V | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out utrecht camelyon16, in distribuzione, T | 0.000 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |

**Esito: adottabile V.**
