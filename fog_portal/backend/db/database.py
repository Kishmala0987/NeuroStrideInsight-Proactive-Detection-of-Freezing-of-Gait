from sqlalchemy import (
    create_engine, Column, Integer, Float, String,
    Text, DateTime, Boolean, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "fog_portal.db")
DATABASE_URL = "sqlite:///" + os.path.abspath(DB_PATH)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models ────────────────────────────────────────────────────────────────

class Subject(Base):
    __tablename__ = "subjects"

    id              = Column(String, primary_key=True, index=True)  # e.g. "011322847a"
    first_upload    = Column(DateTime, default=datetime.utcnow)
    total_visits    = Column(Integer, default=0)

    # Metadata from subjects.csv
    age             = Column(Float, nullable=True)
    sex             = Column(String, nullable=True)
    years_since_dx  = Column(Float, nullable=True)
    updrs_on        = Column(Float, nullable=True)
    updrs_off       = Column(Float, nullable=True)
    nfogq_score     = Column(Float, nullable=True)

    sessions        = relationship("Session", back_populates="subject", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    subject_id              = Column(String, ForeignKey("subjects.id"), nullable=False)
    visit_number            = Column(Integer, nullable=True)
    upload_timestamp        = Column(DateTime, default=datetime.utcnow)
    recording_duration_s    = Column(Float, nullable=True)
    medication_status       = Column(String, nullable=False)   # "on" | "off"
    clinical_note           = Column(Text, nullable=True)
    csv_filename            = Column(String, nullable=True)

    # Derived summary metrics (stored after pipeline)
    total_fog_episodes      = Column(Integer, default=0)
    total_fog_duration_s    = Column(Float, default=0.0)
    fog_burden_pct          = Column(Float, default=0.0)
    avg_episode_duration_s  = Column(Float, default=0.0)
    max_episode_duration_s  = Column(Float, default=0.0)
    dominant_trigger        = Column(String, nullable=True)

    # Data quality
    quality_badge           = Column(String, default="Good")   # Good | Acceptable | Poor

    subject  = relationship("Subject", back_populates="sessions")
    episodes = relationship("Episode", back_populates="session", cascade="all, delete-orphan")
    windows  = relationship("WindowResult", back_populates="session", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episodes"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    session_id              = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    episode_index           = Column(Integer, nullable=False)   # 1-based per session
    start_time_s            = Column(Float, nullable=False)
    end_time_s              = Column(Float, nullable=False)
    duration_s              = Column(Float, nullable=False)

    # Trigger classification
    trigger_label           = Column(String, nullable=True)     # StartHesitation | Turn | Walking
    conf_start_hesitation   = Column(Float, nullable=True)
    conf_turn               = Column(Float, nullable=True)
    conf_walking            = Column(Float, nullable=True)
    low_confidence_flag     = Column(Boolean, default=False)    # True if top conf < 0.60

    # Clinician annotation
    annotation              = Column(String, nullable=True)     # confirmed | uncertain | artifact

    session = relationship("Session", back_populates="episodes")


class WindowResult(Base):
    __tablename__ = "window_results"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    session_id      = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    window_index    = Column(Integer, nullable=False)
    start_time_s    = Column(Float, nullable=False)
    end_time_s      = Column(Float, nullable=False)
    fog_probability = Column(Float, nullable=False)
    fog_predicted   = Column(Boolean, nullable=False)

    session = relationship("Session", back_populates="windows")


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
