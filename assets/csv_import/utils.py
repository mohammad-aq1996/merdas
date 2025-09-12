import csv
import io
import re
import jdatetime
from datetime import datetime
from typing import Iterator, Tuple, Dict, Any

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

def normalize_str(x: Any) -> str | None:
    if x is None:
        return None
    s = str(x).strip().translate(PERSIAN_DIGITS)
    return s if s != "" else None


def iter_csv_rows(django_file, delimiter=",", has_header=True) -> Iterator[Tuple[int | str, Any]]:
    """
    خروجی:
      ("__headers__", ["h1","h2",...])
      (1, {"h1": "...", "h2": "...", ...}), ...
    """
    with django_file.open("rb") as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")
        reader = csv.reader(text, delimiter=delimiter)

        if has_header:
            headers = next(reader, None) or []
            headers = [str(h).strip() for h in headers]
            yield ("__headers__", headers)
            for idx, row in enumerate(reader, start=1):
                row = list(row) + [""] * (len(headers) - len(row))
                yield (idx, {headers[i]: row[i] for i in range(len(headers))})
        else:
            first = next(reader, None)
            if first is None:
                yield ("__headers__", [])
                return
            headers = [f"col_{i+1}" for i in range(len(first))]
            yield ("__headers__", headers)
            yield (1, {headers[i]: first[i] for i in range(len(first))})
            for idx, row in enumerate(reader, start=2):
                row = list(row) + [""] * (len(headers) - len(row))
                yield (idx, {headers[i]: row[i] for i in range(len(headers))})


def parse_date_flex(s: str):
    s = normalize_str(s)
    if not s:
        return None
    # جلالی: 13xx یا 14xx
    if re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", s) and (s.startswith("13") or s.startswith("14")):
        fmt = "%Y/%m/%d" if "/" in s else "%Y-%m-%d"
        return jdatetime.datetime.strptime(s, fmt).togregorian().date()
    # میلادی
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError("فرمت تاریخ معتبر نیست.")


def coerce_value_for_attribute(attribute, raw):
    """برگرداندن dict مناسب یکی از value_* بر اساس نوع خصیصه."""
    from rest_framework import serializers
    s = normalize_str(raw)
    if s is None:
        raise serializers.ValidationError("مقدار خالی است.")

    p = attribute.property_type  # با enum مدل خودت هماهنگ است
    if p == attribute.PropertyType.INT:
        try:
            return {"value_int": int(s)}
        except Exception:
            raise serializers.ValidationError("عدد صحیح معتبر نیست.")
    if p == attribute.PropertyType.FLOAT:
        try:
            return {"value_float": float(s.replace(",", "."))}
        except Exception:
            raise serializers.ValidationError("عدد اعشاری معتبر نیست.")
    if p == attribute.PropertyType.BOOL:
        t, f = {"true","1","yes","on","y","t","بلی","بله"}, {"false","0","no","off","n","f","خیر"}
        ls = s.lower()
        if ls in t: return {"value_bool": True}
        if ls in f: return {"value_bool": False}
        raise serializers.ValidationError("بولین معتبر نیست.")
    if p == attribute.PropertyType.DATE:
        try:
            return {"value_date": parse_date_flex(s)}
        except Exception:
            raise serializers.ValidationError("تاریخ معتبر نیست.")
    if p == attribute.PropertyType.CHOICE:
        parts = [x.strip() for x in re.split(r"[|,،]", s) if x.strip()]
        if not parts:
            raise serializers.ValidationError("مقدار انتخابی خالی است.")
        return {"choice": parts}
    return {"value_str": s}
