from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin
from accounts.models import Skill

from .models import Application, Interview, Job


class JobForm(BootstrapFormMixin, forms.ModelForm):
    skills_input = forms.CharField(
        label="Required skills",
        required=False,
        help_text="Comma-separated, e.g. Python, Django, SQL",
    )

    field_order = [
        "title", "description", "location", "workplace", "job_type", "salary_range",
        "experience_required", "skills_input", "deadline", "is_active",
    ]

    class Meta:
        model = Job
        fields = [
            "title", "description", "location", "workplace", "job_type", "salary_range",
            "experience_required", "deadline", "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "deadline": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["skills_input"].initial = ", ".join(s.name for s in self.instance.skills.all())

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        if deadline and not self.instance.pk and deadline < timezone.localdate():
            raise forms.ValidationError("Deadline cannot be in the past.")
        return deadline

    def save_skills(self, job):
        job.skills.set(Skill.from_csv(self.cleaned_data["skills_input"]))


class ApplicationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_letter"]
        widgets = {"cover_letter": forms.Textarea(attrs={"rows": 5})}


class StatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status"]


class InterviewForm(BootstrapFormMixin, forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Date & time",
    )

    class Meta:
        model = Interview
        fields = ["scheduled_at", "mode", "location_or_link", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def clean_scheduled_at(self):
        value = self.cleaned_data["scheduled_at"]
        if value < timezone.now():
            raise forms.ValidationError("Interview must be scheduled in the future.")
        return value
