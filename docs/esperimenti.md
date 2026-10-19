# Esperimenti

Esperimenti sugli embedding già estratti. Per ognuno il protocollo è fissato qui **prima** di
vedere i risultati; una modifica successiva al protocollo si annota con data e motivo, non si
riscrive. I risultati si aggiungono sotto il protocollo, con la versione del codice.

| # | Esperimento | Stato | Serve a decidere |
|---|---|---|---|
| E1 | Fughe di dati tra split: quasi-duplicati tra sviluppo e test | fatto: nessun duplicato | se l'AUROC 0.993 sul test è credibile |
| E2 | Probe sul centro (Robustness Index) a livello tile, regione, vetrino | fatto: centro codificato ovunque | se e quanto mitigare l'effetto centro |
| E3 | OOD con DB completo, sottoinsieme k-center e regioni | fatto: k-center basta, il punteggio no | il ridisegno del vector DB |
| E3b | Punteggio OOD indipendente dalla composizione del tessuto | fatto: nessun candidato accettabile | come rinviare un vetrino OOD |
| E4 | Baseline con embedding normalizzati per vetrino | fatto: non adottata | se adottare la normalizzazione nel modello |
| E5 | Compressione dei vettori nel vector DB: int8 e PCA | misurato: per ora non serve | come fare spazio su Qdrant quando servirà |
| C17 | Controlli su CAMELYON17: annotazioni, metadati, sovrapposizione con CAMELYON16 | fatto | se le etichette e gli split di CAMELYON17 sono usabili |
| E6 | Baseline su 4 centri (CAMELYON16 + 17), nessuna mitigazione, temperatura globale | fatto: gate non superato, i normali di un centro nuovo salgono | se più centri bastano; riferimento per le mitigazioni (E7) |
| E7 | Mitigazioni del centro nella testa: bilanciamento per dominio, group DRO, mescolanza delle statistiche | fatto: nessuna adottata, l'errore si sposta tra centri | quale ricetta di training adottare per le teste |
| E8 | Discriminatore avversariale del dominio nella testa (DANN), su tutti i vetrini o solo sui negativi | fatto: nessuna adottata; corregge Utrecht, rompe CWZ | se l'invarianza della rappresentazione corregge i negativi di uno scanner nuovo |

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

**Risultati** (16/10/2026, `experiments/e3b_ood_score.py`, report in `data/reports/experiments/e3b/`).
Eseguito come da protocollo. Il k-center è quello del vector DB (`vectordb/reduce.py`: primo
prototipo la tile più vicina alla media del vetrino), non quello con seme casuale di E3; con S0 i
falsi rinvii sono gli stessi di E3 (11 su 74 con k-center 256, 10 con il riferimento completo).
L'analisi a posteriori è in `experiments/e3b_posthoc.py`.

Riferimento k-center 256 (quello del criterio); 74 vetrini Radboud di test, 50 normali e 24 tumorali:

| | Falsi rinvii | Normali | Tumorali | Utrecht rilevati | AUROC | Spearman frazione tumore | Spearman poco tessuto |
|---|---|---|---|---|---|---|---|
| S0 media | 0,149 | 2 | 9 | 1,00 | 1,000 | 0,13 | 0,06 |
| S1 mediana | 0,162 | 2 | 10 | 1,00 | 1,000 | 0,11 | 0,09 |
| S2 25° percentile | 0,162 | 3 | 9 | 1,00 | 1,000 | 0,11 | 0,12 |
| S3 relativa a ρ | 0,189 | 3 | 11 | 1,00 | 1,000 | −0,42 | −0,10 |

Riferimento completo (confronto): falsi rinvii S0 0,135, S1 0,149, S2 0,108, S3 0,230; tumorali
rinviati 8, 9, 6, 13.

**Esito del criterio: nessun candidato è accettabile** (tutti oltre 0,08 di falsi rinvii e oltre 2
vetrini tumorali). Come stabilito, il rinvio OOD a livello di vetrino con un punteggio unico non
viene adottato; il passo successivo è il rinvio per regione.

**Analisi a posteriori** (non nel protocollo, quindi solo ipotesi). I falsi rinvii sono quasi tutti
vetrini tumorali (9 su 24 contro 2 su 50 normali, quanto atteso con α 0,05), eppure il punteggio non
segue la quantità di tumore (Spearman 0,1). Ricalcolando S0 sulle sole tile normali dei vetrini,
con la stessa soglia:

- 5 dei 9 vetrini tumorali restano rinviati: 4 non hanno nessuna tile tumorale tra le 500
  campionate (`test_011`, `test_013`, `test_074`, `test_117`), uno ne ha 17 (`test_051`). Solo
  `test_021` e `test_090` (435 e 220 tile tumorali) sono rinviati per il tumore. Il meccanismo 1 di
  E3 spiega 2 vetrini su 9, non la maggioranza;
- lo spostamento riguarda i vetrini tumorali del **test ufficiale**, non quelli del training: in
  calibrazione (folds 3–4 di Radboud) la mediana di S0 è 0,522 nei tumorali e 0,521 nei normali, e
  sopra soglia ci sono 2 tumorali su 29; nel test Radboud la mediana è 0,572 nei tumorali (0,544
  sulle sole tile normali) e 0,514 nei normali.

Ipotesi: nel test ufficiale di CAMELYON16 i vetrini tumorali di Radboud differiscono da quelli del
training in tutto il tessuto, non solo nel tumore (lotto di preparazione o di scansione diverso, o
linfonodi metastatici con un aspetto diverso anche fuori dalla metastasi). Se è un lotto diverso,
quei rinvii sono almeno in parte cambi di dominio veri, e non falsi rinvii. I dati qui non bastano
per distinguere le due ipotesi.

