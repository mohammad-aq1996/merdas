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