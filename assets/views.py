from django.forms.models import model_to_dict

from drf_spectacular.utils import extend_schema

from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework import status

from core.utils import CustomResponse
from core.persian_response import *
from .serializers import *
from .models import *
from .utils import iter_csv_rows, coerce_value_for_attribute, validate_rules_for_asset


class AttributeCategoryListCreateView(APIView):
    queryset = AttributeCategory.objects.all()

    @extend_schema(responses=AttributeCategorySerializer)
    def get(self, request):
        categories = AttributeCategory.objects.all()
        serializer = AttributeCategorySerializer(categories, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=AttributeCategorySerializer, request=AttributeCategorySerializer)
    def post(self, request):
        serializer = AttributeCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttributeCategoryDetailView(APIView):
    queryset = AttributeCategory.objects.all()

    @extend_schema(responses=AttributeCategorySerializer)
    def get(self, request, pk):
        try:
            categories = AttributeCategory.objects.get(pk=pk)
        except AttributeCategory.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AttributeCategorySerializer(categories)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=AttributeCategorySerializer, request=AttributeCategorySerializer)
    def put(self, request, pk):
        try:
            categories = AttributeCategory.objects.get(pk=pk)
        except AttributeCategory.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AttributeCategorySerializer(categories, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            sr = AttributeCategory.objects.get(pk=pk)
        except AttributeCategory.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        sr.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class AttributeListCreateView(APIView):
    queryset = Attribute.objects.all()

    @extend_schema(responses=AttributeSerializer)
    def get(self, request):
        attributes = Attribute.objects.all()
        serializer = AttributeSerializer(attributes, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=AttributeSerializer, request=AttributeSerializer)
    def post(self, request):
        serializer = AttributeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttributeDetailView(APIView):
    queryset = Attribute.objects.all()

    @extend_schema(responses=AttributeSerializer)
    def get(self, request, pk):
        try:
            attribute = Attribute.objects.get(pk=pk)
        except Attribute.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AttributeSerializer(attribute)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=AttributeSerializer, request=AttributeSerializer)
    def put(self, request, pk):
        try:
            attribute = Attribute.objects.get(pk=pk)
        except Attribute.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AttributeSerializer(attribute, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            attribute = Attribute.objects.get(pk=pk)
        except Attribute.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        attribute.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class AssetListCreateView(APIView):
    queryset = Asset.objects.all()

    @extend_schema(responses=AssetReadSerializer)
    def get(self, request):
        assets = Asset.objects.all()
        serializer = AssetReadSerializer(assets, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=AssetReadSerializer, request=AssetCreateUpdateSerializer)
    def post(self, request):
        serializer = AssetCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer = serializer.save(owner=request.user)
            output_serializer = AssetReadSerializer(serializer)
            return CustomResponse.success(message=create_data(), data=output_serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetDetailView(APIView):
    queryset = Asset.objects.all()

    @extend_schema(responses=AssetReadSerializer)
    def get(self, request, pk):
        try:
            asset = Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AssetReadSerializer(asset)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=AssetReadSerializer, request=AssetCreateUpdateSerializer)
    def put(self, request, pk):
        try:
            asset = Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AssetCreateUpdateSerializer(asset, data=request.data)
        if serializer.is_valid():
            serializer = serializer.save(owner=request.user)
            output_serializer = AssetReadSerializer(serializer)
            return CustomResponse.success(message=update_data(), data=output_serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            asset = Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        asset.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class AssetAttributesView(APIView):
    queryset = Asset.objects.all()

    @extend_schema(responses=AssetAttributeSerializer, request=AssetAttributeSerializer)
    def post(self, request):
        asset_type = request.data.get('asset_type')
        asset_id = request.data.get('asset_id')

        if not asset_type or not asset_id:
            return CustomResponse.error('پارامترها ناقص هستند')

        asset = Asset.objects.filter(pk=asset_id).first()
        if not asset:
            return CustomResponse.error('دارایی پیدا نشد')

        asset_type_attr = asset.type_rules.select_related('attribute__category')
        result = {}

        for type_rule in asset_type_attr:
            category = type_rule.attribute.category
            attr_data = {**model_to_dict(type_rule.attribute),
                         'is_required': type_rule.is_required,
                         'is_multi': type_rule.is_multi,
                         'id': type_rule.attribute.id}
            cat_label = category.title if category else "uncategorized"
            result.setdefault(cat_label, []).append(attr_data)

        return CustomResponse.success(message=get_all_data(), data=result)


"""
{
  "asset": "862656ad-2864-4767-ba05-ff34db20aaa4",
  "attribute_values": [
    {
      "attribute": "9f098939-16f0-40a4-b953-251da5874fca",
      "value": 30
    },
    {
      "attribute": "7296cc24-eee4-4b49-a87a-72fc47e6435a",
      "value": 25
    }
  ],
  "relations": [
    {
      "relation": "e9716cbf-150c-45d1-b5bc-c062b6939367",
      "target_asset": "ac8f0184-4158-4dea-b37a-b724e9f490f3"    }
  ]
}
"""
class AssetAttributeValueView(APIView):
    queryset = AssetAttributeValue.objects.all()

    def get(self, request, asset_id):
        try:
            asset = Asset.objects.get(pk=asset_id)
        except Asset.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد', status=status.HTTP_404_NOT_FOUND)

        values_qs = (
            AssetAttributeValue.objects
            .filter(asset=asset)
            .select_related("attribute", "attribute__category", "choice")
        )

        relations_qs = (
            AssetRelation.objects
            .filter(source_asset=asset)
            .select_related("relation", "target_asset")
            .order_by("relation__key", "target_asset__title")
        )

        serializer = AssetValuesResponseSerializer(
            instance=asset,
            context={
                "values": values_qs,
                "relations": relations_qs,
            }
        )
        return CustomResponse.success(message=get_single_data(), data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=AssetAttributeValueUpsertSerializer, responses=None)
    def post(self, request):
        ser = AssetAttributeValueUpsertSerializer(data=request.data, context={"owner": request.user})
        if not ser.is_valid():
            return CustomResponse.error(message="ناموفق", errors=ser.errors, status=status.HTTP_400_BAD_REQUEST)
        summary = ser.save()
        return CustomResponse.success(message=create_data(), data=summary, status=status.HTTP_201_CREATED)

    @extend_schema(request=AssetAttributeValueUpsertSerializer, responses=None)
    def put(self, request, asset_id: str):
        try:
            asset = Asset.objects.get(asset=asset_id)
        except Asset.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد', status=status.HTTP_404_NOT_FOUND)

        ser = AssetAttributeValueUpsertSerializer(
            instance=asset,  # باعث فراخوانی update می‌شود
            data=request.data,
            context={"owner": request.user},
            partial=False
        )
        if not ser.is_valid():
            return CustomResponse.error(message="ناموفق", errors=ser.errors, status=status.HTTP_400_BAD_REQUEST)
        summary = ser.save()
        return CustomResponse.success(message=update_data(), data=summary, status=status.HTTP_200_OK)


class RelationListCreateView(APIView):
    queryset = Relation.objects.all()

    def get(self, request):
        relations = Relation.objects.all()
        serializer = RelationSerializer(relations, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=RelationSerializer, request=RelationSerializer)
    def post(self, request):
        serializer = RelationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RelationDetailView(APIView):
    queryset = Relation.objects.all()

    def get(self, request, pk):
        try:
            relation = Relation.objects.get(pk=pk)
        except Relation.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = RelationSerializer(relation)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=RelationSerializer, request=RelationSerializer)
    def put(self, request, pk):
        try:
            relation = Relation.objects.get(pk=pk)
        except Relation.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = RelationSerializer(relation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            relation = Relation.objects.get(pk=pk)
        except Relation.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        relation.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)



class AttributeChoiceListCreateView(APIView):
    queryset = AttributeChoice.objects.all()

    def get(self, request):
        qs = AttributeChoice.objects.select_related("attribute")
        serializer = AttributeChoiceSerializer(qs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(request=AttributeChoiceSerializer, responses=AttributeChoiceSerializer)
    def post(self, request):
        serializer = AttributeChoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return CustomResponse.success(message=create_data(), data=serializer.data,
                                          status=status.HTTP_201_CREATED)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors,
                                    status=status.HTTP_400_BAD_REQUEST)


class AttributeChoiceDetailView(APIView):
    queryset = AttributeChoice.objects.all()

    def get_object(self, pk):
        try:
            return AttributeChoice.objects.get(pk=pk)
        except AttributeChoice.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد', status=status.HTTP_404_NOT_FOUND
                                        )
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = AttributeChoiceSerializer(obj)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(request=AttributeChoiceSerializer, responses=AttributeChoiceSerializer)
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = AttributeChoiceSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


