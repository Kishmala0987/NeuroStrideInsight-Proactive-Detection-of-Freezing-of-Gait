"""
Inference service — runs the full 3-stage pipeline on an uploaded CSV.

Stage 1: FOG Detection      (FoGDetectionModel)
Stage 2: Trigger Classification (TriggerClassificationModel)
Stage 3: Derived metrics    (computed from Stage 1 + 2 outputs)
"""

import numpy as np
import pandas as pd
import torch
from dataclasses import dataclass, field
from typing import List, Optional
from ..models.loader import registry, TRIGGER_CLASSES

# ── Constants ─────────────────────────────────────────────────────────────────
FS           = 128        # sampling frequency Hz
WINDOW_SIZE  = 192        # 1.5 seconds
STEP         = 128        # 1.0 second step
FOG_THRESH   = 0.42       # detection threshold (tuned from training)
SMOOTH_K     = 3          # rolling average window for smoothing
MERGE_GAP_S  = 1.0        # merge FOG episodes if gap < 1s
MIN_DURATION = 0.5        # discard episodes shorter than 0.5s
SAFETY_GAP   = 64         # samples before episode onset for trigger window
LOW_CONF_THR = 0.60       # flag trigger if top confidence < 60%

REQUIRED_COLS = {"AccV", "AccML", "AccAP"}


# ── Output dataclasses ────────────────────────────────────────────────────────

@dataclass
class WindowOutput:
    window_index:    int
    start_time_s:    float
    end_time_s:      float
    fog_probability: float
    fog_predicted:   bool


@dataclass
class EpisodeOutput:
    episode_index:        int
    start_time_s:         float
    end_time_s:           float
    duration_s:           float
    trigger_label:        Optional[str]
    conf_start_hesitation: float
    conf_turn:            float
    conf_walking:         float
    low_confidence_flag:  bool


@dataclass
class PipelineResult:
    subject_id:              str
    medication_status:       str
    recording_duration_s:    float
    quality_badge:           str
    windows:                 List[WindowOutput]
    episodes:                List[EpisodeOutput]
    # Derived summary
    total_fog_episodes:      int
    total_fog_duration_s:    float
    fog_burden_pct:          float
    avg_episode_duration_s:  float
    max_episode_duration_s:  float
    dominant_trigger:        Optional[str]
    error:                   Optional[str] = None


# ── Validation ────────────────────────────────────────────────────────────────

def validate_csv(df: pd.DataFrame) -> tuple[bool, str, str]:
    """Returns (ok, quality_badge, error_message)."""
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        return False, "Poor", f"Missing required columns: {missing}"

    if len(df) < WINDOW_SIZE:
        return False, "Poor", (
            f"Recording too short: {len(df)} samples "
            f"(minimum {WINDOW_SIZE} = 1.5s at 128Hz)"
        )

    signals = df[["AccV", "AccML", "AccAP"]].values.astype(np.float32)

    # Flat signal check — variance near zero on any axis
    variances = signals.var(axis=0)
    if any(v < 1e-6 for v in variances):
        return True, "Poor", ""

    # Missing / NaN check
    nan_ratio = df[["AccV", "AccML", "AccAP"]].isna().mean().mean()
    if nan_ratio > 0.05:
        return True, "Poor", ""
    if nan_ratio > 0.01:
        return True, "Acceptable", ""

    # Signal variance quality
    mean_var = float(variances.mean())
    if mean_var < 0.1:
        return True, "Acceptable", ""

    return True, "Good", ""


# ── Stage 1: FOG Detection ────────────────────────────────────────────────────

def _normalize_window(x: torch.Tensor) -> torch.Tensor:
    """Per-channel z-score normalization."""
    mean = x.mean(dim=0, keepdim=True)
    std  = x.std(dim=0,  keepdim=True) + 1e-8
    return (x - mean) / std


