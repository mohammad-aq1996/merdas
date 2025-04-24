from rest_framework import serializers
from .models import (Organization, OrganizationType, SR, Standard, FR, Question, Assessment, Answer,)
from django.contrib.auth import get_user_model
from accounts.serializers import UserGetSerializer
from django.db import transaction


User = get_user_model()


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

        # exclude خود instance هنگام آپدیت
        org_qs = Organization.objects.exclude(pk=self.instance.pk) if self.instance else Organization.objects.all()

        if org_qs.filter(name=name).exists():
            raise serializers.ValidationError({"name": ["سازمان با این اسم از قبل وجود دارد"]})

        if org_qs.filter(code=code).exists():
            raise serializers.ValidationError({"code": ["سازمان با این کد از قبل وجود دارد"]})

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


class OrganizationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name")


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
    sr = SRSerializer(many=True, write_only=True)

    class Meta:
        model = FR
        fields = ('title', 'weight', 'description', 'sr')


class StandardSerializer(serializers.ModelSerializer):
    fr = FRSerializer(many=True)

    class Meta:
        model = Standard
        fields = ('id', 'title', 'fr')


class StandardCreateSerializer(serializers.ModelSerializer):
    fr = FRSerializer(many=True, write_only=True)

    class Meta:
        model = Standard
        fields = ('title', 'fr')

    def validate(self, data):
        if 'fr' not in data: # for partial update
            return data

        fr_list = data.get('fr', [])  # لیست FRهای ارسالی

        if not fr_list:
            raise serializers.ValidationError({"fr": ["حداقل یک FR باید انتخاب شود."]})

        total_weight = sum(fr['weight'] for fr in fr_list)

        if total_weight != 100:
            raise serializers.ValidationError({"fr": ["جمع وزن‌های FR باید دقیقاً ۱۰۰ باشد."]})

        return data

    def create(self, validated_data):
        frs_data = validated_data.pop('fr')
        standard = Standard.objects.create(**validated_data)

        for fr_data in frs_data:
            srs_data = fr_data.pop('sr')
            fr = FR.objects.create(**fr_data)

            for sr_data in srs_data:
                sr, _ = SR.objects.get_or_create(**sr_data)
                fr.sr.add(sr)

            fr.save()
            standard.fr.add(fr)

        return standard

    def update(self, instance, validated_data):
        frs_data = validated_data.pop('fr', None)

        instance.title = validated_data.get('title', instance.title)
        instance.save()

        if frs_data is not None:
            existing_frs = list(instance.fr.all())
            existing_frs_dict = {fr.id: fr for fr in existing_frs}
            updated_fr_ids = []

            for fr_data in frs_data:
                fr_id = fr_data.get('id')
                srs_data = fr_data.pop('sr', [])

                if fr_id and fr_id in existing_frs_dict:
                    # Update existing FR
                    fr = existing_frs_dict[fr_id]
                    fr.title = fr_data.get('title', fr.title)
                    fr.weight = fr_data.get('weight', fr.weight)
                    fr.save()
                else:
                    # Create new FR
                    fr = FR.objects.create(**fr_data)
                    instance.fr.add(fr)

                updated_fr_ids.append(fr.id)

                # Handle SRs
                existing_srs = list(fr.sr.all())
                existing_srs_dict = {sr.id: sr for sr in existing_srs}
                updated_sr_ids = []

                for sr_data in srs_data:
                    sr_id = sr_data.get('id')
                    if sr_id and sr_id in existing_srs_dict:
                        # Update existing SR
                        sr = existing_srs_dict[sr_id]
                        for attr, value in sr_data.items():
                            setattr(sr, attr, value)
                        sr.save()
                    else:
                        # Create new SR
                        sr, _ = SR.objects.get_or_create(**sr_data)

                    fr.sr.add(sr)
                    if sr.id:
                        updated_sr_ids.append(sr.id)

                # Remove SRs not in the update list
                for sr in existing_srs:
                    if sr.id not in updated_sr_ids:
                        fr.sr.remove(sr)

            # Remove FRs not in the update list
            for fr in existing_frs:
                if fr.id not in updated_fr_ids:
                    instance.fr.remove(fr)
                    fr.delete()

        return instance


class QuestionSerializer(serializers.ModelSerializer):
    standard = StandardSerializer()
    fr = FRSerializer()
    sr = SRSerializer()

    class Meta:
        model = Question
        fields = ('id', 'title', 'description', 'standard', 'question_level', 'fr', 'sr')


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('title', 'description', 'standard', 'question_level', 'sr', 'fr')


