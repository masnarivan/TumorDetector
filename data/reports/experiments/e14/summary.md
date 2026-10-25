# E14 — vetrini di un centro nuovo aggiunti al training

Controllo del codice: utrecht escluso senza vetrini aggiunti, seme 0: differenza massima dalle logit LOCO di E6 0.00e+00.

Tutti i 144 modelli riaddestrati presenti.

Media su 3 semi × 3 estrazioni, sugli stessi vetrini di valutazione per centro ed estrazione. Soglia 0,5. «mai visto» = LOCO di E6, «visto» = CV di E6, «offset» = E9 solo in discesa con i negativi tra i vetrini aggiunti. Spec. min = la peggiore dei 9 modelli.

| Centro | Metodo | n (aggiunti; positivi) | Specificità (min) | Sensibilità | Micro | Macro | AUROC | ECE | Mediana negativi / positivi |
|---|---|---|---|---|---|---|---|---|---|
| cwz | valutazione | 52 vetrini, 22 positivi, 14 micro | | | | | | | |
| cwz | mai visto | — | 0.733 (0.548) | 0.939 | 0.902 | 1.000 | 0.960 | 0.178 | -2.4 / 10.9 |
| cwz | visto | — | 0.940 (0.857) | 0.879 | 0.805 | 1.000 | 0.936 | 0.087 | -6.0 / 11.1 |
| cwz | riaddestrato | 5 (5.7; 1.7) | 0.813 (0.571) | 0.913 | 0.860 | 1.000 | 0.958 | 0.147 | -3.7 / 10.5 |
| cwz | offset | 5 (5.7; 1.7) | 0.946 (0.643) | 0.852 | 0.764 | 1.000 | 0.960 | 0.089 | -6.3 / 7.0 |
| cwz | riaddestrato | 10 (10.3; 3.3) | 0.892 (0.581) | 0.859 | 0.769 | 1.000 | 0.939 | 0.113 | -6.6 / 9.0 |
| cwz | offset | 10 (10.3; 3.3) | 0.981 (0.929) | 0.837 | 0.740 | 1.000 | 0.960 | 0.079 | -7.0 / 6.3 |
| cwz | riaddestrato | 20 (20.7; 8.7) | 0.860 (0.581) | 0.874 | 0.797 | 1.000 | 0.946 | 0.125 | -5.0 / 10.1 |
| cwz | offset | 20 (20.7; 8.7) | 0.977 (0.857) | 0.826 | 0.725 | 1.000 | 0.960 | 0.086 | -7.3 / 6.0 |
| cwz | riaddestrato | 40 (41.0; 13.0) | 0.981 (0.929) | 0.848 | 0.756 | 1.000 | 0.968 | 0.066 | -8.2 / 9.5 |
| cwz | offset | 40 (41.0; 13.0) | 0.985 (0.964) | 0.833 | 0.731 | 1.000 | 0.960 | 0.086 | -7.4 / 5.9 |
| radboud | valutazione | 293 vetrini, 107 positivi, 53 micro | | | | | | | |
| radboud | mai visto | — | 0.911 (0.902) | 0.978 | 0.963 | 0.994 | 0.985 | 0.104 | -4.2 / 12.2 |
| radboud | visto | — | 0.964 (0.957) | 0.974 | 0.948 | 1.000 | 0.991 | 0.045 | -6.7 / 12.5 |
| radboud | riaddestrato | 5 (5.0; 1.3) | 0.961 (0.913) | 0.967 | 0.935 | 0.998 | 0.987 | 0.038 | -7.0 / 12.4 |
| radboud | offset | 5 (5.0; 1.3) | 0.975 (0.924) | 0.943 | 0.902 | 0.983 | 0.985 | 0.051 | -7.3 / 9.1 |
| radboud | riaddestrato | 10 (10.0; 2.7) | 0.972 (0.908) | 0.956 | 0.925 | 0.988 | 0.980 | 0.043 | -6.4 / 10.6 |
| radboud | offset | 10 (10.0; 2.7) | 0.985 (0.915) | 0.936 | 0.890 | 0.981 | 0.985 | 0.043 | -8.4 / 8.0 |
| radboud | riaddestrato | 20 (20.0; 6.3) | 0.988 (0.957) | 0.966 | 0.932 | 1.000 | 0.987 | 0.023 | -8.6 / 10.5 |
| radboud | offset | 20 (20.0; 6.3) | 0.994 (0.989) | 0.935 | 0.890 | 0.979 | 0.985 | 0.034 | -8.6 / 7.8 |
| radboud | riaddestrato | 40 (41.0; 13.0) | 0.983 (0.935) | 0.949 | 0.900 | 0.998 | 0.987 | 0.032 | -8.0 / 11.0 |
| radboud | offset | 40 (41.0; 13.0) | 0.977 (0.930) | 0.944 | 0.902 | 0.985 | 0.985 | 0.040 | -7.3 / 9.1 |
| rijnstate | valutazione | 51 vetrini, 16 positivi, 7 micro | | | | | | | |
| rijnstate | mai visto | — | 0.968 (0.941) | 0.939 | 0.875 | 1.000 | 0.974 | 0.040 | -6.5 / 13.5 |
| rijnstate | visto | — | 0.946 (0.912) | 0.939 | 0.875 | 1.000 | 0.983 | 0.055 | -9.5 / 12.5 |
| rijnstate | riaddestrato | 5 (6.3; 4.3) | 0.951 (0.882) | 0.939 | 0.875 | 1.000 | 0.965 | 0.063 | -6.8 / 12.7 |
| rijnstate | offset | 5 (6.3; 4.3) | 0.991 (0.971) | 0.939 | 0.875 | 1.000 | 0.974 | 0.032 | -7.8 / 12.2 |
| rijnstate | riaddestrato | 10 (11.3; 5.7) | 0.981 (0.971) | 0.939 | 0.875 | 1.000 | 0.964 | 0.051 | -6.8 / 13.5 |
| rijnstate | offset | 10 (11.3; 5.7) | 0.984 (0.971) | 0.939 | 0.875 | 1.000 | 0.974 | 0.030 | -7.7 / 12.3 |
| rijnstate | riaddestrato | 20 (22.3; 11.3) | 0.962 (0.889) | 0.939 | 0.875 | 1.000 | 0.964 | 0.052 | -7.2 / 12.3 |
| rijnstate | offset | 20 (22.3; 11.3) | 0.981 (0.971) | 0.939 | 0.875 | 1.000 | 0.974 | 0.030 | -7.5 / 12.5 |
| rijnstate | riaddestrato | 40 (41.0; 15.7) | 0.962 (0.889) | 0.939 | 0.875 | 1.000 | 0.966 | 0.046 | -9.2 / 13.8 |
| rijnstate | offset | 40 (41.0; 15.7) | 0.981 (0.971) | 0.939 | 0.875 | 1.000 | 0.974 | 0.029 | -7.6 / 12.5 |
| utrecht | valutazione | 211 vetrini, 73 positivi, 33 micro | | | | | | | |
| utrecht | mai visto | — | 0.488 (0.083) | 0.980 | 0.956 | 1.000 | 0.980 | 0.274 | -0.7 / 11.9 |
| utrecht | visto | — | 0.978 (0.947) | 0.991 | 0.980 | 1.000 | 0.998 | 0.030 | -7.9 / 12.0 |
| utrecht | riaddestrato | 5 (6.3; 2.3) | 0.954 (0.894) | 0.945 | 0.878 | 1.000 | 0.976 | 0.056 | -6.3 / 10.8 |
| utrecht | offset | 5 (6.3; 2.3) | 0.979 (0.909) | 0.890 | 0.806 | 0.958 | 0.980 | 0.067 | -6.9 / 5.7 |
| utrecht | riaddestrato | 10 (10.7; 3.3) | 0.978 (0.943) | 0.945 | 0.878 | 1.000 | 0.972 | 0.032 | -7.4 / 10.4 |
| utrecht | offset | 10 (10.7; 3.3) | 0.980 (0.943) | 0.903 | 0.819 | 0.970 | 0.980 | 0.061 | -6.7 / 5.9 |
| utrecht | riaddestrato | 20 (20.0; 6.7) | 0.990 (0.972) | 0.940 | 0.866 | 1.000 | 0.973 | 0.025 | -9.3 / 11.2 |
| utrecht | offset | 20 (20.0; 6.7) | 0.982 (0.947) | 0.897 | 0.812 | 0.964 | 0.980 | 0.059 | -6.9 / 5.7 |
| utrecht | riaddestrato | 40 (40.7; 14.7) | 0.974 (0.886) | 0.946 | 0.882 | 1.000 | 0.978 | 0.042 | -7.5 / 11.4 |
| utrecht | offset | 40 (40.7; 14.7) | 0.981 (0.947) | 0.902 | 0.816 | 0.972 | 0.980 | 0.060 | -6.7 / 5.9 |

