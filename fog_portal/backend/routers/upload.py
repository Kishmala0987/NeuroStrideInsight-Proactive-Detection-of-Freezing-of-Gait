"""
Upload router — POST /api/upload
Accepts:
  - csv_file            : recording CSV (filename = series ID, e.g. 011322847a.csv)
  - medication_status   : "on" | "off" (required)
  - clinical_note       : optional str

Metadata files are loaded from backend/data/:
  - tdcsfog_metadata.csv  (Id, Subject, Visit, Test, Medication)
  - subjects.csv          (Subject_ID, Age, Sex, YearsSinceDx, UPDRSIII_On, UPDRSIII_Off, NFOGQ)
"""

import io
import os
import pandas as pd
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession
from typing import Optional

from ..db.database import get_db, Session
from ..services.inference import run_pipeline
from ..services.crud import (
    get_subject, create_or_update_subject,
    get_sessions_for_subject, create_session_from_pipeline
)
from ..services.metadata_parser import (
    extract_subject, extract_subject_metadata
)
from ..models.loader import registry

router = APIRouter(prefix="/api", tags=["upload"])

# ── Load metadata files from backend/data/ at startup ──────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METADATA_PATH = os.path.join(BASE_DIR, "data", "tdcsfog_metadata.csv")
SUBJECTS_PATH  = os.path.join(BASE_DIR, "data", "subjects.csv")

# Load into memory for faster lookup
_metadata_df = None
_subjects_df = None

def load_metadata_files():
    global _metadata_df, _subjects_df
    try:
        if os.path.exists(METADATA_PATH):
            _metadata_df = pd.read_csv(METADATA_PATH)
            _metadata_df.columns = _metadata_df.columns.str.strip()
    except Exception:
        pass
    try:
        if os.path.exists(SUBJECTS_PATH):
            _subjects_df = pd.read_csv(SUBJECTS_PATH)
            _subjects_df.columns = _subjects_df.columns.str.strip()
    except Exception:
        pass
    try:
        if os.path.exists(SUBJECTS_PATH):
            _subjects_df = pd.read_csv(SUBJECTS_PATH)
            _subjects_df.columns = _subjects_df.columns.str.strip()
    except Exception:
        pass


@router.post("/upload")
async def upload_session(
    csv_file:            UploadFile       = File(...),
    medication_status:   str              = Form(..., regex="^(on|off)$"),
    clinical_note:       Optional[str]    = Form(None),
    db:                  DBSession        = Depends(get_db),
):
    if not registry.is_ready():
        raise HTTPException(status_code=503, detail="Models are still loading. Please retry.")

    # Load metadata files if not already loaded
    global _metadata_df, _subjects_df
    if _metadata_df is None or _subjects_df is None:
        load_metadata_files()

    # ── Read recording CSV ────────────────────────────────────────────────────
    csv_bytes = await csv_file.read()
    
    # Series ID = CSV filename without extension (e.g. "011322847a")
    series_id = csv_file.filename.replace(".csv", "").strip()
    if not series_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV filename. File must be named as the series ID (e.g. 011322847a.csv)."
        )

    # Check for duplicate upload
    existing_session = db.query(Session).filter(Session.csv_filename == csv_file.filename).first()
    if existing_session:
        raise HTTPException(
            status_code=409,
            detail=f"This recording has already been analysed. View existing results at /subjects/{existing_session.subject_id}"
        )

    # Parse recording CSV
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    # ── Extract subject from metadata ──────────────────────────────────────────
    patient_subject_id = None
    if _metadata_df is not None:
        row = _metadata_df[_metadata_df["Id"] == series_id]
        if not row.empty:
            r = row.iloc[0]
            patient_subject_id = str(r["Subject"]).strip() if "Subject" in _metadata_df.columns else None
            patient_subject_id = patient_subject_id if patient_subject_id and patient_subject_id.lower() != "nan" else None

    if not patient_subject_id:
        raise HTTPException(
            status_code=422,
            detail=f"Subject ID not found for series '{series_id}' in metadata file."
        )

    # ── Extract demographics from subjects.csv ────────────────────────────────
    subj_meta = {}
    if _subjects_df is not None and patient_subject_id:
        row = _subjects_df[_subjects_df["Subject_ID"].astype(str) == str(patient_subject_id)]
        if row.empty:
            row = _subjects_df[_subjects_df["Subject"].astype(str) == str(patient_subject_id)]
        
        if not row.empty:
            r = row.iloc[0]
            def safe_float(col):
                try:
                    return float(r[col]) if col in _subjects_df.columns else None
                except Exception:
                    return None
            def safe_str(col):
                try:
                    v = str(r[col]).strip() if col in _subjects_df.columns else None
                    return v if v and v.lower() not in ("nan", "none", "") else None
                except Exception:
                    return None
            
            subj_meta = {
                "age":            safe_float("Age"),
                "sex":            safe_str("Sex"),
                "years_since_dx": safe_float("YearsSinceDx"),
                "updrs_on":       safe_float("UPDRSIII_On"),
                "updrs_off":      safe_float("UPDRSIII_Off"),
                "nfogq_score":    safe_float("NFOGQ"),
            }

    # ── Choose stored patient ID ───────────────────────────────────────────────
    stored_subject_id = patient_subject_id

    # ── Check subject history ──────────────────────────────────────────────────
    existing_subject  = get_subject(db, stored_subject_id)
    existing_sessions = get_sessions_for_subject(db, stored_subject_id)
    is_new_subject    = existing_subject is None

    # Auto-assign visit number
    visit_number = len(existing_sessions) + 1

    # ── Create/update subject record ──────────────────────────────────────────
    create_or_update_subject(db, stored_subject_id, subj_meta)

    # ── Run inference pipeline ────────────────────────────────────────────────
    result = run_pipeline(df, stored_subject_id, medication_status)

    if result.error:
        raise HTTPException(status_code=422, detail=result.error)

    # ── Persist session + episodes + windows ──────────────────────────────────
    session = create_session_from_pipeline(
        db=db,
        result=result,
        visit_number=visit_number,
        clinical_note=clinical_note,
        csv_filename=csv_file.filename,
    )

    return JSONResponse({
        "success":          True,
        "session_id":       session.id,
        "subject_id":       stored_subject_id,
        "visit_number":     session.visit_number,
        "is_new_subject":   is_new_subject,
        "has_prior_visits": len(existing_sessions) > 0,
        "quality_badge":    session.quality_badge,
        "summary": {
            "total_fog_episodes":     session.total_fog_episodes,
            "total_fog_duration_s":   session.total_fog_duration_s,
            "fog_burden_pct":         session.fog_burden_pct,
            "avg_episode_duration_s": session.avg_episode_duration_s,
            "max_episode_duration_s": session.max_episode_duration_s,
            "dominant_trigger":       session.dominant_trigger,
            "recording_duration_s":   session.recording_duration_s,
        }
    })
