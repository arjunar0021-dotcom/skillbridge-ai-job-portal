from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import ApplicationViewSet, JobViewSet, RecommendedJobsAPI

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="api-job")
router.register("applications", ApplicationViewSet, basename="api-application")

urlpatterns = [
    path("recommended/", RecommendedJobsAPI.as_view(), name="api-recommended"),
    path("", include(router.urls)),
]
