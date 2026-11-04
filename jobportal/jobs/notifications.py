from django.conf import settings
from django.core.mail import send_mail


def _send(subject, message, to_email):
    if to_email:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=True)


def notify_new_application(application):
    owner = application.job.company.owner
    _send(
        f"New application for {application.job.title}",
        f"{application.applicant.user.display_name} applied for '{application.job.title}' "
        f"(match score {application.match_score}%). Log in to review the application.",
        owner.email,
    )


def notify_status(application):
    _send(
        f"Update on your application: {application.job.title}",
        f"Hi {application.applicant.user.display_name},\n\n"
        f"Your application for '{application.job.title}' at {application.job.company.name} "
        f"is now: {application.get_status_display()}.",
        application.applicant.user.email,
    )


def notify_interview(interview):
    app = interview.application
    _send(
        f"Interview scheduled: {app.job.title}",
        f"Hi {app.applicant.user.display_name},\n\n"
        f"An interview for '{app.job.title}' at {app.job.company.name} is scheduled on "
        f"{interview.scheduled_at:%d %b %Y, %H:%M} ({interview.get_mode_display()}). "
        f"{interview.location_or_link}",
        app.applicant.user.email,
    )
