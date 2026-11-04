from rest_framework import permissions, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.utils import get_seeker_profile

from .matching import rank_jobs
from .models import Application, Job
from .permissions import manageable_applications


class JobSerializer(serializers.ModelSerializer):
    company = serializers.CharField(source="company.name", read_only=True)
    job_type = serializers.CharField(source="get_job_type_display", read_only=True)
    skills = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = Job
        fields = [
            "id", "title", "company", "location", "workplace", "job_type", "salary_range",
            "experience_required", "skills", "deadline", "created_at",
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    applicant = serializers.CharField(source="applicant.user.username", read_only=True)

    class Meta:
        model = Application
        fields = ["id", "job", "job_title", "applicant", "status", "match_score", "applied_at"]


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/jobs/?search=django  and  GET /api/jobs/<id>/  (public)."""

    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Job.objects.open().select_related("company").prefetch_related("skills")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)
        return qs


class ApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/applications/ - seekers see their own, employers see applicants to their jobs."""

    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.SEEKER:
            return Application.objects.filter(applicant__user=user).select_related(
                "job", "applicant__user"
            )
        return manageable_applications(user)


class RecommendedJobsAPI(APIView):
    """GET /api/recommended/ - AI job matches for the logged-in seeker."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.SEEKER:
            return Response({"detail": "Only job seekers have recommendations."}, status=403)
        profile = get_seeker_profile(request.user)
        jobs = Job.objects.open().select_related("company").prefetch_related("skills")
        data = [
            {
                "job": JobSerializer(r["job"]).data,
                "score": r["score"],
                "matched_skills": r["matched"],
                "missing_skills": r["missing"],
            }
            for r in rank_jobs(profile, jobs)
        ]
        return Response(data)
