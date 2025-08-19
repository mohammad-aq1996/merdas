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

    @extend_schema(responses=AssetReadSerializer, request=AssetCreateSerializer)
    def post(self, request):
        serializer = AssetCreateSerializer(data=request.data)
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

    @extend_schema(responses=AssetReadSerializer, request=AssetCreateSerializer)
    def put(self, request, pk):
        try:
            asset = Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AssetCreateSerializer(asset, data=request.data)
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
            result.setdefault(category.value, []).append(attr_data)

        return CustomResponse.success(message=get_all_data(), data=result)


class AssetAttributeValueView(APIView):
    queryset = Asset.objects.all()

    def get(self, request, pk):
        ...

    @extend_schema(responses=AssetAttributeValueSerializer, request=AssetAttributeValueSerializer)
    def post(self, request):
        serializer = AssetAttributeValueSerializer(data=request.data)
        if serializer.is_valid():
            serializer = serializer.save(owner=request.user)
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error('ridi')


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

