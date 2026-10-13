"""The one interface every feature extractor implements (M2).

Everything downstream sees only (name, version, dim) and float32 embeddings, so swapping the
backbone costs a re-extraction, not a rewrite.
"""
from abc import ABC, abstractmethod
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms as T


def get_device(name: str = "auto") -> torch.device:
    if name != "auto":
        return torch.device(name)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def cached_revision(repo_id: str, revision: str | None = None, filename: str = "config.json") -> str:
    """Commit hash of the weights actually used, read from the local HF cache path
    (.../snapshots/<commit>/<filename>). 'unknown' if the file is not cached."""
    from huggingface_hub import try_to_load_from_cache

    path = try_to_load_from_cache(repo_id, filename, revision=revision)
    return Path(path).parent.name if isinstance(path, str) else "unknown"


class Backbone(ABC):
    name: str
    dim: int
    input_px: int
    mpp: float
    version: str = "unloaded"   # set by load(): identifies the exact weights
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)

    def __init__(self, cfg):
        self.cfg = cfg
        self.name, self.dim, self.input_px, self.mpp = cfg.name, cfg.dim, cfg.input_px, cfg.mpp
        self._transform = T.Compose([T.ToTensor(), T.Normalize(mean=self.mean, std=self.std)])

    def transform(self, img: Image.Image) -> torch.Tensor:
        """RGB tile of input_px x input_px -> normalised float tensor (3, H, W)."""
        return self._transform(img)

    @abstractmethod
    def load(self, device: torch.device) -> None: ...

    @abstractmethod
    def encode(self, images: torch.Tensor) -> torch.Tensor:
        """(B, 3, H, W) on any device -> (B, dim) float32 on the CPU."""
