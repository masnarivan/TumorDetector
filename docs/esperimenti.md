# Esperimenti

Esperimenti sugli embedding già estratti. Per ognuno il protocollo è fissato qui **prima** di
vedere i risultati; una modifica successiva al protocollo si annota con data e motivo, non si
riscrive. I risultati si aggiungono sotto il protocollo, con la versione del codice.

| # | Esperimento | Stato | Serve a decidere |
|---|---|---|---|
| E1 | Fughe di dati tra split: quasi-duplicati tra sviluppo e test | fatto: nessun duplicato | se l'AUROC 0.993 sul test è credibile |
| E2 | Probe sul centro (Robustness Index) a livello tile, regione, vetrino | fatto: centro codificato ovunque | se e quanto mitigare l'effetto centro |
| E3 | OOD con DB completo, sottoinsieme k-center e regioni | fatto: k-center basta, il punteggio no | il ridisegno del vector DB |
| E3b | Punteggio OOD indipendente dalla composizione del tessuto | protocollo scritto | come rinviare un vetrino OOD |
| E4 | Baseline con embedding normalizzati per vetrino | fatto: non adottata | se adottare la normalizzazione nel modello |
| E5 | Compressione dei vettori nel vector DB: int8 e PCA | misurato: per ora non serve | come fare spazio su Qdrant quando servirà |

Dopo E1–E3: ridisegno del vector DB, poi ricerca tra centri, probe tumore/normale sulle tile, mappe
tumorali da k-NN, verifica delle annotazioni, mappa morfologica, confronto con H-optimus-0.

## E1 — Fughe di dati: vetrini quasi uguali in split diversi

**Domanda.** Ci sono vetrini dello split di test che sono, di fatto, lo stesso tessuto di un vetrino
di sviluppo (stesso file, stesso vetrino riscansionato, sezioni consecutive dello stesso blocco)? E
tra fold diversi della cross-validation? Se sì, le metriche di test e di CV sono gonfiate.

**Dati.** Tutti i 399 vetrini CAMELYON16, Phikon `057cc0295895`, embedding su disco.

**Metodo.**

1. File identici: MD5 uguali nel manifest.
2. Tessuto quasi uguale. Da ogni vetrino si prendono 200 tile a caso (seme fisso). Embedding
   normalizzati L2, distanza euclidea, ricerca esatta. Per ogni coppia di vetrini (i, j):
   D(i, j) = mediana, sulle 200 tile di i, della distanza dalla tile più vicina di j. D(i, i) usa le
   altre tile dello stesso vetrino (esclusa la tile stessa): è la distanza tipica tra tile vicine
   dello stesso tessuto.
3. Rapporto R(i, j) = D(i, j) / D(i, i). Un vetrino diverso ha R molto sopra 1; un duplicato o una
   riscansione ha R vicino a 1 o sotto (la griglia di tile di una riscansione non è allineata, quindi
   D(i, i) è un riferimento prudente).

**Criterio** (fissato ora). Una coppia è sospetta se R(i, j) ≤ 1,0 in almeno una direzione. Le
coppie sospette si ispezionano a vista (miniature del QC) e si classificano: duplicato, stesso
blocco, falso allarme. Si riportano anche le 10 coppie con R più basso tra split diversi, sospette o
no, e la distribuzione di R.

**Conseguenze.** Duplicati tra sviluppo e test: si ricalcolano le metriche di test escludendoli e si
riportano entrambe le versioni. Duplicati tra fold: si mettono nello stesso fold, con una nuova
versione esplicita del file degli split.

**Limiti.** 200 tile per vetrino bastano per duplicati o riscansioni, non per una piccola porzione
di tessuto in comune. Il raggruppamento per paziente resta un'ipotesi del manifest (un vetrino per
paziente) che questo esperimento verifica solo in parte.

