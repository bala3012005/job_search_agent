"""
AI-powered cover letter generator using local LLM.
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from pathlib import Path
from ..core.config import config

logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    """Generates personalized cover letters using Ollama."""

    def __init__(self):
        self.ollama_url = config.ai.ollama_base_url
        self.model = config.ai.ollama_model
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load cover letter templates."""
        return {
            "professional": """
Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. 
As a {user_education} graduate with {user_experience} years of experience in Java backend development, 
I am excited about the opportunity to contribute to your team.

My technical skills include:
{user_skills}

Key qualifications that align with your requirements:
{job_requirements_match}

I am particularly drawn to {company_name} because of your commitment to innovation and excellence in technology. 
The {job_title} role aligns perfectly with my career goals and technical expertise.

I would welcome the opportunity to discuss how my skills and passion for Java development can contribute to your team's success.

Thank you for your consideration.

Best regards,
{user_name}
            """.strip()
        }

    async def generate_cover_letter(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a personalized cover letter for a job."""
        try:
            # Extract job information
            job_title = job_data.get('title', '')
            company_name = job_data.get('company', '')
            job_description = job_data.get('description', '')
            job_requirements = job_data.get('requirements', '')

            # Create prompt for AI
            prompt = self._create_cover_letter_prompt(
                job_title, company_name, job_description, job_requirements
            )

            # Generate cover letter using Ollama
            cover_letter_text = await self._call_ollama(prompt)

            if cover_letter_text:
                # Save cover letter to file
                file_path = await self._save_cover_letter(
                    cover_letter_text, job_data.get('job_id', 'unknown')
                )

                return {
                    'text': cover_letter_text,
                    'file_path': file_path,
                    'generated_at': asyncio.get_event_loop().time()
                }

            return None

        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return None

    def _create_cover_letter_prompt(self, job_title: str, company_name: str, 
                                  job_description: str, job_requirements: str) -> str:
        """Create a prompt for the AI model."""
        user_skills = ", ".join(config.user_profile.skills)

        prompt = f"""
Write a professional cover letter for a Java backend developer position.

Job Details:
- Position: {job_title}
- Company: {company_name}
- Job Description: {job_description[:500]}...
- Requirements: {job_requirements[:300]}...

Candidate Profile:
- Name: {config.user_profile.name}
- Education: {config.user_profile.education}
- Experience: {config.user_profile.experience_years} years
- Skills: {user_skills}

Requirements:
1. Keep it professional and concise (250-300 words)
2. Highlight relevant Java backend skills
3. Show enthusiasm for the specific company and role
4. Mention 2-3 key technical skills that match the job requirements
5. Use a confident but humble tone
6. End with a call to action

Please write only the cover letter content, no additional text or formatting.
        """

        return prompt.strip()

    async def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API to generate text."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.ai.temperature,
                    "top_p": 0.9,
                    "max_tokens": config.ai.max_tokens
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '').strip()
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            # Fallback to template-based generation
            return self._generate_template_cover_letter(prompt)

    def _generate_template_cover_letter(self, prompt: str) -> str:
        """Generate a cover letter using templates as fallback."""
        template = self.templates["professional"]

        # Extract basic information from prompt
        job_title = "Java Developer"  # Default
        company_name = "the company"  # Default

        # Simple template substitution
        cover_letter = template.format(
            job_title=job_title,
            company_name=company_name,
            user_education=config.user_profile.education,
            user_experience=config.user_profile.experience_years,
            user_skills=", ".join(config.user_profile.skills[:5]),
            job_requirements_match="Strong experience in Java, Spring Boot, and REST APIs",
            user_name=config.user_profile.name
        )

        return cover_letter

    async def _save_cover_letter(self, content: str, job_id: str) -> str:
        """Save cover letter to file."""
        try:
            # Create cover letters directory
            cover_letters_dir = Path(config.data_dir) / "resumes" / "generated"
            cover_letters_dir.mkdir(parents=True, exist_ok=True)

            # Create filename
            filename = f"cover_letter_{job_id}_{int(asyncio.get_event_loop().time())}.txt"
            file_path = cover_letters_dir / filename

            # Save content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Cover letter saved: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Error saving cover letter: {e}")
            return ""
