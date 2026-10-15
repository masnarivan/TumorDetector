"""Attention-based multiple-instance learning (Ilse et al., 2018, gated attention).

A slide is a bag of tile embeddings with one label. The model scores every tile, pools the
tiles with those scores as weights and classifies the pooled vector; the weights show which
tiles drove the prediction.
"""
import numpy as np
import torch
from torch import nn

NORMALIZE = ("none", "slide_mean")


class ABMIL(nn.Module):
    """`normalize="slide_mean"` subtracts the bag's mean tile before anything else: it removes what
    every tile of the slide shares (stain, scanner: the centre, see experiment E2), computed from the
    slide itself. It lives in the model, so a saved model applies it on its own."""

    def __init__(self, dim: int, hidden: int = 256, dropout: float = 0.25, normalize: str = "none"):
        super().__init__()
        if normalize not in NORMALIZE:
            raise ValueError(f"normalize must be one of {NORMALIZE}, not {normalize!r}")
        self.normalize = normalize
        self.embed = nn.Sequential(nn.Linear(dim, hidden), nn.ReLU(), nn.Dropout(dropout))
        self.att_v = nn.Linear(hidden, hidden // 2)
        self.att_u = nn.Linear(hidden, hidden // 2)
        self.att_w = nn.Linear(hidden // 2, 1)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """(n_tiles, dim) -> slide logit (scalar) and attention weights (n_tiles,), summing to 1."""
        if self.normalize == "slide_mean":
            x = x - x.mean(dim=0, keepdim=True)
        h = self.embed(x)
        scores = self.att_w(torch.tanh(self.att_v(h)) * torch.sigmoid(self.att_u(h))).squeeze(-1)
        weights = torch.softmax(scores, dim=0)
        return self.head((weights[:, None] * h).sum(0)).squeeze(-1), weights


def fit(bags: list[np.ndarray], labels: np.ndarray, cfg, seed: int, device: str = "cpu") -> ABMIL:
    """Train on every bag for a fixed number of epochs. No early stopping: there is no
    validation set inside a fold, and picking the epoch on the test fold would leak."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = ABMIL(bags[0].shape[1], cfg.hidden, cfg.dropout, cfg.normalize).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    n_pos = int(labels.sum())
    pos_weight = torch.tensor((len(labels) - n_pos) / max(n_pos, 1), dtype=torch.float32, device=device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    model.train()
    for _ in range(cfg.epochs):
        for i in rng.permutation(len(bags)):
            bag = bags[i]
            if len(bag) > cfg.max_tiles:   # a random subset per step: bounded memory, mild augmentation
                bag = bag[np.sort(rng.choice(len(bag), cfg.max_tiles, replace=False))]
            logit, _ = model(torch.from_numpy(bag.astype(np.float32)).to(device))
            loss = loss_fn(logit, torch.tensor(float(labels[i]), device=device))
            opt.zero_grad()
            loss.backward()
            opt.step()
    return model.eval()


def predict(model: ABMIL, bags: list[np.ndarray], device: str = "cpu") -> tuple[np.ndarray, list[np.ndarray]]:
    """-> probability per slide and attention weights per slide (all tiles, no subsampling)."""
    probs, attention = [], []
    with torch.inference_mode():
        for bag in bags:
            logit, w = model(torch.from_numpy(bag.astype(np.float32)).to(device))
            probs.append(torch.sigmoid(logit).item())
            attention.append(w.cpu().numpy())
    return np.array(probs), attention