**Verifica dei metadati** (16/10/2026, a posteriori, `experiments/e3b_scan_metadata.py`, report in
`data/reports/experiments/e3b/scan_metadata.*`). Lette per HTTP le intestazioni dei .tif di CAMELYON16
(398 su 399; `normal_144` non ha l'XML Philips). Le date di scansione non ci sono. Scanner, versione
del software e conversione in TIFF sono identici per tutti i vetrini di un centro. C'è invece il nome
del file d'origine, che per Radboud è il numero di caso di anatomia patologica `T<aa>-<numero>`: da
lì l'anno del caso (accettazione, non necessariamente scansione).

| Radboud | Anni dei casi, vetrini tumorali | 2015 |
|---|---|---|
| Riferimento E3 (folds 0–2) | 2006–2014 | 0 su 42 |
| Calibrazione (folds 3–4) | 2007–2015 | 2 su 29 |
| Test ufficiale | 2008–2015 | **12 su 24** |

Nel test, i tumorali del 2015 rinviati sono 8 su 12, quelli degli altri anni 1 su 12. Nei normali
del 2015 (6 nel riferimento, 6 nel test) solo 1 su 6 è rinviato. Il punteggio cresce con l'anno nei
tumorali del test (Spearman 0,72), non in calibrazione (−0,11).

Quindi i "falsi rinvii" tumorali di E3/E3b sono quasi tutti **vetrini metastatici del 2015**, un
gruppo che il riferimento non contiene affatto. È un cambio di dominio vero dentro Radboud (un lotto
diverso di preparazione, colorazione o scansione dei casi metastatici del 2015) più che un difetto del
punteggio. I dati non dicono perché riguardi i tumorali e non i normali dello stesso anno.

**Un paziente in due split.** Il caso Utrecht `T13-15766` ha due vetrini: `tumor_091` (training) e
`test_116` (test ufficiale). E1 non lo aveva trovato perché sono vetrini diversi, non quasi-duplicati.
È l'unico caso ripetuto tra i 398 letti.

**Conclusioni.**

1. Nessuna statistica del vetrino (media, mediana, percentile, densità locale) toglie i rinvii in
   eccesso: il problema non è come si riassumono le distanze delle tile.
2. S3 (densità locale) peggiora: corregge troppo e penalizza i vetrini con poco tumore.
3. Prossimo passo, come da protocollo: il rinvio per regione. Le regioni lontane vengono mostrate al
   patologo; il vetrino non viene rinviato in blocco.
4. Da verificare su CAMELYON17, con il punteggio e la soglia fissati prima: se anche lì i vetrini
   tumorali risultano spostati rispetto ai normali dello stesso centro.
5. Il riferimento OOD deve coprire gli anni (o i lotti) dei casi, non solo i centri: un riferimento
   senza i casi metastatici di un anno li rinvia. Per CAMELYON17 l'anno va letto dalle intestazioni
   prima di scegliere riferimento e calibrazione.
6. `test_116` condivide il paziente con `tumor_091`: va tolto dalle metriche sul test (o il paziente
   unificato nel manifest), e il numero di caso va usato come `patient_pseudo_id` dove c'è.


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

## C17 — Controlli su CAMELYON17 prima dell'uso

Controlli del 18/10/2026, dopo l'estrazione dei 500 vetrini etichettati (Phikon; tutti passano il QC).
Codice: `experiments/c17_checks.py`; report in `data/reports/experiments/c17_checks/`. I vetrini sono
letti da remoto per intervalli HTTP, senza scaricarli.

**1. Annotazioni contro griglia di tile** (50 vetrini con XML: 17 macro, 17 micro, 16 ITC). I nomi dei
gruppi sono quelli già gestiti (`Tumor`, un `Exclusion`). Le immagini sovrapposte dei 5 casi dubbi
(`overlays/`) mostrano **annotazioni allineate** in tutti i centri, LPON (Philips) compreso: il contorno
cade sempre su gruppi di cellule tumorali.

- `patient_089_node_3` (LPON, micro, nessuna tile tumorale): annotazione corretta, ma minuscola,
  0,02 mm² in 7 frammenti, il più grande 0,006 mm² (~80 µm), lungo il seno sottocapsulare. Una tile
  è 0,0125 mm² e diventa "tumore" solo oltre metà della superficie: dà 9 tile `boundary`, nessuna
  `tumor`. Lo stesso per `patient_046_node_4` (Utrecht, micro, 78 frammenti, il più grande
  0,009 mm²). Per area annotata sono vicini a un'ITC.
- In 15 vetrini su 50 non c'è nessuna tile `tumor` (13 ITC su 16, 2 micro su 17): con l'etichetta a
  metà tile le ITC sono quasi invisibili a livello di tile.
- **Tumore fuori dalla griglia.** In 6 vetrini meno del 90% del tumore annotato cade in una tile:
  `patient_068_node_1` 0%, `patient_064_node_0` 31%, `patient_067_node_4` 31%, `patient_060_node_3`
  58% (Rijnstate), `patient_089_node_3` 69%, `patient_021_node_3` 74%. Le immagini mostrano cellule
  tumorali nella capsula, nel seno sottocapsulare al bordo del tessuto e nel grasso perilinfonodale:
  zone con meno del 50% di tessuto per tile (`tiling.min_tissue`), dove la griglia non arriva. Non è
  un errore delle annotazioni ma un **punto cieco della pipeline**: proprio dove le metastasi
  iniziano (seno sottocapsulare) e dove stanno le ITC nel grasso.

**2. Metadati di scansione.** I .tif di Radboud, CWZ, Utrecht e Rijnstate in CAMELYON17 sono TIFF
convertiti senza metadati (nessuna descrizione, nessuna data): l'anno dei casi non si può leggere.
Gli LPON sono TIFF Philips nativi, con data e scanner:

- acquisiti tra il 4/4/2016 e il 16/9/2016, su **5 scanner Philips diversi** (numeri di serie FMT0061,
  FMT0063, FMT0106, FMT0107, FMT0113) e 3 versioni del software;
- i 5 linfonodi di un paziente sono scansionati a distanza mediana di 107 giorni (massimo 155);
- nessuna differenza di data tra diagnosi (mediane tutte in giugno 2016).

**3. Sovrapposizione con CAMELYON16.** La misura di E1 (rapporto R tra distanza dal vetrino j e
distanza da sé, 200 tile per vetrino) su tutte le coppie dei 899 vetrini.

| Coppie | R minimo | 1° percentile | Mediana |
|---|---|---|---|
| CAMELYON16 tra loro (E1) | 1,08 | 1,19 | 1,95 |
| CAMELYON16 – CAMELYON17 | 1,18 | 1,66 | 2,44 |
| CAMELYON17, stesso paziente | 1,08 | 1,20 | 1,67 |
| CAMELYON17, pazienti diversi | 1,08 | 1,30 | 2,45 |

Nessuna coppia con R ≤ 1: **nessun vetrino ripetuto o quasi uguale** tra i due dataset.
**Limite:** questa misura non vede lo stesso paziente con un altro tessuto. Il controllo positivo lo
mostra: `tumor_091` e `test_116`, stesso paziente in CAMELYON16 (E3b), hanno R 2,37, al posto 51.568
su 79.401 coppie. Dentro CAMELYON17 i linfonodi dello stesso paziente sono più vicini degli altri
(mediana 1,67 contro 2,45), probabilmente perché preparati insieme; fra due dataset preparati in
anni diversi non c'è da aspettarselo. La sovrapposizione di pazienti tra CAMELYON16 e 17 (stessi
centri Radboud e Utrecht) resta **non verificabile** con i dati pubblici.

