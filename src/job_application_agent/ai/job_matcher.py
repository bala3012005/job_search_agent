"""
AI-powered job matching system.
"""

import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

class JobMatcher:
    """Matches jobs against user profile and preferences."""

    def __init__(self, user_profile: Dict[str, Any]):
        self.user_profile = user_profile
        self.skill_weights = {
            'primary': 0.4,    # Core Java skills
            'secondary': 0.3,  # Framework skills
            'tertiary': 0.2,   # Database/tools
            'bonus': 0.1       # Additional skills
        }

    def calculate_match_score(self, job_data: Dict[str, Any]) -> float:
        """Calculate match score between job and user profile."""
        score = 0.0

        # Job title matching (30%)
        title_score = self._calculate_title_match(job_data.get('title', ''))
        score += title_score * 0.3

        # Skills matching (40%)
        skills_score = self._calculate_skills_match(
            job_data.get('description', '') + ' ' + job_data.get('requirements', '')
        )
        score += skills_score * 0.4

        # Experience matching (20%)
        experience_score = self._calculate_experience_match(job_data.get('experience_required', ''))
        score += experience_score * 0.2

        # Location matching (10%)
        location_score = self._calculate_location_match(job_data.get('location', ''))
        score += location_score * 0.1

        return min(1.0, score)

    def _calculate_title_match(self, job_title: str) -> float:
        """Calculate how well the job title matches user preferences."""
        title_lower = job_title.lower()

        # Primary keywords (high match)
        primary_keywords = [
            'java developer', 'backend developer', 'software engineer',
            'java backend', 'spring developer', 'full stack developer'
        ]

        # Secondary keywords (medium match)
        secondary_keywords = [
            'software developer', 'application developer', 'systems engineer',
            'programmer', 'developer', 'engineer'
        ]

        # Negative keywords (reduce score)
        negative_keywords = [
            'senior', 'lead', 'principal', 'architect', 'manager',
            'director', 'head', 'vp', 'chief'
        ]

        score = 0.0

        # Check primary keywords
        for keyword in primary_keywords:
            if keyword in title_lower:
                score += 0.8
                break

        # Check secondary keywords
        if score == 0:
            for keyword in secondary_keywords:
                if keyword in title_lower:
                    score += 0.6
                    break

        # Apply negative keyword penalty
        for keyword in negative_keywords:
            if keyword in title_lower:
                score *= 0.3  # Significant penalty
                break

        return score

    def _calculate_skills_match(self, text: str) -> float:
        """Calculate skills match percentage."""
        text_lower = text.lower()

        # Categorize user skills
        skill_categories = {
            'primary': ['java', 'spring boot', 'spring framework'],
            'secondary': ['rest api', 'microservices', 'spring security', 'mvc'],
            'tertiary': ['mysql', 'postgresql', 'sql', 'git', 'maven', 'gradle'],
            'bonus': ['junit', 'hibernate', 'redis', 'kafka', 'docker']
        }

        total_score = 0.0

        for category, skills in skill_categories.items():
            category_score = 0.0
            skills_found = 0

            for skill in skills:
                if skill.lower() in text_lower:
                    skills_found += 1

            if skills_found > 0:
                category_score = min(1.0, skills_found / len(skills))
                total_score += category_score * self.skill_weights[category]

        return total_score

    def _calculate_experience_match(self, experience_text: str) -> float:
        """Calculate experience level match."""
        if not experience_text:
            return 0.5  # Neutral score if no info

        exp_lower = experience_text.lower()
        user_experience = self.user_profile.get('experience_years', 1)

        # Look for experience patterns
        if any(term in exp_lower for term in ['fresher', 'entry level', '0-1', '0-2']):
            if user_experience <= 2:
                return 1.0
            else:
                return 0.3

        # Extract numeric experience requirements
        experience_match = re.search(r'(\d+)[-\s]*(\d+)?\s*years?', exp_lower)
        if experience_match:
            min_exp = int(experience_match.group(1))
            max_exp = int(experience_match.group(2)) if experience_match.group(2) else min_exp + 2

            if min_exp <= user_experience <= max_exp:
                return 1.0
            elif user_experience < min_exp:
                return max(0.0, 1.0 - (min_exp - user_experience) * 0.2)
            else:
                return max(0.0, 1.0 - (user_experience - max_exp) * 0.1)

        return 0.5  # Default neutral score

    def _calculate_location_match(self, job_location: str) -> float:
        """Calculate location preference match."""
        if not job_location:
            return 0.5

        preferred_locations = self.user_profile.get('preferred_locations', [])
        job_location_lower = job_location.lower()

        # Check for remote work
        if 'remote' in job_location_lower and 'Remote' in preferred_locations:
            return 1.0

        # Check for city matches
        for location in preferred_locations:
            if location.lower() in job_location_lower:
                return 1.0

        return 0.2  # Low score for non-preferred locations

    def get_match_reasons(self, job_data: Dict[str, Any]) -> List[str]:
        """Get reasons why a job matches or doesn't match."""
        reasons = []

        # Title analysis
        title_score = self._calculate_title_match(job_data.get('title', ''))
        if title_score > 0.7:
            reasons.append("Excellent job title match")
        elif title_score > 0.4:
            reasons.append("Good job title match")

        # Skills analysis
        skills_score = self._calculate_skills_match(
            job_data.get('description', '') + ' ' + job_data.get('requirements', '')
        )
        if skills_score > 0.6:
            reasons.append("Strong skills alignment")
        elif skills_score > 0.3:
            reasons.append("Moderate skills match")

        # Experience analysis
        exp_score = self._calculate_experience_match(job_data.get('experience_required', ''))
        if exp_score > 0.8:
            reasons.append("Perfect experience level match")
        elif exp_score < 0.3:
            reasons.append("Experience requirements may be too high")

        return reasons
