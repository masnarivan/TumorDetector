# E9 — correzione dell'offset con k negativi del centro nuovo

Controllo della riesecuzione di E6 (come in E10): coincide: differenza massima delle logit 0.00e+00 su 4626 righe.

200 estrazioni per seme, centro e k; media sulle estrazioni, poi sui semi. E6 = nessuna correzione sugli stessi vetrini di valutazione. p10 = 10° percentile della specificità sulle estrazioni.

| Variante | k | Centro | Specificità (E6) | p10 | Sensibilità (E6; visto) | ECE (E6) | AUROC (E6) | Mediana logit negativi (E6; rif.) | b (DS) |
|---|---|---|---|---|---|---|---|---|---|
| offset | 3 | cwz | 0.964 (0.770) | 0.879 | 0.847 (0.962; 0.924) | 0.093 (0.182) | 0.976 (0.976) | -7.4 (-2.5; -7.5) | 5.0 (2.2) |
| offset | 3 | radboud | 0.932 (0.911) | 0.817 | 0.940 (0.978; 0.975) | 0.070 (0.104) | 0.984 (0.984) | -7.1 (-4.2; -7.6) | 3.0 (2.8) |
| offset | 3 | rijnstate | 0.982 (0.973) | 0.977 | 0.938 (0.938; 0.938) | 0.034 (0.033) | 0.978 (0.978) | -7.1 (-6.5; -6.9) | 0.6 (1.4) |
| offset | 3 | utrecht | 0.972 (0.492) | 0.936 | 0.901 (0.981; 0.992) | 0.073 (0.271) | 0.980 (0.980) | -6.8 (-0.7; -6.7) | 6.1 (1.7) |
| offset | 5 | cwz | 0.966 (0.771) | 0.887 | 0.854 (0.962; 0.924) | 0.090 (0.179) | 0.976 (0.976) | -7.4 (-2.5; -7.5) | 4.9 (1.9) |
| offset | 5 | radboud | 0.947 (0.911) | 0.864 | 0.943 (0.978; 0.975) | 0.059 (0.104) | 0.984 (0.984) | -7.2 (-4.2; -7.6) | 3.0 (2.3) |
| offset | 5 | rijnstate | 0.984 (0.972) | 0.976 | 0.938 (0.938; 0.938) | 0.032 (0.032) | 0.978 (0.978) | -7.0 (-6.5; -6.9) | 0.5 (1.1) |
| offset | 5 | utrecht | 0.978 (0.492) | 0.962 | 0.909 (0.981; 0.992) | 0.066 (0.270) | 0.980 (0.980) | -6.8 (-0.7; -6.7) | 6.1 (1.2) |
| offset | 10 | cwz | 0.975 (0.770) | 0.924 | 0.860 (0.962; 0.924) | 0.082 (0.172) | 0.976 (0.976) | -7.4 (-2.5; -7.5) | 5.0 (1.2) |
| offset | 10 | radboud | 0.959 (0.911) | 0.912 | 0.942 (0.978; 0.975) | 0.048 (0.103) | 0.984 (0.984) | -7.4 (-4.2; -7.6) | 3.2 (1.5) |
| offset | 10 | rijnstate | 0.984 (0.972) | 0.980 | 0.938 (0.938; 0.938) | 0.030 (0.031) | 0.978 (0.978) | -6.9 (-6.4; -6.9) | 0.5 (0.7) |
| offset | 10 | utrecht | 0.978 (0.491) | 0.970 | 0.911 (0.981; 0.992) | 0.064 (0.267) | 0.980 (0.980) | -6.7 (-0.7; -6.7) | 6.0 (0.9) |
| offset | 20 | cwz | 0.983 (0.773) | 0.965 | 0.861 (0.962; 0.924) | 0.086 (0.154) | 0.977 (0.977) | -7.6 (-2.5; -7.5) | 5.1 (0.8) |
| offset | 20 | radboud | 0.968 (0.912) | 0.928 | 0.941 (0.978; 0.975) | 0.043 (0.100) | 0.984 (0.984) | -7.6 (-4.2; -7.6) | 3.4 (1.0) |
| offset | 20 | rijnstate | 0.984 (0.972) | 0.975 | 0.938 (0.938; 0.938) | 0.030 (0.029) | 0.978 (0.978) | -6.9 (-6.4; -6.9) | 0.4 (0.5) |
| offset | 20 | utrecht | 0.980 (0.492) | 0.972 | 0.912 (0.981; 0.992) | 0.063 (0.260) | 0.980 (0.980) | -6.7 (-0.7; -6.7) | 6.0 (0.6) |
| offset solo in discesa | 3 | cwz | 0.965 (0.770) | 0.879 | 0.846 (0.962; 0.924) | 0.092 (0.182) | 0.976 (0.976) | -7.4 (-2.5; -7.5) | 5.0 (2.2) |
| offset solo in discesa | 3 | radboud | 0.973 (0.911) | 0.946 | 0.938 (0.978; 0.975) | 0.049 (0.104) | 0.984 (0.984) | -7.7 (-4.2; -7.6) | 3.5 (2.1) |
| offset solo in discesa | 3 | rijnstate | 0.985 (0.973) | 0.982 | 0.938 (0.938; 0.938) | 0.025 (0.033) | 0.978 (0.978) | -7.6 (-6.5; -6.9) | 1.2 (0.9) |
| offset solo in discesa | 3 | utrecht | 0.972 (0.492) | 0.936 | 0.901 (0.981; 0.992) | 0.072 (0.271) | 0.980 (0.980) | -6.8 (-0.7; -6.7) | 6.1 (1.6) |
| offset solo in discesa | 5 | cwz | 0.966 (0.771) | 0.887 | 0.854 (0.962; 0.924) | 0.090 (0.179) | 0.976 (0.976) | -7.4 (-2.5; -7.5) | 4.9 (1.9) |
| offset solo in discesa | 5 | radboud | 0.974 (0.911) | 0.947 | 0.942 (0.978; 0.975) | 0.045 (0.104) | 0.984 (0.984) | -7.6 (-4.2; -7.6) | 3.4 (1.8) |
| offset solo in discesa | 5 | rijnstate | 0.986 (0.972) | 0.982 | 0.938 (0.938; 0.938) | 0.025 (0.032) | 0.978 (0.978) | -7.6 (-6.5; -6.9) | 1.1 (0.7) |
| offset solo in discesa | 5 | utrecht | 0.978 (0.492) | 0.962 | 0.909 (0.981; 0.992) | 0.066 (0.270) | 0.980 (0.980) | -6.8 (-0.7; -6.7) | 6.1 (1.2) |
| offset solo in discesa | 10 | cwz | 0.975 (0.770) | 0.924 | 0.860 (0.962; 0.924) | 0.082 (0.172) | 0.976 (0.976) | -7.4 (-2.5; -7.5) | 5.0 (1.2) |
| offset solo in discesa | 10 | radboud | 0.976 (0.911) | 0.958 | 0.941 (0.978; 0.975) | 0.041 (0.103) | 0.984 (0.984) | -7.6 (-4.2; -7.6) | 3.4 (1.2) |
| offset solo in discesa | 10 | rijnstate | 0.985 (0.972) | 0.980 | 0.938 (0.938; 0.938) | 0.025 (0.031) | 0.978 (0.978) | -7.4 (-6.4; -6.9) | 1.0 (0.4) |
| offset solo in discesa | 10 | utrecht | 0.978 (0.491) | 0.970 | 0.911 (0.981; 0.992) | 0.064 (0.267) | 0.980 (0.980) | -6.7 (-0.7; -6.7) | 6.0 (0.9) |
| offset solo in discesa | 20 | cwz | 0.983 (0.773) | 0.965 | 0.861 (0.962; 0.924) | 0.086 (0.154) | 0.977 (0.977) | -7.6 (-2.5; -7.5) | 5.1 (0.8) |
| offset solo in discesa | 20 | radboud | 0.977 (0.912) | 0.960 | 0.941 (0.978; 0.975) | 0.039 (0.100) | 0.984 (0.984) | -7.7 (-4.2; -7.6) | 3.5 (0.9) |
| offset solo in discesa | 20 | rijnstate | 0.984 (0.972) | 0.975 | 0.938 (0.938; 0.938) | 0.027 (0.029) | 0.978 (0.978) | -7.4 (-6.4; -6.9) | 1.0 (0.2) |
| offset solo in discesa | 20 | utrecht | 0.980 (0.492) | 0.972 | 0.912 (0.981; 0.992) | 0.063 (0.260) | 0.980 (0.980) | -6.7 (-0.7; -6.7) | 6.0 (0.6) |