**4. Un'anomalia in CAMELYON16.** Le coppie CAMELYON16–17 più vicine hanno tutte `normal_144`
(Radboud), vicino a vetrini Rijnstate (R 1,18–1,29). È l'unico dei 399 file CAMELYON16 non in
formato Philips: è un TIFF convertito come quelli di CAMELYON17 (stesse dimensioni, 94.968 ×
210.579 pixel, di 203 vetrini CAMELYON17 di CWZ, Radboud e Rijnstate). Non coincide con nessun file
CAMELYON17 (md5 diverso). Probabilmente è una riscansione o riconversione successiva: un vetrino
con un "dominio" diverso dagli altri 243 di Radboud.

**Conseguenze.**

1. Le etichette CAMELYON17 sono usabili: le annotazioni sono allineate in tutti i centri.
2. La regola delle ITC (etichetta vuota, esclusi dal binario) è coerente con quello che si vede: a
   livello di tile sono quasi invisibili.
3. Il filtro sul tessuto taglia capsula, seno sottocapsulare al bordo e grasso perilinfonodale. Va
   misurato quanto conta (tumore annotato perso per centro) e provata una soglia più bassa o una
   griglia sul bordo, con QC sugli artefatti. Riguarda anche CAMELYON16.
4. Split di CAMELYON17 per paziente (5 linfonodi per paziente, più simili tra loro). L'anno dei casi
   non è disponibile, quindi il riferimento OOD non può essere bilanciato per anno come suggerito da
   E3b, tranne che per LPON (data di scansione).
5. LPON ha 5 scanner diversi: un sottogruppo naturale per verificare la robustezza allo scanner.
6. `normal_144` va segnato nel manifest come vetrino con conversione diversa.

## E6 — Più centri, nessuna mitigazione

Protocollo fissato il 18/10/2026, prima di ogni addestramento sul cohort. Progetto in
[training-multicentro.md](training-multicentro.md).

**Domanda.** Addestrato su quattro centri (sei domini) invece di due, senza alcuna mitigazione e con
una sola temperatura globale, l'ABMIL regge su un centro mai visto? Di quanto migliora, sul centro
comune, rispetto al training su CAMELYON16? È il riferimento contro cui E7 giudica le mitigazioni.

**Dati.** Cohort `ln_metastasis` v1 (`data/manifests/heads/ln_metastasis.csv`): 771 vetrini di
sviluppo, CAMELYON16 (train e test ufficiale) e CAMELYON17 di Radboud, Utrecht, CWZ e Rijnstate; ITC
escluse. **I 92 vetrini LPON non vengono letti** (test esterno bloccato). Phikon `057cc0295895`.

**Modello.** ABMIL come il baseline, con gli iperparametri di `conf/config.yaml` (`mil`: hidden 256,
dropout 0,25, lr 2e-4, weight decay 1e-4, 30 epoche, 4096 tile per passo, nessuna normalizzazione),
`pos_weight` globale, nessuna mitigazione. Tre semi (0, 1, 2), un thread.

**Protocollo** (`td task=train_head head=ln_metastasis`).

1. Cross-validation sui 5 fold del cohort (raggruppati per paziente, stratificati per etichetta ×
   dominio).
2. Temperatura globale *T*: minimizza la log-verosimiglianza negativa delle logit fuori fold della
   CV, *T* in [0,05; 20]. Probabilità calibrata = sigmoide(logit / *T*). La soglia 0,5 non cambia
   con *T*: sensibilità e specificità sono le stesse prima e dopo.
