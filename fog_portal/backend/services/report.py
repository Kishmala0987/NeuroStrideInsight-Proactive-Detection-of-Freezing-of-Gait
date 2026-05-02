"""
PDF report generator using ReportLab.
Generates single-visit and progression reports.
"""

import io
from datetime import datetime
from typing import List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Colour palette ────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#0D47A1")
ACCENT    = colors.HexColor("#1565C0")
LIGHT_BG  = colors.HexColor("#E3F2FD")
WARN      = colors.HexColor("#F57F17")
DANGER    = colors.HexColor("#B71C1C")
SUCCESS   = colors.HexColor("#1B5E20")
GREY      = colors.HexColor("#ECEFF1")
TEXT      = colors.HexColor("#212121")
SUBTEXT   = colors.HexColor("#546E7A")

TRIGGER_COLORS = {
    "StartHesitation": colors.HexColor("#C62828"),
    "Turn":            colors.HexColor("#1565C0"),
    "Walking":         colors.HexColor("#2E7D32"),
    None:              SUBTEXT,
}


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", fontSize=22, textColor=PRIMARY,
            fontName="Helvetica-Bold", spaceAfter=4,
            alignment=TA_LEFT
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=11, textColor=SUBTEXT,
            fontName="Helvetica", spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "section", fontSize=13, textColor=PRIMARY,
            fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", fontSize=10, textColor=TEXT,
            fontName="Helvetica", spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "small", fontSize=8, textColor=SUBTEXT,
            fontName="Helvetica", spaceAfter=2,
        ),
        "metric_label": ParagraphStyle(
            "metric_label", fontSize=9, textColor=SUBTEXT,
            fontName="Helvetica",
        ),
        "metric_value": ParagraphStyle(
            "metric_value", fontSize=16, textColor=PRIMARY,
            fontName="Helvetica-Bold",
        ),
    }
    return styles


def _hr():
    return HRFlowable(width="100%", thickness=1, color=LIGHT_BG, spaceAfter=8)


def _metric_table(metrics: list) -> Table:
    """
    metrics: list of (label, value) tuples — renders as a row of metric cards.
    """
    s = _styles()
    header_row = [Paragraph(m[0], s["metric_label"]) for m in metrics]
    value_row  = [Paragraph(str(m[1]), s["metric_value"]) for m in metrics]

    t = Table([header_row, value_row], colWidths=[3.8 * cm] * len(metrics))
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), GREY),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [GREY, colors.white]),
        ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#B0BEC5")),
        ("INNERGRID",   (0, 0), (-1, -1), 0.25, colors.HexColor("#CFD8DC")),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


# ── Single Visit Report ───────────────────────────────────────────────────────

