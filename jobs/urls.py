
from django.urls import path

from . import views

urlpatterns = [
    # Public
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),

    # Employer / admin: job CRUD
    path("jobs/new/", views.job_create, name="job_create"),
    path("jobs/<int:pk>/edit/", views.job_update, name="job_update"),
    path("jobs/<int:pk>/delete/", views.job_delete, name="job_delete"),
    path("jobs/<int:pk>/applicants/", views.job_applicants, name="job_applicants"),
    path("employer/jobs/", views.my_jobs, name="my_jobs"),

    # AI job description generator using Ollama
    path(
        "jobs/ai/generate-description/",
        views.ai_generate_job_description,
        name="ai_generate_job_description",
    ),

    # Seeker
    path("jobs/<int:pk>/apply/", views.apply, name="apply"),
    path("applications/", views.my_applications, name="my_applications"),
    path("applications/<int:pk>/withdraw/", views.application_withdraw, name="application_withdraw"),
    path("interviews/", views.my_interviews, name="my_interviews"),
    path("recommended/", views.recommended, name="recommended"),
    path("saved/", views.saved_jobs, name="saved_jobs"),
    path("jobs/<int:pk>/save/", views.toggle_saved, name="toggle_saved"),

    # Employer / admin: reviewing applications
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/status/", views.application_status, name="application_status"),
    path("applications/<int:pk>/interview/", views.interview_create, name="interview_create"),
    path("interviews/<int:pk>/delete/", views.interview_delete, name="interview_delete"),
]
