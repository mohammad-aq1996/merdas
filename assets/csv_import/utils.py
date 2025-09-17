import csv
import io
import re
import jdatetime
from datetime import datetime
from typing import Iterator, Tuple, Dict, Any
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import calendar


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



_JALALI_DAYS_IN_MONTH = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

def parse_date_flex(raw: str):
    """
    تاریخ ورودی رو به jdatetime.date برمی‌گردونه (شمسی).
    - ورودی می‌تواند جلالی یا میلادی باشد.
    - فرمت‌های YYYY-MM-DD ، MM-DD-YYYY ، DD-MM-YYYY پشتیبانی می‌شود.
    - اگر روز نامعتبر باشد به آخرین روز همان ماه اصلاح می‌شود.
    """
    s = normalize_str(raw)
    if not s:
        return None

    s = re.sub(r"[\/]", "-", s)
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError("فرمت تاریخ معتبر نیست.")

    nums = [int(x) for x in parts]

    def _safe_gregorian(year, month, day):
        if not (1 <= month <= 12):
            raise ValueError("ماه میلادی معتبر نیست.")
        max_day = calendar.monthrange(year, month)[1]
        day = min(day, max_day)
        return datetime(year, month, day).date()

    def _safe_jalali(year, month, day):
        if not (1 <= month <= 12):
            raise ValueError("ماه جلالی معتبر نیست.")
        max_day = _JALALI_DAYS_IN_MONTH[month - 1]
        if month == 12 and jdatetime.date.isleap(year):
            max_day = 30
        day = min(day, max_day)
        return jdatetime.date(year, month, day)

    # حالت‌های مختلف
    if 1300 <= nums[0] <= 1500:  # YYYY-MM-DD جلالی
        return _safe_jalali(nums[0], nums[1], nums[2])

    if nums[0] > 1900:  # YYYY-MM-DD میلادی
        g_date = _safe_gregorian(nums[0], nums[1], nums[2])
        return jdatetime.date.fromgregorian(date=g_date)

    if nums[2] > 1900:  # MM-DD-YYYY یا DD-MM-YYYY
        year = nums[2]
        if nums[0] > 12:
            day, month = nums[0], nums[1]  # DD-MM-YYYY
        else:
            month, day = nums[0], nums[1]  # MM-DD-YYYY
        g_date = _safe_gregorian(year, month, day)
        return jdatetime.date.fromgregorian(date=g_date)

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
        # تمیز کردن ورودی
        parts = [x.strip() for x in re.split(r"[|,،]", s) if x.strip()]
        if not parts:
            raise serializers.ValidationError("مقدار انتخابی خالی است.")

        valid_choices = set(attribute.choices or [])
        invalid_parts = [p for p in parts if p not in valid_choices]

        if invalid_parts:
            # اینجا بهتره raise نکنیم، چون می‌خوای ثبت بشه تو Issue نه اینکه پروسه کلن fail بشه
            raise serializers.ValidationError(
                f"مقادیر نامعتبر: {', '.join(invalid_parts)} | مقادیر مجاز: {', '.join(valid_choices)}"
            )

        return {"choice": parts}
    return {"value_str": s}


def read_csv_all(django_file, delimiter=",", has_header=True):
    """
    خروجی: (headers: list[str], rows: list[list[str]])
    rows شامل فقط رکوردهاست (بدون هدر) و طول هر row == len(headers)
    """
    with django_file.open("rb") as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")
        reader = csv.reader(text, delimiter=delimiter)
        headers = next(reader, [])
        headers = [str(h).strip() for h in headers] if has_header else [f"col_{i+1}" for i in range(len(headers))]
        rows = []
        if not has_header:
            rows.append(headers.copy())  # first line is actually row1, but we fabricated headers for no-header case
        for row in reader:
            row = list(row) + [""] * (len(headers) - len(row))
            rows.append(row[:len(headers)])
    # اگر no-header بوده، سطر اول عملاً داده بوده؛ در بالا هندل شد
    return headers, rows

def write_csv_all(headers, rows, delimiter=",") -> bytes:
    """CSV را در حافظه می‌سازد و bytes برمی‌گرداند (UTF-8, BOM-safe حذف)."""
    sio = io.StringIO(newline="")
    writer = csv.writer(sio, delimiter=delimiter)
    writer.writerow(headers)
    for r in rows:
        writer.writerow([(x if x is not None else "") for x in r])
    data = sio.getvalue().encode("utf-8")
    return data


def overwrite_session_file(session, content_bytes: bytes):
    """
    فایل session را با محتوای جدید جایگزین می‌کند (همان نام/مسیر).
    """
    path = session.file.name
    # حذف فایل قبلی (اگر روی S3 هست، مشکلی ندارد)
    try:
        default_storage.delete(path)
    except Exception:
        pass
    default_storage.save(path, ContentFile(content_bytes))