# E16 — H-optimus-0 contro Phikon a livello di tile

Codice `21850f59b1b3dbd13050ec72b22123712ae04317+dirty`. Media sui semi [0, 1, 2]; LPON non letto.

## Criterio

| | Phikon | H-optimus-0 | Differenza | Soglia | Rispettato |
|---|---|---|---|---|---|
| Specificità per tile, centro peggiore | 0.999 | 1.000 | +0.001 | ≥ +0.1 | no |
| AUROC per tile, centro peggiore | 0.979 | 0.997 | +0.019 | ≥ −0.01 | sì |

**Esito: H-optimus-0 non promettente a livello di tile.**

## Per centro escluso

| Centro escluso | Backbone | Specificità per tile | Specificità per vetrino (mediana) | AUROC per tile | Spostamento dei normali | Precisione@10 |
|---|---|---|---|---|---|---|
| cwz | h_optimus_0 | 1.000 | 1.000 | 0.999 | -1.53 | 0.990 |
| radboud | h_optimus_0 | 1.000 | 1.000 | 0.998 | +1.22 | 0.956 |
| rijnstate | h_optimus_0 | 1.000 | 1.000 | 1.000 | -0.13 | 0.989 |
| utrecht | h_optimus_0 | 1.000 | 1.000 | 0.997 | +4.86 | 0.976 |
| cwz | phikon | 0.999 | 1.000 | 0.994 | -3.34 | 0.853 |
| radboud | phikon | 1.000 | 1.000 | 0.989 | -2.03 | 0.773 |
| rijnstate | phikon | 1.000 | 1.000 | 0.999 | +1.92 | 0.945 |
| utrecht | phikon | 1.000 | 1.000 | 0.979 | -8.83 | 0.908 |

## Centro negli embedding

| Backbone | Probe tile AUROC | Probe tile acc. bil. | Probe vetrino AUROC | Probe vetrino acc. bil. | 10 vicini dello stesso centro |
|---|---|---|---|---|---|
| phikon | 0.999 | 0.986 | 0.999 | 0.997 | 0.967 |
| h_optimus_0 | 0.999 | 0.988 | 1.000 | 0.998 | 0.910 |
