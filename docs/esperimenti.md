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
| E9 | Correzione dell'offset con pochi negativi del centro nuovo | fatto: non proponibile; specificità recuperata da k = 3, ma si perdono micrometastasi | quanti vetrini negativi di un centro nuovo servono per riportarne la specificità vicino ai centri visti; dato per la decisione con i patologi |
| E10 | Insiemi conformal e rinvio al patologo sul centro escluso: marginale, per classe, per classe × centro | fatto: scelta «per classe»; le risposte negative reggono, i falsi positivi di Utrecht no | se la testa può dichiarare l'incertezza su un centro nuovo con copertura garantita, e a quale costo in rinvii |
| E11 | Offset con pochi negativi del centro nuovo + insiemi conformal per classe sulle logit corrette | fatto: non proponibile; le micrometastasi corrette sono negativi chiari, non incerti | se le micrometastasi perse da E9 diventano rinvii invece che risposte «negativo», e a quale costo in rinvii |
| E12 | Punteggio del vetrino dalle tile più sospette: logit d'istanza dell'ABMIL e classificatore di tile supervisionato, top-k | fatto: nessun candidato; anche le tile portano lo spostamento di centro, in direzioni diverse | se un segnale dalle tile trova le micrometastasi di un centro nuovo che la logit del vetrino diluisce, senza falsi positivi in più |
| E13 | Pilota: normalizzazione del colore (Reinhard, Macenko) prima dell'embedding, su 44 vetrini, a livello di tile | protocollo fissato; in pausa, dopo E14 | se vale la pena rifare l'estrazione di tutto lo sviluppo (circa 2 TB da riscaricare) con il colore normalizzato |
| E14 | Vetrini di un centro nuovo aggiunti al training (5, 10, 20, 40), contro centro mai visto, centro visto e offset di E9 | protocollo fissato | quanti casi di uso silente servono perché un centro nuovo entri nella pipeline; se la leva sono i dati raccolti o il segnale a monte (E13) |
| E15 | Riconoscere un dominio non visto dagli embedding: distanza a livello di vetrino e di tile, in leave-one-centre-out | protocollo fissato | se `predict` rinvia anche i cambi di dominio che i metadati non vedono, e con quale punteggio |

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


## E9 — Correzione dell'offset con pochi negativi del centro nuovo

Protocollo fissato il 20/10/2026, dopo E8 e prima di ogni correzione dell'offset su questi dati.
Riferimento: E6 (ricetta vuota). Il numero viene prima di E10 ma il protocollo è stato scritto dopo:
E10 non dipende da E9.

**Domanda.** In E6–E8 i negativi di un centro mai visto salgono verso il tumore come blocco (logit
mediana dei negativi di Utrecht escluso circa +0,1 contro circa −7 sui centri visti), e nessuna
ricetta di training lo corregge senza spostare l'errore altrove. Se all'installazione si dispone di
**k vetrini negativi confermati** del centro nuovo e si sposta di conseguenza la logit di tutti i suoi
vetrini, quanto si recupera di specificità e calibrazione, quanto si perde di sensibilità, e da quale
k in poi?

**Che cosa decide e che cosa no.** E9 misura. Usare vetrini del centro all'installazione rivede la
decisione del 18/10/2026 "solo calibrazione globale" (training-multicentro.md): **l'adozione la
decidono i patologi**, su questi numeri e sul costo di raccogliere k negativi confermati. Il criterio
qui sotto dice solo se e da quale k la correzione è *proponibile*.

**Dati.** Gli stessi di E10: la riesecuzione di E6 (`data/reports/experiments/e10/e6/predictions.csv`)
con il controllo preliminare di E10 superato; se non lo supera, E9 usa comunque la riesecuzione e la
differenza si riporta. Per ogni seme e rotazione LOCO servono:

- le logit LOCO del centro escluso e la temperatura *T* della rotazione;
- le logit dei fold interni dei centri di training (gruppo `loco-calibration`), che danno il livello
  di riferimento dei negativi **senza il centro escluso**.

Nessun nuovo training; LPON non viene letto.

**Correzione.** Livello di riferimento m_ref = mediana delle logit dei negativi nei fold interni della
rotazione. Livello del centro nuovo m_k = mediana delle logit dei k negativi estratti. Offset
b = m_k − m_ref. Per ogni altro vetrino del centro: p = sigmoide((logit − b) / *T*), soglia 0,5. La
temperatura resta quella della rotazione; uno spostamento uguale per tutto il centro non cambia
l'ordinamento, quindi l'AUROC del centro non cambia per costruzione (si riporta come controllo).

Due varianti:

1. `offset`: b come sopra, in entrambe le direzioni.
2. `offset solo in discesa`: b' = max(b, 0). Corregge solo i centri i cui negativi stanno *sopra* il
   riferimento, cioè lo spostamento osservato, e non alza mai le logit di un centro.

In produzione m_ref sarebbe la mediana dei negativi nelle logit fuori fold della CV di tutto lo
sviluppo, applicata al modello finale (come la temperatura).

**Estrazioni.** k ∈ {3, 5, 10, 20}. Per ogni seme, rotazione e k: 200 estrazioni casuali senza
reimmissione di k negativi del centro escluso (generatore con seme 0, fissato), tra tutti i suoi
negativi. Ogni estrazione si valuta sugli **altri** vetrini del centro (tutti i positivi e i negativi
non estratti). Ogni centro ha almeno 58 negativi (CWZ), quindi k = 20 lascia sempre almeno 38
negativi di valutazione.

**Esiti** (per variante e k; media sulle 200 estrazioni, poi sui tre semi; per centro escluso).

- Primari:
  - specificità sul centro escluso peggiore;
  - ECE calibrata sul centro escluso peggiore.
