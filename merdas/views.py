from pyexpat.errors import messages

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Organization, OrganizationType, SR, FR, Standard
from .serializers import *
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


class OrganizationSimpleView(APIView):
    queryset = Organization.objects.only("id", "name")

    @extend_schema(responses=OrganizationSimpleSerializer)
    def get(self, request, *args, **kwargs):
        serializer = OrganizationSimpleSerializer(self.queryset.all(), many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)


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


# SR Views
class SRListCreateView(APIView):
    queryset = SR.objects.all()

    @extend_schema(responses=SRSerializer)
    def get(self, request):
        sr = SR.objects.all()
        serializer = SRSerializer(sr, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=SRSerializer, request=SRSerializer)
    def post(self, request):
        serializer = SRSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SRDetailView(APIView):
    queryset = SR.objects.all()

    @extend_schema(responses=SRSerializer)
    def get(self, request, pk):
        try:
            sr = SR.objects.get(pk=pk)
        except SR.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = SRSerializer(sr)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=SRSerializer, request=SRSerializer)
    def put(self, request, pk):
        try:
            sr = SR.objects.get(pk=pk)
        except SR.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = SRSerializer(sr, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            sr = SR.objects.get(pk=pk)
        except SR.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        sr.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


# FR Views
class FRListCreateView(APIView):
    queryset = FR.objects.all()

    @extend_schema(responses=FRSerializer)
    def get(self, request):
        fr = FR.objects.all()
        serializer = FRSerializer(fr, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=FRSerializer, request=FRCreateSerializer)
    def post(self, request):
        serializer = FRCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)


class FRDetailView(APIView):
    queryset = FR.objects.all()

    @extend_schema(responses=FRSerializer)
    def get(self, request, pk):
        try:
            fr = FR.objects.get(pk=pk)
        except FR.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = FRSerializer(fr)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=FRSerializer, request=FRCreateSerializer)
    def put(self, request, pk):
        try:
            fr = FR.objects.get(pk=pk)
        except FR.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = FRCreateSerializer(fr, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            fr = FR.objects.get(pk=pk)
        except FR.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        fr.delete()
        return CustomResponse.success(message=delete_data())


# Standard Views
class StandardListCreateView(APIView):
    queryset = Standard.objects.all()

    @extend_schema(responses=StandardSerializer)
    def get(self, request):
        standard = Standard.objects.all()
        serializer = StandardSerializer(standard, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=StandardSerializer, request=StandardCreateSerializer)
    def post(self, request):
        serializer = StandardCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)


class StandardDetailView(APIView):
    queryset = Standard.objects.all()

    @extend_schema(responses=StandardSerializer)
    def get(self, request, pk):
        try:
            standard = Standard.objects.get(pk=pk)
        except Standard.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = StandardSerializer(standard)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=StandardSerializer, request=StandardCreateSerializer)
    def put(self, request, pk):
        try:
            standard = Standard.objects.get(pk=pk)
        except Standard.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = StandardCreateSerializer(standard, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            standard = Standard.objects.get(pk=pk)
        except Standard.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        standard.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class QuestionListCreateView(APIView):
    queryset = Question.objects.all()

    @extend_schema(responses=QuestionSerializer)
    def get(self, request):
        question = Question.objects.all()
        serializer = QuestionSerializer(question, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(responses=QuestionSerializer, request=QuestionCreateSerializer)
    def post(self, request):
        serializer = QuestionCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(), data=serializer.data)
        return CustomResponse.error("ناموفق", errors=serializer.errors)


class QuestionDetailView(APIView):
    queryset = Question.objects.all()

    @extend_schema(responses=QuestionSerializer)
    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = QuestionSerializer(question)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=QuestionSerializer, request=QuestionCreateSerializer)
    def put(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = QuestionCreateSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error("ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        question.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class AssessmentListCreateView(APIView):
    queryset = Assessment.objects.all()

    @extend_schema(responses=AssessmentSerializer)
    def get(self, request):
        assessment = Assessment.objects.filter(created_by=request.user)
        serializer = AssessmentSerializer(assessment, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(request=AssessmentSerializer, responses=AssessmentSerializer)
    def post(self, request):
        serializer = AssessmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(),data=serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)


class AssessmentDetailView(APIView):
    queryset = Assessment.objects.all()

    @extend_schema(responses=AssessmentSerializer)
    def get(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk, created_by=request.user)
        except Assessment.DoesNotExist:
            return CustomResponse.error(message="ناموفق", status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentSerializer(assessment)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(responses=AssessmentSerializer, request=AssessmentSerializer)
    def put(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk, created_by=request.user)
        except Assessment.DoesNotExist:
            return CustomResponse.error(message="ناموفق", status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentSerializer(assessment, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=update_data(), data=serializer.data)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk, created_by=request.user)
        except Assessment.DoesNotExist:
            return CustomResponse.error(message="ناموفق", status=status.HTTP_404_NOT_FOUND)
        assessment.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class SubmitAssessmentResponsesAPIView(APIView):
    queryset = AssessmentQuestionResponse.objects.all()

    @extend_schema(
        request=BulkAssessmentResponseSerializer,
        responses={201: "Responses submitted successfully"}
    )
    def post(self, request):
        serializer = BulkAssessmentResponseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse.success(message=create_data(), data=serializer.data, status=status.HTTP_201_CREATED)
        return CustomResponse.error(message="ناموفق", errors=serializer.errors)

    @extend_schema(responses=AssessmentQuestionResponseSerializer)
    def get(self, request):
        responses = AssessmentQuestionResponse.objects.filter(reviewd_by=request.user)
        serializer = AssessmentQuestionResponseSerializer(responses, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

