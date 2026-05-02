"""
Subjects router — patient profile, visit history, progression view, report.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session as DBSession

from ..db.database import get_db, Subject, Session, Episode
from ..services.report import generate_progression_report

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


@router.get("/")
def list_subjects(db: DBSession = Depends(get_db)):
    subjects = db.query(Subject).order_by(Subject.first_upload.desc()).all()
    result = []
    for s in subjects:
        sessions = db.query(Session).filter(Session.subject_id == s.id).all()
        latest   = max(sessions, key=lambda x: x.upload_timestamp) if sessions else None
        result.append({
            "id":           s.id,
            "total_visits": len(sessions),
            "first_upload": s.first_upload.isoformat() if s.first_upload else None,
            "latest_visit_date": latest.upload_timestamp.isoformat() if latest else None,
            "latest_fog_burden": latest.fog_burden_pct if latest else None,
            "age":          s.age,
            "sex":          s.sex,
        })
    return JSONResponse(result)


@router.get("/{subject_id}")
def get_subject_profile(subject_id: str, db: DBSession = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    sessions = (
        db.query(Session)
        .filter(Session.subject_id == subject_id)
        .order_by(Session.visit_number)
        .all()
    )

    return JSONResponse({
        "subject": {
            "id":            subject.id,
            "age":           subject.age,
            "sex":           subject.sex,
            "years_since_dx": subject.years_since_dx,
            "updrs_on":      subject.updrs_on,
            "updrs_off":     subject.updrs_off,
            "nfogq_score":   subject.nfogq_score,
            "total_visits":  len(sessions),
            "first_upload":  subject.first_upload.isoformat() if subject.first_upload else None,
        },
        "sessions": [
            {
                "id":                     s.id,
                "visit_number":           s.visit_number,
                "upload_timestamp":       s.upload_timestamp.isoformat(),
                "medication_status":      s.medication_status,
                "total_fog_episodes":     s.total_fog_episodes,
                "total_fog_duration_s":   s.total_fog_duration_s,
                "fog_burden_pct":         s.fog_burden_pct,
                "avg_episode_duration_s": s.avg_episode_duration_s,
                "max_episode_duration_s": s.max_episode_duration_s,
                "dominant_trigger":       s.dominant_trigger,
                "quality_badge":          s.quality_badge,
                "clinical_note":          s.clinical_note,
            }
            for s in sessions
        ],
    })


@router.get("/{subject_id}/progression")
def get_progression(subject_id: str, db: DBSession = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    sessions = (
        db.query(Session)
        .filter(Session.subject_id == subject_id)
        .order_by(Session.visit_number)
        .all()
    )

    if len(sessions) < 2:
        raise HTTPException(
            status_code=400,
            detail="Progression view requires at least 2 visits."
        )

    # Trigger distribution per visit
    visit_data = []
    for s in sessions:
        episodes = db.query(Episode).filter(Episode.session_id == s.id).all()
        trigger_counts = {"StartHesitation": 0, "Turn": 0, "Walking": 0}
        for ep in episodes:
            if ep.trigger_label in trigger_counts:
                trigger_counts[ep.trigger_label] += 1

        visit_data.append({
            "session_id":             s.id,
            "visit_number":           s.visit_number,
            "upload_date":            s.upload_timestamp.isoformat(),
            "medication_status":      s.medication_status,
            "total_fog_episodes":     s.total_fog_episodes,
            "total_fog_duration_s":   s.total_fog_duration_s,
            "fog_burden_pct":         s.fog_burden_pct,
            "avg_episode_duration_s": s.avg_episode_duration_s,
            "max_episode_duration_s": s.max_episode_duration_s,
            "dominant_trigger":       s.dominant_trigger,
            "trigger_counts":         trigger_counts,
        })

    # Medication delta
    on_visits  = [v for v in visit_data if v["medication_status"] == "on"]
    off_visits = [v for v in visit_data if v["medication_status"] == "off"]
    med_delta  = None
    if on_visits and off_visits:
        import numpy as np
        med_delta = {
            "on_avg_burden":  round(float(np.mean([v["fog_burden_pct"] for v in on_visits])), 2),
            "off_avg_burden": round(float(np.mean([v["fog_burden_pct"] for v in off_visits])), 2),
            "delta":          round(
                float(np.mean([v["fog_burden_pct"] for v in off_visits])) -
                float(np.mean([v["fog_burden_pct"] for v in on_visits])), 2
            ),
        }

    return JSONResponse({
        "subject_id": subject_id,
        "visits":     visit_data,
        "med_delta":  med_delta,
    })


@router.get("/{subject_id}/report")
def download_progression_report(subject_id: str, db: DBSession = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    sessions = (
        db.query(Session)
        .filter(Session.subject_id == subject_id)
        .order_by(Session.visit_number)
        .all()
    )

    pdf_bytes = generate_progression_report(subject, sessions)
    filename  = f"FOG_Progression_{subject_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