def run_fog_detection(
    signals: np.ndarray,
    medication: float,
    device: torch.device
) -> tuple[List[WindowOutput], np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns window outputs + raw arrays for episode reconstruction.
    """
    model = registry.fog_model
    T     = len(signals)
    med_tensor = torch.tensor([[medication]], dtype=torch.float32).to(device)

    windows_out  = []
    all_probs    = []
    all_t_starts = []
    all_t_ends   = []

    with torch.no_grad():
        for i, start in enumerate(range(0, T - WINDOW_SIZE, STEP)):
            end  = start + WINDOW_SIZE
            x    = torch.tensor(signals[start:end], dtype=torch.float32)
            x    = _normalize_window(x).unsqueeze(0).to(device)  # (1, 192, 3)

            logit = model(x, med_tensor)
            prob  = torch.sigmoid(logit).item()
            all_probs.append(prob)
            all_t_starts.append(start / FS)
            all_t_ends.append(end / FS)

    all_probs    = np.array(all_probs,    dtype=np.float32)
    all_t_starts = np.array(all_t_starts, dtype=np.float32)
    all_t_ends   = np.array(all_t_ends,   dtype=np.float32)

    # Rolling mean smoothing
    smoothed = pd.Series(all_probs).rolling(SMOOTH_K, center=True, min_periods=1).mean().values
    preds    = (smoothed > FOG_THRESH).astype(int)

    for i in range(len(all_probs)):
        windows_out.append(WindowOutput(
            window_index=i,
            start_time_s=float(all_t_starts[i]),
            end_time_s=float(all_t_ends[i]),
            fog_probability=float(all_probs[i]),
            fog_predicted=bool(preds[i]),
        ))

    return windows_out, preds, all_t_starts, all_t_ends


def reconstruct_episodes(
    preds:    np.ndarray,
    t_starts: np.ndarray,
    t_ends:   np.ndarray
) -> List[dict]:
    """Merge consecutive FOG windows into discrete episodes."""
    episodes = []
    in_fog   = False
    ep_start = ep_end = 0.0

    for i, pred in enumerate(preds):
        if pred == 1:
            if not in_fog:
                ep_start = float(t_starts[i])
                ep_end   = float(t_ends[i])
                in_fog   = True
            else:
                gap = float(t_starts[i]) - ep_end
                if gap <= MERGE_GAP_S:
                    ep_end = float(t_ends[i])
                else:
                    if ep_end - ep_start >= MIN_DURATION:
                        episodes.append({"start": ep_start, "end": ep_end})
                    ep_start = float(t_starts[i])
                    ep_end   = float(t_ends[i])
        else:
            if in_fog:
                if ep_end - ep_start >= MIN_DURATION:
                    episodes.append({"start": ep_start, "end": ep_end})
                in_fog = False

    if in_fog and ep_end - ep_start >= MIN_DURATION:
        episodes.append({"start": ep_start, "end": ep_end})

    return episodes


# ── Stage 2: Trigger Classification ──────────────────────────────────────────

def run_trigger_classification(
    episodes: List[dict],
    signals:  np.ndarray,
    device:   torch.device
) -> List[EpisodeOutput]:
    """
    For each episode, extract the pre-onset window and classify trigger.
    """
    model   = registry.trigger_model
    results = []

    with torch.no_grad():
        for idx, ep in enumerate(episodes):
            ep_start_sample = int(ep["start"] * FS)
            pre_end         = ep_start_sample - SAFETY_GAP
            pre_start       = pre_end - WINDOW_SIZE

            # If pre-onset window is out of bounds, use zeros (unknown trigger)
            if pre_start < 0:
                confs  = [1/3, 1/3, 1/3]
                label  = None
                low_cf = True
            else:
                win = torch.tensor(signals[pre_start:pre_end], dtype=torch.float32)
                win = _normalize_window(win).unsqueeze(0).to(device)  # (1, 192, 3)

                logits = model(win)                          # (1, 3)
                probs  = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

                confs  = probs.tolist()
                top_i  = int(np.argmax(confs))
                label  = TRIGGER_CLASSES[top_i]
                low_cf = float(confs[top_i]) < LOW_CONF_THR

            duration = ep["end"] - ep["start"]
            results.append(EpisodeOutput(
                episode_index=idx + 1,
                start_time_s=round(ep["start"], 3),
                end_time_s=round(ep["end"], 3),
                duration_s=round(duration, 3),
                trigger_label=label,
                conf_start_hesitation=round(confs[0], 4),
                conf_turn=round(confs[1], 4),
                conf_walking=round(confs[2], 4),
                low_confidence_flag=low_cf,
            ))

    return results


# ── Stage 3: Derived Metrics ──────────────────────────────────────────────────

def compute_derived_metrics(
    episodes:           List[EpisodeOutput],
    recording_duration: float
) -> dict:
    if not episodes:
        return {
            "total_fog_episodes":     0,
            "total_fog_duration_s":   0.0,
            "fog_burden_pct":         0.0,
            "avg_episode_duration_s": 0.0,
            "max_episode_duration_s": 0.0,
            "dominant_trigger":       None,
        }

    durations = [e.duration_s for e in episodes]
    total_dur = sum(durations)

    # Dominant trigger — most frequent label (excluding None)
    labels = [e.trigger_label for e in episodes if e.trigger_label]
    dominant = None
    if labels:
        dominant = max(set(labels), key=labels.count)

    return {
        "total_fog_episodes":     len(episodes),
        "total_fog_duration_s":   round(total_dur, 2),
        "fog_burden_pct":         round((total_dur / recording_duration) * 100, 2) if recording_duration > 0 else 0.0,
        "avg_episode_duration_s": round(float(np.mean(durations)), 2),
        "max_episode_duration_s": round(float(np.max(durations)), 2),
        "dominant_trigger":       dominant,
    }


# ── Main pipeline entry point ─────────────────────────────────────────────────

def run_pipeline(
    df:           pd.DataFrame,
    subject_id:   str,
    medication:   str,          # "on" | "off"
) -> PipelineResult:
    """
    Full pipeline: validate → Stage 1 → Stage 2 → Stage 3.
    Returns a PipelineResult with all data needed to populate the DB.
    """
    # Validate
    ok, quality, err = validate_csv(df)
    if not ok:
        return PipelineResult(
            subject_id=subject_id,
            medication_status=medication,
            recording_duration_s=0,
            quality_badge="Poor",
            windows=[], episodes=[],
            total_fog_episodes=0,
            total_fog_duration_s=0,
            fog_burden_pct=0,
            avg_episode_duration_s=0,
            max_episode_duration_s=0,
            dominant_trigger=None,
            error=err,
        )

    # Prep
    df = df.copy()
    df[["AccV", "AccML", "AccAP"]] = df[["AccV", "AccML", "AccAP"]].fillna(0)
    signals             = df[["AccV", "AccML", "AccAP"]].values.astype(np.float32)
    recording_duration  = len(signals) / FS
    med_flag            = 1.0 if medication == "on" else 0.0
    device              = registry.device

    # Stage 1
    window_outputs, preds, t_starts, t_ends = run_fog_detection(
        signals, med_flag, device
    )
    raw_episodes = reconstruct_episodes(preds, t_starts, t_ends)

    # Stage 2
    episode_outputs = run_trigger_classification(raw_episodes, signals, device)

    # Stage 3
    metrics = compute_derived_metrics(episode_outputs, recording_duration)

    return PipelineResult(
        subject_id=subject_id,
        medication_status=medication,
        recording_duration_s=round(recording_duration, 2),
        quality_badge=quality,
        windows=window_outputs,
        episodes=episode_outputs,
        **metrics,
    )
