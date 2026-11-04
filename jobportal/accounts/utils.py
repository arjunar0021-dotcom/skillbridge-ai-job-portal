from django.core.paginator import Paginator

from .models import Company, SeekerProfile


def get_company(user):
    company, _ = Company.objects.get_or_create(owner=user, defaults={"name": user.username})
    return company


def get_seeker_profile(user):
    profile, _ = SeekerProfile.objects.get_or_create(user=user)
    return profile


def paginate(request, queryset, per_page=9):
    """Return (page_obj, querystring_without_page) so filters survive page changes."""
    page_obj = Paginator(queryset, per_page).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    params.pop("selected", None)
    return page_obj, params.urlencode()