def generate_single_visit_report(
    subject,
    session,
    episodes: list,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    s   = _styles()
    els = []

    # Header
    els.append(Paragraph("Freezing of Gait Analysis Report", s["title"]))
    els.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%d %B %Y, %H:%M UTC')}",
        s["subtitle"]
    ))
    els.append(_hr())

    # Patient info table
    els.append(Paragraph("Patient Information", s["section"]))
    patient_data = [
        ["Subject ID",       subject.id,
         "Age",              str(subject.age or "—")],
        ["Sex",              subject.sex or "—",
         "Years Since Dx",   str(subject.years_since_dx or "—")],
        ["UPDRS III (On)",   str(subject.updrs_on or "—"),
         "UPDRS III (Off)",  str(subject.updrs_off or "—")],
        ["NFOGQ Score",      str(subject.nfogq_score or "—"),
         "Visit Number",     str(session.visit_number)],
        ["Medication",       session.medication_status.upper(),
         "Recording Date",   session.upload_timestamp.strftime("%d %b %Y")],
    ]
    pt = Table(patient_data, colWidths=[3.5*cm, 4.5*cm, 3.5*cm, 4.5*cm])
    pt.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), SUBTEXT),
        ("TEXTCOLOR", (2, 0), (2, -1), SUBTEXT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GREY]),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    els.append(pt)
    els.append(Spacer(1, 12))

    # Summary metrics
    els.append(Paragraph("FOG Summary", s["section"]))
    quality_color = {"Good": SUCCESS, "Acceptable": WARN, "Poor": DANGER}.get(
        session.quality_badge, SUBTEXT
    )
    els.append(_metric_table([
        ("Total Episodes",        session.total_fog_episodes),
        ("FOG Duration (s)",      f"{session.total_fog_duration_s:.1f}"),
        ("FOG Burden",            f"{session.fog_burden_pct:.1f}%"),
        ("Avg Duration (s)",      f"{session.avg_episode_duration_s:.1f}"),
        ("Max Duration (s)",      f"{session.max_episode_duration_s:.1f}"),
    ]))
    els.append(Spacer(1, 6))
    els.append(Paragraph(
        f"Data Quality: <b>{session.quality_badge}</b> &nbsp;|&nbsp; "
        f"Recording Duration: <b>{session.recording_duration_s:.1f}s</b> &nbsp;|&nbsp; "
        f"Dominant Trigger: <b>{session.dominant_trigger or '—'}</b>",
        s["body"]
    ))
    els.append(Spacer(1, 12))

    # Episode table
    els.append(Paragraph("Detected FOG Episodes", s["section"]))
    ep_headers = ["#", "Start (s)", "End (s)", "Duration (s)",
                  "Trigger", "Conf SH", "Conf Turn", "Conf Walk", "Flag", "Annotation"]
    ep_rows = [ep_headers]
    for ep in episodes:
        flag = "⚠" if ep.low_confidence_flag else ""
        ann  = ep.annotation or "—"
        ep_rows.append([
            str(ep.episode_index),
            f"{ep.start_time_s:.2f}",
            f"{ep.end_time_s:.2f}",
            f"{ep.duration_s:.2f}",
            ep.trigger_label or "—",
            f"{ep.conf_start_hesitation:.2f}",
            f"{ep.conf_turn:.2f}",
            f"{ep.conf_walking:.2f}",
            flag,
            ann,
        ])

    ep_table = Table(ep_rows, colWidths=[
        0.8*cm, 1.6*cm, 1.6*cm, 2.0*cm, 3.2*cm,
        1.4*cm, 1.6*cm, 1.6*cm, 0.8*cm, 2.0*cm
    ])
    ep_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.25, colors.HexColor("#CFD8DC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    els.append(ep_table)
    els.append(Spacer(1, 12))

    # Clinical note
    if session.clinical_note:
        els.append(Paragraph("Clinical Note", s["section"]))
        els.append(Paragraph(session.clinical_note, s["body"]))
        els.append(Spacer(1, 8))

    # Footer
    els.append(_hr())
    els.append(Paragraph(
        "This report was generated automatically by the FOG Analysis Portal. "
        "Results should be interpreted by a qualified clinician.",
        s["small"]
    ))

    doc.build(els)
    return buf.getvalue()


# ── Progression Report ────────────────────────────────────────────────────────

def generate_progression_report(subject, sessions: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    s   = _styles()
    els = []

    els.append(Paragraph("FOG Progression Report", s["title"]))
    els.append(Paragraph(
        f"Subject: {subject.id}  |  "
        f"Total Visits: {len(sessions)}  |  "
        f"Generated: {datetime.utcnow().strftime('%d %B %Y, %H:%M UTC')}",
        s["subtitle"]
    ))
    els.append(_hr())

    # Patient info
    els.append(Paragraph("Patient Summary", s["section"]))
    p_data = [
        ["Age", str(subject.age or "—"),
         "Sex", subject.sex or "—",
         "Years Since Dx", str(subject.years_since_dx or "—")],
        ["UPDRS III (On)", str(subject.updrs_on or "—"),
         "UPDRS III (Off)", str(subject.updrs_off or "—"),
         "NFOGQ", str(subject.nfogq_score or "—")],
    ]
    pt = Table(p_data, colWidths=[3*cm, 2.5*cm, 1.5*cm, 2.5*cm, 3*cm, 3*cm])
    pt.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTNAME",  (4, 0), (4, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GREY]),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    els.append(pt)
    els.append(Spacer(1, 12))

    # Visit comparison table
    els.append(Paragraph("Visit-by-Visit Comparison", s["section"]))
    headers = ["Visit", "Date", "Medication", "Episodes",
               "FOG Duration (s)", "FOG Burden %", "Avg Duration (s)", "Dominant Trigger"]
    rows = [headers]
    for sess in sessions:
        rows.append([
            str(sess.visit_number),
            sess.upload_timestamp.strftime("%d %b %Y"),
            sess.medication_status.upper(),
            str(sess.total_fog_episodes),
            f"{sess.total_fog_duration_s:.1f}",
            f"{sess.fog_burden_pct:.1f}%",
            f"{sess.avg_episode_duration_s:.1f}",
            sess.dominant_trigger or "—",
        ])

    vt = Table(rows, colWidths=[1.2*cm, 2.2*cm, 2.2*cm, 1.8*cm,
                                 2.8*cm, 2.2*cm, 2.5*cm, 3.0*cm])
    vt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.25, colors.HexColor("#CFD8DC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    els.append(vt)
    els.append(Spacer(1, 8))

    # Medication comparison
    on_sessions  = [s for s in sessions if s.medication_status == "on"]
    off_sessions = [s for s in sessions if s.medication_status == "off"]
    if on_sessions and off_sessions:
        import numpy as np
        on_burden  = round(float(np.mean([s.fog_burden_pct for s in on_sessions])), 2)
        off_burden = round(float(np.mean([s.fog_burden_pct for s in off_sessions])), 2)
        delta      = round(off_burden - on_burden, 2)
        els.append(Paragraph("Medication Effect", s["section"]))
        els.append(Paragraph(
            f"Average FOG Burden ON medication: <b>{on_burden}%</b> &nbsp;|&nbsp; "
            f"OFF medication: <b>{off_burden}%</b> &nbsp;|&nbsp; "
            f"Delta (Off−On): <b>{delta:+.2f}%</b>",
            s["body"]
        ))

    els.append(_hr())
    els.append(Paragraph(
        "This report was generated automatically by the FOG Analysis Portal. "
        "Results should be interpreted by a qualified clinician.",
        s["small"]
    ))

    doc.build(els)
    return buf.getvalue()
