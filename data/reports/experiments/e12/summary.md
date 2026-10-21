# E12 — punteggio del vetrino dalle tile più sospette

Controllo della riesecuzione di E6: coincide: differenza massima 0.00e+00 su 4626 righe.

Soglia τ per rotazione: lascia sopra il 95% dei positivi dei centri di training (punteggi fuori fold). Media sui tre semi (valori dei semi tra parentesi per i primari).

| Punteggio | k | Centro | Sens. micro | Sens. macro | Specificità | AUROC | AUROC micro | Mediana negativi (training) | Localizzazione | Punto cieco trovato |
|---|---|---|---|---|---|---|---|---|---|---|
| logit del vetrino | — | cwz | 0.899 (0.870, 0.913, 0.913) | 1.000 | 0.862 (1.000, 0.845, 0.741) | 0.976 | 0.964 | -2.51 (-7.51) | — | 1.000 |
| logit del vetrino | — | radboud | 0.967 (0.983, 0.950, 0.967) | 1.000 | 0.720 (0.593, 0.944, 0.621) | 0.984 | 0.970 | -4.19 (-7.57) | — | — |
| logit del vetrino | — | rijnstate | 0.846 (0.846, 0.846, 0.846) | 1.000 | 0.978 (0.967, 0.983, 0.983) | 0.978 | 0.946 | -6.47 (-6.89) | — | 0.000 |
| logit del vetrino | — | utrecht | 0.939 (0.895, 1.000, 0.921) | 1.000 | 0.606 (0.921, 0.006, 0.890) | 0.980 | 0.955 | -0.71 (-6.74) | — | — |
| istanza ABMIL | 1 | cwz | 0.928 (0.870, 0.957, 0.957) | 1.000 | 0.828 (0.966, 0.845, 0.672) | 0.976 | 0.964 | 1.66 (-0.75) | — | 1.000 |
| istanza ABMIL | 1 | radboud | 0.944 (0.950, 0.950, 0.933) | 0.989 | 0.977 (0.977, 0.991, 0.963) | 0.985 | 0.971 | -0.97 (0.18) | — | — |
| istanza ABMIL | 1 | rijnstate | 0.846 (0.846, 0.846, 0.846) | 1.000 | 0.939 (0.833, 0.983, 1.000) | 0.969 | 0.924 | -0.57 (-0.98) | — | 0.000 |
| istanza ABMIL | 1 | utrecht | 0.956 (0.921, 1.000, 0.947) | 1.000 | 0.608 (0.829, 0.244, 0.750) | 0.979 | 0.951 | 3.41 (-0.67) | — | — |
| classificatore di tile | 1 | cwz | 0.826 (0.783, 0.870, 0.826) | 1.000 | 0.753 (0.793, 0.776, 0.690) | 0.897 | 0.849 | 8.39 (6.30) | — | 1.000 |
| classificatore di tile | 1 | radboud | 0.889 (0.867, 0.900, 0.900) | 1.000 | 0.692 (0.836, 0.547, 0.692) | 0.960 | 0.921 | 8.05 (5.87) | — | — |
| classificatore di tile | 1 | rijnstate | 0.872 (0.846, 0.846, 0.923) | 1.000 | 0.950 (0.933, 0.967, 0.950) | 0.962 | 0.907 | 5.62 (6.37) | — | 0.333 |
| classificatore di tile | 1 | utrecht | 0.754 (0.789, 0.789, 0.684) | 0.980 | 0.888 (0.921, 0.756, 0.988) | 0.944 | 0.882 | 4.78 (6.06) | — | — |
| istanza ABMIL | 5 | cwz | 0.971 (0.913, 1.000, 1.000) | 1.000 | 0.569 (0.862, 0.448, 0.397) | 0.972 | 0.957 | 0.70 (-1.52) | 0.917 | 1.000 |
| istanza ABMIL | 5 | radboud | 0.883 (0.850, 0.900, 0.900) | 0.994 | 0.950 (0.986, 0.949, 0.916) | 0.977 | 0.956 | -1.81 (-0.67) | 0.900 | — |
| istanza ABMIL | 5 | rijnstate | 0.872 (0.923, 0.846, 0.846) | 1.000 | 0.844 (0.683, 0.883, 0.967) | 0.968 | 0.922 | -1.26 (-1.87) | 0.833 | 0.333 |
| istanza ABMIL | 5 | utrecht | 0.965 (0.921, 1.000, 0.974) | 1.000 | 0.238 (0.250, 0.079, 0.384) | 0.969 | 0.927 | 2.71 (-1.59) | 0.941 | — |
| classificatore di tile | 5 | cwz | 0.841 (0.826, 0.870, 0.826) | 1.000 | 0.718 (0.759, 0.707, 0.690) | 0.908 | 0.863 | 6.02 (3.83) | 0.750 | 1.000 |
| classificatore di tile | 5 | radboud | 0.883 (0.850, 0.900, 0.900) | 1.000 | 0.684 (0.883, 0.491, 0.678) | 0.958 | 0.917 | 5.10 (3.19) | 0.900 | — |
| classificatore di tile | 5 | rijnstate | 0.846 (0.846, 0.846, 0.846) | 1.000 | 0.939 (0.900, 0.950, 0.967) | 0.965 | 0.915 | 3.90 (3.93) | 0.944 | 0.000 |
| classificatore di tile | 5 | utrecht | 0.711 (0.711, 0.789, 0.632) | 0.993 | 0.846 (0.878, 0.677, 0.982) | 0.934 | 0.856 | 2.03 (3.16) | 0.912 | — |
| istanza ABMIL | 20 | cwz | 0.986 (0.957, 1.000, 1.000) | 1.000 | 0.236 (0.397, 0.069, 0.241) | 0.945 | 0.917 | -0.42 (-2.35) | — | 1.000 |
| istanza ABMIL | 20 | radboud | 0.806 (0.767, 0.800, 0.850) | 0.989 | 0.868 (0.967, 0.925, 0.710) | 0.946 | 0.896 | -2.78 (-1.58) | — | — |
| istanza ABMIL | 20 | rijnstate | 0.949 (1.000, 0.923, 0.923) | 1.000 | 0.494 (0.150, 0.383, 0.950) | 0.967 | 0.918 | -1.93 (-2.80) | — | 1.000 |
| istanza ABMIL | 20 | utrecht | 0.991 (0.974, 1.000, 1.000) | 1.000 | 0.004 (0.006, 0.000, 0.006) | 0.949 | 0.882 | 1.87 (-2.52) | — | — |
| classificatore di tile | 20 | cwz | 0.826 (0.826, 0.826, 0.826) | 1.000 | 0.552 (0.534, 0.552, 0.569) | 0.868 | 0.803 | 3.15 (1.04) | — | 0.667 |
| classificatore di tile | 20 | radboud | 0.900 (0.883, 0.900, 0.917) | 1.000 | 0.536 (0.701, 0.369, 0.537) | 0.944 | 0.890 | 1.48 (0.29) | — | — |
| classificatore di tile | 20 | rijnstate | 0.923 (0.923, 0.923, 0.923) | 1.000 | 0.633 (0.533, 0.650, 0.717) | 0.966 | 0.916 | 2.12 (1.19) | — | 1.000 |
| classificatore di tile | 20 | utrecht | 0.684 (0.737, 0.789, 0.526) | 0.993 | 0.736 (0.707, 0.567, 0.933) | 0.894 | 0.764 | -1.17 (0.24) | — | — |

Tempo del classificatore di tile: 1.14 ms per vetrino e modello (prodotto matrice, embedding già in memoria esclusi i tempi di lettura).

## Criterio

Segnale candidato (k = 5) rispetto alla logit del vetrino: sensibilità sulle micrometastasi del centro peggiore +0.10; specificità peggiore non oltre −0.05; AUROC peggiore non oltre −0.01.

- **istanza ABMIL**: non candidato; sensibilità micro peggiore 0.872 (rijnstate) contro 0.846, Δ +0.026; specificità peggiore Δ -0.368; AUROC peggiore Δ -0.008.
- **classificatore di tile**: non candidato; sensibilità micro peggiore 0.711 (utrecht) contro 0.846, Δ -0.136; specificità peggiore Δ +0.078; AUROC peggiore Δ -0.068.

**Esito: nessun segnale candidato.**
