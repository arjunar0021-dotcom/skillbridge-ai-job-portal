from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Company, Skill, User
from jobs.matching import compute_match
from jobs.models import Application, Job

DEMO_USERS = {
    "admin": ("Admin@123", "admin"),
    "employer1": ("Employer@123", "employer"),
    "employer2": ("Employer@123", "employer"),
    "seeker1": ("Seeker@123", "seeker"),
    "seeker2": ("Seeker@123", "seeker"),
}

# (owner, title, location, workplace, job_type, salary, years, skills, description)
JOBS = [
    ("employer1", "Python Django Developer", "Kochi", "hybrid", "full_time", "6-9 LPA", 2,
     "Python, Django, REST API, SQL", "Build and maintain Django web applications."),
    ("employer1", "Frontend Developer", "Bengaluru", "remote", "full_time", "5-8 LPA", 1,
     "HTML, CSS, JavaScript, React", "Create responsive user interfaces."),
    ("employer1", "Data Analyst Intern", "Thiruvananthapuram", "onsite", "internship", "15k/month", 0,
     "Python, SQL, Excel, Pandas", "Analyse datasets and build dashboards."),
    ("employer2", "Machine Learning Engineer", "Hyderabad", "hybrid", "full_time", "12-18 LPA", 5,
     "Python, Machine Learning, TensorFlow, SQL", "Train and deploy ML models."),
    ("employer2", "DevOps Engineer", "Chennai", "onsite", "full_time", "10-14 LPA", 3,
     "Docker, AWS, Linux, Git", "Own CI/CD pipelines and cloud infrastructure."),
    ("employer2", "Backend Developer (Part-time)", "Kozhikode", "remote", "part_time", "30k/month", 1,
     "Python, Django, Git", "Support backend features on a part-time basis."),
]


class Command(BaseCommand):
    help = "Create demo users, jobs and one sample application (safe to run repeatedly)."

    def handle(self, *args, **options):
        for username, (password, role) in DEMO_USERS.items():
            if User.objects.filter(username=username).exists():
                continue
            if role == "admin":
                User.objects.create_superuser(username, f"{username}@example.com", password)
            else:
                User.objects.create_user(username, f"{username}@example.com", password, role=role)

        for username, name in (("employer1", "TechNova Solutions"), ("employer2", "DataBridge Labs")):
            Company.objects.filter(owner__username=username).update(
                name=name, location="India", description=f"{name} is hiring across engineering roles."
            )

        for owner, title, loc, workplace, jtype, salary, exp, skills, desc in JOBS:
            company = Company.objects.get(owner__username=owner)
            job, created = Job.objects.get_or_create(
                company=company, title=title,
                defaults={
                    "location": loc, "workplace": workplace, "job_type": jtype, "salary_range": salary,
                    "experience_required": exp, "description": desc,
                    "deadline": timezone.localdate() + timedelta(days=45),
                },
            )
            if created:
                job.skills.set(Skill.from_csv(skills))

        seeker_data = {
            "seeker1": ("Asha", "Nair", "Python Developer", 2, "Python, Django, SQL, Git"),
            "seeker2": ("Rahul", "Menon", "Frontend Enthusiast", 1, "HTML, CSS, JavaScript"),
        }
        for username, (first, last, headline, exp, skills) in seeker_data.items():
            user = User.objects.get(username=username)
            user.first_name, user.last_name = first, last
            user.save()
            profile = user.seeker_profile
            profile.headline, profile.experience_years = headline, exp
            profile.location, profile.education = "Kerala", "B.Tech Computer Science"
            profile.bio = "Computer science graduate who enjoys building clean, useful web products."
            profile.target_role, profile.workplace_pref = headline, "hybrid"
            profile.expected_salary = "6-9 LPA"
            profile.linkedin_url = f"https://www.linkedin.com/in/{username}"
            profile.save()
            profile.skills.set(Skill.from_csv(skills))

        job = Job.objects.get(title="Python Django Developer")
        profile = User.objects.get(username="seeker1").seeker_profile
        Application.objects.get_or_create(
            job=job, applicant=profile,
            defaults={"cover_letter": "I love Django and would like to join.",
                      "match_score": compute_match(profile, job)["score"]},
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Logins -> admin / Admin@123 | employer1 / Employer@123 | seeker1 / Seeker@123")
