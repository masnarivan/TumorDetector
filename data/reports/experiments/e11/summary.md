# E11 — offset e insiemi conformal insieme

Controllo della riesecuzione di E6 (come in E10): coincide: differenza massima delle logit 0.00e+00 su 4626 righe.

200 estrazioni per seme, centro e k; media sulle estrazioni, poi sui semi. Offset «offset solo in discesa». Riferimenti sugli stessi vetrini: E10 per classe (senza offset), E9 offset e E6 alla soglia 0.5. f0 cattiva = 90° percentile sulle estrazioni.

## α = 0.05

| Metodo | k | Centro | Copertura positivi | Tumori persi | Sens. centro visto | Negativi con {1} | f0 cattiva | Rinvii | Copertura negativi | Dimensione media | Errore sulle risposte | b medio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| offset + per classe | 3 | cwz | 0.765 | 0.170 | 0.924 | 0.023 | 0.091 | 0.066 | 0.941 | 0.972 | 0.086 | 4.852 |
| offset + per classe | 3 | radboud | 0.954 | 0.040 | 0.975 | 0.051 | 0.090 | 0.055 | 0.936 | 1.033 | 0.052 | 3.601 |
| offset + per classe | 3 | rijnstate | 0.938 | 0.062 | 0.938 | 0.013 | 0.018 | 0.003 | 0.984 | 0.999 | 0.031 | 1.170 |
| offset + per classe | 3 | utrecht | 0.891 | 0.087 | 0.992 | 0.013 | 0.023 | 0.027 | 0.978 | 0.999 | 0.041 | 6.056 |
| offset + per classe | 5 | cwz | 0.766 | 0.166 | 0.924 | 0.015 | 0.069 | 0.066 | 0.953 | 0.974 | 0.081 | 5.017 |
| offset + per classe | 5 | radboud | 0.957 | 0.039 | 0.975 | 0.050 | 0.091 | 0.057 | 0.936 | 1.036 | 0.051 | 3.412 |
| offset + per classe | 5 | rijnstate | 0.938 | 0.062 | 0.938 | 0.013 | 0.018 | 0.003 | 0.984 | 0.999 | 0.031 | 1.065 |
| offset + per classe | 5 | utrecht | 0.894 | 0.084 | 0.992 | 0.012 | 0.021 | 0.025 | 0.980 | 1.000 | 0.039 | 6.101 |
| offset + per classe | 10 | cwz | 0.777 | 0.159 | 0.924 | 0.010 | 0.021 | 0.066 | 0.961 | 0.979 | 0.078 | 5.011 |
| offset + per classe | 10 | radboud | 0.958 | 0.038 | 0.975 | 0.051 | 0.078 | 0.056 | 0.937 | 1.038 | 0.051 | 3.297 |
| offset + per classe | 10 | rijnstate | 0.938 | 0.062 | 0.938 | 0.014 | 0.020 | 0.002 | 0.985 | 1.001 | 0.033 | 0.998 |
| offset + per classe | 10 | utrecht | 0.901 | 0.079 | 0.992 | 0.012 | 0.017 | 0.024 | 0.981 | 1.001 | 0.037 | 6.027 |
| offset + per classe | 20 | cwz | 0.779 | 0.158 | 0.924 | 0.005 | 0.018 | 0.068 | 0.972 | 0.983 | 0.084 | 5.108 |
| offset + per classe | 20 | radboud | 0.957 | 0.041 | 0.975 | 0.051 | 0.074 | 0.052 | 0.941 | 1.041 | 0.052 | 3.483 |
| offset + per classe | 20 | rijnstate | 0.938 | 0.062 | 0.938 | 0.016 | 0.025 | 0.001 | 0.984 | 1.001 | 0.037 | 0.948 |
| offset + per classe | 20 | utrecht | 0.906 | 0.077 | 0.992 | 0.012 | 0.016 | 0.023 | 0.982 | 1.003 | 0.038 | 6.021 |
| offset + per classe, negativi locali | 20 | cwz | 0.779 | 0.107 | 0.924 | 0.005 | 0.018 | 0.077 | 0.956 | 0.926 | 0.058 | 5.108 |
| offset + per classe, negativi locali | 20 | radboud | 0.957 | 0.027 | 0.975 | 0.021 | 0.043 | 0.098 | 0.953 | 1.053 | 0.026 | 3.483 |
| offset + per classe, negativi locali | 20 | rijnstate | 0.938 | 0.055 | 0.938 | 0.017 | 0.025 | 0.023 | 0.948 | 0.977 | 0.035 | 0.948 |
| offset + per classe, negativi locali | 20 | utrecht | 0.906 | 0.046 | 0.992 | 0.012 | 0.021 | 0.043 | 0.954 | 0.964 | 0.026 | 6.021 |
| E10 per classe | 3 | cwz | 0.933 | 0.038 | 0.924 | 0.138 | 0.145 | 0.107 | 0.729 | 0.922 | 0.113 | 4.852 |
| E10 per classe | 3 | radboud | 0.983 | 0.014 | 0.975 | 0.132 | 0.134 | 0.135 | 0.809 | 1.058 | 0.104 | 3.601 |
| E10 per classe | 3 | rijnstate | 0.938 | 0.062 | 0.938 | 0.022 | 0.023 | 0.007 | 0.967 | 0.993 | 0.037 | 1.170 |
| E10 per classe | 3 | utrecht | 0.973 | 0.023 | 0.992 | 0.366 | 0.369 | 0.058 | 0.575 | 0.979 | 0.259 | 6.056 |
| E10 per classe | 5 | cwz | 0.933 | 0.038 | 0.924 | 0.138 | 0.151 | 0.106 | 0.730 | 0.924 | 0.111 | 5.017 |
| E10 per classe | 5 | radboud | 0.983 | 0.014 | 0.975 | 0.132 | 0.136 | 0.135 | 0.808 | 1.057 | 0.104 | 3.412 |
| E10 per classe | 5 | rijnstate | 0.938 | 0.062 | 0.938 | 0.022 | 0.024 | 0.007 | 0.967 | 0.993 | 0.037 | 1.065 |
| E10 per classe | 5 | utrecht | 0.973 | 0.023 | 0.992 | 0.366 | 0.369 | 0.058 | 0.576 | 0.979 | 0.258 | 6.101 |
| E10 per classe | 10 | cwz | 0.933 | 0.038 | 0.924 | 0.138 | 0.160 | 0.105 | 0.730 | 0.928 | 0.108 | 5.011 |
| E10 per classe | 10 | radboud | 0.983 | 0.014 | 0.975 | 0.133 | 0.137 | 0.134 | 0.808 | 1.057 | 0.103 | 3.297 |
| E10 per classe | 10 | rijnstate | 0.938 | 0.062 | 0.938 | 0.022 | 0.027 | 0.007 | 0.967 | 0.993 | 0.038 | 0.998 |
| E10 per classe | 10 | utrecht | 0.973 | 0.023 | 0.992 | 0.366 | 0.372 | 0.057 | 0.575 | 0.979 | 0.255 | 6.027 |
| E10 per classe | 20 | cwz | 0.933 | 0.038 | 0.924 | 0.137 | 0.167 | 0.100 | 0.732 | 0.936 | 0.100 | 5.108 |
| E10 per classe | 20 | radboud | 0.983 | 0.014 | 0.975 | 0.132 | 0.141 | 0.131 | 0.809 | 1.056 | 0.101 | 3.483 |
| E10 per classe | 20 | rijnstate | 0.938 | 0.062 | 0.938 | 0.023 | 0.033 | 0.006 | 0.966 | 0.994 | 0.041 | 0.948 |
| E10 per classe | 20 | utrecht | 0.973 | 0.023 | 0.992 | 0.366 | 0.377 | 0.055 | 0.575 | 0.980 | 0.249 | 6.021 |
| E9 offset | 3 | cwz | 0.850 | 0.150 | 0.924 | 0.040 | 0.139 | 0.000 | 0.960 | 1.000 | 0.083 | 4.852 |
| E9 offset | 3 | radboud | 0.938 | 0.062 | 0.975 | 0.027 | 0.055 | 0.000 | 0.973 | 1.000 | 0.040 | 3.601 |
| E9 offset | 3 | rijnstate | 0.938 | 0.062 | 0.938 | 0.015 | 0.018 | 0.000 | 0.985 | 1.000 | 0.032 | 1.170 |
| E9 offset | 3 | utrecht | 0.903 | 0.097 | 0.992 | 0.027 | 0.041 | 0.000 | 0.973 | 1.000 | 0.052 | 6.056 |
| E9 offset | 5 | cwz | 0.854 | 0.146 | 0.924 | 0.030 | 0.107 | 0.000 | 0.970 | 1.000 | 0.076 | 5.017 |
| E9 offset | 5 | radboud | 0.943 | 0.057 | 0.975 | 0.026 | 0.056 | 0.000 | 0.974 | 1.000 | 0.038 | 3.412 |
| E9 offset | 5 | rijnstate | 0.938 | 0.062 | 0.938 | 0.015 | 0.018 | 0.000 | 0.985 | 1.000 | 0.032 | 1.065 |
| E9 offset | 5 | utrecht | 0.905 | 0.095 | 0.992 | 0.022 | 0.040 | 0.000 | 0.978 | 1.000 | 0.048 | 6.101 |
| E9 offset | 10 | cwz | 0.860 | 0.140 | 0.924 | 0.023 | 0.063 | 0.000 | 0.977 | 1.000 | 0.072 | 5.011 |
| E9 offset | 10 | radboud | 0.942 | 0.058 | 0.975 | 0.025 | 0.046 | 0.000 | 0.975 | 1.000 | 0.037 | 3.297 |
| E9 offset | 10 | rijnstate | 0.938 | 0.062 | 0.938 | 0.016 | 0.020 | 0.000 | 0.984 | 1.000 | 0.034 | 0.998 |
| E9 offset | 10 | utrecht | 0.910 | 0.090 | 0.992 | 0.021 | 0.028 | 0.000 | 0.979 | 1.000 | 0.046 | 6.027 |
| E9 offset | 20 | cwz | 0.860 | 0.140 | 0.924 | 0.015 | 0.035 | 0.000 | 0.985 | 1.000 | 0.074 | 5.108 |
| E9 offset | 20 | radboud | 0.940 | 0.060 | 0.975 | 0.023 | 0.040 | 0.000 | 0.977 | 1.000 | 0.037 | 3.483 |
| E9 offset | 20 | rijnstate | 0.938 | 0.062 | 0.938 | 0.017 | 0.025 | 0.000 | 0.983 | 1.000 | 0.037 | 0.948 |
| E9 offset | 20 | utrecht | 0.912 | 0.088 | 0.992 | 0.020 | 0.025 | 0.000 | 0.980 | 1.000 | 0.046 | 6.021 |
| E6 | 3 | cwz | 0.962 | 0.038 | 0.924 | 0.231 | 0.242 | 0.000 | 0.769 | 1.000 | 0.156 | 4.852 |
| E6 | 3 | radboud | 0.978 | 0.022 | 0.975 | 0.089 | 0.090 | 0.000 | 0.911 | 1.000 | 0.065 | 3.601 |
| E6 | 3 | rijnstate | 0.938 | 0.062 | 0.938 | 0.028 | 0.029 | 0.000 | 0.972 | 1.000 | 0.040 | 1.170 |
| E6 | 3 | utrecht | 0.981 | 0.019 | 0.992 | 0.508 | 0.513 | 0.000 | 0.492 | 1.000 | 0.335 | 6.056 |
| E6 | 5 | cwz | 0.962 | 0.038 | 0.924 | 0.229 | 0.245 | 0.000 | 0.771 | 1.000 | 0.153 | 5.017 |
| E6 | 5 | radboud | 0.978 | 0.022 | 0.975 | 0.089 | 0.091 | 0.000 | 0.911 | 1.000 | 0.064 | 3.412 |
| E6 | 5 | rijnstate | 0.938 | 0.062 | 0.938 | 0.027 | 0.030 | 0.000 | 0.973 | 1.000 | 0.040 | 1.065 |
| E6 | 5 | utrecht | 0.981 | 0.019 | 0.992 | 0.508 | 0.514 | 0.000 | 0.492 | 1.000 | 0.334 | 6.101 |
| E6 | 10 | cwz | 0.962 | 0.038 | 0.924 | 0.230 | 0.257 | 0.000 | 0.770 | 1.000 | 0.149 | 5.011 |
| E6 | 10 | radboud | 0.978 | 0.022 | 0.975 | 0.089 | 0.093 | 0.000 | 0.911 | 1.000 | 0.064 | 3.297 |
| E6 | 10 | rijnstate | 0.938 | 0.062 | 0.938 | 0.028 | 0.033 | 0.000 | 0.972 | 1.000 | 0.041 | 0.998 |
| E6 | 10 | utrecht | 0.981 | 0.019 | 0.992 | 0.508 | 0.518 | 0.000 | 0.492 | 1.000 | 0.330 | 6.027 |
| E6 | 20 | cwz | 0.962 | 0.038 | 0.924 | 0.227 | 0.272 | 0.000 | 0.773 | 1.000 | 0.137 | 5.108 |
| E6 | 20 | radboud | 0.978 | 0.022 | 0.975 | 0.089 | 0.098 | 0.000 | 0.911 | 1.000 | 0.063 | 3.483 |
| E6 | 20 | rijnstate | 0.938 | 0.062 | 0.938 | 0.028 | 0.042 | 0.000 | 0.972 | 1.000 | 0.044 | 0.948 |
| E6 | 20 | utrecht | 0.981 | 0.019 | 0.992 | 0.508 | 0.523 | 0.000 | 0.492 | 1.000 | 0.322 | 6.021 |

