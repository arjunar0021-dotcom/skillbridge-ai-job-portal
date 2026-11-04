from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from accounts.models import Company, SeekerProfile, Skill


class JobQuerySet(models.QuerySet):
    def open(self):
        """Active jobs whose deadline has not passed."""
        today = timezone.localdate()
        return self.filter(is_active=True).filter(Q(deadline__isnull=True) | Q(deadline__gte=today))


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    class Workplace(models.TextChoices):
        ONSITE = "onsite", "On-site"
        HYBRID = "hybrid", "Hybrid"
        REMOTE = "remote", "Remote"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=150)
    description = models.TextField()
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=12, choices=JobType.choices, default=JobType.FULL_TIME)
    workplace = models.CharField(max_length=10, choices=Workplace.choices, default=Workplace.ONSITE)
    salary_range = models.CharField(max_length=60, blank=True, help_text="e.g. 6-9 LPA")
    experience_required = models.PositiveSmallIntegerField(default=0, help_text="Years")
    skills = models.ManyToManyField(Skill, blank=True, related_name="jobs")
    deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JobQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"

    def get_absolute_url(self):
        return reverse("job_detail", args=[self.pk])

    @property
    def level_label(self):
        years = self.experience_required
        if years <= 1:
            return "Entry level"
        if years <= 4:
            return "Mid level"
        return "Senior level"

    @property
    def is_open(self):
        return self.is_active and (self.deadline is None or self.deadline >= timezone.localdate())


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(SeekerProfile, on_delete=models.CASCADE, related_name="applications")
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.APPLIED)
    match_score = models.PositiveSmallIntegerField(default=0)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(fields=["job", "applicant"], name="one_application_per_job")
        ]

    def __str__(self):
        return f"{self.applicant.user.username} -> {self.job.title}"

    @property
    def badge_class(self):
        return {
            "applied": "secondary",
            "shortlisted": "info",
            "rejected": "danger",
            "hired": "success",
        }.get(self.status, "secondary")


class Interview(models.Model):
    class Mode(models.TextChoices):
        ONLINE = "online", "Online"
        ONSITE = "onsite", "On-site"
        PHONE = "phone", "Phone"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="interviews")
    scheduled_at = models.DateTimeField()
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)
    location_or_link = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"Interview for {self.application} on {self.scheduled_at:%d %b %Y %H:%M}"


class SavedJob(models.Model):
    """A job a seeker bookmarked (the 'Saved jobs' page)."""

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "job"], name="one_save_per_user_job")
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"
