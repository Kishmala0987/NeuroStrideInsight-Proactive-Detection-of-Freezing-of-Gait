"""
Model loader — loads both PyTorch models once at server startup.
Exposes a single ModelRegistry instance used by the inference service.
Place your .pth files in:  backend/model_weights/
"""

import os
import torch
from .architectures import FoGDetectionModel, TriggerClassificationModel

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "..", "model_weights")

FOG_WEIGHTS_PATH     = os.path.join(WEIGHTS_DIR, "dl_fog_model_best.pth")
TRIGGER_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, "trigger_dl_model.pth")

TRIGGER_CLASSES = ["StartHesitation", "Turn", "Walking"]


class ModelRegistry:
    def __init__(self):
        self.device        = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.fog_model     = None
        self.trigger_model = None
        self.loaded        = False

    def load(self):
        if self.loaded:
            return

        print(f"[ModelRegistry] Loading models on device: {self.device}")

        # ── FOG Detection ──────────────────────────────────────────────────
        if not os.path.exists(FOG_WEIGHTS_PATH):
            raise FileNotFoundError(
                f"FOG model weights not found at: {FOG_WEIGHTS_PATH}\n"
                f"Place dl_fog_model_best.pth in backend/model_weights/"
            )

        self.fog_model = FoGDetectionModel().to(self.device)
        self.fog_model.load_state_dict(
            torch.load(FOG_WEIGHTS_PATH, map_location=self.device)
        )
        self.fog_model.eval()
        print("[ModelRegistry] ✓ FOG Detection model loaded")

        # ── Trigger Classification ─────────────────────────────────────────
        if not os.path.exists(TRIGGER_WEIGHTS_PATH):
            raise FileNotFoundError(
                f"Trigger model weights not found at: {TRIGGER_WEIGHTS_PATH}\n"
                f"Place trigger_dl_model.pth in backend/model_weights/"
            )

        self.trigger_model = TriggerClassificationModel(num_classes=3).to(self.device)
        self.trigger_model.load_state_dict(
            torch.load(TRIGGER_WEIGHTS_PATH, map_location=self.device)
        )
        self.trigger_model.eval()
        print("[ModelRegistry] ✓ Trigger Classification model loaded")

        self.loaded = True
        print("[ModelRegistry] All models ready.")

    def is_ready(self) -> bool:
        return self.loaded


# Singleton — imported by inference service and app startup
registry = ModelRegistry()