# ----------------- Upload -------------------


class CsvUploadView(APIView):
    queryset = ImportSession.objects.all()

    @extend_schema(request=CsvUploadSerializer, responses=None)
    def post(self, request):
        ser = CsvUploadSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)

        f = ser.validated_data["file"]
        has_header = ser.validated_data["has_header"]
        delimiter = ser.validated_data["delimiter"]

        session = ImportSession.objects.create(
            file=f, filename=f.name, has_header=has_header, delimiter=delimiter, created_by=request.user
        )

        # استخراج headers, preview و total_rows
        headers = []
        preview = []
        total = 0
        for idx, row in iter_csv_rows(session.file, delimiter=delimiter, has_header=has_header):
            if idx == "__headers__":
                headers = row
                continue
            total += 1
            if len(preview) < 10:
                preview.append(row)

        session.headers = headers
        session.preview_rows = preview
        session.total_rows = total
        session.save(update_fields=["headers","preview_rows","total_rows"])

        data = {
            "session_id": str(session.id),
            "filename": session.filename,
            "headers": headers,
            "preview": preview,
            "total_rows": total,
            "state": session.state,
        }
        return CustomResponse.success(message="فایل بارگذاری شد", data=data, status=status.HTTP_201_CREATED)


class CsvMappingView(APIView):
    queryset = ImportSession.objects.all()

    @extend_schema(request=CsvMappingSerializer, responses=None)
    def post(self, request):
        ser = CsvMappingSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)

        sid = ser.validated_data["session_id"]
        try:
            session = ImportSession.objects.get(pk=sid)
        except ImportSession.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد')

        asset_column = ser.validated_data["asset_column"]
        asset_lookup_field = ser.validated_data["asset_lookup_field"]
        attr_map = ser.validated_data["attribute_map"]  # {"col":"uuid", ...}

        # صحت هدرها
        if asset_column not in session.headers:
            return CustomResponse.error("ستون دارایی در هدر CSV پیدا نشد", status=status.HTTP_400_BAD_REQUEST)

        for col, attr_id in attr_map.items():
            if col not in session.headers:
                return CustomResponse.error(f"ستون {col} در هدر CSV نیست", status=status.HTTP_400_BAD_REQUEST)
            if not Attribute.objects.filter(pk=attr_id).exists():
                return CustomResponse.error(f"خصیصه با id={attr_id} یافت نشد", status=status.HTTP_400_BAD_REQUEST)

        # ذخیره‌ی مپینگ
        session.asset_column = asset_column
        session.asset_lookup_field = asset_lookup_field
        session.attribute_map = {col: str(attr_id) for col, attr_id in attr_map.items()}
        session.state = ImportSession.State.MAPPED
        session.save(update_fields=["asset_column","asset_lookup_field","attribute_map","state"])

        return CustomResponse.success(message="مپینگ ثبت شد", data={"session_id": str(session.id)})


