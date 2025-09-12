from rest_framework.views import APIView
from rest_framework import status
from drf_spectacular.utils import extend_schema

from core.utils import CustomResponse

from assets.models import Attribute, ImportSession
from .serializers import CsvUploadSerializer, CsvMappingSerializer, CsvCommitSerializer
from .utils import iter_csv_rows
from .services import CsvImportService


class CsvUploadView(APIView):
    @extend_schema(request=CsvUploadSerializer, responses=None)
    def post(self, request):
        ser = CsvUploadSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)

        f = ser.validated_data["file"]
        has_header = ser.validated_data.get("has_header")
        delimiter = ser.validated_data.get("delimiter")

        session = ImportSession.objects.create(
            file=f, filename=f.name, has_header=has_header, delimiter=delimiter, created_by=request.user
        )

        headers, preview, total = [], [], 0
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
        session.save(update_fields=["headers", "preview_rows", "total_rows"])

        return CustomResponse.success(
            message="فایل بارگذاری شد",
            data={
                "session_id": str(session.id),
                "filename": session.filename,
                "headers": headers,
                "preview": preview,
                "total_rows": total,
                "state": session.state,
            },
            status=status.HTTP_201_CREATED
        )


class CsvMappingView(APIView):
    @extend_schema(request=CsvMappingSerializer, responses=None)
    def post(self, request):
        ser = CsvMappingSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)

        sid = ser.validated_data["session_id"]
        session = ImportSession.objects.filter(pk=sid).first()
        if not session:
            return CustomResponse.error('داده مورد نظر یافت نشد')

        asset_column = ser.validated_data["asset_column"]
        unit_label_column = ser.validated_data["unit_label_column"]
        attr_map = ser.validated_data.get("attribute_map") or {}

        # صحت هدرها
        for col in (asset_column, unit_label_column):
            if col not in session.headers:
                return CustomResponse.error(f"ستون {col} در هدر CSV پیدا نشد", status=status.HTTP_400_BAD_REQUEST)

        # صحت خصیصه‌های map‌شده
        if attr_map:
            n = Attribute.objects.filter(id__in=attr_map.values()).count()
            if n != len(attr_map):
                return CustomResponse.error("برخی خصیصه‌های map‌شده یافت نشدند.", status=status.HTTP_400_BAD_REQUEST)

        session.asset_column = asset_column
        session.unit_label_column = unit_label_column
        session.attribute_map = {c: str(aid) for c, aid in attr_map.items()}
        session.state = ImportSession.State.MAPPED
        session.save(update_fields=["asset_column", "unit_label_column", "attribute_map", "state"])

        return CustomResponse.success("مپینگ ثبت شد", {"session_id": str(session.id)})


class CsvCommitView(APIView):
    @extend_schema(request=CsvCommitSerializer, responses=None)
    def post(self, request):
        ser = CsvCommitSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)

        sid = ser.validated_data["session_id"]
        session = ImportSession.objects.filter(pk=sid).first()
        if not session:
            return CustomResponse.error('داده مورد نظر یافت نشد')

        if session.state != ImportSession.State.MAPPED:
            return CustomResponse.error("ابتدا مپینگ را تکمیل کنید", status=status.HTTP_400_BAD_REQUEST)

        stats = CsvImportService(session, request.user).run()
        data = {
            "session_id": str(session.id),
            **stats,
            "issues_count": session.issues.count(),
            "state": session.state,
        }
        return CustomResponse.success("پردازش CSV (Create-only) انجام شد", data)


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