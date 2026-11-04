from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied  # noqa: F401  (used by decorators)
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User
from accounts.utils import get_company, get_seeker_profile, paginate

from .forms import ApplicationForm, InterviewForm, JobForm, StatusForm
from .ai_services import generate_job_description
from .matching import compute_match, rank_jobs, top_missing_skills
from .models import Application, Interview, Job, SavedJob
from .notifications import notify_interview, notify_new_application, notify_status
from .permissions import manageable_applications, manageable_jobs

ADMIN, EMPLOYER, SEEKER = User.Role.ADMIN, User.Role.EMPLOYER, User.Role.SEEKER


# ====================================================================== helpers
def _saved_ids(user):
    if user.is_authenticated and user.role == SEEKER:
        return set(SavedJob.objects.filter(user=user).values_list("job_id", flat=True))
    return set()


def _safe_next(request, fallback):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return fallback


LEVEL_FILTERS = {
    "entry": Q(experience_required__lte=1),
    "mid": Q(experience_required__gte=2, experience_required__lte=4),
    "senior": Q(experience_required__gte=5),
}
POSTED_DAYS = {"day": 1, "week": 7, "month": 30}


# ====================================================================== public
def job_list(request):
    """Job search: filters on the left, results in the middle, selected job on the right."""
    user = request.user
    jobs = Job.objects.open().select_related("company").prefetch_related("skills")

    q = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    workplaces = [w for w in request.GET.getlist("workplace") if w in Job.Workplace.values]
    job_types = [t for t in request.GET.getlist("job_type") if t in Job.JobType.values]
    levels = [lv for lv in request.GET.getlist("level") if lv in LEVEL_FILTERS]
    posted = request.GET.get("posted", "")

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(company__name__icontains=q)
            | Q(skills__name__icontains=q)
        ).distinct()
    if location:
        jobs = jobs.filter(location__icontains=location)
    if workplaces:
        jobs = jobs.filter(workplace__in=workplaces)
    if job_types:
        jobs = jobs.filter(job_type__in=job_types)
    if levels:
        condition = Q()
        for level in levels:
            condition |= LEVEL_FILTERS[level]
        jobs = jobs.filter(condition)
    if posted in POSTED_DAYS:
        jobs = jobs.filter(created_at__gte=timezone.now() - timedelta(days=POSTED_DAYS[posted]))

    page_obj, querystring = paginate(request, jobs, 8)

    # match score for each job on the page (seekers only)
    profile, skill_ids = None, set()
    if user.is_authenticated and user.role == SEEKER:
        profile = get_seeker_profile(user)
        skill_ids = set(profile.skills.values_list("id", flat=True))
    jobs_on_page = list(page_obj.object_list)
    for job in jobs_on_page:
        job.match = compute_match(profile, job, skill_ids) if profile else None
    page_obj.object_list = jobs_on_page

    # which job is open in the right-hand panel
    selected = None
    selected_id = request.GET.get("selected", "")
    if selected_id.isdigit():
        selected = next((j for j in jobs_on_page if j.pk == int(selected_id)), None)
    if selected is None and jobs_on_page:
        selected = jobs_on_page[0]

    applied = False
    applicant_count = 0
    if selected:
        applicant_count = selected.applications.count()
        if profile:
            applied = Application.objects.filter(job=selected, applicant=profile).exists()

    link_params = request.GET.copy()
    link_params.pop("selected", None)

    return render(request, "jobs/job_list.html", {
        "page_obj": page_obj, "querystring": querystring, "link_qs": link_params.urlencode(),
        "q": q, "location": location, "posted": posted,
        "sel_workplaces": workplaces, "sel_types": job_types, "sel_levels": levels,
        "workplace_choices": Job.Workplace.choices,
        "type_choices": Job.JobType.choices,
        "level_choices": [("entry", "Entry level"), ("mid", "Mid level"), ("senior", "Senior")],
        "selected": selected, "applied": applied, "applicant_count": applicant_count,
        "saved_ids": _saved_ids(user),
    })