## α = 0.10

| Metodo | k | Centro | Copertura positivi | Tumori persi | Sens. centro visto | Negativi con {1} | f0 cattiva | Rinvii | Copertura negativi | Dimensione media | Errore sulle risposte | b medio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| offset + per classe | 3 | cwz | 0.559 | 0.105 | 0.924 | 0.002 | 0.012 | 0.204 | 0.878 | 0.796 | 0.051 | 4.852 |
| offset + per classe | 3 | radboud | 0.828 | 0.031 | 0.975 | 0.005 | 0.006 | 0.131 | 0.870 | 0.869 | 0.017 | 3.601 |
| offset + per classe | 3 | rijnstate | 0.923 | 0.062 | 0.938 | 0.005 | 0.006 | 0.027 | 0.960 | 0.973 | 0.027 | 1.170 |
| offset + per classe | 3 | utrecht | 0.586 | 0.058 | 0.992 | 0.003 | 0.008 | 0.156 | 0.950 | 0.844 | 0.027 | 6.056 |
| offset + per classe | 5 | cwz | 0.549 | 0.107 | 0.924 | 0.001 | 0.006 | 0.199 | 0.896 | 0.801 | 0.052 | 5.017 |
| offset + per classe | 5 | radboud | 0.843 | 0.030 | 0.975 | 0.005 | 0.006 | 0.127 | 0.867 | 0.873 | 0.017 | 3.412 |
| offset + per classe | 5 | rijnstate | 0.927 | 0.062 | 0.938 | 0.005 | 0.006 | 0.025 | 0.961 | 0.975 | 0.027 | 1.065 |
| offset + per classe | 5 | utrecht | 0.589 | 0.057 | 0.992 | 0.003 | 0.008 | 0.152 | 0.957 | 0.848 | 0.026 | 6.101 |
| offset + per classe | 10 | cwz | 0.548 | 0.107 | 0.924 | 0.000 | 0.000 | 0.199 | 0.907 | 0.801 | 0.055 | 5.011 |
| offset + per classe | 10 | radboud | 0.853 | 0.029 | 0.975 | 0.006 | 0.007 | 0.118 | 0.876 | 0.882 | 0.016 | 3.297 |
| offset + per classe | 10 | rijnstate | 0.930 | 0.062 | 0.938 | 0.006 | 0.007 | 0.023 | 0.962 | 0.977 | 0.028 | 0.998 |
| offset + per classe | 10 | utrecht | 0.594 | 0.055 | 0.992 | 0.002 | 0.006 | 0.151 | 0.961 | 0.849 | 0.026 | 6.027 |
| offset + per classe | 20 | cwz | 0.541 | 0.111 | 0.924 | 0.000 | 0.000 | 0.211 | 0.914 | 0.789 | 0.066 | 5.108 |
| offset + per classe | 20 | radboud | 0.847 | 0.029 | 0.975 | 0.005 | 0.007 | 0.112 | 0.891 | 0.888 | 0.016 | 3.483 |
| offset + per classe | 20 | rijnstate | 0.933 | 0.062 | 0.938 | 0.006 | 0.008 | 0.020 | 0.962 | 0.980 | 0.032 | 0.948 |
| offset + per classe | 20 | utrecht | 0.597 | 0.053 | 0.992 | 0.002 | 0.002 | 0.155 | 0.962 | 0.845 | 0.025 | 6.021 |
| offset + per classe, negativi locali | 20 | cwz | 0.541 | 0.077 | 0.924 | 0.000 | 0.000 | 0.229 | 0.912 | 0.771 | 0.048 | 5.108 |
| offset + per classe, negativi locali | 20 | radboud | 0.847 | 0.025 | 0.975 | 0.005 | 0.007 | 0.102 | 0.908 | 0.898 | 0.015 | 3.483 |
| offset + per classe, negativi locali | 20 | rijnstate | 0.933 | 0.045 | 0.938 | 0.006 | 0.008 | 0.062 | 0.900 | 0.938 | 0.025 | 0.948 |
| offset + per classe, negativi locali | 20 | utrecht | 0.597 | 0.033 | 0.992 | 0.002 | 0.002 | 0.196 | 0.908 | 0.804 | 0.017 | 6.021 |
| E10 per classe | 3 | cwz | 0.857 | 0.029 | 0.924 | 0.017 | 0.018 | 0.294 | 0.574 | 0.706 | 0.029 | 4.852 |
| E10 per classe | 3 | radboud | 0.944 | 0.017 | 0.975 | 0.008 | 0.008 | 0.291 | 0.558 | 0.709 | 0.016 | 3.601 |
| E10 per classe | 3 | rijnstate | 0.938 | 0.052 | 0.938 | 0.005 | 0.006 | 0.071 | 0.889 | 0.929 | 0.023 | 1.170 |
| E10 per classe | 3 | utrecht | 0.951 | 0.015 | 0.992 | 0.024 | 0.025 | 0.392 | 0.388 | 0.608 | 0.034 | 6.056 |
| E10 per classe | 5 | cwz | 0.857 | 0.029 | 0.924 | 0.017 | 0.019 | 0.292 | 0.574 | 0.708 | 0.029 | 5.017 |
| E10 per classe | 5 | radboud | 0.944 | 0.017 | 0.975 | 0.008 | 0.008 | 0.290 | 0.558 | 0.710 | 0.016 | 3.412 |
| E10 per classe | 5 | rijnstate | 0.938 | 0.052 | 0.938 | 0.006 | 0.006 | 0.070 | 0.890 | 0.930 | 0.024 | 1.065 |
| E10 per classe | 5 | utrecht | 0.951 | 0.015 | 0.992 | 0.024 | 0.025 | 0.390 | 0.389 | 0.610 | 0.034 | 6.101 |
| E10 per classe | 10 | cwz | 0.857 | 0.029 | 0.924 | 0.018 | 0.021 | 0.284 | 0.574 | 0.716 | 0.029 | 5.011 |
| E10 per classe | 10 | radboud | 0.944 | 0.017 | 0.975 | 0.008 | 0.008 | 0.288 | 0.557 | 0.712 | 0.016 | 3.297 |
| E10 per classe | 10 | rijnstate | 0.938 | 0.052 | 0.938 | 0.006 | 0.007 | 0.069 | 0.888 | 0.931 | 0.025 | 0.998 |
| E10 per classe | 10 | utrecht | 0.951 | 0.015 | 0.992 | 0.024 | 0.026 | 0.386 | 0.388 | 0.614 | 0.033 | 6.027 |
| E10 per classe | 20 | cwz | 0.857 | 0.029 | 0.924 | 0.016 | 0.026 | 0.267 | 0.576 | 0.733 | 0.028 | 5.108 |
| E10 per classe | 20 | radboud | 0.944 | 0.017 | 0.975 | 0.008 | 0.009 | 0.283 | 0.559 | 0.717 | 0.016 | 3.483 |
| E10 per classe | 20 | rijnstate | 0.938 | 0.052 | 0.938 | 0.006 | 0.008 | 0.064 | 0.888 | 0.936 | 0.028 | 0.948 |
| E10 per classe | 20 | utrecht | 0.951 | 0.015 | 0.992 | 0.024 | 0.028 | 0.377 | 0.389 | 0.623 | 0.033 | 6.021 |

