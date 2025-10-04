import csv, io
from rest_framework import serializers
from .models import *
from itertools import zip_longest


def iter_csv_rows(django_file, delimiter=",", has_header=True, emit_headers=True, encoding="utf-8-sig"):
    """
    Generator: هر سطر = (index, {header: value})
    - utf-8-sig برای حذف BOM
    - try/finally برای برگرداندن موقعیت فایل حتی اگر loop نصفه قطع شود
    - zip_longest برای هماهنگی تعداد ستون‌ها
    """
    pos = django_file.tell()
    try:
        django_file.seek(0)
        text = io.TextIOWrapper(django_file, encoding=encoding, newline="")
        reader = csv.reader(text, delimiter=delimiter)

        first = next(reader, None)
        if first is None:
            if emit_headers and has_header:
                yield ("__headers__", [])
            return

        if has_header:
            headers = [h.strip() for h in first]
            if emit_headers:
                yield ("__headers__", headers)
            start_row = None  # header مصرف شد
        else:
            headers = [f"col_{i}" for i in range(1, len(first)+1)]
            start_row = first  # همین سطر، اولین داده است

        i = 0
        if start_row is not None:
            i += 1
            yield (i, dict(zip_longest(headers, (c.strip() for c in start_row), fillvalue="")))
        for row in reader:
            i += 1
            yield (i, dict(zip_longest(headers, (c.strip() for c in row), fillvalue="")))
    finally:
        django_file.seek(pos)



def coerce_value_for_attribute(attribute: Attribute, raw):
    # نسخه ساده‌شده‌ی همون منطق تک‌فیلدی (value→one-hot)
    from datetime import datetime, date
    ptype = attribute.property_type

    def as_int(v):
        if isinstance(v, bool): raise serializers.ValidationError("int نامعتبر")
        try:
            return int(str(v).strip())
        except: raise serializers.ValidationError("int نامعتبر")

    def as_float(v):
        try:
            s = str(v).strip().replace(",", ".")
            x = float(s)
            if x != x or x in (float("inf"), float("-inf")):
                raise ValueError
            return x
        except: raise serializers.ValidationError("float نامعتبر")

    def as_bool(v):
        if isinstance(v, bool): return v
        s = str(v).strip().lower()
        if s in ("true","yes","on","1"): return True
        if s in ("false","no","off","0"): return False
        raise serializers.ValidationError("bool نامعتبر")

    def as_date(v):
        if isinstance(v, date) and not isinstance(v, datetime): return v
        for fmt in ("%Y-%m-%d","%Y/%m/%d","%d-%m-%Y","%d/%m/%Y"):
            try: return datetime.strptime(str(v).strip(), fmt).date()
            except: continue
        try: return date.fromisoformat(str(v).strip())
        except: raise serializers.ValidationError("date نامعتبر (YYYY-MM-DD)")

    if ptype == Attribute.PropertyType.INT:
        return {"value_int": as_int(raw)}
    if ptype == Attribute.PropertyType.FLOAT:
        return {"value_float": as_float(raw)}
    if ptype == Attribute.PropertyType.STR:
        if raw is None or str(raw) == "": raise serializers.ValidationError("string خالی")
        return {"value_str": str(raw)}
    if ptype == Attribute.PropertyType.BOOL:
        return {"value_bool": as_bool(raw)}
    if ptype == Attribute.PropertyType.DATE:
        return {"value_date": as_date(raw)}
    if ptype == Attribute.PropertyType.CHOICE:
        # جستجوی choice با pk → value__iexact → label__iexact
        qs = AttributeChoice.objects.filter(attribute=attribute)
        s = str(raw).strip()
        # pk
        ch = qs.filter(id=s).first()
        if not ch:
            ch = qs.filter(value__iexact=s).first()
        if not ch:
            ch = qs.filter(label__iexact=s).first()
        if not ch:
            raise serializers.ValidationError("گزینه‌ی معتبر پیدا نشد")
        return {"choice": ch}
    raise serializers.ValidationError("property_type نامعتبر")


def validate_rules_for_asset(asset: Asset, incoming_items: list, replace_all: bool):
    # نسخه کوتاه‌شده‌ی همون متد که قبلاً توضیح دادی
    from collections import defaultdict
    rules = {r.attribute_id: r for r in asset.type_rules.select_related("attribute")}
    incoming_by_attr = defaultdict(list)
    for item in incoming_items:
        incoming_by_attr[item["attribute"].id].append(item)

    for attr_id, items in incoming_by_attr.items():
        rule = rules.get(attr_id)
        if not rule:
            raise serializers.ValidationError(f"خصیصه‌ی {attr_id} برای این دارایی مجاز نیست.")

        incoming_count = len(items)
        if replace_all:
            final_count = incoming_count
        else:
            existing_count = AssetAttributeValue.objects.filter(asset=asset, attribute_id=attr_id).count()
            final_count = existing_count + incoming_count

        if not rule.is_multi and final_count > 1:
            raise serializers.ValidationError(f"{rule.attribute.title} تک‌مقداری است.")

        min_needed = max(1, rule.min_count) if rule.is_required else (rule.min_count or 0)
        if final_count < min_needed:
            raise serializers.ValidationError(f"حداقل {min_needed} مقدار برای {rule.attribute.title} لازم است.")

        if rule.max_count is not None and final_count > rule.max_count:
            raise serializers.ValidationError(f"حداکثر {rule.max_count} مقدار برای {rule.attribute.title} مجاز است.")


def parse_header(header: str):
    """
    تبدیل هدر به asset_title, attr_title, required
    مثلا: "پرینتر3dـسریال*" → ("پرینتر3d", "سریال", True)
    """
    required = header.endswith("*")
    if required:
        header = header[:-1]
    try:
        asset_title, attr_title = header.split("ـ", 1)
    except ValueError:
        return None, None, required
    return asset_title.strip(), attr_title.strip(), required


# --- متد کمکی: تشخیص دارایی بر اساس بیشترین مقدار پر ---
def detect_asset_from_row(row):
    counts = {}
    for col_name, value in row.items():
        if col_name == "unit_label" or not value:
            continue
        asset_title, attr_title, required = parse_header(col_name)
        if asset_title:
            counts[asset_title] = counts.get(asset_title, 0) + 1

    if not counts:
        return None

    selected_asset_title = max(counts.items(), key=lambda kv: kv[1])[0]
    try:
        return Asset.objects.get(title=selected_asset_title)
    except Asset.DoesNotExist:
        return None

# --- متد کمکی: گرفتن Attribute از روی mapping یا parse_header ---
def get_attribute_from_column(col_name, mapping):
    attr_id = mapping.get(col_name) if mapping else None
    if attr_id:
        try:
            return Attribute.objects.get(id=attr_id)
        except Attribute.DoesNotExist:
            return None
    if mapping:
        return None

    # fallback → parse_header
    asset_title, attr_title, required = parse_header(col_name)
    if not attr_title:
        return None
    try:
        return Attribute.objects.get(title=attr_title)
    except Attribute.DoesNotExist:
        return None




