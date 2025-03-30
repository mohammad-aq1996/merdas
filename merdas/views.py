from http.client import responses

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Organization, OrganizationType
from .serializers import OrganizationSerializer, OrganizationTypeSerializer, OrganizationReadSerializer
from core.utils import CustomResponse
from drf_spectacular.utils import extend_schema


class OrganizationTypeAPI(APIView):
    @extend_schema(responses=OrganizationTypeSerializer)
    def get(self, request, *args, **kwargs):
        types = OrganizationType.objects.all()
        serializer = OrganizationTypeSerializer(types, many=True)
        return CustomResponse.success(serializer.data)

    @extend_schema(request=OrganizationTypeSerializer, responses=OrganizationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = OrganizationTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(serializer.data)
        return Response(serializer.errors)


class OrganizationTypeDetailAPI(APIView):
    @extend_schema(responses=OrganizationTypeSerializer)
    def get(self, request, pk):
        try:
            qs = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد")
        serializer = OrganizationTypeSerializer(qs)
        return CustomResponse.success(serializer.data)

    @extend_schema(responses=OrganizationTypeSerializer, request=OrganizationTypeSerializer)
    def put(self, request, pk):
        try:
            instance = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد")
        serializer = OrganizationTypeSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(serializer.data)

    def delete(self, request, pk):
        try:
            instance = OrganizationType.objects.get(pk=pk)
        except OrganizationType.DoesNotExist:
            return CustomResponse.error("یافت نشد")
        instance.delete()
        return CustomResponse.success("با موفقیت حذف شد")


class OrganizationAPI(APIView):
    @extend_schema(responses=OrganizationReadSerializer)
    def get(self, request, *args, **kwargs):
        parent_id = request.query_params.get("parent", None)
        if parent_id:
            organizations = Organization.objects.filter(parent_id=parent_id)
        else:
            organizations = Organization.objects.filter(parent=None)

        serializer = OrganizationReadSerializer(organizations, many=True)
        return CustomResponse.success(serializer.data)

    @extend_schema(responses=OrganizationSerializer, request=OrganizationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = OrganizationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse.error(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationDetailAPI(APIView):
    @extend_schema(responses=OrganizationReadSerializer)
    def get(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("سازمان مورد نظر یافت نشد")
        serializer = OrganizationReadSerializer(organization)
        return CustomResponse.success(serializer.data)

    @extend_schema(responses=OrganizationSerializer, request=OrganizationSerializer)
    def put(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("سازمان مورد نظر یافت نشد")
        serializer = OrganizationSerializer(organization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(serializer.data)
        return CustomResponse.error(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, org_id, *args, **kwargs):
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            return CustomResponse.error("سازمان مورد نظر یافت نشد")
        organization.delete()
        return CustomResponse.success("سازمان با موفقیت حذف شد")