def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related("company").prefetch_related("skills"), pk=pk
    )
    user = request.user
    can_manage = user.is_authenticated and (
        user.role == ADMIN or job.company.owner_id == user.id
    )
    if not job.is_open and not can_manage:
        raise Http404

    context = {
        "job": job, "can_manage": can_manage,
        "applicant_count": job.applications.count(),
        "saved_ids": set(),
    }
    if user.is_authenticated and user.role == SEEKER:
        profile = get_seeker_profile(user)
        context["match"] = compute_match(profile, job)
        context["applied"] = Application.objects.filter(job=job, applicant=profile).exists()
        if SavedJob.objects.filter(user=user, job=job).exists():
            context["saved_ids"] = {job.pk}
    return render(request, "jobs/job_detail.html", context)


# ================================================================ employer: CRUD
@role_required(EMPLOYER)
def job_create(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = get_company(request.user)
            job.save()
            form.save_skills(job)
            messages.success(request, "Job posted.")
            return redirect("job_detail", pk=job.pk)
    else:
        form = JobForm()
    return render(request, "jobs/job_form.html", {"form": form, "title": "Post a job"})


@role_required(EMPLOYER, ADMIN)
def job_update(request, pk):
    job = get_object_or_404(manageable_jobs(request.user), pk=pk)
    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save()
            form.save_skills(job)
            messages.success(request, "Job updated.")
            return redirect("job_detail", pk=job.pk)
    else:
        form = JobForm(instance=job)
    return render(request, "jobs/job_form.html", {"form": form, "title": "Edit job"})


@role_required(EMPLOYER, ADMIN)
def job_delete(request, pk):
    job = get_object_or_404(manageable_jobs(request.user), pk=pk)
    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect("my_jobs" if request.user.role == EMPLOYER else "job_list")
    return render(request, "jobs/job_confirm_delete.html", {"job": job})


@role_required(EMPLOYER)
def my_jobs(request):
    jobs = (
        Job.objects.filter(company__owner=request.user)
        .annotate(app_count=Count("applications"))
        .order_by("-created_at")
    )
    return render(request, "jobs/my_jobs.html", {"jobs": jobs})


# ========================================================== seeker: applications
@role_required(SEEKER)
def apply(request, pk):
    job = get_object_or_404(Job.objects.open().select_related("company"), pk=pk)
    profile = get_seeker_profile(request.user)

    if Application.objects.filter(job=job, applicant=profile).exists():
        messages.info(request, "You have already applied to this job.")
        return redirect("job_detail", pk=pk)

    match = compute_match(profile, job)
    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = profile
            application.match_score = match["score"]
            try:
                application.save()
            except IntegrityError:
                messages.info(request, "You have already applied to this job.")
                return redirect("job_detail", pk=pk)
            notify_new_application(application)
            messages.success(request, "Application submitted. Good luck!")
            return redirect("my_applications")
    else:
        form = ApplicationForm()
    return render(request, "jobs/apply.html", {
        "job": job, "form": form, "profile": profile, "match": match,
    })


@role_required(SEEKER)
def my_applications(request):
    applications = (
        Application.objects.filter(applicant__user=request.user)
        .select_related("job__company")
        .prefetch_related("interviews")
    )
    return render(request, "jobs/my_applications.html", {"applications": applications})


@role_required(SEEKER)
@require_POST
def application_withdraw(request, pk):
    application = get_object_or_404(Application, pk=pk, applicant__user=request.user)
    application.delete()
    messages.success(request, "Application withdrawn.")
    return redirect("my_applications")


@role_required(SEEKER)
def my_interviews(request):
    interviews = (
        Interview.objects.filter(
            application__applicant__user=request.user, scheduled_at__gte=timezone.now()
        )
        .select_related("application__job__company")
        .order_by("scheduled_at")
    )
    return render(request, "jobs/my_interviews.html", {"interviews": interviews})


@role_required(SEEKER)
def recommended(request):
    """AI-based job matching + skill-gap analysis."""
    profile = get_seeker_profile(request.user)
    jobs = Job.objects.open().select_related("company").prefetch_related("skills")
    results = rank_jobs(profile, jobs)
    for result in results:
        result["job"].match = result
    return render(request, "jobs/recommended.html", {
        "results": results,
        "gaps": top_missing_skills(results),
        "profile": profile,
        "saved_ids": _saved_ids(request.user),
    })


# =============================================== employer/admin: review applicants
@role_required(EMPLOYER, ADMIN)
def job_applicants(request, pk):
    job = get_object_or_404(manageable_jobs(request.user), pk=pk)
    applications = job.applications.select_related("applicant__user").prefetch_related(
        "applicant__skills"
    )
    status = request.GET.get("status", "")
    skill = request.GET.get("skill", "").strip()
    min_exp = request.GET.get("min_exp", "").strip()

    if status:
        applications = applications.filter(status=status)
    if skill:
        applications = applications.filter(applicant__skills__name__icontains=skill).distinct()
    if min_exp.isdigit():
        applications = applications.filter(applicant__experience_years__gte=int(min_exp))
    applications = applications.order_by("-match_score", "applied_at")

    return render(request, "jobs/job_applicants.html", {
        "job": job, "applications": applications,
        "status": status, "skill": skill, "min_exp": min_exp,
        "status_choices": Application.Status.choices,
    })


@role_required(EMPLOYER, ADMIN)
def application_detail(request, pk):
    application = get_object_or_404(manageable_applications(request.user), pk=pk)
    return render(request, "jobs/application_detail.html", {
        "application": application,
        "profile": application.applicant,
        "match": compute_match(application.applicant, application.job),
        "interviews": application.interviews.all(),
        "interview_form": InterviewForm(),
        "status_choices": Application.Status.choices,
    })


@role_required(EMPLOYER, ADMIN)
@require_POST
def application_status(request, pk):
    application = get_object_or_404(manageable_applications(request.user), pk=pk)
    old_status = application.status
    form = StatusForm(request.POST, instance=application)
    if form.is_valid():
        application = form.save()
        if application.status != old_status:
            notify_status(application)
        messages.success(request, f"Status set to {application.get_status_display()}.")
    else:
        messages.error(request, "Invalid status.")

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("job_applicants", pk=application.job_id)


@role_required(EMPLOYER, ADMIN)
@require_POST
def interview_create(request, pk):
    application = get_object_or_404(manageable_applications(request.user), pk=pk)
    form = InterviewForm(request.POST)
    if form.is_valid():
        interview = form.save(commit=False)
        interview.application = application
        interview.save()
        if application.status == Application.Status.APPLIED:
            application.status = Application.Status.SHORTLISTED
            application.save(update_fields=["status"])
        notify_interview(interview)
        messages.success(request, "Interview scheduled and candidate notified.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("application_detail", pk=application.pk)


@role_required(EMPLOYER, ADMIN)
@require_POST
def interview_delete(request, pk):
    interview = get_object_or_404(
        Interview, pk=pk, application__in=manageable_applications(request.user)
    )
    application_pk = interview.application_id
    interview.delete()
    messages.success(request, "Interview removed.")
    return redirect("application_detail", pk=application_pk)


# ============================================================== seeker: saved jobs
@role_required(SEEKER)
@require_POST
def toggle_saved(request, pk):
    job = get_object_or_404(Job, pk=pk)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if created:
        messages.success(request, "Job saved.")
    else:
        saved.delete()
        messages.info(request, "Removed from saved jobs.")
    return redirect(_safe_next(request, job.get_absolute_url()))


@role_required(SEEKER)
def saved_jobs(request):
    profile = get_seeker_profile(request.user)
    skill_ids = set(profile.skills.values_list("id", flat=True))
    saved = (
        SavedJob.objects.filter(user=request.user)
        .select_related("job__company")
        .prefetch_related("job__skills")
    )
    items = []
    for entry in saved:
        entry.job.match = compute_match(profile, entry.job, skill_ids)
        items.append(entry.job)
    return render(request, "jobs/saved_jobs.html", {"jobs": items, "saved_ids": {j.pk for j in items}})


# ==========================================================
# AI JOB DESCRIPTION GENERATOR USING OLLAMA
# ==========================================================

@role_required(EMPLOYER, ADMIN)
@require_POST
def ai_generate_job_description(request):
    """Generate a job description using Ollama without saving the job."""
    title = request.POST.get("title", "").strip()

    if not title:
        return JsonResponse(
            {"error": "Please enter a job title first."},
            status=400,
        )

    try:
        description = generate_job_description(
            title=title,
            location=request.POST.get("location", "").strip(),
            workplace=request.POST.get("workplace", "").strip(),
            job_type=request.POST.get("job_type", "").strip(),
            salary_range=request.POST.get("salary_range", "").strip(),
            experience_required=request.POST.get("experience_required", "").strip(),
            skills=request.POST.get("skills_input", "").strip(),
        )
        return JsonResponse({"success": True, "description": description})
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=503)
