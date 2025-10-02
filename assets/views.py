import csv
from io import StringIO
from django.http import HttpResponse

from django.forms.models import model_to_dict
from django.db.models import Count, F, Q, Value, JSONField
from django.db.models.functions import JSONObject, Coalesce
from django.contrib.postgres.aggregates import JSONBAgg

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny

from rest_framework.views import APIView
from rest_framework import status

from core.utils import CustomResponse
from core.persian_response import *
from .serializers import *
from .models import *


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
            serializer.save(owner=request.user)
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
        asset_type = request.query_params.get("type")
        title = request.query_params.get("title")
        if asset_type:
            assets = Asset.objects.filter(type=asset_type)
        elif title:
            assets = Asset.objects.filter(title=title)
        else:
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


class AssetAttributesListView(APIView):
    """
        get list of all attributes base on asset type and asset id
    """
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


class AssetAttributeValueView(APIView):
    queryset = AssetAttributeValue.objects.all()

    def get(self, request, unit_id):
        try:
            unit = AssetUnit.objects.get(pk=unit_id)
        except AssetUnit.DoesNotExist:
            return CustomResponse.error('نمونه پیدا نشد', status=status.HTTP_404_NOT_FOUND)

        values_qs = (
            AssetAttributeValue.objects
            .filter(unit=unit)
            .select_related("attribute", "attribute__category")
            .order_by("attribute__category__title", "attribute__title")
        )

        relations_qs = (
            AssetRelation.objects
            .filter(source_asset=unit)
            .select_related("relation", "target_asset")
            .order_by("relation__key", "target_asset__label")
        )

        serializer = AssetUnitDetailSerializer(
            instance=unit,
            context={
                "values": values_qs,
                "relations": relations_qs,
            }
        )
        return CustomResponse.success(message=get_single_data(), data=serializer.data, status=status.HTTP_200_OK)


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
            serializer.save(owner=request.user)
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


class AssetUnitCreateAPIView(APIView):
    queryset = Asset.objects.all()

    @extend_schema(request=AssetUnitUpsertSerializer)
    def post(self, request, asset_id: int):
        payload = dict(request.data)
        payload['asset_id'] = asset_id
        s = AssetUnitUpsertSerializer(data=payload)
        s.is_valid(raise_exception=True)
        unit = s.save(owner=request.user)
        return CustomResponse.success(create_data(), data=AssetUnitSerializer(unit).data)

    def get(self, request, asset_id=None):
        if asset_id:
            qs = AssetUnit.objects.filter(asset_id=asset_id)
        else:
            qs = AssetUnit.objects.all()
        s = AssetUnitSerializer(qs, many=True)
        return CustomResponse.success(get_all_data(), data=s.data)


class AssetUnitUpdateAPIView(APIView):
    queryset = AssetUnit.objects.all()

    def get(self, request, unit_id: str):
        try:
            unit = AssetUnit.objects.get(pk=unit_id)
        except AssetUnit.DoesNotExist:
            return CustomResponse.error('نمونه پیدا نشد', status=status.HTTP_404_NOT_FOUND)

        values_qs = (
            AssetAttributeValue.objects
            .filter(unit=unit)
            .select_related("attribute", "attribute__category")
            .order_by("attribute__category__title", "attribute__title")
        )

        relations_qs = (
            AssetRelation.objects
            .filter(source_asset=unit)
            .select_related("relation", "target_asset")
            .order_by("relation__key", "target_asset__label")
        )

        serializer = AssetUnitDetailSerializer(
            instance=unit,
            context={
                "values": values_qs,
                "relations": relations_qs,
            }
        )
        return CustomResponse.success(message=get_single_data(), data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=AssetUnitUpsertSerializer, responses=AssetUnitSerializer)
    def patch(self, request, unit_id: str):
        try:
            unit = AssetUnit.objects.get(pk=unit_id)
        except AssetUnit.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد')
        s = AssetUnitUpsertSerializer(instance=unit, data=request.data, partial=True, context={"request": request})
        s.is_valid(raise_exception=True)
        unit = s.save()
        return CustomResponse.success(update_data(), data=AssetUnitSerializer(unit).data)

    @extend_schema(request=AssetUnitUpsertSerializer, responses=AssetUnitSerializer)
    def put(self, request, unit_id: str):
        try:
            unit = AssetUnit.objects.get(pk=unit_id)
        except AssetUnit.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد')
        s = AssetUnitUpsertSerializer(instance=unit, data=request.data, partial=False, context={"request": request})
        s.is_valid(raise_exception=True)
        unit = s.save()
        return CustomResponse.success(update_data(), data=AssetUnitSerializer(unit).data)

    def delete(self, request, unit_id):
        try:
            unit = AssetUnit.objects.get(pk=unit_id)
        except AssetUnit.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد')
        aav = AssetAttributeValue.objects.filter(unit=unit)
        with transaction.atomic():
            aav.delete()
            unit.delete()
        return CustomResponse.success(delete_data(), status=status.HTTP_204_NO_CONTENT)


class AssetListWithUnitCountAPIView(APIView):
    # blue table in front
    queryset = Asset.objects.all()

    def get(self, request):
        qs = (
            Asset.objects
            .annotate(
                unit_count=Count("units", distinct=True),
                unit_items=Coalesce(
                    JSONBAgg(
                        JSONObject(id=F('units__id'), label=F('units__label')),
                        filter=Q(units__isnull=False),
                        # order_by=('units__label',)  # اگر مرتب‌سازی یونیت‌ها خواستی
                    ),
                    Value([], output_field=JSONField())
                )
            )
            .values("id", "title", "asset_type", "unit_count", "unit_items")
            .order_by("asset_type", "title")
        )

        grouped = {}
        for row in qs:
            grouped.setdefault(row["asset_type"], []).append({
                "id": row["id"],
                "title": row["title"],
                "unit_count": row["unit_count"],
                "units": row["unit_items"],  # ← اینجا دیگه تداخلی نیست
            })

        return CustomResponse.success(get_all_data(), data=grouped)


class CsvImportIssuesAPIView(APIView):
    queryset = ImportIssue.objects.all()

    def get(self, request, pk):
        try:
            unit = AssetUnit.objects.get(pk=pk)
        except AssetUnit.DoesNotExist:
            return CustomResponse.error('داده مورد نظر یافت نشد')
        issue = ImportIssue.objects.filter(unit=unit)
        serializer = CsvIssueSerializer(issue, many=True)
        return CustomResponse.success(get_single_data(), data=serializer.data)


class GenerateTemplateCSVAPIView(APIView):
    permission_classes = (AllowAny, )
    queryset = Asset.objects.all()

    @extend_schema(request=GenerateCsvSerializer)
    def post(self, request, *args, **kwargs):
        asset_ids = request.data.get("assets", [])
        if not asset_ids:
            return CustomResponse.error("asset_ids الزامی است.")

        headers = ["unit_label"]

        assets = Asset.objects.filter(id__in=asset_ids)
        for asset in assets:
            rules = AssetTypeAttribute.objects.filter(asset=asset).select_related("attribute")
            for rule in rules:
                safe_asset = asset.title.strip().replace(" ", "_").replace("-", "_")
                safe_attr  = rule.attribute.title.strip().replace(" ", "_").replace("-", "_")

                col_name = f"{safe_asset}ـ{safe_attr}"
                if rule.is_required:   # اگر الزامی بود
                    col_name += "*"

                headers.append(col_name)

        # ساخت CSV
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)

        response = HttpResponse(buffer.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="template.csv"'
        return response