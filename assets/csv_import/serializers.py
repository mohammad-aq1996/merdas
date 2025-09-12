from rest_framework import serializers


class CsvUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    has_header = serializers.BooleanField(required=False, default=True)
    delimiter = serializers.CharField(required=False, default=",", max_length=8)

    def validate(self, attrs):
        name = (attrs["file"].name or "").lower()
        if not (name.endswith(".csv") or name.endswith(".txt")):
            raise serializers.ValidationError({"file": "فقط فایل CSV/TXT مجاز است."})
        return attrs


class CsvMappingSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    asset_column = serializers.CharField()       # مثلاً "asset_title"
    unit_label_column = serializers.CharField()  # مثلاً "unit_label"
    # اختیاری: اگر خالی بماند، Auto-Resolve از روی نام ستون انجام می‌شود
    attribute_map = serializers.DictField(child=serializers.UUIDField(), required=False, allow_empty=True)


class CsvCommitSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()


class CsvEditRowsSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    # rows: [{"row_index": 12, "values": {"colA":"...", "colB":"..."}}]
    rows = serializers.ListField(
        child=serializers.DictField(), allow_empty=False
    )


class CsvListRowsQuerySerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=100)


class CsvApplyEditsSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    # edits: [{"row_index": 12, "values": {"colA":"...", "colB":"..."}}]
    edits = serializers.ListField(
        child=serializers.DictField(), allow_empty=False
    )

    def validate(self, attrs):
        edits = attrs["edits"]
        for e in edits:
            if "row_index" not in e or "values" not in e:
                raise serializers.ValidationError("هر آیتم edits باید دارای row_index و values باشد.")
            if not isinstance(e["row_index"], int) or e["row_index"] < 1:
                raise serializers.ValidationError("row_index باید عدد ۱-بنیاد و >=1 باشد.")
            if not isinstance(e["values"], dict) or not e["values"]:
                raise serializers.ValidationError("values باید دیکشنری غیرخالی باشد.")
        return attrs