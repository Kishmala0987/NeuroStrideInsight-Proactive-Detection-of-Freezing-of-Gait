"""
CRUD service — all database read/write operations.
"""

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
from ..db.database import Subject, Session, Episode, WindowResult
from ..services.inference import PipelineResult


# ── Subject ───────────────────────────────────────────────────────────────────

def get_subject(db: DBSession, subject_id: str) -> Optional[Subject]:
    return db.query(Subject).filter(Subject.id == subject_id).first()


def get_all_subjects(db: DBSession) -> List[Subject]:
    return db.query(Subject).order_by(Subject.first_upload.desc()).all()


def create_or_update_subject(
    db:         DBSession,
    subject_id: str,
    metadata:   dict,
) -> Subject:
    subj = get_subject(db, subject_id)
    if not subj:
        subj = Subject(
            id=subject_id,
            first_upload=datetime.utcnow(),
            total_visits=0,
            **metadata,
        )
        db.add(subj)
    else:
        for k, v in metadata.items():
            if v is not None:
                setattr(subj, k, v)
    db.commit()
    db.refresh(subj)
    return subj


# ── Session ───────────────────────────────────────────────────────────────────

def get_sessions_for_subject(db: DBSession, subject_id: str) -> List[Session]:
    return (
        db.query(Session)
        .filter(Session.subject_id == subject_id)
        .order_by(Session.visit_number)
        .all()
    )


def get_session(db: DBSession, session_id: int) -> Optional[Session]:
    return db.query(Session).filter(Session.id == session_id).first()


def create_session_from_pipeline(
    db:            DBSession,
    result:        PipelineResult,
    visit_number:  Optional[int],
    clinical_note: Optional[str],
    csv_filename:  str,
) -> Session:
    session = Session(
        subject_id=result.subject_id,
        visit_number=visit_number,
        upload_timestamp=datetime.utcnow(),
        recording_duration_s=result.recording_duration_s,
        medication_status=result.medication_status,
        clinical_note=clinical_note,
        csv_filename=csv_filename,
        total_fog_episodes=result.total_fog_episodes,
        total_fog_duration_s=result.total_fog_duration_s,
        fog_burden_pct=result.fog_burden_pct,
        avg_episode_duration_s=result.avg_episode_duration_s,
        max_episode_duration_s=result.max_episode_duration_s,
        dominant_trigger=result.dominant_trigger,
        quality_badge=result.quality_badge,
    )
    db.add(session)
    db.flush()  # get session.id before adding children

    # Persist windows
    for w in result.windows:
        db.add(WindowResult(
            session_id=session.id,
            window_index=w.window_index,
            start_time_s=w.start_time_s,
            end_time_s=w.end_time_s,
            fog_probability=w.fog_probability,
            fog_predicted=w.fog_predicted,
        ))

    # Persist episodes
    for ep in result.episodes:
        db.add(Episode(
            session_id=session.id,
            episode_index=ep.episode_index,
            start_time_s=ep.start_time_s,
            end_time_s=ep.end_time_s,
            duration_s=ep.duration_s,
            trigger_label=ep.trigger_label,
            conf_start_hesitation=ep.conf_start_hesitation,
            conf_turn=ep.conf_turn,
            conf_walking=ep.conf_walking,
            low_confidence_flag=ep.low_confidence_flag,
            annotation=None,
        ))

    # Update subject visit count
    subj = db.query(Subject).filter(Subject.id == result.subject_id).first()
    if subj:
        subj.total_visits = db.query(Session).filter(
            Session.subject_id == result.subject_id
        ).count() + 1  # +1 because current session not committed yet

    db.commit()
    db.refresh(session)
    return session


def update_episode_annotation(
    db:         DBSession,
    episode_id: int,
    annotation: str,
) -> Optional[Episode]:
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        return None
    ep.annotation = annotation
    db.commit()
    db.refresh(ep)
    return ep


# ── Statistics (aggregate across all subjects) ────────────────────────────────

def get_population_stats(db: DBSession) -> dict:
    sessions = db.query(Session).all()
    if not sessions:
        return {}

    fog_burdens    = [s.fog_burden_pct for s in sessions if s.fog_burden_pct is not None]
    ep_counts      = [s.total_fog_episodes for s in sessions]
    med_on_burden  = [s.fog_burden_pct for s in sessions if s.medication_status == "on"]
    med_off_burden = [s.fog_burden_pct for s in sessions if s.medication_status == "off"]

    # Trigger distribution across all episodes
    all_episodes = db.query(Episode).all()
    trigger_counts = {"StartHesitation": 0, "Turn": 0, "Walking": 0}
    for ep in all_episodes:
        if ep.trigger_label in trigger_counts:
            trigger_counts[ep.trigger_label] += 1

    import numpy as np

    return {
        "total_subjects":          db.query(Subject).count(),
        "total_sessions":          len(sessions),
        "total_episodes":          len(all_episodes),
        "fog_burden_distribution": fog_burdens,
        "avg_fog_burden_pct":      round(float(np.mean(fog_burdens)), 2) if fog_burdens else 0,
        "avg_episode_count":       round(float(np.mean(ep_counts)), 2) if ep_counts else 0,
        "trigger_counts":          trigger_counts,
        "med_on_avg_burden":       round(float(np.mean(med_on_burden)), 2) if med_on_burden else None,
        "med_off_avg_burden":      round(float(np.mean(med_off_burden)), 2) if med_off_burden else None,
        "sessions_by_medication":  {
            "on":  sum(1 for s in sessions if s.medication_status == "on"),
            "off": sum(1 for s in sessions if s.medication_status == "off"),
        },
    }
