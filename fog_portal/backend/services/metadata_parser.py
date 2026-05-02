"""
Metadata parser — extracts medication status and subject info.

File responsibilities:
  tdcsfog_metadata.csv  → columns: Id, Subject, Visit, Test, Medication
                          'Id' is the series/recording ID (matches CSV filename)
                          'Subject' is the actual patient ID for subjects.csv lookup
  subjects.csv          → columns: Subject, Visit, Age, Sex, YearsSinceDx,
                                    UPDRSIII_On, UPDRSIII_Off, NFOGQ
"""

import pandas as pd
import io
from typing import Optional, Tuple


def extract_subject(
    fog_metadata_bytes: bytes,
    series_id: str,
) -> Optional[str]:
    """
    Parse tdcsfog_metadata.csv.
    Returns subject_id for the given series_id, or None if not found.

    tdcsfog_metadata.csv columns: Id, Subject, Visit, Test, Medication
    """
    try:
        df = pd.read_csv(io.BytesIO(fog_metadata_bytes))
        df.columns = df.columns.str.strip()

        if "Id" not in df.columns or "Subject" not in df.columns:
            return None

        row = df[df["Id"] == series_id]
        if row.empty:
            return None

        r   = row.iloc[0]

        # Extract the Subject column to use for subjects.csv lookup
        subj = str(r["Subject"]).strip() if "Subject" in df.columns else None
        subj = subj if subj and subj.lower() != "nan" else None

        return subj
    except Exception:
        return None


def extract_subject_metadata(
    subjects_bytes: bytes,
    subject_id: str,       # This is the Subject value from tdcsfog_metadata.csv
) -> dict:
    """
    Parse subjects.csv and return demographic/clinical metadata dict.
    subject_id here is the 'Subject' column value (not the series Id).

    subjects.csv columns: Subject, Visit, Age, Sex, YearsSinceDx,
                          UPDRSIII_On, UPDRSIII_Off, NFOGQ
    """
    result = {
        "age":            None,
        "sex":            None,
        "years_since_dx": None,
        "updrs_on":       None,
        "updrs_off":      None,
        "nfogq_score":    None,
    }

    if not subject_id:
        return result

    try:
        df = pd.read_csv(io.BytesIO(subjects_bytes))
        df.columns = df.columns.str.strip()

        if "Subject" not in df.columns:
            return result

        row = df[df["Subject"] == subject_id]
        if row.empty:
            # Try numeric match in case of type mismatch
            try:
                row = df[df["Subject"].astype(str) == str(subject_id)]
            except Exception:
                pass
        if row.empty:
            return result

        r = row.iloc[0]

        def safe_float(col):
            try:
                return float(r[col]) if col in df.columns else None
            except Exception:
                return None

        def safe_str(col):
            try:
                v = str(r[col]).strip() if col in df.columns else None
                return v if v and v.lower() not in ("nan", "none", "") else None
            except Exception:
                return None

        result["age"]            = safe_float("Age")
        result["sex"]            = safe_str("Sex")
        result["years_since_dx"] = safe_float("YearsSinceDx")
        result["updrs_on"]       = safe_float("UPDRSIIIOn")   # exact column name
        result["updrs_off"]      = safe_float("UPDRSIIIOff")  # exact column name
        result["nfogq_score"]    = safe_float("NFOGQ")

    except Exception:
        pass

    return result