## Per dominio (media su estrazioni e semi)

| Variante | k | Centro | camelyon16:radboud/sensitivity | camelyon16:radboud/specificity | camelyon16:utrecht/sensitivity | camelyon16:utrecht/specificity | camelyon17:cwz/sensitivity | camelyon17:cwz/specificity | camelyon17:radboud/sensitivity | camelyon17:radboud/specificity | camelyon17:rijnstate/sensitivity | camelyon17:rijnstate/specificity | camelyon17:utrecht/sensitivity | camelyon17:utrecht/specificity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| offset | 3 | cwz | — | — | — | — | 0.847 | 0.964 | — | — | — | — | — | — |
| offset | 3 | radboud | 0.930 | 0.910 | — | — | — | — | 0.978 | 0.986 | — | — | — | — |
| offset | 3 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.982 | — | — |
| offset | 3 | utrecht | — | — | 0.939 | 0.960 | — | — | — | — | — | — | 0.793 | 0.987 |
| offset | 5 | cwz | — | — | — | — | 0.854 | 0.966 | — | — | — | — | — | — |
| offset | 5 | radboud | 0.933 | 0.927 | — | — | — | — | 0.981 | 0.994 | — | — | — | — |
| offset | 5 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.984 | — | — |
| offset | 5 | utrecht | — | — | 0.946 | 0.967 | — | — | — | — | — | — | 0.803 | 0.991 |
| offset | 10 | cwz | — | — | — | — | 0.860 | 0.975 | — | — | — | — | — | — |
| offset | 10 | radboud | 0.931 | 0.943 | — | — | — | — | 0.982 | 0.997 | — | — | — | — |
| offset | 10 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.984 | — | — |
| offset | 10 | utrecht | — | — | 0.948 | 0.968 | — | — | — | — | — | — | 0.808 | 0.990 |
| offset | 20 | cwz | — | — | — | — | 0.861 | 0.983 | — | — | — | — | — | — |
| offset | 20 | radboud | 0.929 | 0.955 | — | — | — | — | 0.983 | 0.999 | — | — | — | — |
| offset | 20 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.984 | — | — |
| offset | 20 | utrecht | — | — | 0.948 | 0.971 | — | — | — | — | — | — | 0.810 | 0.991 |
| offset solo in discesa | 3 | cwz | — | — | — | — | 0.846 | 0.965 | — | — | — | — | — | — |
| offset solo in discesa | 3 | radboud | 0.928 | 0.961 | — | — | — | — | 0.978 | 0.999 | — | — | — | — |
| offset solo in discesa | 3 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.985 | — | — |
| offset solo in discesa | 3 | utrecht | — | — | 0.939 | 0.960 | — | — | — | — | — | — | 0.793 | 0.987 |
| offset solo in discesa | 5 | cwz | — | — | — | — | 0.854 | 0.966 | — | — | — | — | — | — |
| offset solo in discesa | 5 | radboud | 0.932 | 0.963 | — | — | — | — | 0.981 | 0.999 | — | — | — | — |
| offset solo in discesa | 5 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.986 | — | — |
| offset solo in discesa | 5 | utrecht | — | — | 0.946 | 0.967 | — | — | — | — | — | — | 0.803 | 0.991 |
| offset solo in discesa | 10 | cwz | — | — | — | — | 0.860 | 0.975 | — | — | — | — | — | — |
| offset solo in discesa | 10 | radboud | 0.931 | 0.966 | — | — | — | — | 0.982 | 1.000 | — | — | — | — |
| offset solo in discesa | 10 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.985 | — | — |
| offset solo in discesa | 10 | utrecht | — | — | 0.948 | 0.968 | — | — | — | — | — | — | 0.808 | 0.990 |
| offset solo in discesa | 20 | cwz | — | — | — | — | 0.861 | 0.983 | — | — | — | — | — | — |
| offset solo in discesa | 20 | radboud | 0.929 | 0.968 | — | — | — | — | 0.983 | 1.000 | — | — | — | — |
| offset solo in discesa | 20 | rijnstate | — | — | — | — | — | — | — | — | 0.938 | 0.984 | — | — |
| offset solo in discesa | 20 | utrecht | — | — | 0.948 | 0.971 | — | — | — | — | — | — | 0.810 | 0.991 |