**Aggiunta al protocollo (15/10/2026, prima dell'ispezione delle coppie).** Il metodo non aveva un
controllo positivo: senza, "nessuna coppia sospetta" non distingue l'assenza di duplicati da un test
cieco. Controllo positivo: `tumor_031` rielaborato con la griglia spostata di mezza tile in x e y
(stesso tessuto, nessuna tile in comune: una riscansione ideale), `experiments/e1_control.py`.

**Risultati** (15/10/2026, codice `b17aef9` + script in `experiments/`, 252 s su MPS).

- File identici: nessuno.
- Coppie con R ≤ 1: **nessuna**, né tra sviluppo e test né tra fold. R minimo 1,08; quantili di R
  (minimo della coppia): 0,1% → 1,14, 1% → 1,19, mediana 1,95.
- Controllo positivo: la riscansione simulata di `tumor_031` ha R 0,99 e 0,95, quindi è segnalata;
  il vetrino reale più vicino a `tumor_031` ha R 1,19.
- Ispezione a vista delle due coppie più vicine tra sviluppo e test (`test_054`–`normal_080`,
  `test_036`–`normal_095`, R 1,09–1,10): tessuti diversi (numero, forma e disposizione dei
  frammenti), entrambe di Radboud con molto tessuto adiposo. Falsi allarmi.
- File: `data/reports/experiments/e1/` (riepilogo, coppie più vicine, controllo positivo).

**Conclusione.** Nessuna evidenza di duplicati o riscansioni tra split: l'AUROC sul test non è
gonfiata da questo meccanismo.

**Riserva.** Il margine è stretto: la riscansione ideale sta a 0,95–0,99, le coppie reali più
vicine a 1,08. Una riscansione vera su uno scanner diverso (colore e fuoco diversi) potrebbe cadere
in mezzo, e due sezioni consecutive dello stesso blocco non sarebbero riconosciute in modo
affidabile. Per quel caso servirebbe un confronto della forma dei frammenti di tessuto (le maschere
del QC), non degli embedding.


## E2 — Quanto il centro è leggibile negli embedding

**Domanda.** Gli embedding Phikon codificano il centro di provenienza, e quanto rispetto alla
biologia (tumore / normale)? Lo spostamento dei punteggi visto su Utrecht nel baseline (ECE 0,235,
specificità 0,70) è uno spostamento globale, correggibile normalizzando, o qualcosa di più?

**Dati.** I 399 vetrini CAMELYON16, Phikon `057cc0295895`, embedding su disco.

**Analisi.**

1. *Probe sul centro.* Regressione logistica (L2, feature standardizzate) che predice il centro, a
   tre livelli: tile (200 per vetrino, seme fisso), regione (8×8 tile, media; regioni con almeno 16
   tile), vetrino (media delle tile). Validazione a 5 fold **raggruppati per vetrino** (altrimenti il
   probe riconoscerebbe il vetrino, non il centro). Metriche: AUROC e accuratezza bilanciata; il caso
   è 0,5. A livello tile e regione si riportano anche i risultati sul solo tessuto normale, per non
   misurare differenze di composizione.
2. *Robustness Index* (definizione di de Jong et al., 2025, da verificare sull'articolo). Tile
   tumorali e normali dai vetrini con annotazione completa (fino a 100 per classe per vetrino). Per
   ogni tile, i 10 vicini più prossimi (coseno, esatto) **escludendo il suo vetrino**; RI = numero di
   vicini con stessa classe e altro centro / numero di vicini con altra classe e stesso centro.
   RI > 1: domina la biologia; RI < 1: domina il centro.
3. *Spostamento dei punteggi del baseline.* Dalle predizioni fuori fold e di test del baseline ABMIL:
   distribuzione della probabilità per centro e per classe.
4. *Normalizzazione come anteprima di mitigazione.* Si ripetono 1 e 2 sottraendo a ogni embedding
   (a) la media del suo vetrino, (b) la media del suo centro. Per la tile si riporta anche il probe
   tumore/normale (5 fold per vetrino), per vedere se la normalizzazione toglie anche segnale utile.

**Lettura dei risultati** (fissata ora). Il centro è "fortemente codificato" se il probe sul centro
a livello vetrino ha AUROC ≥ 0,9. La normalizzazione per vetrino diventa la prima mitigazione da
provare nel baseline (leave-one-centre-out) se riduce l'AUROC del centro a livello tile di almeno
0,1 e il probe tumore/normale perde meno di 0,02. La normalizzazione per centro è solo diagnostica:
in esercizio il centro di un vetrino nuovo può non avere statistiche.

**Limiti.** Due centri, un backbone. Il probe lineare misura solo informazione linearmente
leggibile.

**Risultati** (15/10/2026, codice `ff683b9` + `experiments/e2_center.py`, 183 s).

Probe sul centro, AUROC (fuori fold, 5 fold per vetrino):

| Livello | Embedding grezzi | − media del vetrino | − media del centro |
|---|---|---|---|
| Tile | 1,000 | 0,489 | 0,512 |
| Tile, solo tessuto normale | 1,000 | 0,547 | 0,695 |
| Regione | 1,000 | 0,590 | 0,323 |
| Regione, solo tessuto normale | 1,000 | 0,646 | 0,819 |
| Vetrino | 1,000 | n/d | 0,278 |
| *Probe tumore/normale, tile* | *0,992* | *0,978* | *0,992* |
| *Robustness Index (k = 10)* | *0,09* | *0,39* | *0,18* |
| *Vicini dallo stesso centro* | *100%* | *99%* | *100%* |

Valori sotto 0,5 con la media del centro sottratta sono un artefatto noto: sottrarre la media di un
gruppo e poi validare per gruppi inverte la relazione. Quella colonna è solo diagnostica.

Probabilità del baseline sui vetrini **normali** (mediana; 90° percentile):

| Valutazione | Radboud | Utrecht |
|---|---|---|
| Cross-validation | 0,017; 0,37 | 0,000; 0,002 |
| Leave-one-centre-out (centro escluso) | 0,018; 0,07 | **0,388; 0,59** |
| Test | 0,001; 0,30 | 0,013; **0,93** |

Sui vetrini tumorali di Radboud escluso, il 10° percentile scende a 0,07 (contro 0,99 in CV).

**Lettura secondo i criteri fissati.**

- Il centro è **fortemente codificato**: AUROC 1,000 a ogni livello, anche da una singola tile di
  tessuto normale.
- La normalizzazione per vetrino **soddisfa il criterio**: il probe sul centro a livello tile scende
  da 1,000 a 0,489 (caso), il probe tumore/normale perde 0,014 (< 0,02). È la prima mitigazione da
  provare nel baseline in leave-one-centre-out.

**Osservazioni non previste dal protocollo** (da trattare come ipotesi).

- Con gli embedding grezzi, i 10 vicini di una tile presi da altri vetrini sono **tutti dello stesso
  centro** (RI 0,09). Anche dopo la normalizzazione per vetrino sono dello stesso centro nel 99% dei
  casi, mentre il probe lineare non lo legge più: l'informazione sul centro che resta non è uno
  spostamento della media ma sta nella struttura locale (varianza, nitidezza, colore). La
  normalizzazione basta forse al classificatore, non alla ricerca per similarità.
- Per E3 questo significa che Utrecht non è un OOD "lieve" nello spazio degli embedding: la
  distanza dai vicini lo separerà facilmente. Il confronto tra configurazioni resta valido, ma
  serviranno anche OOD più sottili.
- Il problema del baseline è uno spostamento in blocco: con Utrecht escluso, l'intera distribuzione
  dei normali di Utrecht sale (mediana da 0,000 a 0,388). Coerente con la mancata calibrazione.


## E4 — Mitigazione: normalizzazione per vetrino nel baseline

**Domanda.** Sottrarre a ogni tile la media del suo vetrino (E2: toglie il centro al probe lineare,
costa 0,014 al probe tumore/normale) migliora la calibrazione e la specificità del baseline ABMIL su
un centro mai visto, senza perdere capacità di distinguere?

**Perché è applicabile in esercizio.** La media si calcola dal vetrino stesso: nessuna statistica
del centro, nessun dato esterno. La normalizzazione sta dentro il modello (`mil.normalize`), quindi
il modello registrato la applica da sé.

**Rischio noto.** In un vetrino quasi tutto tumorale la media è "tumore": sottrarla può ridurre il
segnale proprio nelle macrometastasi. Si guarda la sensibilità per centro.

**Disegno.** Due varianti, `none` e `slide_mean`, stesso codice, stessi split, stessi iperparametri,
tre semi (0, 1, 2) ciascuna: sei addestramenti con lo stesso protocollo del baseline (CV a 5 fold,
leave-one-centre-out, test). Nessuna variante viene registrata nel registry.

**Esiti, media sui tre semi.**

- Primario: ECE peggiore in leave-one-centre-out (il massimo tra i due centri esclusi).
- Co-primari: AUROC peggiore in leave-one-centre-out; AUROC sullo split di test.
- Secondari: specificità e sensibilità per centro escluso; specificità di Utrecht nel test; ECE e
  AUROC in CV; AUROC dell'attenzione.

**Criterio** (fissato ora). `slide_mean` è adottata se l'ECE peggiore in leave-one-centre-out scende
di almeno 0,05, l'AUROC peggiore in leave-one-centre-out non scende più di 0,02 e l'AUROC di test non
scende più di 0,01. Si riportano anche i valori di ogni seme.

**Risultati** (codice `7712fdb+dirty`, 2026-10-15: le modifiche non committate sono quelle di questo
esperimento; gli split, compresi i fold di CV, sono quelli versionati: il seme cambia solo
inizializzazione, ordine dei vetrini e tile campionate).

| Metrica | none s0 | s1 | s2 | slide_mean s0 | s1 | s2 | media none | media slide_mean | Δ |
|---|---|---|---|---|---|---|---|---|---|
| **ECE peggiore LOCO** | 0,126 | 0,190 | 0,123 | 0,130 | 0,141 | 0,222 | 0,146 | 0,164 | **+0,018** |
| ECE, Radboud escluso | 0,087 | 0,039 | 0,112 | 0,130 | 0,141 | 0,091 | 0,079 | 0,121 | +0,041 |
| ECE, Utrecht escluso | 0,126 | 0,190 | 0,123 | 0,091 | 0,070 | 0,222 | 0,146 | 0,128 | −0,019 |
| **AUROC peggiore LOCO** | 0,945 | 0,986 | 0,988 | 0,983 | 0,989 | 0,966 | 0,973 | 0,979 | **+0,006** |
| **AUROC test** | 0,995 | 0,997 | 0,995 | 0,988 | 0,987 | 0,985 | 0,996 | 0,987 | **−0,009** |
| Sensibilità, Radboud escluso | 0,901 | 0,901 | 0,986 | 0,986 | 1,000 | 0,972 | 0,930 | 0,986 | +0,056 |
| Specificità, Radboud escluso | 0,820 | 0,980 | 0,850 | 0,920 | 0,870 | 0,950 | 0,883 | 0,913 | +0,030 |
| Sensibilità, Utrecht escluso | 0,975 | 1,000 | 1,000 | 0,975 | 0,950 | 0,950 | 0,992 | 0,958 | −0,033 |
| Specificità, Utrecht escluso | 0,898 | 0,763 | 0,932 | 0,881 | 0,898 | 0,610 | 0,864 | 0,797 | −0,068 |
| Specificità Utrecht, test | 0,933 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 0,978 | 1,000 | +0,022 |
| AUROC CV | 0,987 | 0,989 | 0,993 | 0,976 | 0,975 | 0,994 | 0,989 | 0,982 | −0,008 |
| ECE CV | 0,049 | 0,040 | 0,031 | 0,047 | 0,063 | 0,034 | 0,040 | 0,048 | +0,008 |
| AUROC attenzione | 0,992 | 0,990 | 0,985 | 0,938 | 0,934 | 0,952 | 0,989 | 0,941 | −0,048 |

Tutte e sei le esecuzioni superano la batteria del gate.

**Esito: `slide_mean` non è adottata.** L'esito primario va nella direzione sbagliata (ECE peggiore in
leave-one-centre-out +0,018 invece di −0,05); i due co-primari restano nei margini (+0,006 e −0,009).

**Lettura.**

- La normalizzazione non toglie l'errore di calibrazione tra centri, lo sposta: migliora il caso
  "Radboud mai visto" (AUROC 0,973 → 0,993, sensibilità +0,056) e peggiora "Utrecht mai visto"
  (specificità −0,068, con un seme a 0,610).
- Costa localizzazione: l'AUROC dell'attenzione scende di quasi 0,05. Coerente con il rischio
  annotato: sottraendo la media, la tile tumorale si riconosce solo per differenza dal resto del
  vetrino.
- **La variabilità tra semi è grande quanto l'effetto cercato.** Con `none` l'ECE peggiore va da 0,123
  a 0,190. Lo stesso seme 0 con la stessa configurazione del baseline registrato
  (`data/reports/phikon/abmil`) dà ECE con Utrecht escluso 0,126 invece di 0,235 e specificità di
  Utrecht nel test 0,933 invece di 0,70. Il numero singolo del baseline va quindi letto con
  un'incertezza di questo ordine, e il gate deve considerarla.

**Nota del 2026-10-15: causa della differenza col baseline.** È il numero di thread della CPU. Con lo
stesso numero di thread l'addestramento si ripete identico (stessi pesi in due esecuzioni); tra 1
thread (E4) e 6 (il baseline, default della macchina) l'ordine delle somme in virgola mobile cambia e,
in 30 epoche, cambia il modello: sul leave-one-centre-out con Utrecht escluso la probabilità di un
vetrino si sposta fino a 0,512, esattamente lo scarto tra baseline e `none` s0. Non dipende dal
caricamento in memory-map. Da qui il numero di thread è un parametro (`mil.threads`, default 1) e fa
parte del risultato. Che differenze numeriche minime spostino così un vetrino è la stessa
instabilità che si vede tra semi: la riproducibilità esatta non toglie la necessità di più semi.

**Conseguenze.** (1) Il problema di calibrazione tra centri resta aperto: le strade successive sono
la ricalibrazione per centro (temperature scaling con pochi vetrini del nuovo centro) e il rinvio
OOD (E3). (2) Rendere l'addestramento deterministico, o riportare le metriche del gate come media e
intervallo su più semi, prima di usare differenze di pochi centesimi per decidere.

## E3 — OOD: quanto si perde indicizzando un sottoinsieme

**Domanda.** Un rilevatore OOD a distanza dal vicino più prossimo funziona altrettanto bene se il
riferimento contiene solo un sottoinsieme delle tile (k-center greedy) o solo regioni, invece di
tutte le tile?

**Perché il sottoinsieme può bastare.** k-center greedy garantisce un raggio di copertura r: ogni
tile scartata è entro r da una selezionata. Con una distanza metrica, d(q, sottoinsieme) è compresa
tra d(q, tutto) e d(q, tutto) + r: l'errore è limitato e conservativo (più rinvii, mai meno). Con la
calibrazione conformal la soglia si fissa con lo stesso riferimento usato in esercizio, quindi il
tasso di falsi rinvii resta quello dichiarato; quello che si può perdere è la sensibilità, ed è ciò
che questo esperimento misura.

**Dati** (CAMELYON16, Phikon `057cc0295895`, tutti insiemi di vetrini disgiunti):

| Ruolo | Vetrini | Numero |
|---|---|---|
| Riferimento (in distribuzione) | Radboud, sviluppo, fold 0–2 | 102 |
| Calibrazione della soglia | Radboud, sviluppo, fold 3–4 | 69 |
| Valutazione, in distribuzione | Radboud, test | 74 |
| Valutazione, OOD simulato | Utrecht, test | 55 |

Utrecht come OOD simula uno scanner e un laboratorio mai visti, non un organo diverso o un
artefatto: è un OOD lieve, quindi un banco severo per il confronto.

**Configurazioni del riferimento.**

1. Tutte le tile dei vetrini di riferimento.
2. k-center greedy per vetrino, N = 256 (principale); N = 64 e 1024 come analisi secondarie. Per ogni
   vetrino si registra il raggio di copertura r e quante tile rappresenta ogni tile selezionata.
3. Regioni di 8×8 tile (circa 0,9 mm), vettore = media delle tile della regione; regioni con almeno
   16 tile.
4. Secondaria: tutte le tile, ma cercate con l'indice HNSW già presente in pgvector (399 vetrini,
   filtro sui vetrini di riferimento, `ef_search` 200, scansione iterativa), cioè come funzionerebbe in
   esercizio. Confrontata con la configurazione 1 misura il costo dell'approssimazione dell'indice;
   100 tile per vetrino interrogato invece di 500, per contenere i tempi.

