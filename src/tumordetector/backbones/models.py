"""Backbone implementations. Heavy imports stay inside load() so tests never pay for them."""
import torch
import torch.nn.functional as F

from tumordetector.backbones.base import Backbone, cached_revision


class Dummy(Backbone):
    """Fixed random projection of an 8x8 average-pooled tile: deterministic, no weights."""

    def load(self, device: torch.device) -> None:
        g = torch.Generator().manual_seed(int(self.cfg.seed))
        self.proj = torch.randn(3 * 8 * 8, self.dim, generator=g)
        self.version = f"seed{self.cfg.seed}"

    def encode(self, images: torch.Tensor) -> torch.Tensor:
        return F.adaptive_avg_pool2d(images.cpu().float(), 8).flatten(1) @ self.proj


class Phikon(Backbone):
    """owkin/phikon, ViT-B/16 (iBOT on TCGA). Embedding = CLS token of the last layer."""

    def load(self, device: torch.device) -> None:
        from transformers import ViTModel

        model = ViTModel.from_pretrained(self.cfg.repo_id, revision=self.cfg.revision,
                                         local_files_only=bool(self.cfg.offline))
        self.model, self.device = model.eval().to(device), device
        self.version = cached_revision(self.cfg.repo_id, self.cfg.revision)

    def encode(self, images: torch.Tensor) -> torch.Tensor:
        with torch.inference_mode():
            return self.model(pixel_values=images.to(self.device)).last_hidden_state[:, 0].float().cpu()


class HOptimus0(Backbone):
    """bioptimus/H-optimus-0, ViT-g/14 with 1.1 B parameters. Embedding = pooled CLS (1536-d).
    Loading and normalisation follow the model card."""

    mean = (0.707223, 0.578729, 0.703617)
    std = (0.211883, 0.230117, 0.177517)

    def load(self, device: torch.device) -> None:
        import timm

        hub = f"hf-hub:{self.cfg.repo_id}" + (f"@{self.cfg.revision}" if self.cfg.revision else "")
        model = timm.create_model(hub, pretrained=True, init_values=1e-5, dynamic_img_size=False)
        self.model, self.device = model.eval().to(device), device
        self.version = cached_revision(self.cfg.repo_id, self.cfg.revision)

    def encode(self, images: torch.Tensor) -> torch.Tensor:
        half = bool(self.cfg.half) and self.device.type == "cuda"
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16, enabled=half):
            return self.model(images.to(self.device)).float().cpu()


REGISTRY: dict[str, type[Backbone]] = {"dummy": Dummy, "phikon": Phikon, "h_optimus_0": HOptimus0}


def build_backbone(cfg) -> Backbone:
    if cfg.name not in REGISTRY:
        raise KeyError(f"unknown backbone {cfg.name!r}; available: {sorted(REGISTRY)}")
    return REGISTRY[cfg.name](cfg)