## Offset trasferito tra dataset dello stesso centro (secondario)

k negativi da un dataset, valutazione su tutti i vetrini dell'altro.

| Variante | k | Centro | Da → a | Specificità (E6) | Sensibilità (E6) | b |
|---|---|---|---|---|---|---|
| offset | 3 | radboud | camelyon16 → camelyon17 | 0.998 (0.990) | 0.967 (1.000) | 4.6 |
| offset | 3 | radboud | camelyon17 → camelyon16 | 0.729 (0.878) | 0.972 (0.972) | -1.3 |
| offset | 3 | utrecht | camelyon16 → camelyon17 | 0.992 (0.569) | 0.777 (0.928) | 6.5 |
| offset | 3 | utrecht | camelyon17 → camelyon16 | 0.936 (0.427) | 0.951 (1.000) | 5.3 |
| offset | 5 | radboud | camelyon16 → camelyon17 | 0.999 (0.990) | 0.970 (1.000) | 4.5 |
| offset | 5 | radboud | camelyon17 → camelyon16 | 0.750 (0.878) | 0.972 (0.972) | -1.2 |
| offset | 5 | utrecht | camelyon16 → camelyon17 | 0.993 (0.569) | 0.783 (0.928) | 6.5 |
| offset | 5 | utrecht | camelyon17 → camelyon16 | 0.946 (0.427) | 0.953 (1.000) | 5.3 |
| offset | 10 | radboud | camelyon16 → camelyon17 | 1.000 (0.990) | 0.972 (1.000) | 4.7 |
| offset | 10 | radboud | camelyon17 → camelyon16 | 0.760 (0.878) | 0.973 (0.972) | -1.2 |
| offset | 10 | utrecht | camelyon16 → camelyon17 | 0.995 (0.569) | 0.797 (0.928) | 6.4 |
| offset | 10 | utrecht | camelyon17 → camelyon16 | 0.957 (0.427) | 0.955 (1.000) | 5.4 |
| offset | 20 | radboud | camelyon16 → camelyon17 | 1.000 (0.990) | 0.973 (1.000) | 4.6 |
| offset | 20 | radboud | camelyon17 → camelyon16 | 0.762 (0.878) | 0.973 (0.972) | -1.2 |
| offset | 20 | utrecht | camelyon16 → camelyon17 | 0.996 (0.569) | 0.797 (0.928) | 6.5 |
| offset | 20 | utrecht | camelyon17 → camelyon16 | 0.959 (0.427) | 0.957 (1.000) | 5.3 |
| offset solo in discesa | 3 | radboud | camelyon16 → camelyon17 | 1.000 (0.990) | 0.967 (1.000) | 4.8 |
| offset solo in discesa | 3 | radboud | camelyon17 → camelyon16 | 0.910 (0.878) | 0.966 (0.972) | 0.7 |
| offset solo in discesa | 3 | utrecht | camelyon16 → camelyon17 | 0.992 (0.569) | 0.777 (0.928) | 6.5 |
| offset solo in discesa | 3 | utrecht | camelyon17 → camelyon16 | 0.937 (0.427) | 0.951 (1.000) | 5.3 |
| offset solo in discesa | 5 | radboud | camelyon16 → camelyon17 | 1.000 (0.990) | 0.970 (1.000) | 4.6 |
| offset solo in discesa | 5 | radboud | camelyon17 → camelyon16 | 0.908 (0.878) | 0.967 (0.972) | 0.6 |
| offset solo in discesa | 5 | utrecht | camelyon16 → camelyon17 | 0.993 (0.569) | 0.783 (0.928) | 6.5 |
| offset solo in discesa | 5 | utrecht | camelyon17 → camelyon16 | 0.946 (0.427) | 0.953 (1.000) | 5.3 |
| offset solo in discesa | 10 | radboud | camelyon16 → camelyon17 | 1.000 (0.990) | 0.972 (1.000) | 4.7 |
| offset solo in discesa | 10 | radboud | camelyon17 → camelyon16 | 0.905 (0.878) | 0.967 (0.972) | 0.5 |
| offset solo in discesa | 10 | utrecht | camelyon16 → camelyon17 | 0.995 (0.569) | 0.797 (0.928) | 6.4 |
| offset solo in discesa | 10 | utrecht | camelyon17 → camelyon16 | 0.957 (0.427) | 0.955 (1.000) | 5.4 |
| offset solo in discesa | 20 | radboud | camelyon16 → camelyon17 | 1.000 (0.990) | 0.973 (1.000) | 4.6 |
| offset solo in discesa | 20 | radboud | camelyon17 → camelyon16 | 0.904 (0.878) | 0.968 (0.972) | 0.5 |
| offset solo in discesa | 20 | utrecht | camelyon16 → camelyon17 | 0.996 (0.569) | 0.797 (0.928) | 6.5 |
| offset solo in discesa | 20 | utrecht | camelyon17 → camelyon16 | 0.959 (0.427) | 0.957 (1.000) | 5.3 |