## Micrometastasi e macrometastasi (α = 0.05)

| Metodo | k | Centro | Micro persi | Micro rinviati | Macro persi | Macro rinviati |
|---|---|---|---|---|---|---|
| offset + per classe | 3 | cwz | 0.239 | 0.122 | 0.037 | 0.096 |
| offset + per classe | 3 | radboud | 0.069 | 0.031 | 0.011 | 0.005 |
| offset + per classe | 3 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| offset + per classe | 3 | utrecht | 0.159 | 0.062 | 0.032 | 0.048 |
| offset + per classe | 5 | cwz | 0.237 | 0.133 | 0.032 | 0.088 |
| offset + per classe | 5 | radboud | 0.067 | 0.026 | 0.011 | 0.004 |
| offset + per classe | 5 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| offset + per classe | 5 | utrecht | 0.157 | 0.062 | 0.029 | 0.048 |
| offset + per classe | 10 | cwz | 0.226 | 0.146 | 0.031 | 0.059 |
| offset + per classe | 10 | radboud | 0.067 | 0.026 | 0.010 | 0.005 |
| offset + per classe | 10 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| offset + per classe | 10 | utrecht | 0.152 | 0.059 | 0.023 | 0.045 |
| offset + per classe | 20 | cwz | 0.224 | 0.155 | 0.033 | 0.042 |
| offset + per classe | 20 | radboud | 0.072 | 0.024 | 0.011 | 0.004 |
| offset + per classe | 20 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| offset + per classe | 20 | utrecht | 0.150 | 0.056 | 0.021 | 0.041 |
| offset + per classe, negativi locali | 20 | cwz | 0.163 | 0.157 | 0.000 | 0.040 |
| offset + per classe, negativi locali | 20 | radboud | 0.046 | 0.085 | 0.009 | 0.026 |
| offset + per classe, negativi locali | 20 | rijnstate | 0.134 | 0.019 | 0.000 | 0.000 |
| offset + per classe, negativi locali | 20 | utrecht | 0.100 | 0.072 | 0.005 | 0.039 |
| E10 per classe | 3 | cwz | 0.058 | 0.101 | 0.000 | 0.000 |
| E10 per classe | 3 | radboud | 0.028 | 0.017 | 0.000 | 0.000 |
| E10 per classe | 3 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E10 per classe | 3 | utrecht | 0.053 | 0.009 | 0.000 | 0.000 |
| E10 per classe | 5 | cwz | 0.058 | 0.101 | 0.000 | 0.000 |
| E10 per classe | 5 | radboud | 0.028 | 0.017 | 0.000 | 0.000 |
| E10 per classe | 5 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E10 per classe | 5 | utrecht | 0.053 | 0.009 | 0.000 | 0.000 |
| E10 per classe | 10 | cwz | 0.058 | 0.101 | 0.000 | 0.000 |
| E10 per classe | 10 | radboud | 0.028 | 0.017 | 0.000 | 0.000 |
| E10 per classe | 10 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E10 per classe | 10 | utrecht | 0.053 | 0.009 | 0.000 | 0.000 |
| E10 per classe | 20 | cwz | 0.058 | 0.101 | 0.000 | 0.000 |
| E10 per classe | 20 | radboud | 0.028 | 0.017 | 0.000 | 0.000 |
| E10 per classe | 20 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E10 per classe | 20 | utrecht | 0.053 | 0.009 | 0.000 | 0.000 |
| E9 offset | 3 | cwz | 0.216 | 0.000 | 0.024 | 0.000 |
| E9 offset | 3 | radboud | 0.106 | 0.000 | 0.018 | 0.000 |
| E9 offset | 3 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E9 offset | 3 | utrecht | 0.171 | 0.000 | 0.040 | 0.000 |
| E9 offset | 5 | cwz | 0.218 | 0.000 | 0.010 | 0.000 |
| E9 offset | 5 | radboud | 0.097 | 0.000 | 0.017 | 0.000 |
| E9 offset | 5 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E9 offset | 5 | utrecht | 0.169 | 0.000 | 0.039 | 0.000 |
| E9 offset | 10 | cwz | 0.212 | 0.000 | 0.002 | 0.000 |
| E9 offset | 10 | radboud | 0.099 | 0.000 | 0.017 | 0.000 |
| E9 offset | 10 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E9 offset | 10 | utrecht | 0.166 | 0.000 | 0.033 | 0.000 |
| E9 offset | 20 | cwz | 0.212 | 0.000 | 0.000 | 0.000 |
| E9 offset | 20 | radboud | 0.101 | 0.000 | 0.018 | 0.000 |
| E9 offset | 20 | rijnstate | 0.154 | 0.000 | 0.000 | 0.000 |
| E9 offset | 20 | utrecht | 0.167 | 0.000 | 0.028 | 0.000 |

