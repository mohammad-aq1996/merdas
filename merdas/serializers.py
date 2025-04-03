from rest_framework import serializers
from .models import Organization, OrganizationType, SR, Standard, FR, Question


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = ("id", "name", "description")


class OrganizationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(validators=[])
    code = serializers.CharField(validators=[])

    class Meta:
        model = Organization
        fields = ("name", "description", "code", "organization_type", "parent")

    def validate(self, data):
        name = data.get("name")
        code = data.get("code")
        if Organization.objects.filter(name=name).exists():
            raise serializers.ValidationError("سازمان با این اسم از قبل وجود دارد")
        if Organization.objects.filter(code=code).exists():
            raise serializers.ValidationError("سازمان با این کد از قبل وجود دارد")
        return data


class OrganizationReadSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    organization_type = OrganizationTypeSerializer(many=False, read_only=True)
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ("id", "name", "code", "parent", "description", "organization_type", "children")

    def get_children(self, obj):
        return OrganizationReadSerializer(obj.get_children(), many=True).data

    def get_parent(self, obj):
        return obj.parent.name if obj.parent else None


class SRSerializer(serializers.ModelSerializer):
    class Meta:
        model = SR
        fields = ('id', 'title', 'description')


class FRSerializer(serializers.ModelSerializer):
    sr = SRSerializer(many=True)

    class Meta:
        model = FR
        fields = ('id', 'title', 'weight', 'description', 'sr')


class FRCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FR
        fields = ('title', 'weight', 'description', 'sr')


class StandardSerializer(serializers.ModelSerializer):
    fr = FRSerializer(many=True)

    class Meta:
        model = Standard
        fields = ('id', 'title', 'fr')


class StandardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Standard
        fields = ('title', 'fr')

    def validate(self, data):
        if 'fr' not in data: # for partial update
            return data

        fr_list = data.get('fr', [])  # لیست FRهای ارسالی

        if not fr_list:
            raise serializers.ValidationError("حداقل یک FR باید انتخاب شود.")

        total_weight = sum(fr.weight for fr in fr_list)

        if total_weight != 100:
            raise serializers.ValidationError("جمع وزن‌های FR باید دقیقاً ۱۰۰ باشد.")

        return data


class QuestionSerializer(serializers.ModelSerializer):
    standard = StandardSerializer()

    class Meta:
        model = Question
        fields = ('id', 'title', 'description', 'standard', 'question_level')


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('title', 'description', 'standard', 'question_level')
