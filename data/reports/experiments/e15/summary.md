# E15 — riconoscere un dominio non visto dagli embedding

α = 0.05; soglia dai vetrini di calibrazione (fold 3) di ogni rotazione; riferimento fold 0, 1, 2; in distribuzione fold 4. V = media del vetrino, 5 vicini; T = 200 tile, distanza dal più vicino dei 256 prototipi k-center per vetrino.

## Primari

| Candidato | Falsi rinvii in distribuzione | sui positivi | Falsi positivi di E6 rinviati (semi) | Utrecht escluso rilevato | Esito |
|---|---|---|---|---|---|
| V | 0.053 (474) | 0.065 | 0.997 (0.990, 1.000, 1.000; 96, 185, 71 FP) | 1.000 | adottabile |
| T | 0.042 (474) | 0.077 | 1.000 (1.000, 1.000, 1.000; 96, 185, 71 FP) | 1.000 | adottabile |

## Per rotazione (secondari)

| Rotazione | Candidato | Falsi rinvii in distribuzione | Rilevamento fuori distribuzione | AUROC | Falsi negativi di E6 rinviati | Positivi fuori distribuzione rinviati: micro / macro |
|---|---|---|---|---|---|---|
| held-out cwz | V | 0.050 | 1.000 | 1.000 | 1.000 | 1.000 / 1.000 |
| held-out cwz | T | 0.043 | 1.000 | 1.000 | 1.000 | 1.000 / 1.000 |
| held-out radboud | V | 0.011 | 0.946 | 0.994 | 1.000 | 0.983 / 0.967 |
| held-out radboud | T | 0.033 | 0.928 | 0.991 | 1.000 | 0.967 / 0.967 |
| held-out rijnstate | V | 0.043 | 0.891 | 0.977 | 0.500 | 0.692 / 0.947 |
| held-out rijnstate | T | 0.050 | 0.804 | 0.957 | 1.000 | 0.692 / 0.947 |
| held-out utrecht | V | 0.106 | 1.000 | 1.000 | 1.000 | 1.000 / 1.000 |
| held-out utrecht | T | 0.038 | 1.000 | 1.000 | 1.000 | 1.000 / 1.000 |
| held-out radboud camelyon16 | V | 0.055 | 0.996 | 0.998 | — | 1.000 / 1.000 |
| held-out radboud camelyon16 | T | 0.055 | 0.996 | 0.999 | — | 1.000 / 1.000 |
| held-out utrecht camelyon16 | V | 0.086 | 0.903 | 0.975 | — | 0.867 / 0.857 |
| held-out utrecht camelyon16 | T | 0.047 | 0.883 | 0.983 | — | 0.900 / 0.886 |

## Falsi rinvii in distribuzione per dominio e per diagnosi (rotazioni principali)

| Gruppo | Vetrini | V | T |
|---|---|---|---|
| camelyon16:radboud | 147 | 0.041 | 0.020 |
| camelyon16:utrecht | 90 | 0.033 | 0.011 |
| camelyon17:cwz | 57 | 0.000 | 0.018 |
| camelyon17:radboud | 54 | 0.130 | 0.111 |
| camelyon17:rijnstate | 54 | 0.093 | 0.056 |
| camelyon17:utrecht | 72 | 0.056 | 0.083 |
| macro | 75 | 0.013 | 0.093 |
| micro | 93 | 0.108 | 0.065 |
| negative | 306 | 0.046 | 0.023 |

## Radboud, casi del 2015 (secondario, E3b)

| Valutazione | Positivi del 2015 | Positivi di altri anni | Negativi del 2015 | Negativi di altri anni |
|---|---|---|---|---|
| held-out cwz, in distribuzione, V | 0.667 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out cwz, in distribuzione, T | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out radboud, fuori distribuzione, V | 1.000 (14) | 1.000 (81) | 1.000 (18) | 1.000 (131) |
| held-out radboud, fuori distribuzione, T | 1.000 (14) | 1.000 (81) | 1.000 (18) | 1.000 (131) |
| held-out rijnstate, in distribuzione, V | 0.667 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out rijnstate, in distribuzione, T | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out utrecht, in distribuzione, V | 0.667 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out utrecht, in distribuzione, T | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out radboud camelyon16, fuori distribuzione, V | 1.000 (14) | 1.000 (81) | 1.000 (18) | 1.000 (131) |
| held-out radboud camelyon16, fuori distribuzione, T | 1.000 (14) | 1.000 (81) | 1.000 (18) | 1.000 (131) |
| held-out utrecht camelyon16, in distribuzione, V | 0.667 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |
| held-out utrecht camelyon16, in distribuzione, T | 0.333 (3) | 0.000 (16) | 0.000 (5) | 0.000 (25) |

**Esito: adottabile V.**
