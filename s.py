import os
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from rapidfuzz import process, fuzz

def read_excel_smart(path: str | Path) -> pd.DataFrame:
    """Read Excel file into pandas with engine auto-detection."""
    path = str(path)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xls":
        return pd.read_excel(path, engine="xlrd")
    return pd.read_excel(path, engine="openpyxl")

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d.columns = (
        d.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )
    return d

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.split())

def prepare_siddha(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = normalize_headers(df_raw)
    if "namc_code" not in df.columns:
        raise ValueError("Siddha dataset must have NAMC_CODE")
    df = df.copy()
    df["__text"] = df.get("short_definition", df.get("namc_term", "")).astype(str)
    df["__norm"] = df["__text"].map(normalize_text)
    df["__discipline"] = "Siddha"
    df["__code_str"] = df["namc_code"].astype(str).str.strip()
    return df[df["__norm"] != ""]


def prepare_unani(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = normalize_headers(df_raw)
    if "numc_code" not in df.columns:
        raise ValueError("Unani dataset must have NUMC_CODE")
    df = df.copy()
    df["__text"] = df.get("short_definition", df.get("numc_term", "")).astype(str)
    df["__norm"] = df["__text"].map(normalize_text)
    df["__discipline"] = "Unani"
    df["__code_str"] = df["numc_code"].astype(str).str.strip()
    return df[df["__norm"] != ""]


def build_search_space(sid: pd.DataFrame, una: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([sid, una], ignore_index=True)

def find_exact(base: pd.DataFrame, q_norm: str) -> Optional[pd.Series]:
    hits = base[base["__norm"] == q_norm]
    return hits.iloc[0] if not hits.empty else None

def find_partial(base: pd.DataFrame, q_norm: str) -> Optional[pd.Series]:
    hits = base[base["__norm"].str.contains(q_norm, na=False)]
    return hits.iloc[0] if not hits.empty else None

def find_fuzzy(
    base: pd.DataFrame,
    q_norm: str,
    top_k: int = 5,
    threshold: int = 85
) -> List[Tuple[str, float, int]]:
    if base.empty:
        return []
    choices = base["__norm"].tolist()
    results = process.extract(q_norm, choices, scorer=fuzz.token_sort_ratio, limit=top_k)
    return [(c, float(score), int(idx)) for (c, score, idx) in results if score >= threshold]


def pick_row_by_index(base: pd.DataFrame, idx: int) -> Optional[pd.Series]:
    if idx < 0 or idx >= len(base):
        return None
    return base.iloc[idx]


def prepare_merged(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    if "sidha_code" in df.columns:
        df.rename(columns={"sidha_code": "siddha_code"}, inplace=True)
    for c in ("siddha_code", "unani_code"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    return df


def lookup_merged(merged: pd.DataFrame, discipline: str, code_str: str) -> Optional[pd.Series]:
    if merged is None or merged.empty:
        return None
    col = "siddha_code" if discipline.lower() == "siddha" else "unani_code"
    if col not in merged.columns:
        return None
    m = merged[merged[col] == code_str.strip()]
    return m.iloc[0] if not m.empty else None

def make_result(row: pd.Series, merged_row: Optional[pd.Series], suggestions: List[Dict] | None = None) -> Dict:
    return {
        "discipline": row["__discipline"],
        "code": row["__code_str"],
        "label": row["__text"],
        "merged": merged_row.to_dict() if merged_row is not None else None,
        "suggestions": suggestions or []
    }

def search_disease(
    disease_name: str,
    siddha_df: pd.DataFrame,
    unani_df: pd.DataFrame,
    merged_df: pd.DataFrame,
    fuzzy_top_k: int = 5,
    fuzzy_threshold: int = 85
) -> Dict:
    q_norm = normalize_text(disease_name)
    sid = prepare_siddha(siddha_df)
    una = prepare_unani(unani_df)
    base = build_search_space(sid, una)

    # exact
    row = find_exact(base, q_norm)
    if row is not None:
        m = lookup_merged(merged_df, row["__discipline"], row["__code_str"])
        return make_result(row, m)

    # partial
    row = find_partial(base, q_norm)
    if row is not None:
        m = lookup_merged(merged_df, row["__discipline"], row["__code_str"])
        return make_result(row, m)

    # fuzzy → return suggestions
    suggestions_out: List[Dict] = []
    for choice, score, idx in find_fuzzy(base, q_norm, top_k=fuzzy_top_k, threshold=fuzzy_threshold):
        srow = pick_row_by_index(base, idx)
        if srow is None:
            continue
        suggestions_out.append({
            "discipline": srow["__discipline"],
            "code": srow["__code_str"],
            "label": srow["__text"],
            "score": score
        })

    if suggestions_out:
        return {
            "error": "No exact/partial match; showing fuzzy suggestions",
            "suggestions": suggestions_out
        }

    return {"error": "No match found in Siddha or Unani."}
