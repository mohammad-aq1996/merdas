from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Organization, OrganizationType
from .serializers import OrganizationSerializer, OrganizationTypeSerializer, OrganizationReadSerializer
from core.utils import CustomResponse
from drf_spectacular.utils import extend_schema
from core.persian_response import *


class OrganizationTypeAPI(APIView):
    queryset = OrganizationType.objects.all()

    @extend_schema(responses=OrganizationTypeSerializer)
    def get(self, request, *args, **kwargs):
        types = OrganizationType.objects.all()
        serializer = OrganizationTypeSerializer(types, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(request=OrganizationTypeSerializer, responses=OrganizationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = OrganizationTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success("نوع سازمان مورد نظر با موفقیت ذخیره شد", data=serializer.data)
        return CustomResponse.error(message=create_data(), errors=serializer.errors)


class OrganizationTypeDetailAPI(APIView):
    queryset = OrganizationType.objects.all()

    @extend_schema(responses=OrganizationTypeSerializer)
    def get(self, request, pk):
        try:
            qs = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationTypeSerializer(qs)
        return CustomResponse.success(get_single_data(), data=serializer.data)

    @extend_schema(responses=OrganizationTypeSerializer, request=OrganizationTypeSerializer)
    def put(self, request, pk):
        try:
            instance = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationTypeSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=update_data(), data=serializer.data)

    def delete(self, request, pk):
        try:
            instance = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class OrganizationAPI(APIView):
    queryset = Organization.objects.all()

    @extend_schema(responses=OrganizationReadSerializer)
    def get(self, request, *args, **kwargs):
        parent_id = request.query_params.get("parent", None)
        if parent_id:
            organizations = Organization.objects.filter(parent_id=parent_id)
        else:
            organizations = Organization.objects.filter(parent=None)

        serializer = OrganizationReadSerializer(organizations, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=OrganizationSerializer, request=OrganizationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = OrganizationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(create_data(), data=serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse.error("ذخیره سازمان ناموفق بود", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationDetailAPI(APIView):
    queryset = Organization.objects.all()

    @extend_schema(responses=OrganizationReadSerializer)
    def get(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationReadSerializer(organization)
        return CustomResponse.success(get_single_data(), data=serializer.data)

    @extend_schema(responses=OrganizationSerializer, request=OrganizationSerializer)
    def put(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(update_data(), data=serializer.data)
        return CustomResponse.error("بروزرسانی ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        organization.delete()
        return CustomResponse.success(delete_data(), status=status.HTTP_204_NO_CONTENT)