**Punteggio.** Embedding normalizzati L2, distanza euclidea (metrica, quindi vale la disuguaglianza
triangolare). Punteggio di una tile o regione = distanza dal vicino più prossimo nel riferimento,
ricerca esatta per le configurazioni 1–3 (nessun indice approssimato, per non confondere l'effetto
del sottoinsieme con quello dell'indice; la configurazione 4 serve proprio a misurare il secondo). Punteggio di un
vetrino = media dei punteggi delle sue tile (o regioni). Per contenere il calcolo, da ogni vetrino
interrogato si prendono 500 tile a caso con seme fisso (tutte le regioni).

**Metriche.**

- Primaria: AUROC a livello di vetrino, Radboud test (negativi) contro Utrecht test (positivi).
- Soglia conformal con α = 0,05 sui vetrini di calibrazione: tasso di falsi rinvii sui vetrini
  Radboud test (atteso intorno a 0,05) e tasso di rilevamento sui vetrini Utrecht test.
- Secondarie: AUROC a livello di tile; distribuzione del raggio di copertura r; tempo e memoria.

**Criterio di decisione** (fissato ora). Il sottoinsieme con N = 256 è adottato se la sua AUROC
primaria è almeno quella del riferimento completo meno 0,02, e il tasso di falsi rinvii resta entro
0,05 ± 0,03. Altrimenti si prova N = 1024; se non basta, l'OOD sulle tile usa un indice completo
quantizzato. Le regioni sono adottate per l'OOD se rispettano lo stesso margine.

**Limiti.** Due soli centri; un solo backbone; l'OOD simulato è uno spostamento di dominio, non un
caso clinicamente diverso. Da ripetere con CAMELYON17 e con OOD veri (altri organi, artefatti).

**Aggiunta al protocollo (15/10/2026, dopo una prova di 35 interrogazioni della configurazione 4,
prima di ogni risultato).** La prova: con l'indice HNSW sui 399 vetrini filtrato ai 102 di
riferimento, 9 tile su 10 di un vetrino Utrecht (`test_001`) non ricevono **nessun** vicino: i loro
vicini più prossimi sono tutti in vetrini esclusi dal filtro e la scansione iterativa si ferma a
`hnsw.max_scan_tuples` (20 000, il default). Ogni interrogazione richiede 0,7–2,7 s. Quindi:

- Configurazione 4, regola fissata ora: una tile senza vicino ha punteggio +∞ (rinvio: è ciò che
  farebbe in esercizio un sistema che non trova riferimenti). Si riporta la frazione di tile senza
  vicino per ruolo; le interrogazioni girano su 8 connessioni parallele.
- Nuova configurazione 4b: indice HNSW costruito **solo** sulle tile dei 102 vetrini di riferimento
  (tabella temporanea, stessi parametri dell'indice esistente: m 16, ef_construction 64; ef_search
  200; nessun filtro), cioè il ridisegno candidato. Stesse 100 tile per vetrino interrogato.
  Confrontata con la configurazione 1 sulle stesse tile; si riportano anche tempo di costruzione e
  dimensione dell'indice.
- Per le configurazioni 4 e 4b si riporta anche il recall: frazione di tile per cui l'indice trova
  un vicino alla stessa distanza del vicino esatto (scarto ≤ 0,001).
- Dettagli non fissati prima e fissati ora: il k-center parte da una tile a caso (seme fisso) e
  N = 64, 256, 1024 sono prefissi della stessa sequenza greedy; il vettore di una regione è la media
  delle sue tile, poi normalizzata L2; soglia conformal = il ⌈(n+1)(1−α)⌉-esimo punteggio di
  calibrazione (n = 69: il 67°), rinvio se il punteggio la supera; per le differenze di AUROC dalla
  configurazione 1 si riporta un intervallo bootstrap al 95% (2000 ricampionamenti dei vetrini,
  stratificati per classe).

**Risultati** (15/10/2026, codice `32e9a7c` + `experiments/e3_ood.py`; ricerca esatta su MPS in
circa 5 minuti compreso il k-center; file in `data/reports/experiments/e3/`).

| Configurazione | Vettori | MB (float16) | AUROC vetrino | AUROC tile | Falsi rinvii Radboud test | Rilevamento Utrecht |
|---|---|---|---|---|---|---|
| 1. Tutte le tile | 925 283 | 1355 | 1,000 | 0,998 | 0,135 (10/74) | 1,00 |
| 2. k-center N = 64 | 6 528 | 10 | 1,000 | 0,997 | 0,162 | 1,00 |
| **2. k-center N = 256** | **26 112** | **38** | **1,000** | **0,998** | **0,149 (11/74)** | **1,00** |
| 2. k-center N = 1024 | 103 373 | 151 | 1,000 | 0,999 | 0,149 | 1,00 |
| 3. Regioni 8×8 | 18 065 | 26 | 1,000 | 1,000 | 0,162 | 1,00 |

Su 100 tile per vetrino (configurazioni 4 e 4b, confrontate con la ricerca esatta sulle stesse
tile: AUROC 1,000, falsi rinvii 0,135):

| | 4. HNSW su 399 vetrini, filtro sul riferimento | 4b. HNSW sul solo riferimento |
|---|---|---|
| Tile senza alcun vicino | calibrazione e Radboud 0%, **Utrecht 93%** | 0% |
| Recall del vicino esatto | 0,95 sulle tile con risposta (0,71 su tutte) | 0,98 |
| Secondi per interrogazione (mediana) | Radboud 0,08–0,17; **Utrecht 2,1** | 0,03 |
| AUROC; falsi rinvii; rilevamento | 1,000; 0,135; 1,00 (per la regola +∞) | 1,000; 0,135; 1,00 |
| Indice | 8,1 GB (esistente) | 1,8 GB, costruito in 142 s |

- Il limite del k-center è rispettato su tutte le 98 741 tile interrogate (nessuna violazione; la
  distanza dal sottoinsieme supera quella da tutte le tile in mediana di 0,10, 0,07, 0,04 per N 64,
  256, 1024). Il raggio di copertura è però grande (N 256: mediana 0,67, contro 0,43 di distanza
  tipica dal vicino): la garanzia teorica è troppo larga per essere utile, conta la misura.
- Le differenze di AUROC dalla configurazione 1 sono tutte nulle o quasi (k-center 64: −0,0002,
  IC 95% −0,0015…0): l'AUROC è al tetto, come previsto da E2.

**Lettura secondo il criterio fissato.** Margine di AUROC: rispettato da tutte le configurazioni.
Falsi rinvii entro 0,05 ± 0,03: **non rispettato da nessuna, compreso il riferimento completo**. Alla
lettera il sottoinsieme N = 256 non è adottato, e nemmeno N = 1024. Il ripiego previsto (indice
completo quantizzato) non risolverebbe: il riferimento completo fallisce allo stesso modo.

**Analisi non previste dal protocollo** (ipotesi, da confermare).

- 8 dei 10 falsi rinvii (riferimento completo) sono vetrini tumorali: falsi rinvii 0,04 sui 50
  normali (2/50, in tutte le configurazioni), 0,33 sui 24 tumorali. Le tile tumorali distano dal
  riferimento quanto in calibrazione (mediana 0,64 contro 0,64): non sono più "nuove" nel test, ma
  il punteggio medio cresce con la quantità di tumore. Se calibrazione e test fossero scambiabili,
  10 o più rinvii su 74 avrebbero probabilità 0,02.
- Nei vetrini rinviati senza tumore campionato le mappe delle distanze mostrano lontano il tessuto
  non linfoide (grasso, connettivo, capsula, vasi); vicino il parenchima linfoide. Dettaglio e
  ipotesi in E3b.
- Il vendor registrato (`philips`) e la risoluzione (0,243 µm/px) sono identici per tutti i vetrini
  Radboud: nessuna differenza di scanner tra sviluppo e test.

**Conclusioni.**

1. **Per il vector DB:** il riferimento per l'OOD non deve essere filtrato da un indice comune.
   Con il filtro, proprio le tile OOD restano senza risposta e sono le più lente: la ricerca filtrata
   fallisce nel caso per cui esiste. Un indice dedicato al riferimento è piccolo, veloce e quasi
   esatto. Il sottoinsieme k-center N = 256 è equivalente al riferimento completo su ogni misura di
   questo esperimento con 35 volte meno vettori (38 MB: entra in memoria, non serve un indice
   approssimato). Questo non è l'esito del criterio, che fallisce per un'altra causa: è la base
   proposta per il ridisegno, da confermare con il punteggio di E3b.
2. **Per il rinvio OOD:** la media delle distanze misura la composizione del tessuto (tumore, grasso)
   insieme al dominio; i falsi rinvii vanno contro i casi con molto tumore. Il punteggio va rifatto
   (E3b) prima di usarlo.
3. L'indice HNSW da 14 GB sui 399 vetrini resta utile solo per la ricerca di casi simili, non per
   l'OOD.


## E3b — Un punteggio OOD che non misuri la composizione del tessuto

**Perché.** In E3, con il punteggio "media delle distanze dal vicino", 10 vetrini Radboud di test su
74 superano la soglia (atteso circa 5%), anche con il riferimento completo. Due meccanismi, visti
dopo i risultati di E3 (quindi ipotesi che guidano questo protocollo, non conclusioni):

1. Le tile tumorali sono lontane dal riferimento sempre, in calibrazione come in test (mediana
   0,64 contro 0,43 delle tile normali): il tumore è raro nel riferimento e diverso da paziente a
   paziente. Un vetrino con molto tumore supera la soglia per la quantità di tumore (`test_021`, 87%
   di tile tumorali).
2. Nei vetrini rinviati senza tumore campionato, le mappe delle distanze (miniature del QC, 64×)
   mostrano il parenchima linfoide vicino al riferimento e lontani grasso perilinfonodale,
   connettivo lasso, capsula e vasi. Sono rinviati i vetrini con molto tessuto non linfoide
   (`test_108`, `test_119`, `test_081`). Nessun artefatto tecnico evidente a questa risoluzione
   (pieghe, penna, sfocatura). Eccezione: in `test_011` (linfonodi quasi sostituiti da grasso) è
   lontano anche il bordo linfoide: è il caso più vicino a un OOD vero.

In entrambi i casi il punteggio misura **di che tessuto è fatto il vetrino**, non se viene da un
dominio diverso. Un rilevatore OOD che rinvia le macrometastasi è clinicamente sbagliato.

**Domanda.** Esiste un punteggio che rinvia i vetrini di un centro mai visto ma è indipendente dalla
quantità di tumore e di tessuto non linfoide?

**Dati e ruoli.** Gli stessi di E3 (riferimento 102, calibrazione 69, valutazione 74 + 55), le
stesse 500 tile per vetrino interrogato. **Riserva:** i vetrini di valutazione sono già stati visti
in E3, e i candidati sono scelti conoscendo i due meccanismi sopra. Il risultato di E3b basta per
scegliere il punteggio da sviluppare, non per adottarlo in esercizio: serve una conferma su vetrini
mai usati (CAMELYON17) con il protocollo che risulterà da qui.

**Candidati** (fissati ora; tile score d = distanza euclidea dal vicino più prossimo, embedding L2):

- S0, media di d sulle tile (E3, confronto).
- S1, mediana di d.
- S2, 25° percentile di d: "quanto è familiare il quarto più familiare del vetrino". Un cambio di
  dominio sposta tutto il vetrino; tumore e grasso ne occupano di solito una parte.
- S3, distanza relativa alla densità locale: per ogni tile, d(q, v) / ρ(v), dove v è il vicino più
  prossimo nel riferimento e ρ(v) è la distanza di v dal suo vicino più prossimo in **altri** vetrini
  del riferimento. Il tessuto che è disperso anche nel riferimento (tumore, grasso) ha ρ grande, quindi
  conta meno. Vetrino = media sulle tile.

Ogni candidato si calcola con due riferimenti: k-center 256 per vetrino (il ridisegno proposto da
E3; ρ calcolata dentro il sottoinsieme) e, come confronto, tutte le tile. Soglia conformal come in
E3 (α 0,05, il 67° punteggio di calibrazione su 69, rinvio se maggiore).

**Esiti.**

- Falsi rinvii sui 74 vetrini Radboud di test: complessivi, sui 50 normali e sui 24 tumorali.
- Rilevamento dei 55 vetrini Utrecht di test e AUROC a livello di vetrino.
- Dipendenza dalla composizione, sui vetrini Radboud di test: correlazione di Spearman tra il
  punteggio e la frazione di tile tumorali (vetrini tumorali), e tra il punteggio e la frazione di
  tile con poco tessuto (`tissue_frac` < 0,8, approssimazione del tessuto lasso e del grasso).

**Criterio** (fissato ora, sul riferimento k-center 256). Un candidato è accettabile se:
falsi rinvii complessivi tra 0,02 e 0,08; falsi rinvii sui vetrini tumorali al massimo 2 su 24;
rilevamento di Utrecht almeno 0,95; AUROC almeno 0,98. Se più candidati sono accettabili si sceglie
il primo nell'ordine S1, S2, S3 (dal più semplice). Se nessuno lo è, il rinvio OOD a livello di
vetrino con un punteggio unico non viene adottato e il passo successivo è un rinvio per regione (le
regioni lontane si mostrano al patologo, il vetrino non viene rinviato in blocco).

**Limiti.** Utrecht è un OOD facile (E2): il rilevamento sarà alto per tutti; il protocollo misura
soprattutto i falsi rinvii. Il quarto più familiare (S2) può nascondere un problema locale
(artefatto su una parte del vetrino): quello resta compito del QC (GrandQC), non dell'OOD.

**Risultati.** —

## E5 — Compressione dei vettori nel vector DB

Misura esplorativa del 16/10/2026, fatta dopo il caricamento su Qdrant (commit 589d77f) e senza un
protocollo fissato prima: serve a orientare una decisione futura, non a validarla.
Codice: `experiments/e5_compression.py`.

**Domanda.** Se il cluster Qdrant si riempie, quanto si perde rimpicciolendo i vettori?

**Stato del cluster al 16/10/2026** (piano gratuito: 3,9 GB di disco, 1,1 GB di RAM). Con 404
vetrini (399 CAMELYON16 + 5 CAMELYON17), 185k punti: ~285 MB di vettori (float16, su disco),
~71 MB di payload, qualche decina di MB di grafo HNSW (in RAM). In tutto ~0,4 GB di disco, ~120 MB
di RAM residente. Circa 0,9 MB per vetrino: c'è posto per altri ~3.500 vetrini (tutto CAMELYON17
porta il totale a ~0,85 GB).

