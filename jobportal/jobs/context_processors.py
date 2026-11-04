from accounts.models import User

from .models import Application, SavedJob


def nav_counts(request):
    """Badge numbers for the seeker sidebar (Applications / Saved jobs)."""
    user = request.user
    if user.is_authenticated and user.role == User.Role.SEEKER:
        return {
            "nav_app_count": Application.objects.filter(applicant__user=user).count(),
            "nav_saved_count": SavedJob.objects.filter(user=user).count(),
        }
    return {}
