from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import CompanyForm, SeekerProfileForm, SignUpForm, UserEditForm
from .models import User
from .utils import get_company, get_seeker_profile, paginate
from jobs.matching import rank_jobs, top_missing_skills
from jobs.models import Job


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Please complete your profile.")
            return redirect("profile_edit" if user.role == User.Role.SEEKER else "profile")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    """Seekers see their profile page; employers edit their company; admins go to the dashboard."""
    user = request.user
    if user.role == User.Role.SEEKER:
        profile_obj = get_seeker_profile(user)
        jobs = Job.objects.open().select_related("company").prefetch_related("skills")
        top_gap = top_missing_skills(rank_jobs(profile_obj, jobs), limit=1)
        return render(request, "accounts/profile_view.html", {
            "profile": profile_obj,
            "next_skill": top_gap[0] if top_gap else None,
        })

    if user.role == User.Role.EMPLOYER:
        company = get_company(user)
        if request.method == "POST":
            form = CompanyForm(request.POST, request.FILES, instance=company)
            if form.is_valid():
                form.save()
                messages.success(request, "Company profile saved.")
                return redirect("profile")
        else:
            form = CompanyForm(instance=company)
        return render(request, "accounts/profile_form.html", {"form": form, "title": "Company profile"})

    return redirect("dashboard")


@role_required(User.Role.SEEKER)
def profile_edit(request):
    profile_obj = get_seeker_profile(request.user)
    if request.method == "POST":
        form = SeekerProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile saved.")
            return redirect("profile")
    else:
        form = SeekerProfileForm(instance=profile_obj)
    return render(request, "accounts/profile_form.html", {"form": form, "title": "Edit profile"})


# ---------------------------------------------------------- user management (admin only)
@role_required(User.Role.ADMIN)
def manage_users(request):
    users = User.objects.all().order_by("-date_joined")
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    if role:
        users = users.filter(role=role)
    page_obj, querystring = paginate(request, users, 10)
    return render(request, "accounts/manage_users.html", {
        "page_obj": page_obj, "querystring": querystring,
        "q": q, "role": role, "roles": User.Role.choices,
    })


@role_required(User.Role.ADMIN)
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target.is_superuser:
        messages.error(request, "Admin accounts can only be changed from the Django admin site.")
        return redirect("manage_users")
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=target)
        if form.is_valid():
            user = form.save()
            # make sure the matching profile exists after a role change
            if user.role == User.Role.SEEKER:
                get_seeker_profile(user)
            elif user.role == User.Role.EMPLOYER:
                get_company(user)
            messages.success(request, f"{user.username} updated.")
            return redirect("manage_users")
    else:
        form = UserEditForm(instance=target)
    return render(request, "accounts/user_form.html", {"form": form, "target": target})


@role_required(User.Role.ADMIN)
@require_POST
def user_delete(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target.pk == request.user.pk or target.is_superuser:
        messages.error(request, "You cannot delete an admin account.")
    else:
        target.delete()
        messages.success(request, "User deleted.")
    return redirect("manage_users")