**Misura.** I 102k prototipi k-center (256 per vetrino) dei 399 vetrini CAMELYON16, Phikon; 1.000
tile di query (10 da un vetrino ogni 4), cercate tra i prototipi degli altri vetrini. Riferimento:
ricerca esatta a 768 dimensioni. La PCA è stimata su 50k prototipi normalizzati, con distanza
euclidea (centrare cambia il coseno, non la distanza euclidea). int8: quantizzazione per dimensione
su 256 livelli, come quella scalare di Qdrant.

| Formato | Byte per vettore | Varianza tenuta | Recall@10 | Top-1 | Spearman distanza dal più vicino |
|---|---|---|---|---|---|
| float16, 768 (attuale) | 1536 | 1 | 1,000 | 1,000 | 1,000 |
| int8, 768 | 768 | — | 0,993 | 0,995 | 1,000 |
| PCA 384, float16 | 768 | 0,966 | 0,953 | 0,936 | 0,998 |
| PCA 384, int8 | 384 | 0,966 | 0,952 | 0,932 | 0,998 |
| PCA 256, float16 | 512 | 0,932 | 0,912 | 0,875 | 0,992 |
| PCA 128, float16 | 256 | 0,857 | 0,821 | 0,756 | 0,963 |
| PCA 64, float16 | 128 | 0,761 | 0,690 | 0,572 | 0,882 |

