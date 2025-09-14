from typing import Dict, Set
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from assets.models import (
    Asset, AssetUnit, Attribute, AssetAttributeValue,
    ImportSession, ImportIssue, AssetTypeAttribute
)
from .utils import iter_csv_rows, normalize_str, coerce_value_for_attribute


class CsvImportService:
    """
    Create-only Import Service:
      - اگر Asset با title پیدا نشود → ERROR و سطر رد می‌شود.
      - اگر Unit (asset, label) از قبل باشد → WARN و سطر نادیده گرفته می‌شود.
      - اگر خصیصه‌های الزامی مقدار نداشته باشند → is_registered=False می‌ماند.
      - مقادیر موجود ذخیره می‌شوند تا بعداً کاربر بتواند ویرایش کند.
    """

    def __init__(self, session: ImportSession, user):
        self.session = session
        self.user = user
        self.attr_cache: Dict[str, Attribute] = {}
        if self.session.attribute_map:
            qs = Attribute.objects.filter(id__in=self.session.attribute_map.values())
            self.attr_cache.update({str(a.id): a for a in qs})

    def run(self) -> Dict[str, int]:
        s = self.session
        s.issues.all().delete()

        stats = dict(units_created=0, rows_skipped=0, values_created=0, errors=0, warnings=0)
        seen: Set[tuple] = set()

        for idx, row in iter_csv_rows(s.file, delimiter=s.delimiter, has_header=s.has_header):
            if idx == "__headers__":
                continue

            asset_ref = normalize_str(row.get(s.asset_column))
            unit_label = normalize_str(row.get(s.unit_label_column))

            if not asset_ref:
                self._issue(idx, None, None, code="ASSET_REF_EMPTY", msg="ستون دارایی خالی است")
                stats["errors"] += 1
                continue
            if not unit_label:
                self._issue(idx, asset_ref, None, code="UNIT_LABEL_EMPTY", msg="label نمونه (unit) خالی است")
                stats["errors"] += 1
                continue

            try:
                asset = Asset.objects.get(title=asset_ref)
            except Asset.DoesNotExist:
                self._issue(idx, asset_ref, None, code="ASSET_NOT_FOUND",
                            msg=f"دارایی با title={asset_ref} یافت نشد")
                stats["errors"] += 1
                continue

            key = (str(asset.pk), unit_label)
            if key in seen:
                self._issue(idx, asset_ref, unit_label, asset=asset, level=ImportIssue.Level.WARN,
                            code="DUPLICATE_ROW_SKIPPED",
                            msg="این ترکیب asset+unit_label قبلاً در همین ایمپورت دیده شد.")
                stats["rows_skipped"] += 1
                stats["warnings"] += 1
                continue

            if AssetUnit.objects.filter(asset=asset, label=unit_label).only("id").exists():
                self._issue(idx, asset_ref, unit_label, asset=asset, level=ImportIssue.Level.WARN,
                            code="UNIT_ALREADY_EXISTS_SKIPPED",
                            msg="برای این دارایی، یونیتی با این label از قبل وجود دارد. سطر نادیده گرفته شد.")
                stats["rows_skipped"] += 1
                stats["warnings"] += 1
                seen.add(key)
                continue

            with transaction.atomic():
                # ✅ ساخت Unit با is_registered=False به‌صورت پیش‌فرض
                unit = AssetUnit.objects.create(asset=asset, label=unit_label, is_registered=False)
                stats["units_created"] += 1
                seen.add(key)

                # ✅ پیدا کردن خصیصه‌های الزامی
                # required_attrs = Attribute.objects.filter(
                #     id__in=AssetTypeAttribute.objects.filter(
                #         asset_type=asset.asset_type,
                #         is_required=True
                #     ).values_list("attribute_id", flat=True)
                # )
                required_attrs = AssetTypeAttribute.objects.filter(
                        asset=asset,
                        is_required=True
                    ).values_list("attribute", flat=True)
                # ✅ نگاشت خصیصه‌ها
                effective_map = dict(s.attribute_map) if s.attribute_map else {}
                if not effective_map:
                    for col_name, raw_val in row.items():
                        if col_name in (s.asset_column, s.unit_label_column):
                            continue
                        if raw_val is None or str(raw_val).strip() == "":
                            continue
                        attr = Attribute.objects.filter(Q(title=col_name) | Q(title_en=col_name)).first()
                        if attr:
                            effective_map[col_name] = str(attr.id)
                        else:
                            self._issue(idx, asset_ref, unit_label, asset=asset, unit=unit,
                                        level=ImportIssue.Level.WARN, code="ATTR_NOT_FOUND",
                                        msg=f"ستون '{col_name}' به خصیصه‌ای نگاشت نشد؛ نادیده گرفته شد.")
                            stats["warnings"] += 1

                # ✅ بررسی مقادیر الزامی
                missing_required = []
                for ra in required_attrs:
                    raw_val = None
                    for col, attr_id in effective_map.items():
                        if attr_id == str(ra.id):
                            raw_val = row.get(col)
                            break
                    if raw_val is None or str(raw_val).strip() == "":
                        missing_required.append(ra.title)

                if missing_required:
                    self._issue(idx, asset_ref, unit_label, asset=asset, unit=unit,
                                code="REQUIRED_ATTR_MISSING",
                                msg=f"خصیصه‌های الزامی بدون مقدار: {', '.join(missing_required)}")
                    stats["errors"] += 1
                    unit.is_registered=False
                else:
                    unit.is_registered = True
                    unit.save(update_fields=["is_registered"])

                # ✅ ساخت AAVها حتی اگر ناقص باشد
                for col, attr_id in effective_map.items():
                    raw_val = row.get(col, None)
                    if raw_val is None or str(raw_val).strip() == "":
                        continue
                    try:
                        attribute = self.attr_cache.get(attr_id) or Attribute.objects.get(pk=attr_id)
                        self.attr_cache.setdefault(attr_id, attribute)

                        payload = coerce_value_for_attribute(attribute, raw_val)
                        aav = AssetAttributeValue(
                            asset=asset,
                            unit=unit,
                            attribute=attribute,
                            value_int=payload.get("value_int"),
                            value_float=payload.get("value_float"),
                            value_str=payload.get("value_str"),
                            value_bool=payload.get("value_bool"),
                            value_date=payload.get("value_date"),
                            choice=payload.get("choice"),
                        )
                        if hasattr(aav, "owner"):
                            aav.owner = self.user
                        aav.save()
                        stats["values_created"] += 1
                    except Attribute.DoesNotExist:
                        self._issue(idx, asset_ref, unit_label, asset=asset, unit=unit,
                                    code="ATTR_NOT_FOUND", msg=f"خصیصه با id={attr_id} یافت نشد")
                        stats["errors"] += 1
                    except serializers.ValidationError as e:
                        self._issue(idx, asset_ref, unit_label, asset=asset, unit=unit,
                                    code="TYPE_INVALID",
                                    msg=f"خصیصه '{getattr(attribute,'title','?')}': {getattr(e, 'detail', e)}")
                        stats["errors"] += 1

        s.state = ImportSession.State.COMMITTED
        s.save(update_fields=["state"])
        return stats

    def _issue(self, idx, asset_ref, unit_label, *, asset=None, unit=None,
               code: str, msg: str, level=ImportIssue.Level.ERROR):
        ImportIssue.objects.create(
            session=self.session, row_index=idx, asset_ref=asset_ref, asset=asset,
            unit_label=unit_label, unit=unit, code=code, message=msg, level=level
        )