## Alla prevalenza (α = 0.05, media sui semi)

| Metodo | k | Centro | π = 0.05: rinvii / PPV / NPV | π = 0.10: rinvii / PPV / NPV | π = 0.20: rinvii / PPV / NPV | π = 0.30: rinvii / PPV / NPV | π = 0.36: rinvii / PPV / NPV |
|---|---|---|---|---|---|---|---|
| offset + per classe | 3 | cwz | 0.039 / 0.739 / 0.991 | 0.043 / 0.832 / 0.981 | 0.051 / 0.908 / 0.958 | 0.059 / 0.941 / 0.930 | 0.063 / 0.953 / 0.912 |
| offset + per classe | 3 | radboud | 0.074 / 0.615 / 0.998 | 0.071 / 0.742 / 0.995 | 0.065 / 0.849 / 0.989 | 0.059 / 0.901 / 0.982 | 0.056 / 0.920 / 0.977 |
| offset + per classe | 3 | rijnstate | 0.005 / 0.797 / 0.997 | 0.005 / 0.892 / 0.993 | 0.004 / 0.949 / 0.984 | 0.004 / 0.969 / 0.973 | 0.003 / 0.976 / 0.966 |
| offset + per classe | 3 | utrecht | 0.013 / 0.822 / 0.995 | 0.016 / 0.897 / 0.990 | 0.020 / 0.949 / 0.979 | 0.024 / 0.969 / 0.964 | 0.027 / 0.975 / 0.954 |
| offset + per classe | 5 | cwz | 0.036 / 0.788 / 0.991 | 0.041 / 0.874 / 0.981 | 0.049 / 0.935 / 0.959 | 0.058 / 0.960 / 0.932 | 0.062 / 0.968 / 0.914 |
| offset + per classe | 5 | radboud | 0.077 / 0.615 / 0.998 | 0.074 / 0.742 / 0.995 | 0.068 / 0.850 / 0.989 | 0.061 / 0.901 / 0.982 | 0.057 / 0.920 / 0.977 |
| offset + per classe | 5 | rijnstate | 0.005 / 0.793 / 0.997 | 0.004 / 0.890 / 0.993 | 0.004 / 0.948 / 0.984 | 0.003 / 0.969 / 0.973 | 0.003 / 0.976 / 0.966 |
| offset + per classe | 5 | utrecht | 0.012 / 0.837 / 0.996 | 0.014 / 0.907 / 0.991 | 0.018 / 0.954 / 0.979 | 0.023 / 0.972 / 0.965 | 0.025 / 0.978 / 0.955 |
| offset + per classe | 10 | cwz | 0.034 / 0.841 / 0.991 | 0.038 / 0.912 / 0.982 | 0.047 / 0.957 / 0.961 | 0.055 / 0.974 / 0.936 | 0.060 / 0.980 / 0.918 |
| offset + per classe | 10 | radboud | 0.077 / 0.653 / 0.998 | 0.073 / 0.761 / 0.995 | 0.067 / 0.856 / 0.990 | 0.061 / 0.904 / 0.983 | 0.057 / 0.922 / 0.978 |
| offset + per classe | 10 | rijnstate | 0.003 / 0.780 / 0.997 | 0.003 / 0.882 / 0.993 | 0.003 / 0.944 / 0.984 | 0.002 / 0.966 / 0.973 | 0.002 / 0.974 / 0.966 |
| offset + per classe | 10 | utrecht | 0.011 / 0.837 / 0.996 | 0.013 / 0.906 / 0.991 | 0.017 / 0.953 / 0.981 | 0.022 / 0.971 / 0.967 | 0.024 / 0.977 / 0.958 |
| offset + per classe | 20 | cwz | 0.028 / 0.903 / 0.992 | 0.033 / 0.950 / 0.982 | 0.042 / 0.977 / 0.962 | 0.051 / 0.986 / 0.936 | 0.057 / 0.989 / 0.919 |
| offset + per classe | 20 | radboud | 0.073 / 0.675 / 0.998 | 0.070 / 0.771 / 0.995 | 0.063 / 0.860 / 0.989 | 0.057 / 0.906 / 0.982 | 0.054 / 0.923 / 0.976 |
| offset + per classe | 20 | rijnstate | 0.002 / 0.760 / 0.997 | 0.002 / 0.870 / 0.993 | 0.002 / 0.937 / 0.984 | 0.001 / 0.963 / 0.973 | 0.001 / 0.971 / 0.966 |
| offset + per classe | 20 | utrecht | 0.011 / 0.838 / 0.996 | 0.012 / 0.907 / 0.991 | 0.016 / 0.953 / 0.981 | 0.020 / 0.971 / 0.968 | 0.023 / 0.978 / 0.959 |
| offset + per classe, negativi locali | 20 | cwz | 0.044 / 0.903 / 0.994 | 0.047 / 0.950 / 0.988 | 0.055 / 0.977 / 0.973 | 0.063 / 0.986 / 0.954 | 0.067 / 0.989 / 0.942 |
| offset + per classe, negativi locali | 20 | radboud | 0.120 / 0.744 / 0.998 | 0.117 / 0.848 / 0.997 | 0.110 / 0.922 / 0.992 | 0.103 / 0.952 / 0.987 | 0.099 / 0.962 / 0.983 |
| offset + per classe, negativi locali | 20 | rijnstate | 0.033 / 0.741 / 0.997 | 0.032 / 0.858 / 0.994 | 0.029 / 0.931 / 0.986 | 0.026 / 0.959 / 0.976 | 0.025 / 0.968 / 0.969 |
| offset + per classe, negativi locali | 20 | utrecht | 0.037 / 0.817 / 0.997 | 0.038 / 0.900 / 0.995 | 0.040 / 0.952 / 0.988 | 0.042 / 0.971 / 0.980 | 0.043 / 0.977 / 0.974 |