3. Leave-one-centre-out sui 4 centri (un centro escluso per intero, entrambi i dataset). Per ogni
   rotazione la temperatura si stima **solo con i centri di training**: 3 fold interni
   (`cv_fold mod 3`), le loro logit fuori fold, la stessa procedura del punto 2. Il centro escluso non
   contribuisce mai alla sua temperatura.
4. Modello finale su tutto lo sviluppo, con la temperatura del punto 2.
5. Robustezza al centro, sul modello finale:
   - probe sul centro: regressione logistica multinomiale (feature standardizzate) dalla
     rappresentazione pooled *z* della testa al centro; 5 fold raggruppati per paziente e
     stratificati per centro; AUROC macro one-vs-rest fuori fold. **Primario sui soli vetrini
     negativi** (togli la differenza di composizione, come in E2); secondario su tutti;
   - Robustness Index sulle rappresentazioni *h* delle tile (dopo il primo strato della testa): fino
     a 100 tile tumorali e 100 normali per vetrino, dai vetrini negativi e da quelli con annotazione
     completa; 10 vicini per coseno da altri vetrini; RI = vicini con stessa classe e altro centro /
     vicini con altra classe e stesso centro (definizione di E2).

**Esiti** (media sui tre semi, valori di ogni seme nel report).

- La batteria del gate della testa (`conf/head/ln_metastasis.yaml`): AUROC in CV ≥ 0,90; AUROC
  peggiore in leave-one-centre-out ≥ 0,85; ECE calibrata in CV ≤ 0,10; **ECE calibrata peggiore in
  leave-one-centre-out ≤ 0,10**; specificità peggiore in leave-one-centre-out ≥ 0,80; AUROC del probe
  sul centro (negativi) ≤ 0,80; Robustness Index ≥ 0,5.
- Effetto della temperatura: ECE peggiore in leave-one-centre-out grezza e calibrata.
- Confronto con CAMELYON16 sul centro comune: ECE e specificità con Utrecht escluso, calcolate sui
  soli vetrini Utrecht di CAMELYON16, contro E4 `none` (stesso codice di training, tre semi, un
  thread: ECE 0,146, specificità 0,864). Il baseline registrato non si usa (sei thread, E4).
- Secondari: metriche per centro e per dominio in CV, AUROC dell'attenzione, temperature stimate.

**Lettura** (fissata ora).

- E6 è il riferimento di E7 qualunque sia l'esito.
- "Più centri aiutano" se, sui vetrini Utrecht di CAMELYON16 con Utrecht escluso, l'ECE calibrata
  scende di almeno 0,05 sotto 0,146 e la specificità non scende sotto 0,864 − 0,02.
- Se E6 supera tutta la batteria, E7 si fa comunque, ma una mitigazione si adotta solo se migliora
  il probe o il Robustness Index senza peggiorare le voci del gate oltre i margini che E7 fisserà.
- Riferimenti per leggere la robustezza: sugli embedding grezzi Phikon probe 1,000 e RI 0,09 (E2).
  Un probe sopra 0,80 in E6 è atteso e non invalida le altre misure.

**Limiti.** Il test ufficiale di CAMELYON16 sta nello sviluppo: non c'è un test in distribuzione
separato, la CV ne fa le veci. Una sovrapposizione di pazienti tra CAMELYON16 e 17 (Radboud, Utrecht)
non è verificabile (C17 §3): può gonfiare la CV, non il leave-one-centre-out. Un backbone; il punto
cieco della griglia resta (C17 §1). La temperatura è un solo parametro: corregge la scala, non uno
spostamento diverso per classe. La CV calibrata è ottimista (la temperatura è stimata sulle stesse
predizioni): il gate la usa, ma la misura che conta è quella in leave-one-centre-out.

**Risultati** (18/10/2026, codice `72140b2`, `dvc repro -s head-ln_metastasis`, circa 3 ore e mezza
con tre semi in parallelo; report in `data/reports/phikon/heads/ln_metastasis/`, modello
`head-ln_metastasis-phikon` v1, alias `candidate`). Eseguito come da protocollo; i 92 vetrini LPON
non sono stati letti.

| Voce del gate | Media (semi 0, 1, 2) | Soglia | Esito |
|---|---|---|---|
| AUROC in CV | 0,989 (0,992; 0,987; 0,988) | ≥ 0,90 | sì |
| AUROC peggiore in leave-one-centre-out | 0,974 (0,970; 0,978; 0,974) | ≥ 0,85 | sì |
| ECE calibrata in CV | 0,033 | ≤ 0,10 | sì |
| **ECE calibrata peggiore in leave-one-centre-out** | **0,293** (0,252; 0,414; 0,214) | ≤ 0,10 | **no** |
| **Specificità peggiore in leave-one-centre-out** | **0,430** (0,561; 0,091; 0,638) | ≥ 0,80 | **no** |
| **Probe sul centro, negativi** | **0,999** | ≤ 0,80 | **no** |
| Robustness Index | 2,65 (vicini dallo stesso centro 97%) | ≥ 0,5 | sì |

Per centro escluso (media sui semi):

| Centro escluso | AUROC | Sensibilità | Specificità | ECE calibrata | Temperatura della rotazione |
|---|---|---|---|---|---|
| CWZ | 0,976 | 0,962 | 0,770 | 0,186 | 2,05 |
| Radboud | 0,984 | 0,978 | 0,911 (C16 0,878; C17 0,990) | 0,105 | 1,76 |
| Rijnstate | 0,978 | 0,938 | 0,972 | 0,033 | 1,75 |
| Utrecht | 0,980 | 0,981 | **0,492** (0,091–0,823) | **0,273** | 1,86 |

