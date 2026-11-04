
import requests


OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"


def generate_job_description(
    title,
    location="",
    workplace="",
    job_type="",
    salary_range="",
    experience_required="",
    skills=""
):
    """
    Generate a professional job description using Ollama.
    """

    prompt = f"""
    Create a professional and attractive job description
    using the following employer-provided details.

    Job Title: {title}
    Location: {location}
    Workplace Type: {workplace}
    Employment Type: {job_type}
    Salary Range: {salary_range}
    Experience Required: {experience_required}
    Required Skills: {skills}

    Structure the job description with these sections:

    1. About the Role
    2. Key Responsibilities
    3. Required Skills and Qualifications
    4. Preferred Skills (only if supported by the given details)

    Instructions:
    - Use professional language.
    - Make the description clear and readable.
    - Do not invent company details, benefits, salary,
      qualifications, or other employer commitments.
    - Do not invent requirements that are not supported
      by the supplied information.
    - Return only the job description.
    """

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.4
                }
            },
            timeout=180
        )

        response.raise_for_status()

        result = response.json()

        description = result.get("message", {}).get("content", "").strip()

        if not description:
            raise ValueError("Ollama returned an empty description.")

        return description

    except requests.exceptions.Timeout:
        raise Exception("AI generation timed out. Please try again.")

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Cannot connect to Ollama. Make sure Ollama is running."
        )

    except requests.exceptions.RequestException as error:
        raise Exception(f"Ollama API error: {error}")
