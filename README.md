# skillBridge – AI-Powered Job Portal

**Connecting Skills to Opportunities**

skillBridge is a Django-based job portal designed to connect job seekers with employers through skill-based job matching, job recommendations, application tracking, and AI-powered job description generation.

The platform provides separate workspaces for administrators, employers, and job seekers, making recruitment and job searching easier through a unified web application.

🌐 **Live Demo:** https://arjunm1112.pythonanywhere.com/ 
💻 **GitHub Repository:** https://github.com/arjunar0021-dotcom/skillbridge-ai-job-portal.git

---

## 1. Project Overview

Finding suitable employment opportunities and identifying qualified candidates can be challenging.

skillBridge aims to simplify this process by providing a centralised platform where:

- Job seekers can discover jobs matching their skills and experience.
- Employers can publish and manage job vacancies.
- Candidates can apply for jobs and track application progress.
- Employers can review applications and schedule interviews.
- Job seekers can identify missing skills through skill-gap analysis.
- Employers can generate professional job descriptions using local AI through Ollama.

## 2. Main Features

### User Authentication and Role Management
- User registration and login.
- Secure password authentication.
- Role-based access control.
- Separate dashboards for Admin, Employer, and Job Seeker.
- User profile management.

### Job Seeker Module
- Browse and search job opportunities.
- Filter jobs by location, workplace, experience level, and employment type.
- Apply for jobs.
- View and withdraw applications.
- Save and manage bookmarked jobs.
- View recommended jobs.
- Track interview schedules.
- Manage professional profiles and resumes.

### Employer Module
- Employer dashboard with recruitment statistics.
- Create, view, update, and delete job postings.
- Manage company information.
- View applicants for posted jobs.
- Review applicant profiles.
- Update application statuses.
- Schedule and manage interviews.
- Export applicant information to CSV.

### Skill-Based Job Recommendation
- Match jobs with candidate skills and experience.
- Display job match percentages.
- Identify skills that candidates already possess.
- Highlight missing skills through skill-gap analysis.
- Rank recommended jobs based on compatibility.

### AI Job Description Generator
- Integrated with Ollama for local AI inference.
- Generates professional job descriptions based on employer-provided job information.
- Automatically fills the job description field.
- Allows employers to review and edit generated descriptions before publishing.
- The AI job description generator requires Ollama to be installed and running locally. It is available when the application is run in an environment with the configured Ollama service.

### Admin Module
- Administrative access to the application.
- User and account management.
- Platform management through Django Admin.
- Role-based access restrictions.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, JavaScript |
| UI Framework | Bootstrap 5 |
| Database | SQLite |
| AI Integration | Ollama |
| AI Model | Llama 3.2 3B (local model) |
| API Integration | Ollama HTTP API |
| Version Control | Git and GitHub |
| Development Environment | Visual Studio Code |

## 4. System Architecture

The application follows a Django-based architecture.

```text
                    skillBridge
                         |
              Django Web Application
                         |
          +--------------+--------------+
          |              |              |
       Accounts         Jobs         Dashboard
          |              |              |
      User Roles     Job Management   Analytics
      Authentication Applications    Statistics
      Profiles       Recommendations
                     Interviews
                         |
                  SQLite Database
                         |
                AI Integration Layer
                         |
                       Ollama
                         |
                  Llama 3.2 3B
```

## 5. Project Structure

The main Django project structure is organised as follows:

```text
jobportal/
│
├── accounts/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── ...
│
├── jobs/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── matching.py
│   ├── ai_services.py
│   ├── urls.py
│   └── ...
│
├── dashboard/
│
├── jobportal/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── templates/
│   ├── accounts/
│   ├── jobs/
│   ├── dashboard/
│   └── ...
│
├── static/
├── media/
├── manage.py
├── requirements.txt
└── README.md
```

*Note: This is a simplified overview. Adjust the file names if your final project structure differs.*

## 6. Installation and Setup

