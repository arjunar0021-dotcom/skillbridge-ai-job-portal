from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Company, SeekerProfile, Skill, User


class BootstrapFormMixin:
    """Adds Bootstrap 5 CSS classes to every widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    # Admin is deliberately NOT offered: nobody can sign up as an admin.
    role = forms.ChoiceField(
        choices=[(User.Role.SEEKER, "Job Seeker"), (User.Role.EMPLOYER, "Employer")],
        initial=User.Role.SEEKER,
        label="I am a",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role")


class SeekerProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    skills_input = forms.CharField(
        label="Skills",
        required=False,
        help_text="Comma-separated, e.g. Python, Django, SQL, Git",
    )

    field_order = [
        "first_name", "last_name", "avatar", "headline", "bio", "location", "education",
        "experience_years", "linkedin_url", "skills_input", "resume", "open_to_work",
        "target_role", "workplace_pref", "expected_salary",
    ]

    class Meta:
        model = SeekerProfile
        fields = [
            "avatar", "headline", "bio", "location", "education", "experience_years",
            "linkedin_url", "resume", "open_to_work", "target_role", "workplace_pref",
            "expected_salary",
        ]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}
        labels = {
            "avatar": "Profile photo",
            "open_to_work": "Open to work",
            "linkedin_url": "LinkedIn / portfolio link",
            "workplace_pref": "Preferred workplace",
            "expected_salary": "Salary expectation",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["skills_input"].initial = ", ".join(s.name for s in self.instance.skills.all())
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit:
            profile.skills.set(Skill.from_csv(self.cleaned_data["skills_input"]))
            user = profile.user
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.save(update_fields=["first_name", "last_name"])
        return profile


class CompanyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "description", "website", "location", "logo"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class UserEditForm(BootstrapFormMixin, forms.ModelForm):
    """Used by admins on the Manage Users page."""

    class Meta:
        model = User
        fields = ["username", "email", "role", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [c for c in User.Role.choices if c[0] != User.Role.ADMIN]