La distanza dal più vicino è quella del punteggio OOD (E3).

**Conclusioni (consiglio per dopo).**

1. Per ora non serve comprimere: il cluster è pieno al ~10%.
2. Quando servirà spazio, prima alleggerire il payload (~20% dello spazio): per esempio l'hash
   degli embedding ripetuto su ogni punto può stare solo in `data/index/<backbone>.json`. Non costa
   nulla in qualità.
3. Poi int8: metà dello spazio, vicini e distanze praticamente identici. La quantizzazione scalare
   di Qdrant (`quantization_config`, int8 in RAM con rescoring sugli originali) risparmia RAM ma
   non disco, perché tiene gli originali. Per risparmiare disco i vettori vanno salvati già in int8
   da noi.
4. La PCA è sconsigliata: a parità di byte con int8 (PCA 384 float16) perde il 5% dei vicini, e a
   256 o meno peggio. Inoltre è stimata su CAMELYON16: rischia di scartare proprio le direzioni
   che distinguono un centro o un tessuto nuovo, cioè quello che il punteggio OOD deve vedere.
   Se mai la si usasse, andrebbe rivalidata sul rilevamento OOD (E3/E3b), non solo sul recall.
5. Un'altra leva, da misurare con E3: meno prototipi per vetrino (128 invece di 256).
