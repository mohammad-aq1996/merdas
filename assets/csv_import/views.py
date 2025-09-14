from rest_framework.views import APIView
from rest_framework import status
from drf_spectacular.utils import extend_schema

from core.utils import CustomResponse

from assets.models import Attribute, ImportSession
from .serializers import CsvUploadSerializer, CsvMappingSerializer, CsvCommitSerializer, CsvEditRowsSerializer,\
                          CsvListRowsQuerySerializer, CsvApplyEditsSerializer
from .utils import iter_csv_rows, read_csv_all, write_csv_all, overwrite_session_file
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

        if session.state not in [ImportSession.State.MAPPED, ImportSession.State.EDITED]:
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
        # session.state = ImportSession.State.EDITED
        # session.save(update_fields=["state"])
        return CustomResponse.success(message="ویرایش‌ها ثبت شد (placeholder)", data={"session_id": str(session.id)})


class CsvRowsView(APIView):
    queryset = ImportSession.objects.all()
    """
    نمایش صفحه‌بندی‌شدهٔ سطرهای CSV برای ویرایش (هدر فقط جهت نمایش برمی‌گردد و غیرقابل‌تغییر است).
    GET params: session_id, page=1, page_size=100
    """
    @extend_schema(parameters=[CsvListRowsQuerySerializer], responses=None)
    def get(self, request):
        ser = CsvListRowsQuerySerializer(data=request.query_params)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)

        sid = ser.validated_data["session_id"]
        page = ser.validated_data["page"]
        page_size = ser.validated_data["page_size"]

        session = ImportSession.objects.filter(pk=sid).first()
        if not session:
            return CustomResponse.error('داده مورد نظر یافت نشد')

        headers, rows = read_csv_all(session.file, delimiter=session.delimiter, has_header=session.has_header)
        total_rows = len(rows)
        start = (page - 1) * page_size
        end = min(start + page_size, total_rows)

        page_rows = []
        # برگرداندن به صورت dict با row_index ۱-بنیاد
        for i in range(start, end):
            row_dict = {headers[j]: rows[i][j] for j in range(len(headers))}
            page_rows.append({"row_index": i + 1, "values": row_dict})

        return CustomResponse.success(
            message="لیست سطرها",
            data={
                "headers": headers,
                "page": page,
                "page_size": page_size,
                "total_rows": total_rows,
                "items": page_rows,
                "state": session.state,
            }
        )


class CsvApplyEditsView(APIView):
    queryset = ImportSession.objects.all()
    """
    اعمال ویرایش‌ها روی خود فایل CSV ذخیره‌شده.
    ورودی: { session_id, edits: [ {row_index:int>=1, values:{col:value,...}}, ... ] }
    - هدر قابل‌تغییر نیست؛ keys باید زیرمجموعهٔ headers باشند.
    - اضافه/حذف سطر فعلاً پشتیبانی نمی‌شود (فقط ویرایش مقادیر).
    """
    @extend_schema(request=CsvApplyEditsSerializer, responses=None)
    def post(self, request):
        ser = CsvApplyEditsSerializer(data=request.data)
        if not ser.is_valid():
            return CustomResponse.error("ناموفق", ser.errors, status=status.HTTP_400_BAD_REQUEST)

        sid = ser.validated_data["session_id"]
        edits = ser.validated_data["edits"]

        session = ImportSession.objects.filter(pk=sid).first()
        if not session:
            return CustomResponse.error('داده مورد نظر یافت نشد')

        headers, rows = read_csv_all(session.file, delimiter=session.delimiter, has_header=session.has_header)
        if not headers:
            return CustomResponse.error("فایل CSV فاقد هدر معتبر است.", status=status.HTTP_400_BAD_REQUEST)

        header_set = set(headers)
        h_index = {h: i for i, h in enumerate(headers)}
        total_rows = len(rows)

        # اعتبارسنجی اولیهٔ edits
        for e in edits:
            ri = e["row_index"]
            if ri < 1 or ri > total_rows:
                return CustomResponse.error(f"row_index نامعتبر: {ri}", status=status.HTTP_400_BAD_REQUEST)
            keys = set(e["values"].keys())
            unknown = keys - header_set
            if unknown:
                return CustomResponse.error(f"ستون‌های نامعتبر در ویرایش: {', '.join(sorted(unknown))}",
                                            status=status.HTTP_400_BAD_REQUEST)

        # اعمال ویرایش‌ها
        edited_count = 0
        for e in edits:
            ri = e["row_index"] - 1  # به ۰-بنیاد
            for col, val in e["values"].items():
                j = h_index[col]
                rows[ri][j] = "" if val is None else str(val)
            edited_count += 1

        # بازنویسی فایل
        content = write_csv_all(headers, rows, delimiter=session.delimiter)
        overwrite_session_file(session, content)

        # به‌روزرسانی preview_rows (۱۰ ردیف اول)
        preview = []
        for idx, row in iter_csv_rows(session.file, delimiter=session.delimiter, has_header=session.has_header):
            if idx == "__headers__":
                continue
            if len(preview) < 10:
                preview.append(row)
            else:
                break

        session.preview_rows = preview
        session.total_rows = total_rows  # تعداد سطر ثابت مانده
        session.state = ImportSession.State.EDITED
        session.save(update_fields=["preview_rows", "total_rows", "state"])

        return CustomResponse.success(
            "ویرایش‌ها اعمال شد",
            {
                "edited_batches": edited_count,
                "headers": headers,
                "preview": preview,
                "total_rows": total_rows,
                "state": session.state,
            }
        )