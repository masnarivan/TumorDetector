"""The answer of a head for one slide (contract M4): positive, negative or referral, with every reason.

Only a version validated by its battery answers, and only for centres and scanners of its development
(docs/training-multicentro.md, principle 6, proposed on 22/10/2026): a centre never seen moves the
negatives towards the tumour (E6). The domain check (E15) refers also what the metadata do not see: a slide
whose embeddings are far from the development's. Within those, the conformal set per class (E10) decides: {1} positive,
{0} negative, {0, 1} uncertain and {} unlike either class are referrals.
"""
from tumordetector.heads.conformal import prediction_set

POSITIVE, NEGATIVE, REFER = "positivo", "negativo", "rinvio"


def answer(p: float, q0: float, q1: float, validated: bool, center_seen: bool | None,
           scanner_seen: bool | None, domain_seen: bool | None = None) -> dict:
    """`center_seen` / `scanner_seen` / `domain_seen`: None when the check is off. Every reason is listed,
    not just the first."""
    has0, has1 = (bool(v[0]) for v in prediction_set([p], q0, q1))
    labels = [y for y, inside in ((0, has0), (1, has1)) if inside]
    reasons = []
    if not validated:
        reasons.append("versione non validata: la batteria di promozione non è superata")
    if center_seen is False:
        reasons.append("centro non visto nello sviluppo di questa versione")
    if scanner_seen is False:
        reasons.append("scanner non visto nello sviluppo di questa versione")
    if domain_seen is False:
        reasons.append("dominio non riconosciuto dagli embedding: il vetrino è lontano da quelli di sviluppo")
    if has0 and has1:
        reasons.append("incerto: l'insieme conformal contiene entrambe le classi")
    elif not labels:
        reasons.append("atipico: l'insieme conformal è vuoto")
    if reasons:
        decision = REFER
    else:
        decision = POSITIVE if labels == [1] else NEGATIVE
    return {"set": labels, "decision": decision, "reasons": reasons}
