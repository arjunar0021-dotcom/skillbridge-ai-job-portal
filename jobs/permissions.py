"""Query helpers that enforce object-level access (employers see only their own data)."""
from accounts.models import User

from .models import Application, Job


def manageable_jobs(user):
    qs = Job.objects.select_related("company")
    if user.role == User.Role.ADMIN:
        return qs
    return qs.filter(company__owner=user)


def manageable_applications(user):
    qs = Application.objects.select_related("job__company", "applicant__user")
    if user.role == User.Role.ADMIN:
        return qs
    return qs.filter(job__company__owner=user)