## Frazione di distanza chiusa (specificità, riaddestrato)

| Centro | Distanza visto − mai visto | n = 5 | n = 10 | n = 20 | n = 40 |
|---|---|---|---|---|---|
| cwz | +0.206 | 0.388 | 0.769 | 0.613 | 1.202 |
| radboud | +0.053 | 0.957 | 1.158 | 1.466 | 1.375 |
| rijnstate | -0.023 | — | — | — | — |
| utrecht | +0.490 | 0.950 | 0.999 | 1.023 | 0.992 |

## Specificità per dominio (secondario)

| Centro | Metodo | n | camelyon16:radboud/specificity | camelyon16:utrecht/specificity | camelyon17:cwz/specificity | camelyon17:radboud/specificity | camelyon17:rijnstate/specificity | camelyon17:utrecht/specificity |
|---|---|---|---|---|---|---|---|---|
| cwz | mai visto | 0 | — | — | 0.733 | — | — | — |
| radboud | mai visto | 0 | 0.876 | — | — | 0.992 | — | — |
| rijnstate | mai visto | 0 | — | — | — | — | 0.968 | — |
| utrecht | mai visto | 0 | — | 0.417 | — | — | — | 0.573 |
| cwz | riaddestrato | 5 | — | — | 0.813 | — | — | — |
| radboud | riaddestrato | 5 | 0.952 | — | — | 0.983 | — | — |
| rijnstate | riaddestrato | 5 | — | — | — | — | 0.951 | — |
| utrecht | riaddestrato | 5 | — | 0.956 | — | — | — | 0.948 |
| cwz | riaddestrato | 10 | — | — | 0.892 | — | — | — |
| radboud | riaddestrato | 10 | 0.963 | — | — | 0.992 | — | — |
| rijnstate | riaddestrato | 10 | — | — | — | — | 0.981 | — |
| utrecht | riaddestrato | 10 | — | 0.973 | — | — | — | 0.983 |
| cwz | riaddestrato | 20 | — | — | 0.860 | — | — | — |
| radboud | riaddestrato | 20 | 0.989 | — | — | 0.986 | — | — |
| rijnstate | riaddestrato | 20 | — | — | — | — | 0.962 | — |
| utrecht | riaddestrato | 20 | — | 0.991 | — | — | — | 0.988 |
| cwz | riaddestrato | 40 | — | — | 0.981 | — | — | — |
| radboud | riaddestrato | 40 | 0.979 | — | — | 0.994 | — | — |
| rijnstate | riaddestrato | 40 | — | — | — | — | 0.962 | — |
| utrecht | riaddestrato | 40 | — | 0.969 | — | — | — | 0.983 |
| cwz | visto | 0 | — | — | 0.940 | — | — | — |
| radboud | visto | 0 | 0.948 | — | — | 1.000 | — | — |
| rijnstate | visto | 0 | — | — | — | — | 0.946 | — |
| utrecht | visto | 0 | — | 0.967 | — | — | — | 0.991 |

