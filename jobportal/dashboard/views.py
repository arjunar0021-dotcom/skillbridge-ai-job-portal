import csv
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import Company, User
from accounts.utils import get_seeker_profile
from jobs.matching import rank_jobs
from jobs.models import Application, Interview, Job
from jobs.permissions import manageable_applications

ADMIN, EMPLOYER, SEEKER = User.Role.ADMIN, User.Role.EMPLOYER, User.Role.SEEKER


def _counts(queryset, field, choices):
    """Count rows per choice value -> (labels, data) lists, including zeros."""
    found = {row[field]: row["c"] for row in queryset.values(field).annotate(c=Count("id"))}
    return [label for _, label in choices], [found.get(value, 0) for value, _ in choices]


def _chart(chart_id, chart_type, title, labels, data):
    return {"id": chart_id, "type": chart_type, "title": title, "labels": labels, "data": data}


# ------------------------------------------------------------------ landing page
def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    context = {
        "latest_jobs": Job.objects.open().select_related("company").prefetch_related("skills")[:6],
        "stats": [
            ("Open jobs", Job.objects.open().count()),
            ("Companies", Company.objects.count()),
            ("Job seekers", User.objects.filter(role=SEEKER).count()),
        ],
        "job_types": Job.JobType.choices,
    }
    return render(request, "home.html", context)


# --------------------------------------------------------------------- dashboard
@login_required
def dashboard(request):
    role = request.user.role
    if role == ADMIN:
        return _admin_dashboard(request)
    if role == EMPLOYER:
        return _employer_dashboard(request)
    return _seeker_dashboard(request)


def _admin_dashboard(request):
    user_labels, user_data = _counts(User.objects.all(), "role", User.Role.choices)
    status_labels, status_data = _counts(Application.objects.all(), "status", Application.Status.choices)

    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    per_day = {
        row["day"]: row["c"]
        for row in Application.objects.filter(applied_at__date__gte=days[0])
        .annotate(day=TruncDate("applied_at"))
        .values("day")
        .annotate(c=Count("id"))
    }
    charts = [
        _chart("usersChart", "doughnut", "Users by role", user_labels, user_data),
        _chart("statusChart", "bar", "Applications by status", status_labels, status_data),
        _chart("dailyChart", "line", "Applications (last 7 days)",
               [d.strftime("%d %b") for d in days], [per_day.get(d, 0) for d in days]),
    ]
    context = {
        "stats": [
            ("Users", User.objects.count()),
            ("Employers", User.objects.filter(role=EMPLOYER).count()),
            ("Job seekers", User.objects.filter(role=SEEKER).count()),
            ("Open jobs", Job.objects.open().count()),
            ("Applications", Application.objects.count()),
            ("Hired", Application.objects.filter(status=Application.Status.HIRED).count()),
        ],
        "charts": charts,
        "recent_users": User.objects.order_by("-date_joined")[:5],
        "recent_jobs": Job.objects.select_related("company")[:5],
    }
    return render(request, "dashboard/admin.html", context)


def _employer_dashboard(request):
    apps = Application.objects.filter(job__company__owner=request.user)
    status_labels, status_data = _counts(apps, "status", Application.Status.choices)
    per_job = list(
        Job.objects.filter(company__owner=request.user)
        .annotate(c=Count("applications"))
        .order_by("-c")[:8]
    )
    charts = [
        _chart("statusChart", "doughnut", "Applicants by status", status_labels, status_data),
        _chart("jobsChart", "bar", "Applicants per job",
               [j.title[:22] for j in per_job], [j.c for j in per_job]),
    ]
    upcoming = (
        Interview.objects.filter(application__job__company__owner=request.user,
                                 scheduled_at__gte=timezone.now())
        .select_related("application__applicant__user", "application__job")
        .order_by("scheduled_at")[:5]
    )
    context = {
        "stats": [
            ("My jobs", Job.objects.filter(company__owner=request.user).count()),
            ("Applicants", apps.count()),
            ("Shortlisted", apps.filter(status=Application.Status.SHORTLISTED).count()),
            ("Hired", apps.filter(status=Application.Status.HIRED).count()),
        ],
        "charts": charts,
        "upcoming": upcoming,
        "recent_apps": apps.select_related("job", "applicant__user").order_by("-applied_at")[:6],
    }
    return render(request, "dashboard/employer.html", context)


def _greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _seeker_dashboard(request):
    user = request.user
    profile = get_seeker_profile(user)
    now = timezone.now()
    apps = Application.objects.filter(applicant=profile)
    upcoming = list(
        Interview.objects.filter(application__applicant=profile, scheduled_at__gte=now)
        .select_related("application__job__company")
        .order_by("scheduled_at")
    )

    jobs = Job.objects.open().select_related("company").prefetch_related("skills")
    top_matches = []
    for result in rank_jobs(profile, jobs)[:2]:
        result["job"].match = result
        top_matches.append(result["job"])

    in_review = apps.filter(
        status__in=[Application.Status.APPLIED, Application.Status.SHORTLISTED]
    ).count()

    context = {
        "greeting": _greeting(),
        "first_name": user.first_name or user.username,
        "profile": profile,
        "stats": {
            "sent": apps.count(),
            "this_week": apps.filter(applied_at__gte=now - timedelta(days=7)).count(),
            "in_review": in_review,
            "interviews": len(upcoming),
            "next_interview": upcoming[0] if upcoming else None,
        },
        "top_matches": top_matches,
        "applications": apps.select_related("job__company").order_by("-applied_at")[:5],
        "next_interview": upcoming[0] if upcoming else None,
        "top_skills": profile.skills.all()[:6],
        "saved_ids": set(user.saved_jobs.values_list("job_id", flat=True)),
    }
    return render(request, "dashboard/seeker.html", context)


# ---------------------------------------------------------------------- reports
@role_required(EMPLOYER, ADMIN)
def export_applications_csv(request):
    """Download applications (admin: all, employer: own jobs) as CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="applications.csv"'
    writer = csv.writer(response)
    writer.writerow(["Job", "Company", "Applicant", "Email", "Experience (yrs)",
                     "Match %", "Status", "Applied on"])
    for a in manageable_applications(request.user).order_by("-applied_at"):
        writer.writerow([
            a.job.title, a.job.company.name, a.applicant.user.display_name,
            a.applicant.user.email, a.applicant.experience_years, a.match_score,
            a.get_status_display(), a.applied_at.strftime("%Y-%m-%d %H:%M"),
        ])
    return response