## Criterio

Proponibile: specificità peggiore +0.10 o ECE peggiore −0.03 rispetto a E6; sensibilità di nessun centro più di 0.05 sotto quella del centro visto in CV; p10 della specificità sul centro peggiore di E6 non sotto la specificità di E6 su quel centro.

- **offset, k = 3**: non proponibile; specificità peggiore radboud Δ +0.441; ECE peggiore Δ -0.178; perdita di sensibilità massima 0.091 rispetto al centro visto (utrecht), 0.115 rispetto a E6; p10 su utrecht (peggiore in E6) 0.936 contro E6 0.492.
- **offset, k = 5**: non proponibile; specificità peggiore radboud Δ +0.455; ECE peggiore Δ -0.179; perdita di sensibilità massima 0.084 rispetto al centro visto (utrecht), 0.108 rispetto a E6; p10 su utrecht (peggiore in E6) 0.962 contro E6 0.492.
- **offset, k = 10**: non proponibile; specificità peggiore radboud Δ +0.468; ECE peggiore Δ -0.184; perdita di sensibilità massima 0.081 rispetto al centro visto (utrecht), 0.102 rispetto a E6; p10 su utrecht (peggiore in E6) 0.970 contro E6 0.491.
- **offset, k = 20**: non proponibile; specificità peggiore radboud Δ +0.477; ECE peggiore Δ -0.173; perdita di sensibilità massima 0.081 rispetto al centro visto (utrecht), 0.101 rispetto a E6; p10 su utrecht (peggiore in E6) 0.972 contro E6 0.492.
- **offset solo in discesa, k = 3**: non proponibile; specificità peggiore cwz Δ +0.473; ECE peggiore Δ -0.179; perdita di sensibilità massima 0.092 rispetto al centro visto (utrecht), 0.115 rispetto a E6; p10 su utrecht (peggiore in E6) 0.936 contro E6 0.492.
- **offset solo in discesa, k = 5**: non proponibile; specificità peggiore cwz Δ +0.474; ECE peggiore Δ -0.179; perdita di sensibilità massima 0.084 rispetto al centro visto (utrecht), 0.108 rispetto a E6; p10 su utrecht (peggiore in E6) 0.962 contro E6 0.492.
- **offset solo in discesa, k = 10**: non proponibile; specificità peggiore cwz Δ +0.483; ECE peggiore Δ -0.184; perdita di sensibilità massima 0.081 rispetto al centro visto (utrecht), 0.102 rispetto a E6; p10 su utrecht (peggiore in E6) 0.970 contro E6 0.491.
- **offset solo in discesa, k = 20**: non proponibile; specificità peggiore radboud Δ +0.486; ECE peggiore Δ -0.173; perdita di sensibilità massima 0.081 rispetto al centro visto (utrecht), 0.101 rispetto a E6; p10 su utrecht (peggiore in E6) 0.972 contro E6 0.492.

**Esito: nessun k proponibile: la correzione dell'offset non si porta ai patologi in questa forma.**
