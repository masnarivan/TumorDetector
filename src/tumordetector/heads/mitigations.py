"""Training recipes against the centre effect (experiment E7). Training only: the model they produce
is the plain ABMIL, so inference and the registered model do not depend on the recipe.

  balanced    every domain weighs the same in an epoch and, inside a domain, so do the two classes
  group_dro   the worst domain's loss is minimised (Sagawa et al., 2020, online version)
  stat_mix    a slide's tiles are re-coloured with a mix of its own statistics (per-dimension mean
              and standard deviation over the slide) and those of a slide of another domain
              (MixStyle, Zhou et al., 2021, on slide statistics)
  adversarial domain discriminators on the slide representation z and on a sample of tile
              representations h, trained through a gradient reversal layer (DANN, Ganin et al.,
              2016): the head learns to classify while making z and h useless for telling domains apart.
              The discriminators are dropped after training
  adversarial_negatives  the same, on negative slides only: E6 found that only the negatives of an
              unseen centre move, so invariance is asked of normal tissue and the tumour signal is left alone

The hyperparameters of the first three are fixed by the E7 protocol from the papers' values, not tuned;
those of the adversarial recipes are the papers' defaults, fixed by the E8 protocol.
An empty recipe is not handled here: the protocol then calls `abmil.fit`, the training of E6.
"""
import numpy as np
import torch
from torch import nn

from tumordetector.mil.abmil import ABMIL

RECIPES = ("balanced", "group_dro", "stat_mix", "adversarial", "adversarial_negatives")
DRO_ETA = 0.01              # step size of the domain weights
MIX_P, MIX_ALPHA = 0.5, 0.1  # probability of mixing a slide at a step; lambda ~ Beta(alpha, alpha)
DANN_LAMBDA, DANN_GAMMA = 1.0, 10.0   # reversal strength, reached with Ganin's ramp 2 / (1 + e^(-gamma p)) - 1
DANN_HIDDEN, DANN_TILES = 128, 256    # discriminator width; tiles per step seen by the tile discriminator
EPS = 1e-6


class _Reverse(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, lam):
        ctx.lam = lam
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad):
        return -ctx.lam * grad, None


def grad_reverse(x: torch.Tensor, lam: float) -> torch.Tensor:
    """Identity going forward; going back, the gradient is multiplied by -lam: what helps the
    discriminator tell domains apart pushes the head the other way."""
    return _Reverse.apply(x, lam)


def dann_lambda(progress: float, lam: float = DANN_LAMBDA, gamma: float = DANN_GAMMA) -> float:
    """Reversal strength at training progress 0..1: from 0 (the head first learns the task) up to lam."""
    return lam * (2 / (1 + np.exp(-gamma * progress)) - 1)


class Adversary(nn.Module):
    """Two domain discriminators, one on z (the slide) and one on h (tiles), with a domain-balanced
    cross-entropy: a discriminator that only guesses the largest domain learns nothing."""

    def __init__(self, hidden: int, domains: np.ndarray, width: int = DANN_HIDDEN):
        super().__init__()
        names, counts = np.unique(domains, return_counts=True)
        self.index = {d: i for i, d in enumerate(names)}
        self.slide = nn.Sequential(nn.Linear(hidden, width), nn.ReLU(), nn.Linear(width, len(names)))
        self.tile = nn.Sequential(nn.Linear(hidden, width), nn.ReLU(), nn.Linear(width, len(names)))
        weight = torch.tensor(len(domains) / (len(names) * counts), dtype=torch.float32)
        self.register_buffer("weight", weight)

    def loss(self, h: torch.Tensor, z: torch.Tensor, domain: str, lam: float, rng: np.random.Generator) -> torch.Tensor:
        target = torch.tensor(self.index[domain], device=z.device)
        w = self.weight[target]
        slide = nn.functional.cross_entropy(self.slide(grad_reverse(z, lam))[None], target[None]) * w
        pick = torch.from_numpy(np.sort(rng.choice(len(h), min(DANN_TILES, len(h)), replace=False))).to(h.device)
        logits = self.tile(grad_reverse(h[pick], lam))
        tile = nn.functional.cross_entropy(logits, target.expand(len(pick))) * w
        return slide + tile


def balanced_weights(labels: np.ndarray, domains: np.ndarray) -> np.ndarray:
    """Weight of each slide = 1 / (n domains x 2 x slides of its class in its domain), mean 1."""
    labels, domains = np.asarray(labels), np.asarray(domains)
    keys = np.char.add(np.char.add(domains.astype(str), "|"), labels.astype(str))
    _, inverse, counts = np.unique(keys, return_inverse=True, return_counts=True)
    w = 1.0 / (len(np.unique(domains)) * 2 * counts[inverse])
    return w / w.mean()


