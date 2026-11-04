from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Company, SeekerProfile, Skill, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role", "phone")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Role", {"fields": ("role", "email")}),)
    list_display = ("username", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("username", "email")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(SeekerProfile)
class SeekerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "location", "experience_years")
    search_fields = ("user__username", "headline", "location")
    filter_horizontal = ("skills",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "location")
    search_fields = ("name", "owner__username")
