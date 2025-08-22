from django.forms.models import model_to_dict

from drf_spectacular.utils import extend_schema

from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
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
            cat_label = category.value if category else "uncategorized"
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