- Effetto della temperatura: ECE peggiore in leave-one-centre-out da 0,320 (grezza) a 0,293. Temperatura
  globale 1,69: dopo 30 epoche il modello è troppo sicuro, ma non è questo il problema principale.
- Confronto con CAMELYON16 (Utrecht escluso, vetrini Utrecht di CAMELYON16): ECE calibrata **0,275**,
  specificità **0,427**, contro E4 `none` 0,146 e 0,864. Aggiunta a posteriori: E4 valutava solo i 99
  vetrini Utrecht dello split di training; sugli stessi 99 vetrini E6 dà ECE 0,268 e specificità 0,458.
- Attenzione: AUROC 0,988 (E4 `none` 0,989).

**Lettura secondo il protocollo.**

- **Il gate non è superato**: ECE e specificità sul centro escluso peggiore, e probe sul centro.
- **"Più centri aiutano": no.** Sul centro comune la calibrazione e la specificità peggiorano
  (ECE +0,13, specificità −0,41), ben oltre i margini fissati.
- Il probe sopra 0,80 era atteso e non invalida le altre misure.
- E6 è il riferimento di E7.

**Analisi a posteriori** (non nel protocollo, quindi ipotesi). Mediana delle logit per centro, in CV
(centro visto) e in leave-one-centre-out (centro escluso):

| Centro | Negativi, CV | Negativi, escluso | Positivi, CV | Positivi, escluso |
|---|---|---|---|---|
| CWZ | −6,1 | −2,7 | 11,3 | 10,9 |
| Radboud | −6,6 | −3,8 | 12,5 | 12,1 |
| Rijnstate | −9,5 | −6,4 | 13,0 | 13,7 |
| Utrecht | −8,0 | **+0,1** | 11,8 | 11,9 |

- **Lo spostamento riguarda solo i vetrini negativi.** Su un centro mai visto i positivi restano dove
  sono; i negativi salgono verso il tumore, fino a metà dei normali di Utrecht oltre la soglia. Il
  modello ha imparato "normale" come "tessuto normale come appare negli scanner del training": un
  tessuto normale non familiare è spinto verso il positivo. Le tile tumorali, che l'attenzione
  seleziona, bastano invece a riconoscere il tumore in ogni centro (AUROC peggiore 0,974).
- **Una temperatura non può correggerlo**: cambia la scala, non uno spostamento che colpisce una sola
  classe, e non sposta la decisione a 0,5. Quello che manca è una correzione dell'offset sui negativi
  del centro nuovo.
- **Utrecht è l'unico centro con uno scanner diverso** (Hamamatsu). Senza di lui il training vede solo
  vetrini 3DHistech (Radboud di CAMELYON16 e 17, CWZ, Rijnstate). In E4 il training era il solo Radboud
  di CAMELYON16 e Utrecht stava meglio: aggiungere centri dello stesso scanner sembra rendere il modello
  più sicuro su quel dominio e più fragile sugli altri. È coerente con E2: il centro è leggibile ovunque.
- **La variabilità tra semi è enorme proprio dove il modello fallisce** (specificità di Utrecht da 0,09
  a 0,82): la posizione dei normali di un dominio nuovo non è vincolata dal training.
- Dentro Radboud, i vetrini di CAMELYON16 sono specifici 0,878 contro 0,990 di quelli di CAMELYON17:
  il dominio conta anche dentro un centro (coerente con E3b).
- Dettaglio del protocollo emerso: con 5 fold e `cv_fold mod 3` i fold interni sono sbilanciati (il
  terzo ha circa la metà dei vetrini). Non cambia la lettura; si tiene uguale in E7 per confrontabilità.

**Conseguenze.**

1. Per E7 il problema da risolvere è chiaro: **la posizione dei negativi di un dominio nuovo**. Tra le
   tre varianti, `stat_mix` è l'unica che agisce su questo (mescola le statistiche dei domini in
   training); bilanciamento e group DRO agiscono sul peso dei domini visti.
2. La decisione "solo calibrazione globale" va ridiscussa se E7 non basta: una correzione dell'offset
   con pochi vetrini **negativi** del centro nuovo (non serve una diagnosi positiva) risolverebbe
   proprio lo spostamento osservato. Resta una decisione da prendere, non una modifica del protocollo.
3. Il rinvio OOD diventa più importante: i normali di un dominio nuovo sono esattamente i casi da
   rinviare finché il modello non è calibrato su quel dominio.
4. Il test esterno (LPON, Philips: un terzo scanner) per ora non va consultato: il gate non è superato.

## E7 — Mitigazioni del centro nella testa

Protocollo fissato il 18/10/2026, **dopo la fine dell'esecuzione di E6 e prima di leggerne i
risultati**. Riferimento: E6.

**Domanda.** A parità di dati, split, protocollo, temperatura e gate, una ricetta di training
migliora la calibrazione sul centro escluso peggiore o riduce quanto il centro è leggibile nella
rappresentazione della testa, senza perdere capacità di distinguere e di localizzare?

**Disegno.** Tre varianti, ognuna contro E6 (ricetta vuota), stesso codice e stessi tre semi:

1. `balanced`: in ogni epoca ogni dominio pesa uguale e, dentro il dominio, le due classi pesano
   uguale (peso del vetrino = 1 / (n domini × 2 × vetrini della sua classe nel suo dominio),
   normalizzato a media 1); sostituisce il `pos_weight` globale.
