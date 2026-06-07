from __future__ import annotations

import re

import numpy as np
import pandas as pd


COUNTRY_NORMALIZATION = {
    "usa": "United States",
    "u.s.a": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "uae": "United Arab Emirates",
    "u.a.e": "United Arab Emirates",
    "south korea": "Korea, Republic Of",
    "korea": "Korea, Republic Of",
    "korea republic of": "Korea, Republic Of",
    "russia": "Russian Federation",
    "czech republic": "Czechia",
    "viet nam": "Vietnam",
}


def standardize_country(country_name: object) -> str | float:
    if pd.isna(country_name):
        return np.nan

    normalized = str(country_name).replace("_", " ").strip()
    if not normalized:
        return np.nan

    key = normalized.lower()
    if key in COUNTRY_NORMALIZATION:
        return COUNTRY_NORMALIZATION[key]

    return normalized.title()


def parse_numeric(value: object) -> float:
    if pd.isna(value):
        return np.nan

    text = str(value)
    text = text.replace(",", "")
    text = re.sub(r"[^0-9.\-]", "", text)

    if not text:
        return np.nan

    try:
        return float(text)
    except ValueError:
        return np.nan


def normalize_bool(value: object) -> bool | float:
    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "false", "f", "no", "n"}:
        return False
    return np.nan
