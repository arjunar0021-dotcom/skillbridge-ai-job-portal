from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import validate_file_size


class User(AbstractUser):
    """Custom user with a role field used for role-based access control."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EMPLOYER = "employer", "Employer"
        SEEKER = "seeker", "Job Seeker"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SEEKER)
    phone = models.CharField(max_length=15, blank=True)

    def save(self, *args, **kwargs):
        # Superusers are always admins; admins can always enter the Django admin site.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        first, last = self.first_name.strip(), self.last_name.strip()
        if first and last:
            return (first[0] + last[0]).upper()
        return self.username[:2].upper()

    @property
    def avatar_url(self):
        """Profile photo (seeker) or company logo (employer); '' if none."""
        try:
            if self.role == self.Role.SEEKER and self.seeker_profile.avatar:
                return self.seeker_profile.avatar.url
            if self.role == self.Role.EMPLOYER and self.company.logo:
                return self.company.logo.url
        except ObjectDoesNotExist:
            pass
        return ""

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_employer(self):
        return self.role == self.Role.EMPLOYER

    @property
    def is_seeker(self):
        return self.role == self.Role.SEEKER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @classmethod
    def from_csv(cls, text):
        """Turn 'Python, django , SQL' into a list of Skill objects (created if new)."""
        skills, seen = [], set()
        for raw in (text or "").split(","):
            name = " ".join(raw.split())[:50]
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            skill = cls.objects.filter(name__iexact=name).first() or cls.objects.create(name=name)
            skills.append(skill)
        return skills


class SeekerProfile(models.Model):
    class Workplace(models.TextChoices):
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"
        ONSITE = "onsite", "On-site"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seeker_profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True, validators=[validate_file_size])
    headline = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    linkedin_url = models.URLField(blank=True)
    open_to_work = models.BooleanField(default=True)
    # job preferences
    target_role = models.CharField(max_length=100, blank=True)
    workplace_pref = models.CharField(max_length=10, choices=Workplace.choices, blank=True)
    expected_salary = models.CharField(max_length=60, blank=True)
    resume = models.FileField(
        upload_to="resumes/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "doc", "docx"]), validate_file_size],
    )
    skills = models.ManyToManyField(Skill, blank=True, related_name="seekers")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def completeness_items(self):
        """(label, done) pairs shown as the checklist on the dashboard."""
        return [
            ("Headline and location", bool(self.headline and self.location)),
            ("About me", bool(self.bio)),
            ("Resume uploaded", bool(self.resume)),
            ("Experience and education", bool(self.experience_years and self.education)),
            ("Skills added", bool(self.pk and self.skills.exists())),
            ("LinkedIn or portfolio link", bool(self.linkedin_url)),
        ]

    @property
    def completeness(self):
        items = self.completeness_items
        return int(100 * sum(done for _, done in items) / len(items))

    @property
    def next_step(self):
        """First unfinished checklist item, or None."""
        return next((label for label, done in self.completeness_items if not done), None)


class Company(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, validators=[validate_file_size])

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name