2. `balanced + group_dro`: in più, perdita del dominio peggiore (Sagawa et al., 2020, versione
   online): un peso q per dominio, aggiornato a ogni vetrino con q_d ← q_d · exp(η · perdita), η = 0,01,
   poi normalizzato; la perdita del passo è moltiplicata per n domini × q del dominio del vetrino.
3. `balanced + stat_mix`: in più, con probabilità 0,5 per vetrino e per passo, le tile vengono
   standardizzate con media e deviazione standard del loro vetrino e riportate con una miscela
   λ · (statistiche proprie) + (1 − λ) · (statistiche di un vetrino a caso di un altro dominio del
   training), λ ~ Beta(0,1; 0,1) (MixStyle, Zhou et al., 2021, sulle statistiche per vetrino). Solo
   in training; in inferenza il modello è quello di sempre.

Gli iperparametri (η, p, α della Beta) sono fissati qui dai valori degli articoli, **non tarati**:
con tre semi e quattro rotazioni una taratura sceglierebbe il rumore. I domini sono quelli del
cohort (dataset × centro); il bilanciamento usa solo i domini presenti nel training della singola
esecuzione (in leave-one-centre-out il centro escluso non c'è).

**Esiti** (media sui tre semi, differenza da E6).

- Primari: ECE calibrata peggiore in leave-one-centre-out; AUROC del probe sul centro (negativi).
- Vincoli: AUROC peggiore in leave-one-centre-out, AUROC in CV, specificità peggiore in
  leave-one-centre-out, AUROC dell'attenzione.
- Secondari: Robustness Index, ECE grezza peggiore, metriche per centro e per dominio, temperature.

**Criterio di adozione** (fissato ora). Una variante è adottata se migliora almeno uno dei primari
— ECE calibrata peggiore in leave-one-centre-out **−0,03** o più, oppure probe sul centro **−0,10** o
più — e rispetta tutti i vincoli: AUROC peggiore in leave-one-centre-out e AUROC in CV non scendono
più di 0,01; specificità peggiore in leave-one-centre-out non scende più di 0,02; AUROC
dell'attenzione non scende più di 0,02. Se più varianti sono adottabili, si sceglie quella che
supera il gate; a parità, la più semplice nell'ordine 1, 2, 3. Combinazioni diverse da quelle
elencate (per esempio group DRO + stat_mix) sono un nuovo protocollo, non una scelta a posteriori.

**Se nessuna è adottata** si tiene la ricetta vuota. Se il probe resta sopra la soglia del gate per
tutte, la decisione tra discriminatore avversariale e revisione della soglia si prende con i
patologi, guardando calibrazione e specificità sul centro escluso, non il probe da solo.

**Limiti.** Tre semi: in E4 la variabilità tra semi dell'ECE peggiore era dell'ordine di 0,07, più
grande del margine di 0,03. Il report riporta il valore di ogni seme e l'esito va letto con quella
incertezza. Un solo backbone (Phikon): la ricetta va rivalidata con H-optimus-0.

**Risultati** (18–19/10/2026, codice `b350cfd`, `experiments/e7_run.sh`: circa 4 ore per variante, tre
semi in parallelo; report in `data/reports/experiments/e7/`, confronto in
`data/reports/experiments/e7/summary.md` scritto da `experiments/e7_compare.py`, fissato prima dei
risultati). Eseguito come da protocollo; nessun modello registrato.

| Metrica (media sui semi) | E6 | balanced | + group DRO | + stat_mix |
|---|---|---|---|---|
| **ECE calibrata peggiore LOCO** (primario, −0,03) | 0,293 | 0,313 (+0,020) | 0,277 (−0,016) | 0,296 (+0,003) |
| **Probe sul centro, negativi** (primario, −0,10) | 0,999 | 0,995 | 0,995 | 0,994 |
| AUROC peggiore LOCO (vincolo, −0,01) | 0,974 | 0,967 | 0,970 | **0,959 (−0,015)** |
| AUROC CV (vincolo, −0,01) | 0,989 | 0,985 | 0,988 | 0,986 |
| Specificità peggiore LOCO (vincolo, −0,02) | 0,430 | 0,485 | 0,541 | 0,530 |
| AUROC attenzione (vincolo, −0,02) | 0,988 | 0,988 | 0,989 | 0,989 |
| Robustness Index | 2,65 | 2,70 | 2,94 | 2,90 |
| Specificità, Utrecht escluso | 0,492 | 0,490 | **0,713** | 0,530 |
| Specificità, CWZ escluso | 0,770 | 0,759 | **0,569** | **0,920** |
| Gate | non superato | non superato | non superato | non superato |

**Esito secondo il criterio: nessuna variante adottata, si tiene la ricetta vuota.** Nessuna raggiunge
un primario; `stat_mix` viola anche il vincolo sull'AUROC peggiore in leave-one-centre-out (−0,015).
Il probe resta a 0,99 per tutte: come previsto da E6, il gate sul probe non è avvicinabile con queste
ricette.

**Analisi a posteriori** (ipotesi). Mediana delle logit dei vetrini **negativi** del centro escluso
(in CV, centro visto, tutte le varianti stanno fra −6,3 e −8,0):

| | CWZ escluso | Utrecht escluso |
|---|---|---|
| E6 | −2,7 | +0,1 |
| balanced | −3,4 | +0,1 |
| + group DRO | −0,7 | **−2,0** |
| + stat_mix | **−3,7** | −0,1 |

- **L'errore si sposta tra centri invece di sparire**, come in E4. Group DRO aiuta Utrecht
  (specificità +0,22) e peggiora CWZ (−0,20); la specificità peggiore sale solo perché il peggiore
  cambia centro.
- **stat_mix aiuta il centro dello stesso scanner, non quello di scanner diverso.** CWZ (3DHistech
  come i centri di training) passa da 0,77 a 0,92 di specificità; Utrecht (Hamamatsu) resta a 0,53.
  Coerente con E2: media e varianza per vetrino non bastano, la differenza di scanner sta anche nella
  struttura locale.
- Nessuna ricetta riporta i negativi di Utrecht vicino a quelli visti in training (−2,0 nel migliore
  dei casi, contro circa −7).

**Conseguenze.**

1. Con le ricette di E7 il problema di E6 resta: lo spostamento dei negativi su uno scanner mai visto.
2. Restano due strade, da decidere: il discriminatore avversariale (DANN, implementato come ricetta
   `adversarial`, da usare con un protocollo suo), che agisce sulla struttura della rappresentazione e
   non solo sulle statistiche, e la correzione dell'offset con pochi vetrini negativi del centro nuovo,
   che risponde direttamente allo spostamento osservato ma richiede di rivedere la decisione "solo
   calibrazione globale".
3. Il gate sul probe (≤ 0,80) è fuori portata per tutte le ricette senza un vincolo esplicito sulla
   rappresentazione; va ridiscusso insieme alla strada scelta.

## E8 — Discriminatore avversariale del dominio (DANN)

Protocollo fissato il 19/10/2026, dopo E7 e prima di ogni addestramento con le ricette avversariali
sui dati reali (una prova da 1 epoca e 1 seme, solo per verificare che il codice giri, si fa dopo
questo protocollo e non entra nei risultati). Riferimento: E6 (in E7 nessuna ricetta è stata adottata).

**Domanda.** Se la testa viene addestrata a rendere la sua rappresentazione inutile per riconoscere il
dominio, i vetrini negativi di un centro mai visto restano vicini ai negativi del training, invece di
salire verso il tumore come in E6 ed E7?

**Perché ora.** E7 ha mostrato che pesare i domini (bilanciamento, group DRO) sposta l'errore da un
centro all'altro, e che mescolare media e varianza per vetrino aiuta il centro con lo stesso scanner
(CWZ) ma non quello con uno scanner diverso (Utrecht). Il discriminatore agisce su tutta la struttura
della rappresentazione che un classificatore non lineare sa leggere, non solo sulle statistiche.

**Disegno.** Due varianti, ognuna contro E6, stesso codice di E6/E7 e stessi tre semi:

1. `balanced + adversarial`: due discriminatori del dominio (dataset × centro), uno sulla
   rappresentazione del vetrino *z* e uno su 256 tile campionate a ogni passo dalla loro
   rappresentazione *h*; MLP con uno strato nascosto da 128; entropia incrociata pesata per dominio
   (inverso della frequenza dei domini nel training); collegati alla testa con l'inversione del
   gradiente, forza λ(p) = 2 / (1 + e^(−10 p)) − 1 con p = avanzamento del training da 0 a 1 (Ganin et
   al., 2016), fino a 1. Stesso ottimizzatore (AdamW, stesso learning rate) per testa e
   discriminatori. I discriminatori sono scartati alla fine: il modello è l'ABMIL di sempre.
2. `balanced + adversarial_negatives`: lo stesso, ma la perdita avversariale si calcola **solo sui
   vetrini negativi** (pesi per dominio contati sui negativi). È lo spostamento osservato in E6 (solo i
   negativi salgono), e lascia stare il segnale del tumore.

`balanced` è in entrambe perché la prevalenza del tumore cambia tra domini: senza bilanciamento il
discriminatore potrebbe riconoscere il dominio dalla quota di tumore. Gli iperparametri sono i valori
dell'articolo, **non tarati**, per la stessa ragione di E7.

**Esiti** (media sui tre semi, differenza da E6).

- Primari: ECE calibrata peggiore in leave-one-centre-out; specificità peggiore in leave-one-centre-out.
- Vincoli: AUROC peggiore in leave-one-centre-out, AUROC in CV, AUROC dell'attenzione, e la
  **specificità di ogni centro escluso** (perché il peggiore non può migliorare solo cambiando centro).
- Secondari: probe sul centro (negativi), Robustness Index, mediana delle logit dei negativi di
  ciascun centro escluso (la misura di E6), metriche per dominio, temperature.

Il probe passa da primario (E7) a secondario: le ricette avversariali ottimizzano proprio la leggibilità
del centro in *z*, quindi il probe può scendere senza che cambi nulla sul centro escluso. Resta voce del
gate e si riporta.

**Criterio di adozione** (fissato ora). Una variante è adottata se raggiunge almeno un primario — ECE
calibrata peggiore in leave-one-centre-out **−0,03** o più, oppure specificità peggiore in
leave-one-centre-out **+0,10** o più — e rispetta tutti i vincoli: AUROC peggiore in leave-one-centre-out
e AUROC in CV non scendono più di 0,01; AUROC dell'attenzione non scende più di 0,02; **la specificità di
nessun centro escluso scende più di 0,05**. Se entrambe sono adottabili si sceglie quella che supera il
gate; a parità, la 2 (agisce solo dove E6 ha visto il problema, toglie meno segnale). Nessuna combinazione
con group DRO o stat_mix in questo esperimento.

**Se nessuna è adottata**, si tiene la ricetta vuota e il passo successivo è la correzione dell'offset
con pochi vetrini negativi del centro nuovo, che richiede di rivedere con i patologi la decisione "solo
calibrazione globale".

**Limiti.** Tre semi, con la variabilità di E6–E7 (specificità di Utrecht da 0,09 a 0,82 tra semi):
il margine di 0,10 sulla specificità è dell'ordine di quella variabilità, e il report riporta ogni
seme. Nella rotazione "Utrecht escluso" il training contiene solo vetrini 3DHistech: il discriminatore
impara a cancellare le differenze fra centri 3DHistech, non necessariamente quella verso Hamamatsu; è
proprio ciò che il leave-one-centre-out misura. Un backbone; λ non tarato.

**Risultati** (19/10/2026, codice `b350cfd` più le modifiche non committate della DANN, registrato nei
report come `b350cfd+dirty`; un primo lancio è stato interrotto da un riavvio e rifatto da capo;
circa 5 ore e 45 minuti la prima variante, 4 ore e 50 la seconda, con la CPU frenata da `kernel_task`;
report in `data/reports/experiments/e8/`, confronto in `data/reports/experiments/e8/summary.md` da
`experiments/e8_compare.py`, fissato prima dei risultati). Nessun modello registrato.

| Metrica (media sui semi) | E6 | balanced + adversarial | balanced + adversarial_negatives |
|---|---|---|---|
| **ECE calibrata peggiore LOCO** (primario, −0,03) | 0,293 | 0,389 (+0,096) | 0,301 (+0,008) |
| **Specificità peggiore LOCO** (primario, +0,10) | 0,430 | 0,383 (−0,048) | **0,561 (+0,131)** |
| AUROC peggiore LOCO (vincolo, −0,01) | 0,974 | **0,962 (−0,012)** | **0,952 (−0,022)** |
| AUROC CV (vincolo, −0,01) | 0,989 | 0,986 | 0,980 |
| AUROC attenzione (vincolo, −0,02) | 0,988 | 0,992 | 0,990 |
| Specificità, CWZ escluso (vincolo, −0,05) | 0,770 | **0,414 (−0,356)** | **0,718 (−0,052)** |
| Specificità, Radboud escluso | 0,911 | 0,896 | 0,917 |
| Specificità, Rijnstate escluso | 0,972 | 0,989 | 0,989 |
| Specificità, Utrecht escluso | 0,492 (0,56; 0,09; 0,82) | **0,870 (0,87; 0,85; 0,89)** | 0,663 (0,52; 0,68; 0,79) |
| Probe sul centro, negativi | 0,999 | 0,991 | 0,997 |
| Robustness Index | 2,65 | 3,09 | 2,38 |
| Logit mediana dei negativi, Utrecht escluso (CV: da −5 a −8) | +0,1 | −2,3 | −1,2 |
| Logit mediana dei negativi, CWZ escluso | −2,7 | +1,2 | −3,0 |

**Esito secondo il criterio: nessuna variante adottata, si tiene la ricetta vuota.**

- `balanced + adversarial`: nessun primario; viola l'AUROC peggiore (−0,012) e soprattutto la
  specificità di CWZ (−0,36, con un seme a 0,05).
- `balanced + adversarial_negatives`: raggiunge un primario (specificità peggiore +0,131), ma viola
  l'AUROC peggiore (−0,022) e, di poco, la specificità di CWZ (−0,052 contro un margine di 0,05).

**Lettura** (oltre il criterio, quindi ipotesi).

- **La DANN su tutti i vetrini corregge Utrecht, ed è stabile**: specificità 0,87 in tutti e tre i semi
  (E6 da 0,09 a 0,82). È la prima ricetta che lo fa. In quella rotazione il training contiene solo
  vetrini 3DHistech: un vincolo sulla rappresentazione basta per uno scanner mai visto, contro
  l'ipotesi "è lo scanner, quindi serve vederlo".
- **Ma lo schema di E4 ed E7 si ripete**: l'errore va su CWZ, con una variabilità enorme (0,97; 0,05;
  0,22). Escludere CWZ lascia nel training due domini Utrecht (Hamamatsu) e due Radboud; cosa renda
  CWZ instabile con la DANN non è chiaro dai dati.
