from django.db import models
from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model
from core.models import BaseModel
import django_jalali.db.models as jmodels


User = get_user_model()


class SR(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class FR(BaseModel):
    title = models.CharField(max_length=255)
    weight = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    sr = models.ManyToManyField(SR, related_name="fr")

    def __str__(self):
        return self.title


class Standard(BaseModel):
    title = models.CharField(max_length=255)
    fr = models.ManyToManyField(FR, related_name='standards')

    def __str__(self):
        return self.title


class Question(BaseModel):
    class QuestionLevel(models.TextChoices):
        low = "Low"
        moderate = "Moderate"
        high = "High"
        very_high = "Very High"

    title = models.CharField(max_length=2048)
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name="questions")
    fr = models.ForeignKey(FR, related_name="questions", on_delete=models.CASCADE)
    sr = models.ForeignKey(SR, related_name="questions", on_delete=models.CASCADE)
    question_level = models.CharField(choices=QuestionLevel.choices, max_length=20)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.question_level


class Assessment(BaseModel):
    SAL_CHOICES = [('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High'), ('very_high', 'Very High')]

    name = models.CharField(max_length=255)
    date = jmodels.jDateTimeField()
    facility_name = models.CharField(max_length=255)
    site_or_province_or_region = models.CharField(max_length=255)
    city_or_site_name = models.CharField(max_length=255)

    contacts = models.ManyToManyField(User, related_name="assessments_cantacts")
    asset_gross_value = models.CharField(max_length=255)
    expected_effort = models.CharField(max_length=255)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, related_name='assessments_org')
    business_unit_or_agency = models.CharField(max_length=255)
    organization_type = models.ForeignKey("accounts.OrganizationType", on_delete=models.CASCADE)
    org_contact = models.ForeignKey(User, related_name='assessments_contact', on_delete=models.CASCADE)
    facilitator = models.CharField(max_length=255)
    critical_service = models.ForeignKey(User, related_name='assessments_critical', on_delete=models.CASCADE)
    critical_service_name = models.TextField(blank=True, null=True)

    overall_sal = models.CharField(max_length=20, choices=SAL_CHOICES)
    confidentiality = models.CharField(max_length=20, choices=SAL_CHOICES)
    integrity = models.CharField(max_length=20, choices=SAL_CHOICES)
    availability = models.CharField(max_length=20, choices=SAL_CHOICES)

    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='assessments')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assessments')

    def __str__(self):
        return self.name


class Answer(BaseModel):
    class AnswerChoices(models.TextChoices):
        YES = 'yes', 'Yes'
        NO = 'no', 'No'
        NA = 'not_applicable', 'N/A'
        ALT = 'alternate', 'Alt'

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='responses', blank=True, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    answer = models.CharField(max_length=20, choices=AnswerChoices.choices)
    substitute_text = models.TextField(blank=True, null=True)

    comment = models.TextField(blank=True, null=True)
    documents = models.FileField(upload_to='documents/%Y/%m/%d', blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    reviewed = models.BooleanField(default=False)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('assessment', 'question')






















