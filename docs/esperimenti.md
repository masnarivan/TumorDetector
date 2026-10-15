# Esperimenti

Esperimenti sugli embedding già estratti. Per ognuno il protocollo è fissato qui **prima** di
vedere i risultati; una modifica successiva al protocollo si annota con data e motivo, non si
riscrive. I risultati si aggiungono sotto il protocollo, con la versione del codice.

| # | Esperimento | Stato | Serve a decidere |
|---|---|---|---|
| E1 | Fughe di dati tra split: quasi-duplicati tra sviluppo e test | fatto: nessun duplicato | se l'AUROC 0.993 sul test è credibile |
| E2 | Probe sul centro (Robustness Index) a livello tile, regione, vetrino | da fare | se e quanto mitigare l'effetto centro |
| E3 | OOD con DB completo, sottoinsieme k-center e regioni | da fare | il ridisegno del vector DB |

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

**Risultati.** —
