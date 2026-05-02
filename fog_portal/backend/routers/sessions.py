"""
Sessions router — GET /api/sessions/{session_id}
Returns full session data including episodes and window probabilities.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session as DBSession

from ..db.database import get_db, Session, Episode, WindowResult, Subject
from ..services.crud import update_episode_annotation
from ..services.report import generate_single_visit_report
from pydantic import BaseModel

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/{session_id}")
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    subject = db.query(Subject).filter(Subject.id == session.subject_id).first()

    windows  = db.query(WindowResult).filter(
        WindowResult.session_id == session_id
    ).order_by(WindowResult.window_index).all()

    episodes = db.query(Episode).filter(
        Episode.session_id == session_id
    ).order_by(Episode.episode_index).all()

    return JSONResponse({
        "session": {
            "id":                     session.id,
            "subject_id":             session.subject_id,
            "visit_number":           session.visit_number,
            "upload_timestamp":       session.upload_timestamp.isoformat(),
            "recording_duration_s":   session.recording_duration_s,
            "medication_status":      session.medication_status,
            "clinical_note":          session.clinical_note,
            "csv_filename":           session.csv_filename,
            "quality_badge":          session.quality_badge,
            "total_fog_episodes":     session.total_fog_episodes,
            "total_fog_duration_s":   session.total_fog_duration_s,
            "fog_burden_pct":         session.fog_burden_pct,
            "avg_episode_duration_s": session.avg_episode_duration_s,
            "max_episode_duration_s": session.max_episode_duration_s,
            "dominant_trigger":       session.dominant_trigger,
        },
        "subject": {
            "id":            subject.id if subject else None,
            "age":           subject.age if subject else None,
            "sex":           subject.sex if subject else None,
            "years_since_dx": subject.years_since_dx if subject else None,
            "updrs_on":      subject.updrs_on if subject else None,
            "updrs_off":     subject.updrs_off if subject else None,
            "nfogq_score":   subject.nfogq_score if subject else None,
            "total_visits":  subject.total_visits if subject else None,
        },
        "windows": [
            {
                "window_index":    w.window_index,
                "start_time_s":    w.start_time_s,
                "end_time_s":      w.end_time_s,
                "fog_probability": w.fog_probability,
                "fog_predicted":   w.fog_predicted,
            }
            for w in windows
        ],
        "episodes": [
            {
                "id":                    ep.id,
                "episode_index":         ep.episode_index,
                "start_time_s":          ep.start_time_s,
                "end_time_s":            ep.end_time_s,
                "duration_s":            ep.duration_s,
                "trigger_label":         ep.trigger_label,
                "conf_start_hesitation": ep.conf_start_hesitation,
                "conf_turn":             ep.conf_turn,
                "conf_walking":          ep.conf_walking,
                "low_confidence_flag":   ep.low_confidence_flag,
                "annotation":            ep.annotation,
            }
            for ep in episodes
        ],
    })


class AnnotationRequest(BaseModel):
    annotation: str  # "confirmed" | "uncertain" | "artifact"


@router.patch("/{session_id}/episodes/{episode_id}/annotate")
def annotate_episode(
    session_id:  int,
    episode_id:  int,
    body:        AnnotationRequest,
    db:          DBSession = Depends(get_db),
):
    valid = {"confirmed", "uncertain", "artifact"}
    if body.annotation not in valid:
        raise HTTPException(status_code=400, detail=f"annotation must be one of {valid}")

    ep = update_episode_annotation(db, episode_id, body.annotation)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")

    return JSONResponse({"success": True, "episode_id": episode_id, "annotation": body.annotation})


@router.get("/{session_id}/report")
def download_report(session_id: int, db: DBSession = Depends(get_db)):
    session  = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    subject  = db.query(Subject).filter(Subject.id == session.subject_id).first()
    episodes = db.query(Episode).filter(
        Episode.session_id == session_id
    ).order_by(Episode.episode_index).all()

    pdf_bytes = generate_single_visit_report(subject, session, episodes)

    filename = f"FOG_Report_{session.subject_id}_Visit{session.visit_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{session_id}/export-csv")
def export_episodes_csv(session_id: int, db: DBSession = Depends(get_db)):
    session  = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    episodes = db.query(Episode).filter(
        Episode.session_id == session_id
    ).order_by(Episode.episode_index).all()

    import csv, io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "episode_index", "start_time_s", "end_time_s", "duration_s",
        "trigger_label", "conf_start_hesitation", "conf_turn", "conf_walking",
        "low_confidence_flag", "annotation"
    ])
    for ep in episodes:
        writer.writerow([
            ep.episode_index, ep.start_time_s, ep.end_time_s, ep.duration_s,
            ep.trigger_label or "", ep.conf_start_hesitation, ep.conf_turn,
            ep.conf_walking, ep.low_confidence_flag, ep.annotation or ""
        ])

    filename = f"FOG_Episodes_{session.subject_id}_Visit{session.visit_number}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
