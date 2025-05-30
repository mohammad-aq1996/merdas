from pyexpat.errors import messages
from drf_nested_forms.parsers import NestedMultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SR, FR, Standard, Assessment
from .serializers import *
from core.utils import CustomResponse
from drf_spectacular.utils import extend_schema
from core.persian_response import *
from collections import defaultdict
import csv
import codecs
from rest_framework.parsers import MultiPartParser
from io import StringIO
from django.http import HttpResponse


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
            serializer = serializer.save()
            output_serializer = QuestionSerializer(serializer)
            return CustomResponse.success(message=create_data(), data=output_serializer.data)
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
            serializer = serializer.save()
            output_serializer = QuestionSerializer(serializer)
            return CustomResponse.success(message=update_data(), data=output_serializer.data)
        return CustomResponse.error("ناموفق", errors=serializer.errors)

    def delete(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return CustomResponse.error(message="داده مورد نظر یافت نشد", status=status.HTTP_404_NOT_FOUND)
        question.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class QuestionsGroupedByFRSRView(APIView):
    queryset = Question.objects.all()

    LEVEL_ORDER = {
        "Low": 0,
        "Moderate": 1,
        "High": 2,
        "Very High": 3,
    }

    @extend_schema(request=QuestionFRSRSerializer)
    def post(self, request):
        standard_id = request.data.get("standard_id")
        overall_sal = request.data.get("overall_sal")

        if not standard_id or not overall_sal:
            return CustomResponse.error("standard_id and overall_sal are required")

        level_threshold = self.LEVEL_ORDER.get(overall_sal)
        if level_threshold is None:
            return CustomResponse.error("Invalid overall_sal value")

        allowed_levels = [level for level, rank in self.LEVEL_ORDER.items() if rank <= level_threshold]

        questions = Question.objects.filter(
            standard_id=standard_id,
            question_level__in=allowed_levels
        ).select_related('fr', 'sr')

        # گروه‌بندی: FR -> SR -> سوال‌ها
        fr_map = defaultdict(lambda: defaultdict(list))

        for q in questions:
            fr_map[(q.fr.id, q.fr.title)][(q.sr.id, q.sr.title)].append(q)

        # تبدیل به ساختار JSON
        result = []
        for (fr_id, fr_title), sr_dict in fr_map.items():
            sr_list = []
            for (sr_id, sr_title), q_list in sr_dict.items():
                sr_list.append({
                    "sr_id": sr_id,
                    "sr": sr_title,
                    "questions": QuestionSerializer(q_list, many=True).data
                })
            result.append({
                "fr_id": fr_id,
                "fr": fr_title,
                "srs": sr_list
            })

        return CustomResponse.success(message=create_data(), data=result)


class AssessmentCreateView(APIView):
    parser_classes = (NestedMultiPartParser,)
    queryset = Assessment.objects.all()

    @extend_schema(responses=AssessmentReadSerializer)
    def get(self, request):
        qs = Assessment.objects.filter(created_by=request.user)
        serializer = AssessmentReadSerializer(qs, many=True)
        return CustomResponse.success(message=get_all_data(), data=serializer.data)

    @extend_schema(request=AssessmentSerializer)
    def post(self, request):
        serializer = AssessmentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(create_data(), data=serializer.data, status=status.HTTP_201_CREATED)


class AssessmentUpdateView(APIView):
    parser_classes = (NestedMultiPartParser,)
    queryset = Assessment.objects.all()

    @extend_schema(responses=AssessmentReadSerializer)
    def get(self, request, pk):
        try:
            assessment = Assessment.objects.get(created_by=request.user, pk=pk)
        except Assessment.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentReadSerializer(assessment)
        return CustomResponse.success(message=get_single_data(), data=serializer.data)

    @extend_schema(request=AssessmentSerializer)
    def put(self, request, pk):
        try:
            assessment = Assessment.objects.get(created_by=request.user, pk=pk)
        except Assessment.DoesNotExist:
            return CustomResponse.error("یافت نشد", status=status.HTTP_404_NOT_FOUND)
        serializer = AssessmentSerializer(
            assessment, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(update_data(), data=serializer.data)

    def delete(self, request, pk):
        try:
            assessment = Assessment.objects.get(created_by=request.user, pk=pk)
        except Assessment.DoesNotExist:
            return CustomResponse.success("یافت نشد")
        assessment.delete()
        return CustomResponse.success(message=delete_data(), status=status.HTTP_204_NO_CONTENT)


class QuestionCSVUploadByTitleView(APIView):
    parser_classes = [MultiPartParser]
    queryset = Question.objects.all()

    def post(self, request):
        csv_file = request.FILES.get('file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            return CustomResponse.error("فایل باید با فرمت CSV ارسال شود.")

        decoded_file = codecs.iterdecode(csv_file, 'utf-8-sig')  # handles BOM too
        reader = csv.DictReader(decoded_file)

        created = 0
        errors = []

        for index, row in enumerate(reader, start=2):  # row 1 is header
            try:
                # استخراج عنوان‌ها
                st_title = row.get('standard_title', '').strip()
                fr_title = row.get('fr_title', '').strip()
                sr_title = row.get('sr_title', '').strip()

                # پیدا کردن آبجکت‌ها با title
                standard_qs = Standard.objects.filter(title=st_title)
                fr_qs = FR.objects.filter(title=fr_title)
                sr_qs = SR.objects.filter(title=sr_title)

                # بررسی ambiguity و وجود
                if not standard_qs.exists():
                    return CustomResponse.error(f"Standard با عنوان '{st_title}' یافت نشد.")
                if standard_qs.count() > 1:
                    return CustomResponse.error(f"بیش از یک Standard با عنوان '{st_title}' یافت شد.")

                if not fr_qs.exists():
                    return CustomResponse.error(f"FR با عنوان '{fr_title}' یافت نشد.")
                if fr_qs.count() > 1:
                    return CustomResponse.error(f"بیش از یک FR با عنوان '{fr_title}' یافت شد.")

                if not sr_qs.exists():
                    return CustomResponse.error(f"SR با عنوان '{sr_title}' یافت نشد.")
                if sr_qs.count() > 1:
                    return CustomResponse.error(f"بیش از یک SR با عنوان '{sr_title}' یافت شد.")

                # ساخت سوال
                Question.objects.create(
                    title=row.get('title', '').strip(),
                    question_level=row.get('question_level', '').strip(),
                    standard=standard_qs.first(),
                    fr=fr_qs.first(),
                    sr=sr_qs.first(),
                    description=row.get('description', '').strip()
                )
                created += 1

            except Exception as e:
                errors.append({
                    "row": index,
                    "detail": str(e)
                })

        return CustomResponse.success({
            "created_count": created,
            "errors": errors
        }, status=status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED)


class QuestionCSVTemplateDownloadView(APIView):
    permission_classes = (AllowAny, )  # یا [IsAdminUser] برای محدودسازی

    def get(self, request):
        header = ['standard_title', 'fr_title', 'sr_title', 'title', 'question_level', 'description']

        csv_buffer = StringIO()
        csv_buffer.write('\ufeff')  # فقط یکبار BOM برای Excel

        writer = csv.writer(csv_buffer)
        writer.writerow(header)

        response = HttpResponse(
            csv_buffer.getvalue(),
            content_type='text/csv'
        )
        response['Content-Disposition'] = 'attachment; filename="questions_template.csv"'
        return response