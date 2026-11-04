"""AI-style job matching and skill-gap analysis.

Score (0-100) = 80% skill overlap + 20% experience fit.
Skill gap  = skills the job needs that the candidate does not have.
"""
from collections import Counter

SKILL_WEIGHT = 0.8
EXPERIENCE_WEIGHT = 0.2


def compute_match(profile, job, profile_skill_ids=None):
    if profile_skill_ids is None:
        profile_skill_ids = set(profile.skills.values_list("id", flat=True))

    job_skills = list(job.skills.all())
    matched = [s.name for s in job_skills if s.id in profile_skill_ids]
    missing = [s.name for s in job_skills if s.id not in profile_skill_ids]

    if not job_skills:
        return {"score": 0, "matched": [], "missing": []}

    skill_ratio = len(matched) / len(job_skills)
    if job.experience_required:
        exp_ratio = min(profile.experience_years / job.experience_required, 1)
    else:
        exp_ratio = 1
    score = round(100 * (SKILL_WEIGHT * skill_ratio + EXPERIENCE_WEIGHT * exp_ratio))
    return {"score": score, "matched": matched, "missing": missing}


def rank_jobs(profile, jobs):
    """Return jobs with at least one matching skill, best match first."""
    skill_ids = set(profile.skills.values_list("id", flat=True))
    results = []
    for job in jobs:
        match = compute_match(profile, job, skill_ids)
        if match["matched"]:
            results.append({"job": job, **match})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def top_missing_skills(results, limit=8):
    """Most common missing skills across the matched jobs -> 'what to learn next'."""
    counter = Counter(name for r in results for name in r["missing"])
    return counter.most_common(limit)