- **La variante sui soli negativi è un compromesso**: aiuta Utrecht meno (0,66), tiene quasi CWZ (0,72),
  e porta la specificità peggiore a 0,56, il valore migliore di E6–E8. Paga 0,02 di AUROC sul centro
  peggiore. È fuori dal criterio per poco su due vincoli: il criterio resta quello, e la variante non
  è adottata.
- **Le temperature salgono** (1,9–2,1 contro 1,7): con la DANN il modello è più sicuro di sé sui domini
  visti, e la temperatura globale lo corregge solo in parte (ECE peggiore invariata o peggiore).
- **Il probe resta a 0,99** anche con il discriminatore: la testa nasconde il dominio al discriminatore
  non lineare durante il training, ma un probe lineare lo ritrova nel modello finale. Il Robustness
  Index sale solo con la DANN su tutti i vetrini (3,09).

**Conseguenze.**

1. Dopo E7 ed E8 nessuna ricetta di training, a parità di dati, sposta il centro peggiore senza
   spostare l'errore su un altro centro. La ricetta di `ln_metastasis` resta vuota.
2. Lo spostamento dei negativi di un centro nuovo è reale e dipende dal centro escluso in modo
   instabile tra semi. È un argomento forte per la correzione dell'offset con pochi vetrini negativi del
   centro nuovo, da discutere con i patologi, e per il rinvio OOD dei casi di un dominio non calibrato.
3. Il probe sul centro non è una misura utile come soglia di promozione: lo si toglie dal gate (decisione
   del 19/10/2026) e si tiene come voce riportata con una regola di non regressione.
4. Se si riprende la DANN, il passo naturale è un protocollo nuovo che ne misuri l'instabilità (più semi,
   λ più basso), non una scelta a posteriori tra le varianti di E8.

