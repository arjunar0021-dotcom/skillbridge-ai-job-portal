from django.contrib import admin

from .models import Application, Interview, Job, SavedJob


class InterviewInline(admin.TabularInline):
    model = Interview
    extra = 0


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "job_type", "workplace", "location", "is_active", "deadline")
    list_filter = ("job_type", "workplace", "is_active", "company")
    search_fields = ("title", "description", "company__name")
    filter_horizontal = ("skills",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "job", "status", "match_score", "applied_at")
    list_filter = ("status",)
    search_fields = ("applicant__user__username", "job__title")
    inlines = [InterviewInline]


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("application", "scheduled_at", "mode")
    list_filter = ("mode",)


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "created_at")