## Criterio

Proponibile (α = 0.05) se: 1) copertura dei positivi ≥ 0.90 su ogni centro; 2) positivi non persi ≥ sensibilità del centro visto − 0.05 su ogni centro; 3) negativi con {1} sul centro peggiore almeno 0.10 sotto E10 per classe; 4) 90° percentile dei negativi con {1} sul centro peggiore di E10 per classe non sopra E10 per classe lì; 5) rinvii di nessun centro oltre E10 per classe + 0.10.

- **offset + per classe, k = 3**: non proponibile (non superate: copertura, tumori persi); copertura peggiore 0.765 (cwz); positivi non persi meno sensibilità del centro visto, minimo -0.094 (cwz); negativi con {1} sul peggiore 0.051 (radboud) contro E10 per classe 0.366; 90° percentile su utrecht 0.023 contro 0.366; rinvii fino a -0.004 oltre E10 per classe (rijnstate).
- **offset + per classe, k = 5**: non proponibile (non superate: copertura, tumori persi); copertura peggiore 0.766 (cwz); positivi non persi meno sensibilità del centro visto, minimo -0.090 (cwz); negativi con {1} sul peggiore 0.050 (radboud) contro E10 per classe 0.366; 90° percentile su utrecht 0.021 contro 0.366; rinvii fino a -0.004 oltre E10 per classe (rijnstate).
- **offset + per classe, k = 10**: non proponibile (non superate: copertura, tumori persi); copertura peggiore 0.777 (cwz); positivi non persi meno sensibilità del centro visto, minimo -0.083 (cwz); negativi con {1} sul peggiore 0.051 (radboud) contro E10 per classe 0.366; 90° percentile su utrecht 0.017 contro 0.366; rinvii fino a -0.005 oltre E10 per classe (rijnstate).
- **offset + per classe, k = 20**: non proponibile (non superate: copertura, tumori persi); copertura peggiore 0.779 (cwz); positivi non persi meno sensibilità del centro visto, minimo -0.082 (cwz); negativi con {1} sul peggiore 0.051 (radboud) contro E10 per classe 0.366; 90° percentile su utrecht 0.016 contro 0.366; rinvii fino a -0.005 oltre E10 per classe (rijnstate).
- **offset + per classe, negativi locali, k = 20**: non proponibile (non superate: copertura); copertura peggiore 0.779 (cwz); positivi non persi meno sensibilità del centro visto, minimo -0.039 (utrecht); negativi con {1} sul peggiore 0.021 (radboud) contro E10 per classe 0.366; 90° percentile su utrecht 0.021 contro 0.366; rinvii fino a +0.017 oltre E10 per classe (rijnstate).

**Esito: nessuna combinazione proponibile.**