class CsvEditsView(APIView):
    @extend_schema(request=CsvEditRowsSerializer, responses=None)
    def post(self, request):
        ser = CsvEditRowsSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)
        sid = ser.validated_data["session_id"]
        try:
            session = ImportSession.objects.get(pk=sid)
        except ImportSession.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد')

        # برای سادگی: ویرایش‌ها را روی فایل اصلی اعمال نمی‌کنیم؛
        # یک ساختار edits در DB ذخیره می‌کنیم (ستون→مقدار) برای هر row_index.
        # اینجا برای brevity نگه نمی‌داریم؛ اگر خواستی اضافه می‌کنم: ImportRowEdit مدل.
        session.state = ImportSession.State.EDITED
        session.save(update_fields=["state"])
        return CustomResponse.success(message="ویرایش‌ها ثبت شد (placeholder)", data={"session_id": str(session.id)})


class CsvCommitView(APIView):
    @extend_schema(request=CsvCommitSerializer, responses=None)
    def post(self, request):
        ser = CsvCommitSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)
        sid = ser.validated_data["session_id"]
        mode = ser.validated_data["mode"]  # "append" | "replace"

        try:
            session = ImportSession.objects.get(pk=sid)
        except ImportSession.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد')
        if session.state not in [ImportSession.State.MAPPED, ImportSession.State.EDITED]:
            return CustomResponse.error("ابتدا مپینگ را تکمیل کنید", status=status.HTTP_400_BAD_REQUEST)

        # پیش‌واکشی خصیصه‌ها
        attr_ids = list(session.attribute_map.values())
        attrs = Attribute.objects.filter(id__in=attr_ids).select_related("category")
        attr_by_id = {str(a.id): a for a in attrs}

        # برای asset lookup
        lookup_field = session.asset_lookup_field

        # پاک‌سازی issues قبلی
        session.issues.all().delete()

        created_values = 0
        updated_assets = set()
        assets_with_issues = set()

        # پردازش
        """
        id,name,age
        1,Ali,23
        2,Sara,30
        
        ("__headers__", ["id", "name", "age"])
        (1, {"id": "1", "name": "Ali", "age": "23"})
        (2, {"id": "2", "name": "Sara", "age": "30"})
        """
        for idx, row in iter_csv_rows(session.file, delimiter=session.delimiter, has_header=session.has_header):
            if idx == "__headers__":
                continue

            asset_ref = row.get(session.asset_column, "").strip() if row.get(session.asset_column) is not None else ""
            if not asset_ref:
                ImportIssue.objects.create(
                    session=session, row_index=idx, asset_ref=None, code="ASSET_REF_EMPTY",
                    message="ستون دارایی خالی است", level=ImportIssue.Level.ERROR
                )
                continue

            # پیدا کردن دارایی
            try:
                asset = Asset.objects.get(title=asset_ref)

                # if lookup_field == "id":
                #     asset = Asset.objects.get(pk=asset_ref)
                # elif lookup_field == "code":
                #     asset = Asset.objects.get(code=asset_ref)
                # else:
                #     asset = Asset.objects.get(title=asset_ref)

            except Asset.DoesNotExist:
                ImportIssue.objects.create(
                    session=session, row_index=idx, asset_ref=asset_ref, code="ASSET_NOT_FOUND",
                    message=f"دارایی با {lookup_field}={asset_ref} یافت نشد", level=ImportIssue.Level.ERROR
                )
                assets_with_issues.add(asset_ref)
                continue

            # آماده‌سازی ورودی‌های attribute_values برای این سطر
            incoming_items = []
            row_issues = []
            # {'col1': 'attr_id', ...}
            for col, attr_id in session.attribute_map.items():
                raw_val = row.get(col, None)
                if raw_val is None or str(raw_val).strip() == "":
                    # خالی بودن مقدار: بعداً در requiredها بررسی می‌شود
                    continue

                attribute = attr_by_id.get(attr_id)
                if not attribute:
                    row_issues.append(("ATTR_NOT_FOUND", f"خصیصه با id={attr_id} یافت نشد"))
                    continue

                # تبدیل به one-hot (مثل Serializer تک‌فیلدی که قبلاً نوشتیم)
                try:
                    coerced = coerce_value_for_attribute(attribute, raw_val)  # تابع کمکی پایین
                    item = {"attribute": attribute, **coerced}  # مثلا {"value_int": 12}
                    incoming_items.append(item)
                except serializers.ValidationError as e:
                    row_issues.append(("TYPE_INVALID", f"{attribute.title}: {e.detail if hasattr(e,'detail') else e}"))

            # قوانین type_rules (برای این Asset)
            try:
                validate_rules_for_asset(asset, incoming_items, replace_all=(mode=="replace"))
            except serializers.ValidationError as e:
                row_issues.append(("RULE_VIOLATION", str(e.detail if hasattr(e, 'detail') else e)))

            # ذخیره‌سازی (اتمیک برای هر ردیف)
            with transaction.atomic():
                if mode == "replace":
                    AssetAttributeValue.objects.filter(asset=asset).delete()

                for item in incoming_items:
                    aav = AssetAttributeValue(
                        asset=asset,
                        attribute=item["attribute"],
                        value_int=item.get("value_int"),
                        value_float=item.get("value_float"),
                        value_str=item.get("value_str"),
                        value_bool=item.get("value_bool"),
                        value_date=item.get("value_date"),
                        choice=item.get("choice"),
                        status=AssetAttributeValue.Status.REGISTERED,
                        owner=request.user
                    )
                    aav.save()
                    created_values += 1

                # اگر خطایی داشتیم: دارایی را رجیسترنشده کن و issueها را ثبت کن
                if row_issues:
                    assets_with_issues.add(asset.pk)
                    Asset.objects.filter(pk=asset.pk).update(is_registered=False)
                    for code, msg in row_issues:
                        ImportIssue.objects.create(
                            session=session, row_index=idx, asset_ref=asset_ref, asset=asset,
                            code=code, message=str(msg), level=ImportIssue.Level.ERROR
                        )
                else:
                    # اگر هیچ issue برای این ردیف نبود، ممکنه asset قبلاً pending بوده؛ تنظیم نکنیم تا در انتها summary بدهیم
                    updated_assets.add(asset.pk)

        session.state = ImportSession.State.COMMITTED
        session.save(update_fields=["state"])

        # خلاصه خروجی
        issues_count = session.issues.count()
        data = {
            "session_id": str(session.id),
            "created_values": created_values,
            "issues": issues_count,
            "assets_pending": list(assets_with_issues),
            "assets_updated": list(updated_assets),
        }
        return CustomResponse.success(message="پردازش CSV انجام شد", data=data)



