- Vincoli:
  - sensibilità di ogni centro escluso;
  - 10° percentile della specificità sulle estrazioni, sul centro peggiore (un'estrazione sfortunata
    è ciò che succede in un'installazione vera, che ne fa una sola).
- Secondari:
  - mediana delle logit dei negativi dopo la correzione, accanto a m_ref (la misura di E6);
  - b medio e la sua dispersione tra estrazioni;
  - AUROC del centro (controllo: invariata);
  - sensibilità e specificità per dominio;
  - **offset trasferito tra domini dello stesso centro**: per Radboud e Utrecht, che hanno vetrini di
    CAMELYON16 e di CAMELYON17, i k negativi si estraggono da un dataset e la correzione si valuta
    sull'altro, nei due versi. È la cosa più vicina a "negativi raccolti in un periodo, vetrini
    analizzati in un altro" (E3b: i casi di Radboud del 2015 sono un dominio a parte).

Riferimento per ogni esito: E6 senza correzione sugli stessi vetrini di valutazione.

**Criterio** (fissato ora). Per ciascuna variante, il k minimo *proponibile* è il più piccolo k
dell'insieme per cui, in media su estrazioni e semi:

- almeno un primario migliora rispetto a E6: specificità sul centro peggiore **+0,10** o più, oppure
  ECE calibrata peggiore **−0,03** o più (le soglie di E7 ed E8);
- la sensibilità di nessun centro escluso scende più di **0,05**;
- il 10° percentile della specificità sul centro peggiore non è sotto la specificità di E6 su quel
  centro.

*Modifica del 20/10/2026, prima dell'esecuzione sui dati reali.* Il centro della terza condizione è
**il centro peggiore di E6** (quello da correggere), non il peggiore dopo la correzione. Motivo: la
prova su dati sintetici con un solo centro spostato ha mostrato che, una volta corretto quel centro, il
peggiore diventa un centro che andava già bene, dove il 10° percentile delle estrazioni sta per
costruzione sotto la media di E6; la condizione fallirebbe sempre. L'intento era proteggere il centro
corretto da un'estrazione sfortunata.

*Seconda modifica del 20/10/2026, prima dell'esecuzione sui dati reali.* Il vincolo sulla sensibilità
si misura rispetto alla sensibilità **dello stesso centro quando è visto in training** (CV di E6,
soglia 0,5), non rispetto a E6 sul centro escluso: la sensibilità di ogni centro escluso dopo la
correzione non scende più di 0,05 sotto quella. Motivo: nella prova sintetica il centro spostato aveva
in E6 sensibilità 1,00 *perché* tutto il centro saliva verso il tumore; la correzione lo riportava a
0,94, come gli altri centri, e il vincolo la bocciava. Lo scopo della correzione è riportare il centro
nuovo a comportarsi come uno visto: il confronto è con quello. La perdita rispetto a E6 resta nel
report.

Se entrambe le varianti hanno un k proponibile, si propone quella con k minore; a parità di k, la 2
(non alza mai le logit, quindi non può creare falsi positivi dove E6 non ne aveva). Se nessun k è
proponibile, la correzione dell'offset non si porta ai patologi in questa forma.

**Legame con E10.** Se l'offset viene adottato, con gli stessi negativi si possono calcolare anche i
quantili conformal dei negativi del centro nuovo; per α = 0,05 ne servono almeno 19, quindi k = 20.
La combinazione offset + conformal è un protocollo nuovo, non una variante di questo.

**Limiti.**

- I k negativi vengono dallo stesso insieme di vetrini storici del leave-one-centre-out: in
  un'installazione vera vengono da un periodo e da una preparazione diversi. Il trasferimento tra
  dataset dello stesso centro misura in parte questo effetto, ma solo per due centri.
- Si sposta solo il livello: se un centro nuovo cambia anche la dispersione delle logit dei
  negativi, una sola correzione additiva non basta (si vede dalla specificità che resta bassa con k
  grande).
- Si assume che i positivi del centro nuovo si spostino quanto i negativi; se salgono meno, o non
  salgono, la correzione costa sensibilità. È il vincolo sulla sensibilità a misurarlo.
- Tre semi, con la variabilità di E6–E8 (specificità di Utrecht escluso da 0,09 a 0,82 tra semi);
  quattro rotazioni; un backbone (va rivalidato con H-optimus-0).
- I k negativi devono avere diagnosi confermata: è un costo per il centro, che il criterio non pesa.

**Codice.** Il calcolo sarà in `experiments/e9_offset.py`; lo script si committa prima di eseguirlo
sulla riesecuzione di E6.

**Risultati** (20/10/2026, codice `b6da989`, due minuti di calcolo sulla riesecuzione di E6 di E10;
risultati in `data/reports/experiments/e9/summary.md`, da `experiments/e9_offset.py` committato prima
dell'esecuzione, con le due modifiche al criterio annotate sopra). Controllo della riesecuzione superato
(come in E10).

Media su 200 estrazioni e tre semi; tra parentesi E6 senza correzione sugli stessi vetrini:

| Centro escluso | Specificità, k = 3 | Specificità, k = 20 | Sensibilità, k = 20 (E6; centro visto) | ECE, k = 20 | b medio |
|---|---|---|---|---|---|
| Utrecht | 0,972 (0,492) | 0,980 (0,492) | **0,912** (0,981; 0,992) | 0,063 (0,260) | 6,0 |
| CWZ | 0,965 (0,770) | 0,983 (0,773) | **0,861** (0,962; 0,924) | 0,086 (0,154) | 5,1 |
| Radboud | 0,973 (0,911) | 0,977 (0,912) | 0,941 (0,978; 0,975) | 0,039 (0,100) | 3,5 |
| Rijnstate | 0,985 (0,973) | 0,984 (0,972) | 0,938 (0,938; 0,938) | 0,027 (0,029) | 1,0 |

(Variante `offset solo in discesa`; la variante in due versi dà gli stessi numeri a Utrecht e CWZ e una
specificità più bassa a Radboud con k piccolo.)

**Esito secondo il criterio: nessun k proponibile, per nessuna delle due varianti.** I primari sono
raggiunti con ampio margine per ogni k (specificità peggiore da +0,44 a +0,49; ECE peggiore da −0,17 a
−0,18), e il 10° percentile delle estrazioni su Utrecht è 0,94 già con k = 3. Il vincolo sulla
sensibilità no: Utrecht perde 0,08 rispetto al centro visto, CWZ 0,06–0,07, con ogni k.

**Lettura** (oltre il criterio, quindi ipotesi).

- **Lo spostamento dei negativi è davvero di livello, e pochi negativi bastano a misurarlo.** Con 3
  negativi la mediana delle logit dei negativi di Utrecht torna da −0,7 a −6,8, quella di riferimento è
  −6,7; la specificità passa da 0,49 a 0,97. Aumentare k riduce la dispersione di b (da 1,6 a 0,6) ma
  cambia poco la media: **il problema non è la stima dell'offset**.
- **La sensibilità persa è quasi tutta micrometastasi.** I positivi che scendono sotto la soglia dopo la
  correzione, a Utrecht e CWZ, sono 16 vetrini diversi tra i semi: 15 micrometastasi e una
  macrometastasi (`patient_045_node_0`, in due semi su tre). In un vetrino con poco tumore la logit è
  fatta soprattutto dal tessuto normale. In E6 lo spostamento del tessuto normale li spingeva sopra la
  soglia: la sensibilità di E6 sul centro escluso è in parte quella di un modello che dice "tumore" a
  tutto il centro. La correzione toglie lo spostamento anche a loro.
- **Il trasferimento tra dataset dà due risposte diverse.** A Utrecht la correzione stimata su un dataset
  funziona sull'altro (specificità da 0,43 a 0,96 e da 0,57 a 1,00), ma da CAMELYON16 a CAMELYON17 la
  sensibilità scende da 0,93 a 0,80. A Radboud l'offset stimato su CAMELYON17 e applicato a CAMELYON16
  (i casi del 2015, E3b) è negativo (b = −1,2) e nella variante in due versi abbassa la specificità da
  0,88 a 0,76; la variante solo in discesa la tiene a 0,90. **È l'unico argomento netto tra le due
  varianti: solo in discesa.**

*Correzione del 21/10/2026, dopo E11.* La frase "dopo la correzione i negativi stanno a −7 e le
micrometastasi perse intorno a 0" (punto 2 delle conseguenze) è sbagliata: intorno a 0 (mediana tra +2 e
+4) stanno le logit dei positivi persi **prima** della correzione. Dopo, la mediana è −4,2 a CWZ e −2,1 a
Utrecht, e metà sono sotto −3. Su quella lettura si basava l'ipotesi di E11.

**Conseguenze.**

1. Nella forma di questo protocollo la correzione dell'offset non si porta ai patologi come
   proponibile. I numeri vanno comunque portati: su Utrecht si scambiano circa 49 punti di specificità
   con 8 di sensibilità, e quella sensibilità sono micrometastasi. Se lo scambio sia accettabile è una
   decisione clinica (pN1mi), non un parametro.
2. Il limite non è la correzione ma la soglia unica a livello di vetrino: dopo la correzione i negativi
   stanno a −7 e le micrometastasi perse intorno a 0. Due strade, ognuna un protocollo nuovo:
   - **offset + soglia scelta per la sensibilità** (per esempio il quantile dei positivi di E10 sulle
     logit corrette), così che le micrometastasi finiscano in rinvio invece che in "negativo";
   - **un segnale che non dipenda dalla media del vetrino** per i tumori piccoli (attenzione o
     punteggio per tile), dove il tessuto normale non diluisce il tumore.
3. Le micrometastasi sono il punto debole in tutti e due gli esperimenti di oggi (E10: tutti i tumori
   persi; E9: quasi tutta la sensibilità persa). Vanno riportate come sottogruppo nella batteria della
   testa.

## E10 — Insiemi conformal e rinvio al patologo

Protocollo fissato il 20/10/2026, **prima di calcolare qualunque insieme conformal o tasso di rinvio**
su questi dati. Riferimento: E6 (ricetta vuota, la ricetta di `ln_metastasis` dopo E7 ed E8). Il
numero E9 è riservato alla correzione dell'offset con pochi negativi del centro nuovo, ancora da
discutere con i patologi.

**Domanda.** Se la testa, invece di una risposta sì/no alla soglia 0,5, restituisce un insieme di
etichette con copertura dichiarata, su un centro mai visto (a) la copertura dei positivi regge, e (b)
i negativi spostati verso il tumore (E6: logit mediana dei negativi di Utrecht escluso circa +0,1
contro circa −7 sui centri visti) diventano **rinvii** invece di falsi positivi? A quale tasso di
rinvio, alla prevalenza attesa?

**Perché ora.** E7 ed E8 non hanno trovato una ricetta che sposti il centro peggiore senza spostare
l'errore. Il piano prevede che ogni modulo possa rispondere "rinvio al patologo"; la batteria ha
ancora a "no" le voci copertura conformal e tasso di rinvio alla prevalenza reale. È un'analisi sulle
logit, nessun nuovo training.

**Dati.** Cohort `ln_metastasis` v1, 771 vetrini di sviluppo, Phikon `057cc0295895`, ricetta vuota,
semi 0, 1, 2. LPON non viene letto.

- Le logit di CV e di leave-one-centre-out di E6 sono salvate per vetrino e per seme
  (`data/reports/phikon/heads/ln_metastasis/predictions.csv`, verificato: 771 righe di CV e 771 di
  LOCO per seme, con la temperatura di ogni valutazione).
- **Mancano le logit dei fold interni del leave-one-centre-out** (quelle che danno la temperatura
  della rotazione): `heads/protocol.py` le usa e non le registra. Senza di loro il quantile della
  rotazione dovrebbe venire dalle logit di CV, prodotte da modelli che hanno visto il centro escluso.
  Quindi: (1) il protocollo registra anche le logit interne (gruppo `loco-calibration`), senza altre
  modifiche al training; (2) E6 si riesegue con lo stesso codice di training, gli stessi semi e un
  thread (`mil.register=false`, report in `data/reports/experiments/e10/e6/`); (3) **controllo
  preliminare**: le logit di CV e di LOCO della riesecuzione devono coincidere con quelle salvate
  (differenza massima ≤ 1e-6). Se non coincidono, E10 usa solo la riesecuzione e la differenza si
  riporta.

**Punteggio e insiemi.** Per ogni vetrino p = sigmoide(logit / *T*), con la temperatura della sua
valutazione (globale in CV, della rotazione in LOCO). Punteggio di non conformità rispetto
all'etichetta y: s = 1 − p(y). Per un gruppo di calibrazione di n punteggi, q è il
⌈(n + 1)(1 − α)⌉-esimo più piccolo (q = 1 se l'indice supera n). Un'etichetta entra nell'insieme se
il suo punteggio è ≤ q del suo gruppo. Esito per il vetrino:

| Insieme | Esito |
|---|---|
| `{1}` | risposta: positivo |
| `{0}` | risposta: negativo |
| `{0, 1}` | rinvio, motivo "incerto" |
| `{}` | rinvio, motivo "anomalo" |

**Calibrazione e valutazione.**

- *Centro escluso* (la misura principale): in ogni rotazione i quantili si calcolano sulle logit dei
  fold interni dei soli centri di training, con la temperatura della rotazione, e si applicano alle
  probabilità LOCO del centro escluso. Il centro escluso non contribuisce mai ai suoi quantili.
- *Centro visto* (riferimento): per ogni fold k di CV i quantili si calcolano sulle logit fuori fold
  degli altri fold, e si applicano al fold k.

**Varianti** (Mondrian = un quantile per gruppo).

1. `marginale`: un solo quantile per tutti i vetrini.
2. `per classe`: un quantile per i positivi e uno per i negativi.
3. `per classe × centro`: un quantile per classe e per centro di calibrazione. Sul centro escluso,
   che per costruzione non ha vetrini di calibrazione, si usa per ogni classe **il quantile più alto
   tra i centri di training** (la scelta più prudente, fissata ora); sul centro visto, quello del
   suo centro. La variante con vetrini del centro nuovo è E9, non questa.

Livelli: α = 0,05 (principale) e α = 0,10.

**Esiti** (per seme e media sui tre semi; per centro escluso e per classe).

- Primari, α = 0,05:
  - copertura dei positivi sul centro escluso peggiore;
  - quota dei negativi del centro escluso con risposta `{1}` (falsi positivi dati come risposta) sul
    centro peggiore, accanto a 1 − specificità di E6 alla soglia 0,5 sullo stesso centro.
- Secondari:
  - copertura dei negativi;
  - tumori persi (positivi con risposta `{0}`);
  - tasso di rinvio per classe e per motivo;
  - dimensione media dell'insieme;
  - errore sulle risposte (insiemi di una sola etichetta sbagliati / insiemi di una sola etichetta);
  - tutte le voci sul centro visto;
  - α = 0,10.
- Alla prevalenza π dei positivi, per π ∈ {0,05; 0,10; 0,20; 0,30} e quella del cohort, per ogni
  centro escluso. Con r = tasso di rinvio, a₁ = P(`{1}` | y = 1), f₀ = P(`{1}` | y = 0),
  a₀ = P(`{0}` | y = 0), f₁ = P(`{0}` | y = 1):
  - rinvii(π) = π · r₁ + (1 − π) · r₀;
  - PPV(π) = π a₁ / (π a₁ + (1 − π) f₀);
  - NPV(π) = (1 − π) a₀ / ((1 − π) a₀ + π f₁).
  
  Il valore di π del centro va chiesto ai patologi; la griglia serve a non sceglierlo dopo aver visto i
  numeri.

**Criterio** (fissato ora). A α = 0,05 una variante è **utilizzabile** se, in media sui semi, la
copertura dei positivi è ≥ 0,90 (1 − α − 0,05) **su ogni centro escluso**. Tra le varianti
utilizzabili si sceglie quella con il tasso di rinvio più basso sul centro escluso che ne ha di
più; a parità entro 0,02, la più semplice nell'ordine 1, 2, 3. Se una variante è scelta:

- la testa restituisce anche l'insieme e il motivo del rinvio, con i quantili calcolati sulle logit
  fuori fold della CV di tutto lo sviluppo, applicati al modello finale (come la temperatura);
- la voce "Copertura conformal" della batteria passa a "sì", con la regola di questo criterio nel
  gate della testa.

Se nessuna è utilizzabile, la copertura non si può dichiarare su un centro nuovo senza vetrini di
quel centro: insiemi e rinvii si rimandano a E9.

Il tasso di rinvio accettabile non è un vincolo di questo esperimento: lo decidono i patologi, sui
numeri alla prevalenza.

**Limiti.**

- La garanzia formale del conformal richiede che i vetrini nuovi siano scambiabili con quelli di
  calibrazione: un centro mai visto la viola per costruzione, ed è proprio ciò che il
  leave-one-centre-out misura.
- I punteggi di calibrazione vengono dai modelli dei fold interni, non dal modello LOCO a cui si
  applicano; è la stessa approssimazione della temperatura (in produzione: CV fuori fold applicata al
  modello finale), più vicina a una cross-conformal che a una split conformal in senso stretto.
- Pochi positivi per centro (CWZ 35, Rijnstate 32): l'errore standard di una copertura di 0,95 è
  circa 0,04, dell'ordine della tolleranza di 0,05.
- Tre semi, con la variabilità di E6–E8 (specificità di Utrecht escluso da 0,09 a 0,82 tra semi).
- Solo il livello del vetrino (nessun insieme per regione), un backbone (va rivalidato con
  H-optimus-0), prevalenze non stimate su dati locali.

**Codice.** Il calcolo è in `experiments/e10_conformal.py`; lo script si committa prima di
eseguirlo sulla riesecuzione di E6, come per E7 ed E8.

**Risultati** (20/10/2026, codice `7595dbb`, `experiments/e10_run.sh`: riesecuzione di E6 in 5 ore e 17
minuti, tre semi in parallelo; risultati in `data/reports/experiments/e10/summary.md` e `metrics.csv`,
da `experiments/e10_conformal.py` committato prima dell'esecuzione).

**Controllo preliminare superato**: le logit di CV e di LOCO della riesecuzione coincidono con quelle
di E6 (differenza massima 0 su 4626 righe). Il codice di E7 ed E8 non ha cambiato la ricetta vuota.

Centro escluso, α = 0,05, media sui semi:

| | marginale | per classe | per classe × centro |
|---|---|---|---|
| **Copertura dei positivi, centro peggiore** (primario, ≥ 0,90) | 0,938 (Rijnstate) | 0,933 (CWZ) | 0,979 (Rijnstate) |
| **Negativi di Utrecht con risposta {1}** (primario; E6 alla soglia 0,5: 0,508) | 0,453 | 0,366 | 0,187 |
| Negativi di CWZ con risposta {1} (E6: 0,230) | 0,144 | 0,138 | 0,190 |
| Negativi di Radboud con risposta {1} (E6: 0,089) | 0,048 | 0,132 | 0,073 |
| Rinvii, centro che ne ha di più | 0,233 (CWZ) | 0,136 (Radboud) | 0,516 (CWZ) |
| Rinvii a Utrecht | 0,060 | 0,058 | 0,507 |
| Tumori persi, centro peggiore | 0,062 (Rijnstate) | 0,062 (Rijnstate) | 0,021 (Rijnstate) |

**Esito secondo il criterio: scelta la variante «per classe».** Tutte e tre sono utilizzabili (copertura
dei positivi ≥ 0,90 su ogni centro escluso); «per classe» ha meno rinvii sul centro peggiore.

**Lettura** (oltre il criterio, quindi ipotesi).

- **Risposta (a) sì, risposta (b) no.** La copertura dei positivi regge su ogni centro escluso, ma i
  negativi spostati di Utrecht **non diventano rinvii**: con «per classe» il 37% riceve comunque la
  risposta «positivo», e i rinvii a Utrecht sono solo il 6%. Nel seme 1 i negativi con risposta {1}
  sono il 91%, come i falsi positivi di E6. Lo spostamento non è incertezza: il modello è *sicuro* che
  quei negativi siano tumori, e un insieme conformal non lo può vedere. È un argomento per E9 (lo
  spostamento è di livello) e per un controllo OOD a monte (M3), non per un α diverso.
- **Le risposte negative reggono su ogni centro.** Tumori persi ≤ 6% ovunque, NPV ≥ 0,98 su ogni centro
  escluso per π ≤ 0,30. I tumori persi sono sempre gli stessi vetrini, e sono tutti **micrometastasi**:
  `patient_067_node_4` e `patient_073_node_3` (Rijnstate, in tutti i semi), `patient_020_node_1`,
  `patient_020_node_2` e `patient_021_node_4` (CWZ, in alcuni semi). `patient_067_node_4` è uno dei vetrini
  del punto cieco della griglia (C17 §1: 31% del tumore nelle tile). Le risposte positive invece non
  reggono su uno scanner nuovo: PPV di Utrecht 0,55 a π = 0,20. Lo strumento oggi è credibile per
  **escludere**, non per confermare.
- **Garantire la sensibilità costa specificità dove E6 andava bene.** Il quantile dei positivi può
  portare la soglia di {1} sotto 0,5 (Rijnstate, seme 2: p ≥ 0,39): a Radboud «per classe» dà più
  negativi con risposta {1} di E6 (0,132 contro 0,089).
- **Con due classi l'insieme vuoto non vuol dire "anomalo".** È vuoto quando i due quantili lasciano
  scoperta la zona centrale delle probabilità, cioè per i vetrini incerti; a α = 0,10 quasi tutti i
  rinvii sono di questo tipo. Il motivo "anomalo" fissato nel protocollo (punto *Punteggio e insiemi*)
  è sbagliato: entrambi i tipi di rinvio sono "incerto" (nota del 20/10/2026, dopo i risultati). Il
  rinvio per vetrino anomalo resta compito del controllore (M3).
- **Il quantile più prudente per centro** dimezza i negativi di Utrecht con risposta {1} (0,187), ma
  rinvia circa metà dei vetrini su tre centri su quattro.

**Conseguenze.**

1. Come previsto dal criterio, la testa restituirà anche l'insieme «per classe» con il motivo del
   rinvio (quantili dalle logit fuori fold della CV, applicati al modello finale), e la voce
   "Copertura conformal" della batteria passa a "sì" con la regola di questo criterio nel gate. Da
   implementare: ancora nessun modello registrato con gli insiemi.
2. Il conformal non risolve lo spostamento dei negativi su uno scanner nuovo: E9 resta necessario, e la
   combinazione offset + conformal con k = 20 negativi è il protocollo naturale dopo E9.
3. Da portare ai patologi: con un'installazione senza vetrini locali, le risposte «negativo» sono
   affidabili su ogni centro misurato (micrometastasi a parte), quelle «positivo» no.

## E11 — Offset e insiemi conformal insieme

Protocollo fissato il 21/10/2026, dopo i risultati di E9 ed E10 e prima di ogni calcolo che li
combini. Riferimenti: E10 «per classe» (la variante scelta) ed E9 `offset solo in discesa`.

**Domanda.** E9 riporta i negativi di un centro nuovo al livello dei centri visti con pochi vetrini, ma
alla soglia 0,5 perde sensibilità, quasi tutta micrometastasi; E10 garantisce la copertura dei positivi
ma lascia i negativi spostati di Utrecht come risposte «positivo». Applicando gli insiemi conformal «per
classe» alle logit **corrette** dall'offset, le micrometastasi perse da E9 diventano **rinvii** invece di
risposte «negativo», mantenendo il guadagno di specificità di E9? Quanti rinvii costa?

**Ipotesi** (dai risultati di E9, quindi dichiarata come tale). Dopo la correzione i negativi stanno
intorno a −7 e le micrometastasi perse intorno a 0: una probabilità vicina a 0,5, che gli insiemi per
classe dovrebbero mettere in `{0, 1}`.

**Scelte prese dai risultati precedenti** (dichiarate: non sono a priori). La variante dell'offset è
`solo in discesa`, l'unica che regge il trasferimento tra dataset di Radboud in E9. La variante conformal
è «per classe», scelta in E10. Nessun'altra combinazione entra in questo esperimento.

**Dati.** La riesecuzione di E6 di E10 (`data/reports/experiments/e10/e6/predictions.csv`), con le logit
LOCO del centro escluso, le logit dei fold interni dei centri di training (`loco-calibration`) e la
temperatura di ogni rotazione. Nessun nuovo training; LPON non viene letto. Positivi per centro
(macro / micro): CWZ 12 / 23, Radboud 60 / 60, Rijnstate 19 / 13, Utrecht 50 / 38.

**Procedura**, per ogni seme, rotazione, k ∈ {3, 5, 10, 20} e una di 200 estrazioni di k negativi del
centro escluso (generatore con seme 0, estrazioni nuove rispetto a E9):

1. offset come in E9: b' = max(mediana dei k negativi − m_ref, 0), con m_ref = mediana dei negativi nei
   fold interni della rotazione;
2. probabilità corrette degli altri vetrini del centro: p = sigmoide((logit − b') / *T*);
3. insiemi conformal come in E10, con il punteggio s = 1 − p(y) e i quantili per classe.

Due varianti, che differiscono solo per il quantile dei negativi q₀:

1. `offset + per classe`: q₀ e q₁ dai fold interni dei centri di training, come in E10 (non dipendono
   dall'estrazione). Tutti i k.
2. `offset + per classe, negativi locali`: q₁ come sopra; q₀ dai k negativi estratti, con le loro logit
   corrette. Solo k = 20, perché per α = 0,05 servono almeno 19 vetrini (con k < 19 l'indice del quantile
   supera n e il negativo entra in ogni insieme).

Ogni estrazione si valuta sugli altri vetrini del centro (tutti i positivi e i negativi non estratti).
Esito per vetrino come in E10: `{1}` risposta positivo, `{0}` risposta negativo, `{0, 1}` e `{}` rinvio
(per due classi l'insieme vuoto è un altro caso di incertezza, nota di E10).

Livelli: α = 0,05 (principale), α = 0,10.

**Riferimenti, sugli stessi vetrini di valutazione di ogni estrazione.** E10 «per classe» senza offset;
E9 `offset solo in discesa` alla soglia 0,5; E6 alla soglia 0,5.

**Esiti** (media sulle 200 estrazioni, poi sui tre semi; per centro escluso).

- Primari:
  - **tumori persi** (positivi con risposta `{0}`) su ogni centro escluso, e la quota non persa
    (1 − tumori persi) accanto alla sensibilità dello stesso centro visto in training (CV di E6);
  - negativi con risposta `{1}` sul centro escluso peggiore, accanto a E10 «per classe».
- Vincoli e costo:
  - copertura dei positivi su ogni centro escluso;
  - tasso di rinvio per centro escluso;
  - 10° percentile sulle estrazioni dei negativi con risposta `{1}`, sul centro peggiore di E10
    «per classe».
- Secondari:
  - tumori persi e rinvii separati per micrometastasi e macrometastasi (`reference_diagnosis` del
    cohort);
  - copertura dei negativi, dimensione media dell'insieme, errore sulle risposte;
  - alla prevalenza, con la griglia di E10 (π ∈ {0,05; 0,10; 0,20; 0,30} e quella del cohort): rinvii,
    PPV e NPV;
  - α = 0,10.

**Criterio** (fissato ora). A α = 0,05, una variante con un dato k è **proponibile** se, in media su
estrazioni e semi:

1. la copertura dei positivi è ≥ 0,90 su ogni centro escluso (la regola di E10);
2. su ogni centro escluso la quota di positivi non persi è almeno la sensibilità dello stesso centro
   visto in training meno 0,05 (il vincolo di E9, dopo la modifica);
3. i negativi con risposta `{1}` sul centro peggiore sono almeno **0,10** sotto quelli di E10 «per
   classe» sugli stessi vetrini;
4. il 10° percentile dei negativi con risposta `{1}` sul centro peggiore di E10 «per classe» non supera
   il valore di E10 su quel centro (un'estrazione sfortunata non peggiora rispetto a non correggere);
5. il tasso di rinvio di nessun centro escluso supera di più di **0,10** quello di E10 «per classe» sullo
   stesso centro.

*Modifica del 21/10/2026, prima dell'esecuzione.* Nella condizione 4 (e nella voce corrispondente degli
esiti) il percentile è il **90°**, non il 10°: per una quota in cui più alto è peggio, l'estrazione
sfortunata è quella alta. È l'equivalente del 10° percentile della specificità usato in E9, che era
l'intento; scrivendo lo script è emerso l'errore.

Il quinto vincolo esclude la soluzione banale (rinviare tutto). Il tasso di rinvio accettabile in
assoluto resta una decisione dei patologi, sui numeri alla prevalenza.

Per ogni variante si riporta il k minimo proponibile; si propone la combinazione con k minore, a parità
di k la variante 1 (non richiede quantili locali).

**Che cosa decide.** Come E9, misura. Usare vetrini del centro all'installazione resta una decisione dei
patologi (rivede "solo calibrazione globale"). Se una combinazione è proponibile, i numeri da portare
sono: quanti negativi confermati servono, quanti rinvii, quante micrometastasi restano risposte
«negativo».

**Limiti.**

- Gli stessi di E9 (negativi estratti dagli stessi vetrini storici del leave-one-centre-out, un solo
  spostamento additivo) ed E10 (scambiabilità violata sul centro nuovo, punteggi di calibrazione dai
  modelli dei fold interni).
- I quantili della variante 1 vengono dai centri di training: dopo la correzione il centro nuovo ha lo
  stesso livello dei negativi, non necessariamente la stessa dispersione.
- Pochi positivi per centro e ancora meno micrometastasi (Rijnstate 13): il sottogruppo micro è
  descrittivo.
- Tre semi, quattro rotazioni, un backbone (va rivalidato con H-optimus-0).

**Codice.** Il calcolo sarà in `experiments/e11_offset_conformal.py`, che riusa le funzioni di
`e9_offset.py` ed `e10_conformal.py`; lo script si prova su dati sintetici e si committa prima di
eseguirlo.

**Risultati** (21/10/2026, codice `35f5986`, sei secondi di calcolo sulla riesecuzione di E6 di E10;
risultati in `data/reports/experiments/e11/summary.md`, da `experiments/e11_offset_conformal.py`
committato prima dell'esecuzione, con la modifica al percentile annotata sopra). Controllo della
riesecuzione superato.

α = 0,05, k = 20, media su 200 estrazioni e tre semi, sugli stessi vetrini di valutazione:

| | V1 offset + per classe | V2 negativi locali | E10 per classe | E9 offset |
|---|---|---|---|---|
| Negativi con risposta {1}, Utrecht | 0,012 | 0,012 | 0,366 | 0,020 |
| Negativi con risposta {1}, centro peggiore | 0,051 (Radboud) | 0,021 (Radboud) | 0,366 (Utrecht) | 0,023 (Radboud) |
| **Copertura dei positivi, CWZ** (≥ 0,90) | **0,779** | **0,779** | 0,933 | — |
| Tumori persi, CWZ (sensibilità del centro visto 0,924) | 0,158 | 0,107 | 0,038 | 0,140 |
| Tumori persi, Utrecht (visto 0,992) | 0,077 | 0,046 | 0,023 | 0,088 |
| Micrometastasi perse, CWZ / Utrecht | 0,224 / 0,150 | 0,163 / 0,100 | 0,058 / 0,053 | 0,212 / 0,167 |
| Micrometastasi rinviate, CWZ / Utrecht | 0,155 / 0,056 | 0,157 / 0,072 | 0,101 / 0,009 | — |
| Rinvii, CWZ / Utrecht | 0,068 / 0,023 | 0,077 / 0,043 | 0,100 / 0,055 | — |

**Esito secondo il criterio: nessuna combinazione proponibile.** V1 non supera la copertura dei positivi
(CWZ 0,78) né il vincolo sui tumori persi, per ogni k; V2 (solo k = 20) supera i tumori persi (margine
minimo −0,039, Utrecht) ma non la copertura (CWZ 0,78). I falsi positivi, la cattiva estrazione e i
rinvii passano per tutte.

**Lettura** (oltre il criterio, quindi ipotesi).

- **L'ipotesi è smentita, e la sua premessa era sbagliata** (correzione annotata in E9). Dopo l'offset le
  micrometastasi perse non sono incerte: le loro logit corrette hanno mediana −4,2 a CWZ e −2,1 a
  Utrecht. Un insieme conformal rinvia ciò che il modello non sa decidere, non ciò che vede come un
  negativo chiaro. Il conformal sulle logit corrette perde quasi gli stessi tumori della sola correzione
  (V1 0,158 contro E9 0,140 a CWZ).
- **V1 perde a volte più di E9.** Il quantile dei negativi dei centri di training può superare 0,5 (in
  E10 fino a 0,84 a CWZ): la zona della risposta «negativo» si allarga sopra la soglia di E9.
- **I negativi locali aiutano** (V2: tumori persi a Utrecht da 0,077 a 0,046, micrometastasi da 0,150 a
  0,100), perché il quantile stimato sul centro è più stretto. Non bastano a CWZ.
- **Il problema non è di calibrazione.** Sul centro visto in training la sensibilità di CWZ è 0,92; sul
  centro escluso le micrometastasi superano la soglia in E6 soprattutto grazie allo spostamento di tutto
  il vetrino. Tolto lo spostamento, il modello LOCO non le vede: la logit del vetrino, dominata dal tessuto
  normale, non porta il segnale di un tumore piccolo su uno scanner nuovo.

**Conseguenze.**

1. Con E9, E10 ed E11 le correzioni a valle sulla logit del vetrino (temperatura, offset, insiemi
   conformal, e le loro combinazioni) sono esaurite per questo problema: spostano lo scambio tra
   specificità e micrometastasi, non lo eliminano.
2. Per i patologi restano due configurazioni, entrambe senza criterio superato. **Senza vetrini locali**
   (E10 «per classe»): micrometastasi perse circa 5–6%, ma il 37% dei negativi di Utrecht ha risposta
   «positivo». **Con 20 negativi locali** (V2): negativi con risposta «positivo» ≤ 2%, ma micrometastasi
   perse 10–16% a Utrecht e CWZ.
3. Il passo successivo è sul segnale, non sulla calibrazione: un punteggio per i tumori piccoli che non
   dipenda dalla media del vetrino (attenzione o punteggio per tile, il secondo candidato dopo E9), oppure
   il backbone dell'MVP (H-optimus-0), che può separare meglio tumore e scanner a livello di tile.

## E12 — Un punteggio del vetrino dalle tile più sospette

Protocollo fissato il 21/10/2026, dopo E11 e prima di ogni calcolo di punteggi per tile sul
leave-one-centre-out. Riferimento: E6 (ricetta vuota).

**Domanda.** E9–E11 hanno mostrato che su un centro nuovo le micrometastasi superano la soglia solo
grazie allo spostamento di tutto il vetrino: tolto lo spostamento, la logit del vetrino le vede come
negativi. Un punteggio fatto dalle **poche tile più sospette** del vetrino, invece che dalla media su
tutte, separa le micrometastasi di un centro mai visto dai negativi di quel centro meglio della logit
del vetrino, con una soglia scelta senza quel centro?

**Perché un punteggio dalle tile.** La testa dell'ABMIL è lineare sulla rappresentazione pooled
z = Σ wᵢ hᵢ: la logit del vetrino è esattamente la **media pesata dall'attenzione delle logit delle
singole tile**, sᵢ = W·hᵢ + b. Una micrometastasi occupa poche tile (la più piccola, 0,2 mm, ne copre
2–3 da 0,0125 mm²) su una mediana di circa 9 500 per vetrino: nella media pesata pesa poco, e lo
spostamento del tessuto normale di un centro nuovo pesa su tutte. Un massimo o una media delle prime k
tile non diluisce il tumore piccolo; resta da misurare quanto lo spostamento alzi anche le tile normali
più alte (E2: il centro è leggibile da una singola tile).

**Punteggi** (tutti a livello di vetrino, tutti calcolati nel leave-one-centre-out senza il centro
escluso).

1. `logit del vetrino` (riferimento): la logit ABMIL di E6.
2. `istanza ABMIL, top-5`: media delle 5 logit d'istanza sᵢ più alte del vetrino, dallo **stesso
   modello** della rotazione. Nessun modello in più: in produzione è lo stesso ABMIL.
3. `classificatore di tile, top-5`: media delle 5 log-odds più alte di una regressione logistica
   tumore/normale sugli embedding delle tile, addestrata per ogni rotazione sui soli centri di training:
   - tile tumorali (`label = tumor`; le tile di bordo escluse) dai positivi **con annotazione
     completa** (`exhaustive_annot`), fino a 500 per vetrino;
   - tile normali dai vetrini negativi, fino a 200 per vetrino;
   - feature standardizzate sulle tile di training; L2 con C = 1; classi pesate (`balanced`);
     campionamento delle tile con il seme del run (0, 1, 2).

k = 5 è fissato ora: copre la micrometastasi più piccola (2–3 tile) con un margine contro il rumore
di una singola tile. k = 1 e k = 20 sono secondari, non si sceglie tra loro a posteriori.

**Soglia, senza il centro escluso.** Per ogni punteggio e rotazione, τ è il valore che lascia sopra il
95% dei positivi dei centri di training nei loro punteggi fuori fold (i 3 fold interni di E6:
`cv_fold mod 3`): il ⌊(n + 1) · 0,05⌋-esimo più piccolo tra gli n positivi. È la stessa regola per i
tre punteggi, quindi il confronto non dipende dalla scala. Per la logit del vetrino vale la stessa
regola (non la soglia 0,5 di E6), così che i tre partano dalla stessa sensibilità sui centri visti.

**Dati e codice.**

- Classificatore di tile: gli embedding Phikon e le etichette delle tile (`<vetrino>.parquet`) già su
  disco, nessun nuovo training ABMIL; modelli dei fold interni e di rotazione addestrati come sopra.
- Istanza ABMIL: le logit d'istanza non sono salvate. Il protocollo registra, per ogni vetrino valutato
  (LOCO e fold interni `loco-calibration`), le 20 logit d'istanza più alte e la loro posizione; E6 si
  riesegue (circa 5 ore, `mil.register=false`, report in `data/reports/experiments/e12/e6/`) e le logit
  del vetrino devono coincidere con quelle salvate (come in E10).
- Analisi in `experiments/e12_tile_score.py`, provata su dati sintetici e committata prima
  dell'esecuzione.

**Esiti** (per centro escluso, media sui tre semi).

- Primari, alla soglia τ:
  - sensibilità sulle **micrometastasi**, sul centro escluso peggiore;
  - specificità sul centro escluso peggiore.
- Secondari:
  - sensibilità sulle macrometastasi e su tutti i positivi;
  - AUROC per centro escluso, tutti i positivi contro i negativi e micrometastasi contro negativi;
  - mediana del punteggio dei negativi del centro escluso accanto a quella dei negativi dei centri di
    training (la misura dello spostamento di E6, per ogni punteggio);
  - k = 1 e k = 20;
  - **localizzazione**: sui positivi annotati del centro escluso, quota dei vetrini in cui almeno una
    delle 5 tile più alte è tumorale (il punteggio guarda il tumore, non un artefatto);
  - tempo di calcolo per vetrino.

**Criterio** (fissato ora). Un punteggio delle tile è un **segnale candidato** se, in media sui semi,
rispetto alla logit del vetrino con la stessa regola di soglia:

1. la sensibilità sulle micrometastasi del centro escluso peggiore sale di almeno **0,10**;
2. la specificità del centro escluso peggiore non scende più di **0,05**;
3. l'AUROC peggiore (tutti i positivi) non scende più di **0,01**.

Se entrambi sono candidati si sceglie quello con la sensibilità sulle micrometastasi peggiore più alta;
a parità entro 0,02, l'istanza ABMIL (nessun modello in più da validare e mantenere).

**Che cosa decide.** Solo se esiste un segnale dalle tile che vale la pena combinare con la decisione
del vetrino. La combinazione (per esempio rinvio se il punteggio delle tile supera τ e la logit corretta
no, con l'offset di E9 e gli insiemi di E10) è un protocollo successivo, non una scelta a posteriori qui.

**Limiti.**

- Annotazioni complete solo per una parte dei positivi (CWZ 8, Rijnstate 6): quando è escluso Utrecht,
  il classificatore impara il tumore soprattutto da Radboud; lo sbilanciamento di centro tra tile
  tumorali e normali può far imparare anche il centro (E2). La valutazione usa le etichette del vetrino,
  quindi non ne dipende.
- Il punto cieco della griglia (C17 §1): il tumore fuori dalle tile non può essere trovato da nessun
  punteggio; i vetrini noti si riportano come sottogruppo.
- Il massimo su migliaia di tile è sensibile ad artefatti (pieghe, inchiostro, sfocatura), che il
  controllo qualità non rileva ancora (GrandQC non è integrato); la localizzazione serve a vederlo.
- I tre semi rappresentano il training ABMIL e il campionamento delle tile, non la variabilità tra
  vetrini; un backbone (va rivalidato con H-optimus-0).

**Risultati** (21/10/2026, codice `0f9f02f` per l'analisi, `6d08eb7` per la riesecuzione di E6 con le
logit d'istanza: 5 ore e 33 minuti; classificatore di tile 6 minuti, 48 modelli; risultati in
`data/reports/experiments/e12/summary.md`). **Controllo superato**: le logit del vetrino della riesecuzione
coincidono con E6 (differenza 0 su 4626 righe), quindi registrare le istanze non cambia il modello.

k = 5, soglia τ dai centri di training, media sui tre semi:

| | Logit del vetrino | Istanza ABMIL | Classificatore di tile |
|---|---|---|---|
| **Sensibilità micro, centro peggiore** | 0,846 (Rijnstate) | 0,872 (Rijnstate) | 0,711 (Utrecht) |
| **Specificità, centro peggiore** | 0,606 (Utrecht) | **0,238** (Utrecht) | 0,684 (Radboud) |
| AUROC, centro peggiore | 0,976 | 0,968 | 0,908 |
| Mediana dei negativi, Utrecht escluso (training) | −0,71 (−6,74) | 2,71 (−1,59) | 2,03 (3,16) |
| Mediana dei negativi, CWZ escluso (training) | −2,51 (−7,51) | 0,70 (−1,52) | 6,02 (3,83) |
| Localizzazione (una delle 5 tile più alte è tumore) | — | 0,83–0,94 | 0,75–0,94 |

**Esito secondo il criterio: nessun segnale candidato.** L'istanza ABMIL guadagna 0,03 di sensibilità
micro (serve 0,10) e perde 0,37 di specificità peggiore; il classificatore di tile perde 0,14 di
sensibilità micro e 0,07 di AUROC peggiore, pur guadagnando 0,08 di specificità.

**Lettura** (oltre il criterio, quindi ipotesi).

- **Con la soglia dai centri di training, la logit del vetrino trova già le micrometastasi** di un centro
  nuovo: sensibilità micro tra 0,85 e 0,97, persa solo a Rijnstate (2 vetrini su 13 in tutti i semi, gli
  stessi di E10, uno è del punto cieco). La perdita di micrometastasi di E9–E11 era l'effetto della
  correzione dell'offset, non un limite della logit. Il problema della logit resta la specificità
  (Utrecht 0,61, con un seme a 0,006).
- **Le logit d'istanza dell'ABMIL sono più spostate della logit del vetrino**: i negativi di Utrecht
  salgono di 4,3 (contro 6,0 della logit del vetrino, su una scala più stretta) e le 5 tile più alte di un
  vetrino negativo di un centro nuovo superano la soglia nel 76% dei casi. L'ABMIL non impara un
  rilevatore di tumore per tile, ma un punteggio che porta anche il centro, e il massimo su migliaia di
  tile lo amplifica. Con k = 20 la specificità di Utrecht è 0,004.
- **Il classificatore supervisionato è meno spostato, ma in direzioni diverse per centro**: i negativi
  salgono a CWZ (+2,2) e Radboud (+1,9) e **scendono** a Utrecht (−1,1). A Utrecht, scanner Hamamatsu
  mai visto quando è escluso, scende tutto, anche il tumore: sensibilità micro 0,71. È E2 a livello di
  tile: il centro è leggibile da una tile, e qualunque punteggio imparato sui centri di training si sposta
  su uno scanner nuovo, in una direzione che non si conosce prima.
- **Le tile più alte sono quasi sempre tumore** (localizzazione 0,83–0,94 per l'istanza ABMIL): sui
  positivi entrambi i punteggi guardano il posto giusto. Il problema sono le tile più alte dei negativi.

**Conseguenze.**

1. Nessun punteggio dalle tile entra in un protocollo di combinazione: non c'è un segnale da combinare.
2. Dopo E6–E12, ricette di training, correzioni a valle e punteggi dalle tile si fermano sullo stesso
   punto: negli embedding Phikon lo scanner di un centro nuovo sposta il tessuto normale, a livello di
   vetrino e di tile. La leva che resta è a monte del modello: il backbone (H-optimus-0, previsto per
   l'MVP e addestrato su più centri e scanner) o la normalizzazione del colore prima dell'embedding;
   entrambe richiedono una nuova estrazione.
3. Per i patologi: alla soglia che garantisce il 95% di sensibilità sui centri visti, la logit del
   vetrino senza correzioni perde poche micrometastasi su un centro nuovo e dà molti falsi positivi su
   uno scanner diverso. Coerente con E10: le risposte «negativo» sono affidabili, quelle «positivo» no.

## E13 — Pilota: normalizzazione del colore prima dell'embedding

Protocollo fissato il 21/10/2026, dopo E12 e prima di ogni embedding di tile normalizzate. Riferimento:
gli stessi vetrini senza normalizzazione, ri-letti con lo stesso codice.

**Domanda.** E6–E12 si fermano sullo stesso punto: negli embedding Phikon lo scanner di un centro
nuovo sposta il tessuto normale, già a livello di tile. Se il colore delle tile viene normalizzato
**prima** dell'embedding, un rilevatore di tumore per tile addestrato su tre centri sposta meno i normali
del quarto, senza perdere la capacità di distinguere il tumore? È il pilota che decide se rifare
l'estrazione di tutto lo sviluppo.

**Perché un pilota.** Rifare l'estrazione vuol dire riscaricare i vetrini (752 GB di CAMELYON16, 1 259 GB
dei vetrini di sviluppo di CAMELYON17) e circa 24 ore di embedding (11 ms per tile). H-optimus-0 non è
eseguibile in locale. Il pilota costa 143 GB di download, un vetrino alla volta, e circa un'ora di
embedding. E4 ha già escluso la normalizzazione *negli embedding* (media del vetrino); qui la
normalizzazione è sui pixel, prima del backbone.

**Campione** (fissato ora, `experiments/data/e13_sample.csv`, generatore con seme 0). Per ogni centro di
sviluppo 8 negativi e 3 positivi con annotazione completa; a Radboud e Utrecht divisi tra CAMELYON16 e
CAMELYON17 (negativi 4 + 4, positivi 2 + 1): 44 vetrini, 32 negativi e 12 positivi. **LPON non viene
letto.** Per vetrino, dalle tile già nella griglia (stesse coordinate, stesso livello di lettura di
`td task=stream`): fino a 1 000 tile normali (`label = normal`) a caso, e nei positivi anche fino a 500
tile tumorali (`label = tumor`); le tile di bordo escluse.

**Condizioni** (stesso backbone Phikon `057cc0295895`, stessa trasformazione).

1. `grezzo`: le tile come oggi. Controllo: devono coincidere con gli embedding salvati (differenza
   massima ≤ 1e-2 in float16); se non coincidono, il pilota si ferma e il percorso di lettura va capito
   prima.
2. `reinhard` (Reinhard et al., 2001): media e deviazione standard per canale nello spazio Lab, stimate
   sul **vetrino** (dalle sue tile campionate, solo pixel di tessuto) e riportate a quelle di
   riferimento.
3. `macenko` (Macenko et al., 2009): matrice delle colorazioni H&E e concentrazioni massime (99°
   percentile) stimate sul **vetrino** (β = 0,15, α = 1), riportate a quelle di riferimento.

**Riferimento del colore, senza il centro escluso.** Per ogni rotazione, il riferimento è la media dei
parametri per vetrino (Lab per Reinhard; matrice e massimi per Macenko) sui vetrini del campione dei soli
centri di training. Ogni tile ha quindi 1 embedding grezzo e 4 + 4 normalizzati (uno per rotazione e
metodo). Implementazione propria in numpy (nessuna dipendenza nuova da far passare dal controllo delle
licenze), con test su immagini sintetiche.

**Misure, a livello di tile, leave-one-centre-out sui 4 centri** (per ogni condizione; in ogni rotazione
gli embedding normalizzati con il riferimento di quella rotazione):

- rilevatore di tumore per tile: regressione logistica come in E12 (standardizzata, L2, C = 1, classi
  pesate), addestrata sulle tile dei 3 centri di training: tumorali dai loro positivi, normali dai loro
  negativi. Soglia τ: lascia sopra il 95% delle tile tumorali di training;
- sul centro escluso: specificità per tile (tile normali dei negativi sotto τ), AUROC tumore contro
  normale per tile (positivi del centro), **spostamento dei normali** = mediana delle log-odds delle tile
  normali dei negativi del centro escluso meno la mediana sulle tile normali dei negativi di training.

**Esiti.**

- Primario: specificità per tile sul centro escluso peggiore.
- Vincolo: AUROC per tile sul centro escluso peggiore.
- Secondari:
  - spostamento dei normali per centro escluso;
  - probe sul centro (come E2): AUROC macro one-vs-rest dalle tile normali dei negativi, 5 fold
    raggruppati per vetrino, per condizione (con il riferimento della rotazione di Radboud escluso per i
    normalizzati, fissato ora);
  - quota dei 10 vicini (coseno) dello stesso centro, da vetrini diversi (la misura di E2);
  - statistiche di colore per centro prima e dopo (media Lab, densità H ed E);
  - tempo di normalizzazione per tile.

Le stime per tile sono raggruppate per vetrino: una media su 8 vetrini per centro, non su 8 000 tile
indipendenti; si riporta anche la specificità per vetrino del centro escluso (mediana sui vetrini).

**Criterio** (fissato ora). Un metodo è **promettente**, e giustifica la nuova estrazione di tutto lo
sviluppo, se rispetto a `grezzo`:

1. la specificità per tile sul centro escluso peggiore sale di almeno **0,10**;
2. l'AUROC per tile sul centro escluso peggiore non scende più di **0,01**.

Se entrambi sono promettenti si sceglie quello con la specificità peggiore più alta; a parità entro 0,02,
Reinhard (più semplice, meno parametri stimati per vetrino). Se nessuno è promettente, la normalizzazione
del colore non va all'estrazione completa.

**Che cosa decide e che cosa no.** Solo se rifare l'estrazione. Il giudizio a livello di vetrino (E6 con
gli embedding normalizzati, e il confronto con E6) è un protocollo successivo, sull'estrazione completa.

**Limiti.**

- 8 negativi e 3 positivi per centro: la variabilità tra vetrini domina, e CWZ e Rijnstate hanno solo 3
  positivi annotati da cui imparare e misurare il tumore.
- Un rilevatore lineare sulle tile non è l'ABMIL; il pilota misura lo spostamento negli embedding, che è
  ciò che E6–E12 indicano come causa, non le prestazioni della testa.
- Un riferimento medio per rotazione, non uno scelto per qualità; le stime per vetrino possono fallire
  su vetrini con poco tessuto o molta penna (GrandQC non è integrato): i fallimenti si contano e si
  riportano.
- Un backbone; la normalizzazione può interagire diversamente con H-optimus-0.

**Codice.** `experiments/e13_stain.py` (download un vetrino alla volta con il codice di `td task=stream`,
lettura delle tile, normalizzazioni, embedding, misure), con la normalizzazione in
`src/tumordetector/wsi/stain.py` e i suoi test; provato su dati sintetici e committato prima
dell'esecuzione.

## E14 — Quanti vetrini di un centro nuovo servono nel training

Protocollo fissato il 22/10/2026, dopo E13 (protocollo) e prima di ogni addestramento con vetrini del
centro escluso. Riferimenti: E6 (stessa ricetta, vuota), E9 (offset con i negativi del centro). E13 resta
fissato ma in pausa: viene dopo E14 (motivo nella *Lettura* qui sotto).

**Domanda.** E6–E12 mostrano che un centro *visto* in training si comporta bene (CV di E6: specificità
0,94–0,98, sensibilità 0,92–0,99) e uno *mai visto* no (Utrecht escluso: specificità 0,49), e che nessuna
ricetta di training o correzione a valle, senza vetrini del centro, chiude la distanza. Una pipeline che
nel tempo raccoglie vetrini diagnosticati da centri nuovi (uso silente, M9) e li rimette nel training
la chiude per costruzione, *se* ne bastano pochi. **Quanti vetrini con diagnosi di un centro nuovo,
aggiunti al training dell'ABMIL, servono perché quel centro si comporti come un centro visto?** E rende
di più riaddestrare con quei vetrini o usarne i negativi per l'offset di E9?

**Che cosa decide e che cosa no.** E14 misura il costo d'ingresso di un centro nella pipeline: quanti
casi di uso silente prima che il centro riceva risposte. Non decide l'adozione del percorso (accordi sui
dati, regole sugli aggiornamenti del modello: progetto in
[training-multicentro.md](training-multicentro.md), *Ingresso di un centro nuovo*), né rivede da solo la
decisione "solo calibrazione globale": il centro entra nello sviluppo, non viene ricalibrato.

**Dati.** Cohort `ln_metastasis` v1, 771 vetrini di sviluppo, Phikon `057cc0295895`. LPON non viene
letto. Le etichette usate sono solo quelle del vetrino (`reference_diagnosis` → `label`), come quelle che
darebbe il patologo nell'uso silente: nessuna annotazione.

**Estrazioni.** Per ogni centro *c* (le 4 rotazioni del leave-one-centre-out) e per ogni estrazione
d ∈ {0, 1, 2} (generatore con seme 0, fissato): una permutazione casuale dei **pazienti** di *c* (un
paziente ha fino a 5 vetrini in CAMELYON17; i pazienti di CAMELYON16 e 17 dello stesso centro si trattano
come distinti, C17 §3). Per n ∈ {5, 10, 20, 40}, i vetrini aggiunti sono quelli dei primi pazienti della
permutazione finché se ne contano almeno n (il numero esatto e i positivi tra essi si riportano). Le
estrazioni sono **annidate**: i vetrini di n = 5 stanno in quelli di n = 10, e così via, come in una
raccolta che cresce. Non si stratifica per classe: un centro nuovo dà i casi che arrivano.

**Vetrini di valutazione** (per centro ed estrazione, fissi al variare di n): tutti i vetrini di *c* dei
pazienti **non** inclusi con n = 40. Così ogni n e ogni riferimento si confrontano sugli stessi vetrini.
Con CWZ (93 vetrini, 20 pazienti) restano circa 50 vetrini, di cui circa 20 positivi.

**Modello.** Come E6: ABMIL con gli iperparametri di `conf/config.yaml`, ricetta vuota, `pos_weight`
globale, un thread, semi di training {0, 1, 2}. Training: i vetrini di sviluppo degli altri tre centri
+ gli n vetrini aggiunti di *c*. Nessun peso in più per il centro nuovo (vedi *Limiti*). Per ogni
centro, n ed estrazione, tre semi: 4 × 4 × 3 × 3 = **144 modelli**.

**Riferimenti** (sugli stessi vetrini di valutazione, dalla riesecuzione di E6 di E10,
`data/reports/experiments/e10/e6/predictions.csv`):

- **n = 0**: logit LOCO di E6 (centro mai visto);
- **centro visto**: logit fuori fold della CV di E6 (il centro contribuisce circa l'80% dei suoi vetrini
  al training);
- **offset**: la correzione di E9, variante `solo in discesa`, con i **negativi tra gli n vetrini
  aggiunti** come k, applicata alle logit LOCO di E6 (non si stima se l'estrazione non ha negativi). È
  l'alternativa senza riaddestramento con gli stessi vetrini.

**Esiti** (soglia 0,5 sulla logit, che non dipende dalla temperatura; per centro, per n; media sui tre
semi e sulle tre estrazioni, e i 9 valori nel report).

- Primari: specificità, sensibilità, sensibilità sulle micrometastasi, sul centro *c*.
- Secondari:
  - mediana delle logit dei negativi e dei positivi di *c* (la misura di E6), accanto a quelle in CV;
  - AUROC sul centro;
  - ECE calibrata con la temperatura della rotazione di E6 (gruppo `loco-calibration`): una stima, perché
    la temperatura non è ristimata con i vetrini aggiunti;
  - frazione di distanza chiusa: (specificità_n − specificità_0) / (specificità_visto − specificità_0),
    per i centri dove la distanza è almeno 0,05;
  - sensibilità sulle macrometastasi e specificità per dominio (Radboud e Utrecht: CAMELYON16 e 17).

**Criterio** (fissato ora). Per ogni centro, n è **sufficiente** se, in media su semi ed estrazioni, sui
vetrini di valutazione:

1. la specificità non è sotto quella del centro visto di più di **0,05**;
2. la sensibilità non è sotto quella del centro visto di più di **0,05** (il vincolo di E9);
3. la sensibilità sulle micrometastasi non è sotto quella del centro visto di più di **0,10** (margine più
   largo: circa 5–15 micrometastasi di valutazione per centro);
4. nessuno dei 9 modelli (semi × estrazioni) ha specificità sotto **0,80**, la soglia del gate:
   un'installazione vera fa una sola raccolta e un solo training.

Il **costo d'ingresso** di un centro è il più piccolo n sufficiente (0 se lo è già E6 LOCO). La risposta di
E14 è il costo d'ingresso dei centri dove E6 fallisce (Utrecht, CWZ); se per un centro nessun n ≤ 40 è
sufficiente, si riporta "oltre 40" e la frazione di distanza chiusa a n = 40.

Riaddestrare **rende più dell'offset** a un dato n se rispetta le condizioni 1–3 e l'offset con gli stessi
vetrini no, oppure se le rispettano entrambi e il riaddestramento ha sensibilità sulle micrometastasi più
alta di almeno 0,05.

**Lettura** (fissata ora).

- Costo d'ingresso ≤ 20 vetrini su Utrecht e CWZ: l'ingresso di un centro con l'uso silente è
  praticabile (pochi giorni o settimane di casi); il percorso si progetta per la decisione con i patologi,
  e la normalizzazione del colore (E13) e H-optimus-0 diventano modi di ridurre quel costo, non
  precondizioni.
- Costo d'ingresso 40: praticabile ma lento; E13 torna prioritario.
- Oltre 40, ma con la distanza che si chiude al crescere di n: il centro va visto con più vetrini o
  pesato di più; serve un protocollo con il peso del centro nuovo come variabile.
- Distanza che non si chiude: vedere il centro in training non basta con pochi vetrini; la leva torna a
  monte (E13, H-optimus-0).
- Perché E14 prima di E13: dice se il problema si risolve con i dati che la pipeline raccoglierà comunque,
  senza riscaricare circa 2 TB; e il suo esito decide quanto conta E13.

**Limiti.**

- I vetrini aggiunti vengono dallo stesso insieme storico dei vetrini di valutazione: in esercizio arrivano
  dopo, con una preparazione che può essere cambiata (E3b: i casi di Radboud del 2015 sono un dominio a
  parte). A Radboud e Utrecht le estrazioni mescolano CAMELYON16 e 17; la specificità per dominio lo
  mostra in parte.
- La prevalenza di CAMELYON17 è arricchita (pazienti scelti per stadio pN): un centro clinico dà meno
  positivi, quindi i positivi aggiunti qui sono più del reale per lo stesso n.
- Nessun peso per il centro nuovo: con 5 vetrini su circa 600 il training può ignorarli. È la situazione
  di una pipeline semplice; un peso è una variabile per un protocollo successivo, se la curva lo chiede.
- Temperatura non ristimata: l'ECE è indicativa; le decisioni usano la soglia 0,5, che non ne dipende.
- Tre estrazioni e tre semi: la variabilità tra semi di E6 su Utrecht è grande (specificità da 0,09 a
  0,82); la condizione 4 la controlla, ma 9 modelli sono pochi per un quantile.
- Quattro centri, di cui uno solo con uno scanner diverso (Utrecht, Hamamatsu): il costo d'ingresso di
  uno scanner nuovo si misura in sostanza su un centro. Un backbone.

**Costo.** 144 modelli. In E12 la riesecuzione di E6 (22 modelli per seme, tre semi in parallelo) ha
richiesto circa 5 ore e mezza, circa 15 minuti per modello per processo; con tre processi in parallelo
E14 richiede circa 12 ore. Lo script deve poter riprendere da dove si è fermato (un file di logit per
modello).

**Codice.** `experiments/e14_new_centre.py` (estrazioni, training con il codice del protocollo della
testa, logit dei vetrini di valutazione, analisi) e `experiments/e14_run.sh`; provato su dati sintetici e
committato prima dell'esecuzione sui dati reali.

## E15 — Riconoscere un dominio non visto dagli embedding

Protocollo fissato il 22/10/2026, prima di ogni calcolo di questo esperimento. Riferimenti: E3 ed E3b (punteggi
OOD a distanza su CAMELYON16), E6 (errori della testa sul centro escluso).

**Domanda.** `td task=predict` rinvia oggi i vetrini di un centro o di uno scanner che la versione non ha
visto, leggendo i **metadati**. Un cambio dentro un centro noto (colorazione, protocollo, conversione, un lotto
di casi: `normal_144`, i casi metastatici di Radboud del 2015 in E3b) nei metadati non si vede. Un punteggio
calcolato dagli embedding riconosce i vetrini di un centro mai visto, e in particolare quelli su cui la testa
sbaglia, senza rinviare i vetrini dei centri visti, e senza rinviare i vetrini con molto tumore (il difetto di
E3/E3b)?

**Che cosa decide e che cosa no.** Se `predict` aggiunge il motivo di rinvio «dominio non riconosciuto dagli
embedding», con quale punteggio e con quale regola per la soglia. Non sostituisce il controllo sui metadati, che
resta. Non è il rinvio per regione proposto da E3b (mostrare al patologo le regioni lontane): quello misura il
tessuto, questo il dominio del vetrino.

**Dati.** Cohort `ln_metastasis` v1, 771 vetrini di sviluppo, Phikon `057cc0295895`; tile normalizzate L2 (come
E3). LPON non viene letto. Le predizioni di E6 vengono dalla riesecuzione di E10
(`data/reports/experiments/e10/e6/predictions.csv`).

**Ruoli, per ogni rotazione del leave-one-centre-out** (centro escluso *c*, 4 rotazioni). Sui vetrini dei tre
centri di training, con i fold del cohort (per paziente):

- riferimento: fold 0, 1, 2;
- calibrazione della soglia: fold 3;
- valutazione in distribuzione: fold 4;
- valutazione fuori distribuzione: tutti i vetrini di *c*.

**Candidati** (fissati ora, nell'ordine di semplicità):

- **V, vetrino:** media delle tile del vetrino; punteggio = distanza euclidea media dai 5 vetrini più vicini del
  riferimento (stessa media). Nessuna ricerca sulle tile.
- **T, tile (S0 di E3):** riferimento = k-center 256 per vetrino di riferimento (`vectordb/reduce.kcenter`, il
  riassunto del vector DB); per 200 tile a caso del vetrino (seme 0) la distanza dal prototipo più vicino;
  punteggio = media.

**Soglia.** Conformal come in E3: α = 0,05, il ⌈(n + 1)(1 − α)⌉-esimo punteggio dei vetrini di calibrazione;
rinvio se il punteggio lo supera.

**Esiti** (per candidato).

- Primari:
  1. falsi rinvii sulla valutazione in distribuzione, su tutte le rotazioni insieme;
  2. falsi rinvii sui soli vetrini **positivi** in distribuzione (il difetto di E3b);
  3. quota dei **falsi positivi di E6 sul centro escluso** (logit LOCO ≥ 0, negativo) che il punteggio rinvia,
     media sui tre semi: gli errori che il rinvio deve intercettare;
  4. rilevamento dei vetrini di Utrecht escluso (l'unico scanner diverso).
- Secondari:
  - rilevamento per centro escluso e AUROC in distribuzione contro fuori distribuzione, per rotazione;
  - quota dei falsi negativi di E6 sul centro escluso rinviati, e dei positivi per diagnosi (micro, macro);
  - falsi rinvii in distribuzione per centro, per dominio e per diagnosi;
  - **dominio dentro un centro:** per Radboud e Utrecht, una rotazione in più in cui riferimento e calibrazione
    hanno di quel centro solo i vetrini di CAMELYON17 e la valutazione sono i suoi vetrini di CAMELYON16
    (anni e conversioni diversi); per Radboud, quota rinviata dei casi del 2015 (anno da
    `data/reports/experiments/e3b/scan_metadata.csv`) contro gli altri anni.

**Criterio** (fissato ora). Un candidato è **adottabile** se:

1. falsi rinvii in distribuzione ≤ **0,08** (α più il margine di E3b);
2. falsi rinvii sui positivi in distribuzione ≤ **0,10**;
3. rinvia almeno il **90%** dei falsi positivi di E6 sul centro escluso;
4. rileva almeno il **95%** dei vetrini di Utrecht escluso.

Se lo sono entrambi si sceglie V (più semplice, nessuna ricerca sulle tile). Se nessuno lo è, `predict` resta
con il solo controllo sui metadati e il cambio di dominio dentro un centro resta compito del monitoraggio dei
negativi confermati (*Ingresso di un centro nuovo*, passo 6).

**Lettura** (fissata ora). Se un candidato rispetta 1, 2 e 4 ma non 3, riconosce lo scanner nuovo ma non gli
errori della testa sui centri dello stesso scanner (CWZ, Rijnstate, Radboud sono tutti 3DHistech): si riporta
così, senza adottarlo. Il secondario sul dominio dentro un centro non entra nel criterio: dice se il punteggio
vede anche i cambi che i metadati non vedono, che è il motivo dell'esperimento, ma i gruppi sono piccoli.

**In produzione.** Riferimento = i riassunti di tutti i vetrini di sviluppo meno un insieme di calibrazione per
paziente (un fold), soglia con la stessa regola; il riferimento e la soglia diventano un artefatto della
versione, come la temperatura.

**Limiti.**

- I fold di calibrazione e valutazione hanno circa 120 vetrini per rotazione: il tasso di falsi rinvii ha
  un'incertezza di circa ±0,02–0,04.
- Il criterio 3 dipende dai falsi positivi di E6, che cambiano molto tra semi (Utrecht: specificità da 0,09 a
  0,82): sono il bersaglio giusto, ma sono un bersaglio mobile.
- Tre centri su quattro hanno lo stesso scanner: un centro nuovo con uno scanner noto è il caso difficile, e
  qui ne abbiamo tre esempi su un solo scanner.
- 200 tile per vetrino in T (E3 ne usava 500), per contenere il calcolo mentre gira E14.
- Un backbone.

**Costo.** Lettura degli embedding di 771 vetrini (12,6 GB), k-center dei vetrini di riferimento, ricerca esatta
del vicino; stima circa un'ora con quattro thread, accanto a E14.

**Codice.** `experiments/e15_domain.py`; provato su dati sintetici e committato prima dell'esecuzione.