class QuestionFRSRSerializer(serializers.Serializer):
    standard_id = serializers.IntegerField()
    overall_sal = serializers.CharField()


class AnswerSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())

    class Meta:
        model = Answer
        fields = [
            'question',
            'answer',
            'substitute_text',
            'comment',
            'references',
            'reviewed',
        ]
        extra_kwargs = {
            'substitute_text': {'required': False, 'allow_blank': True},
            'comment': {'required': False, 'allow_blank': True},
            'references': {'required': False, 'allow_blank': True},
            'reviewed': {'default': False},
        }

    def validate(self, attrs):
        if attrs['answer'] == Answer.AnswerChoices.ALT and not attrs.get('substitute_text'):
            raise serializers.ValidationError({attrs['answer']: "متن پاسخ را وارد کنید"})
        return attrs


class AssessmentSerializer(serializers.ModelSerializer):
    standard = serializers.PrimaryKeyRelatedField(queryset=Standard.objects.all())
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    organization_type = serializers.PrimaryKeyRelatedField(queryset=OrganizationType.objects.all())
    org_contact = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    critical_service = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    contacts = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )
    responses = AnswerSerializer(many=True)

    class Meta:
        model = Assessment
        fields = [
            'id',
            'standard',
            'name',
            'date',
            'facility_name',
            'site_or_province_or_region',
            'city_or_site_name',
            'asset_gross_value',
            'expected_effort',
            'organization',
            'organization_type',
            'business_unit_or_agency',
            'org_contact',
            'facilitator',
            'critical_service',
            'critical_service_name',
            'contacts',
            'overall_sal',
            'confidentiality',
            'integrity',
            'availability',
            'responses',
        ]
        read_only_fields = ['id']

    @transaction.atomic
    def create(self, validated_data):
        answers_data = validated_data.pop('responses')
        contacts_data = validated_data.pop('contacts', [])
        user = self.context['request'].user

        if Assessment.objects.filter(created_by=user).exists():
            raise serializers.ValidationError({"name": "کاربر گرامی شما یک فرآیند نیمه کاره دارید."})

        assessment = Assessment.objects.create(created_by=user, **validated_data)
        if contacts_data:
            assessment.contacts.set(contacts_data)

        for ans in answers_data:
            Answer.objects.create(assessment=assessment, owner=user, **ans)
        return assessment

    @transaction.atomic
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('responses')
        contacts_data = validated_data.pop('contacts', None)
        user = self.context['request'].user

        # ۱. به‌روزرسانی فیلدهای اصلی Assessment
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ۲. contacts اگر ارسال شده، ست کن
        if contacts_data is not None:
            instance.contacts.set(contacts_data)

        # ۳. به‌روزرسانی یا ایجاد Answerها
        #   - می‌توانیم ابتدا همه پاسخ‌های قبلی را پاک کنیم، یا update_or_create
        #   اینجا از update_or_create استفاده می‌کنیم:
        existing_qs = {a.question_id: a for a in instance.responses.all()}
        for ans in answers_data:
            q = ans['question']
            if q.id in existing_qs:
                # آپدیت موجود
                a_obj = existing_qs[q.id]
                for k, v in ans.items():
                    setattr(a_obj, k, v)
                a_obj.owner = user
                a_obj.save()
            else:
                # ایجاد جدید
                Answer.objects.create(assessment=instance, owner=user, **ans)

        return instance


class AssessmentReadSerializer(serializers.ModelSerializer):
    standard = StandardSerializer(read_only=True)
    organization = OrganizationReadSerializer()
    org_contact = UserGetSerializer()
    critical_service = UserGetSerializer()
    contacts = UserGetSerializer(many=True, read_only=True)
    responses = AnswerSerializer(many=True)

    class Meta:
        model = Assessment
        fields = (
            'id',
            'standard',
            'name',
            'date',
            'facility_name',
            'site_or_province_or_region',
            'city_or_site_name',
            'asset_gross_value',
            'expected_effort',
            'organization',
            'business_unit_or_agency',
            'org_contact',
            'facilitator',
            'critical_service',
            'critical_service_name',
            'contacts',
            'overall_sal',
            'confidentiality',
            'integrity',
            'availability',
            'responses',
        )