### Prerequisites

Install the following software:

- Python 3.10 or later (use a version compatible with your dependencies).
- Visual Studio Code.
- Git.
- Ollama.
- A compatible Ollama model.

### Step 1: Clone the Repository

```bash
git clone https://github.com/arjunar0021-dotcom/skillbridge-ai-job-portal.git
cd skillbridge-ai-job-portal

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Ollama

Install Ollama from:

https://ollama.com/download

Download the model:

```bash
ollama pull llama3.2:3b
```

Check the downloaded models:

```bash
ollama list
```

Make sure the Ollama service is running locally. Its default API address is:

```text
http://localhost:11434
```

The Django AI integration should be configured to use the same model name:

```text
llama3.2:3b
```

### Step 5: Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create an Administrator Account

```bash
python manage.py createsuperuser
```

Follow the prompts to create your administrator credentials.

### Step 7: Run the Development Server

```bash
python manage.py runserver
```

Open the application:

http://127.0.0.1:8000/

Django Admin:

http://127.0.0.1:8000/admin/

## 7. AI Job Description Generation

skillBridge integrates Ollama to generate job descriptions locally.

**Workflow:**

1. Employer opens the Post a Job page.
2. Employer enters job details.
3. Employer clicks Generate with AI.
4. Django sends the job information to the local Ollama API.
5. The configured language model generates a job description.
6. The generated content is inserted into the description field.
7. Employer reviews and edits the content.
8. Employer saves the job posting.

**Note:** AI-generated content should always be reviewed by the employer before publishing.

## 8. Database

The application uses SQLite for database storage during development.

The database manages information related to:

- Users and roles.
- Job seeker profiles.
- Company profiles.
- Skills.
- Job postings.
- Job applications.
- Saved jobs.
- Interview schedules.

Django ORM is used for database operations and model relationships.

## 9. Running Tests

Run Django's system check:

```bash
python manage.py check
```

Run application tests:

```bash
python manage.py test
```

Check migration status:

```bash
python manage.py showmigrations
```
## Demo Login Credentials

Use the following credentials to explore the application:

| Role | Username | Password |
|---|---|---|
| Administrator | admin | Admin@123 |
| Employer | employer1 | Employer@123 |
| Job Seeker | seeker1 | Seeker@123 |



## 10. Screenshots

Add screenshots of the following application pages to a `screenshots/` directory:

- Login page.
- Registration page.
- Job Seeker dashboard.
- Find Jobs page.
- Recommended Jobs page.
- Applications page.
- Saved Jobs page.
- Interviews page.
- Profile page.
- Employer dashboard.
- My Jobs page.
- Post a Job page with AI generation.
- Applicants management page.
- Admin dashboard.

Example:

```text
screenshots/
    login.png
    signup.png
    seeker-dashboard.png
    find-jobs.png
    recommendations.png
    applications.png
    employer-dashboard.png
    ai-job-generator.png
    admin-dashboard.png
```

## 11. Future Enhancements

- Email notifications for application status updates.
- Advanced recruitment analytics.
- Improved AI-powered candidate-job matching.
- Automated resume analysis.
- Interview reminders.
- Integration with external job platforms.
- Cloud deployment and scalable database support.

## 12. Project Objective

The primary objective of skillBridge is to create an intelligent and user-friendly recruitment platform that connects candidates with suitable employment opportunities while helping employers manage their hiring process efficiently.

---

## 13. Author and Project Information

**Project Name:** skillBridge – AI-Powered Job Portal

**Developed Using:** Python, Django, Bootstrap, SQLite and Ollama.

**GitHub Repository:** [(https://github.com/arjunar0021-dotcom/skillbridge-ai-job-portal.git)]

**Developer:** Arjun S Murali

**Academic Project:** Entri Final Project


**Deployment Link:**[(https://arjunm1112.pythonanywhere.com/)]

---

*skillBridge – Connecting Skills to Opportunities.*