## Criterio

n sufficiente: specificità e sensibilità entro 0.05 dal centro visto, micrometastasi entro 0.1, nessuno dei 9 modelli con specificità sotto 0.8. Costo d'ingresso = il più piccolo n sufficiente (0 se lo è già il centro mai visto).

- **cwz, mai visto**: no: specificità 0.733 < visto 0.940 − 0.05; specificità minima 0.548 < 0.8.
- **cwz, n = 5**: no: specificità 0.813 < visto 0.940 − 0.05; specificità minima 0.571 < 0.8. Offset: no: specificità minima 0.643 < 0.8. Riaddestrare non rende più dell'offset.
- **cwz, n = 10**: no: specificità minima 0.581 < 0.8. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **cwz, n = 20**: no: specificità 0.860 < visto 0.940 − 0.05; specificità minima 0.581 < 0.8. Offset: no: sensibilità 0.826 < visto 0.879 − 0.05. Riaddestrare non rende più dell'offset.
- **cwz, n = 40**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **radboud, mai visto**: no: specificità 0.911 < visto 0.964 − 0.05.
- **radboud, n = 5**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **radboud, n = 10**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **radboud, n = 20**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **radboud, n = 40**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **rijnstate, mai visto**: sufficiente.
- **rijnstate, n = 5**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **rijnstate, n = 10**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **rijnstate, n = 20**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **rijnstate, n = 40**: sufficiente. Offset: sufficiente. Riaddestrare non rende più dell'offset.
- **utrecht, mai visto**: no: specificità 0.488 < visto 0.978 − 0.05; specificità minima 0.083 < 0.8.
- **utrecht, n = 5**: no: micrometastasi 0.878 < visto 0.980 − 0.1. Offset: no: sensibilità 0.890 < visto 0.991 − 0.05; micrometastasi 0.806 < visto 0.980 − 0.1. Riaddestrare non rende più dell'offset.
- **utrecht, n = 10**: no: micrometastasi 0.878 < visto 0.980 − 0.1. Offset: no: sensibilità 0.903 < visto 0.991 − 0.05; micrometastasi 0.819 < visto 0.980 − 0.1. Riaddestrare non rende più dell'offset.
- **utrecht, n = 20**: no: sensibilità 0.940 < visto 0.991 − 0.05; micrometastasi 0.866 < visto 0.980 − 0.1. Offset: no: sensibilità 0.897 < visto 0.991 − 0.05; micrometastasi 0.812 < visto 0.980 − 0.1. Riaddestrare non rende più dell'offset.
- **utrecht, n = 40**: sufficiente. Offset: no: sensibilità 0.902 < visto 0.991 − 0.05; micrometastasi 0.816 < visto 0.980 − 0.1. Riaddestrare rende più dell'offset.

**Costo d'ingresso:** cwz 40; radboud 5; rijnstate 0; utrecht 40.