class GroupDRO:
    """One weight q per domain, raised exponentially with the domain's loss at each step and
    renormalised; the step's loss is scaled by n domains x q of the slide's domain."""

    def __init__(self, domains: np.ndarray, eta: float = DRO_ETA):
        self.names = sorted(set(domains))
        self.index = {d: i for i, d in enumerate(self.names)}
        self.q = np.full(len(self.names), 1 / len(self.names))
        self.eta = eta

    def scale(self, loss: torch.Tensor, domain: str) -> torch.Tensor:
        i = self.index[domain]
        self.q[i] *= np.exp(self.eta * float(loss.detach()))
        self.q /= self.q.sum()
        return loss * (len(self.names) * self.q[i])


class StatMix:
    """Per-slide statistics of every training bag (all tiles), and the mixing step."""

    def __init__(self, bags: list[np.ndarray], domains: np.ndarray, rng: np.random.Generator,
                 p: float = MIX_P, alpha: float = MIX_ALPHA):
        self.mu = np.stack([b.astype(np.float32).mean(0) for b in bags])
        self.sigma = np.stack([b.astype(np.float32).std(0) for b in bags]) + EPS
        self.domains, self.rng, self.p, self.alpha = np.asarray(domains), rng, p, alpha

    def __call__(self, x: torch.Tensor, i: int) -> torch.Tensor:
        others = np.flatnonzero(self.domains != self.domains[i])
        if not len(others) or self.rng.random() >= self.p:
            return x
        j = self.rng.choice(others)
        lam = float(self.rng.beta(self.alpha, self.alpha))
        mu, sigma = x.mean(0, keepdim=True), x.std(0, keepdim=True) + EPS
        mu_mix = lam * mu + (1 - lam) * torch.from_numpy(self.mu[j]).to(x)
        sigma_mix = lam * sigma + (1 - lam) * torch.from_numpy(self.sigma[j]).to(x)
        return (x - mu) / sigma * sigma_mix + mu_mix


def fit_recipe(bags: list[np.ndarray], labels: np.ndarray, domains: np.ndarray, cfg, seed: int,
               recipe: list[str], device: str = "cpu") -> ABMIL:
    """`abmil.fit` with the recipe's mitigations: same model, optimiser, epochs and tile sampling."""
    if not recipe or set(recipe) - set(RECIPES):
        raise ValueError(f"recipe must be a non-empty subset of {RECIPES}, not {recipe}")
    if {"adversarial", "adversarial_negatives"} <= set(recipe):
        raise ValueError("adversarial and adversarial_negatives are alternatives, not a combination")
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    labels, domains = np.asarray(labels), np.asarray(domains)
    model = ABMIL(bags[0].shape[1], cfg.hidden, cfg.dropout, cfg.normalize).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    if "balanced" in recipe:
        weights, loss_fn = balanced_weights(labels, domains), nn.BCEWithLogitsLoss()
    else:   # the class weighting of abmil.fit
        n_pos = int(labels.sum())
        pos_weight = torch.tensor((len(labels) - n_pos) / max(n_pos, 1), dtype=torch.float32, device=device)
        weights, loss_fn = np.ones(len(labels)), nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    dro = GroupDRO(domains) if "group_dro" in recipe else None
    mix = StatMix(bags, domains, rng) if "stat_mix" in recipe else None
    adversary, negatives_only = None, "adversarial_negatives" in recipe
    seen = domains[labels == 0] if negatives_only else domains     # the slides the adversary looks at
    if ("adversarial" in recipe or negatives_only) and len(set(seen)) > 1:   # one domain: nothing to hide
        adversary = Adversary(cfg.hidden, seen).to(device)
        opt.add_param_group({"params": adversary.parameters()})
    model.train()
    step, total = 0, cfg.epochs * len(bags)
    for _ in range(cfg.epochs):
        for i in rng.permutation(len(bags)):
            bag = bags[i]
            if len(bag) > cfg.max_tiles:
                bag = bag[np.sort(rng.choice(len(bag), cfg.max_tiles, replace=False))]
            x = torch.from_numpy(bag.astype(np.float32)).to(device)
            if mix is not None:
                x = mix(x, i)
            h, _, z = model.encode(x)
            logit = model.head(z).squeeze(-1)                 # = model(x), keeping h and z for the adversary
            loss = loss_fn(logit, torch.tensor(float(labels[i]), device=device)) * float(weights[i])
            if dro is not None:
                loss = dro.scale(loss, domains[i])
            if adversary is not None and not (negatives_only and labels[i] == 1):
                loss = loss + adversary.loss(h, z, domains[i], dann_lambda(step / total), rng)
            step += 1
            opt.zero_grad()
            loss.backward()
            opt.step()
    return model.eval()
