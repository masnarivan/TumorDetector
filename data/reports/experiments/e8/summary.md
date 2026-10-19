# E8 — confronto con E6

Media sui semi (valori dei semi tra parentesi); Δ = variante − E6.

| Metrica | E6 | balanced+adversarial | Δ | balanced+adversarial_negatives | Δ |
|---|---|---|---|---|---|
| ECE calibrata peggiore LOCO | 0.293 (0.252; 0.414; 0.214) | 0.389 (0.200; 0.522; 0.446) | +0.096 | 0.301 (0.310; 0.300; 0.293) | +0.008 |
| Specificità peggiore LOCO | 0.430 (0.561; 0.091; 0.638) | 0.383 (0.872; 0.052; 0.224) | -0.048 | 0.561 (0.524; 0.677; 0.483) | +0.131 |
| AUROC peggiore LOCO | 0.974 (0.970; 0.978; 0.974) | 0.962 (0.974; 0.955; 0.957) | -0.012 | 0.952 (0.955; 0.947; 0.953) | -0.022 |
| AUROC CV | 0.989 (0.992; 0.987; 0.988) | 0.986 (0.983; 0.987; 0.988) | -0.003 | 0.980 (0.977; 0.978; 0.985) | -0.009 |
| AUROC attenzione | 0.988 (0.991; 0.986; 0.987) | 0.992 (0.991; 0.993; 0.991) | +0.004 | 0.990 (0.990; 0.988; 0.992) | +0.002 |
| Specificità, cwz escluso | 0.770 (0.948; 0.724; 0.638) | 0.414 (0.966; 0.052; 0.224) | -0.356 | 0.718 (0.741; 0.931; 0.483) | -0.052 |
| Specificità, radboud escluso | 0.911 (0.916; 0.911; 0.907) | 0.896 (0.958; 0.864; 0.864) | -0.016 | 0.917 (0.939; 0.879; 0.935) | +0.006 |
| Specificità, rijnstate escluso | 0.972 (0.950; 0.983; 0.983) | 0.989 (0.983; 1.000; 0.983) | +0.017 | 0.989 (0.983; 0.983; 1.000) | +0.017 |
| Specificità, utrecht escluso | 0.492 (0.561; 0.091; 0.823) | 0.870 (0.872; 0.848; 0.890) | +0.378 | 0.663 (0.524; 0.677; 0.787) | +0.171 |
| Probe sul centro (negativi) | 0.999 (0.999; 0.999; 0.998) | 0.991 (0.991; 0.990; 0.991) | -0.008 | 0.997 (0.994; 0.999; 0.999) | -0.001 |
| Robustness Index | 2.649 (2.716; 2.456; 2.774) | 3.086 (3.002; 3.236; 3.021) | +0.437 | 2.376 (2.465; 2.295; 2.369) | -0.273 |
| ECE grezza peggiore LOCO | 0.320 (0.253; 0.487; 0.219) | 0.381 (0.115; 0.561; 0.468) | +0.062 | 0.284 (0.305; 0.250; 0.295) | -0.036 |
| Temperatura globale | 1.694 (1.576; 1.725; 1.780) | 1.920 (2.142; 1.751; 1.865) | +0.226 | 2.117 (1.928; 2.086; 2.338) | +0.423 |

## Logit mediana dei negativi (centro visto in CV, centro escluso in LOCO)

| Variante | cwz cv | cwz loco | radboud cv | radboud loco | rijnstate cv | rijnstate loco | utrecht cv | utrecht loco |
|---|---|---|---|---|---|---|---|---|
| E6 | -6.1 | -2.7 | -6.6 | -3.8 | -9.5 | -6.4 | -8.0 | 0.1 |
| balanced+adversarial | -4.6 | 1.2 | -5.1 | -4.2 | -5.6 | -7.0 | -6.0 | -2.3 |
| balanced+adversarial_negatives | -3.3 | -3.0 | -4.8 | -5.7 | -5.7 | -7.3 | -5.1 | -1.2 |

## Criterio di adozione

- **balanced+adversarial**: non adottabile; primari raggiunti: nessuno; vincoli violati: AUROC peggiore LOCO, Specificità, cwz escluso; gate: failed.
- **balanced+adversarial_negatives**: non adottabile; primari raggiunti: Specificità peggiore LOCO; vincoli violati: AUROC peggiore LOCO, Specificità, cwz escluso; gate: failed.

**Esito: nessuna variante adottata, si tiene la ricetta vuota.**
