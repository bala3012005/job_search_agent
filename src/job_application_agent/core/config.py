"""
Configuration management for the Job Application Agent.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class UserProfile:
    """User profile configuration for job matching."""
    name: str = "Java Developer"
    email: str = "developer@example.com"
    phone: str = "+91-9999999999"
    education: str = "B.Tech CSE"
    experience_years: int = 1
    skills: List[str] = field(default_factory=lambda: [
        "Java", "Spring Framework", "Spring Boot", "REST APIs",
        "Spring Security", "MVC", "Microservices", "SQL", "MySQL",
        "PostgreSQL", "Git", "Maven", "Gradle", "JUnit"
    ])
    preferred_locations: List[str] = field(default_factory=lambda: [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Remote"
    ])
    target_companies: List[str] = field(default_factory=lambda: [
        "TCS", "Infosys", "Wipro", "Accenture", "IBM", "Cognizant",
        "HCL", "Tech Mahindra", "Capgemini", "Startups", "MNCs", "PSUs"
    ])

@dataclass
class JobSearchConfig:
    """Job search and filtering configuration."""
    experience_min: int = 0
    experience_max: int = 2
    keywords: List[str] = field(default_factory=lambda: [
        "Java Developer", "Backend Developer", "Spring Boot Developer",
        "Java Backend", "Software Engineer", "Associate Software Engineer"
    ])
    excluded_keywords: List[str] = field(default_factory=lambda: [
        "Senior", "Lead", "Manager", "Architect", "Principal"
    ])
    max_applications_per_day: int = 50
    application_delay_min: int = 2
    application_delay_max: int = 5

@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_path: str = "data/database/app.db"
    encryption_key: str = os.getenv("FERNET_KEY", "")
    backup_enabled: bool = True
    backup_interval_hours: int = 24

@dataclass
class AIConfig:
    """AI and LLM configuration."""
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    cover_letter_template: str = "professional"
    max_tokens: int = 1000
    temperature: float = 0.7

@dataclass
class BrowserConfig:
    """Browser automation configuration."""
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    viewport_width: int = 1366
    viewport_height: int = 768
    timeout: int = 30000
    slow_mo: int = 100

@dataclass
class NotificationConfig:
    """Notification system configuration."""
    desktop_notifications: bool = True
    email_notifications: bool = False
    sound_enabled: bool = True
    notification_types: List[str] = field(default_factory=lambda: [
        "new_jobs", "application_success", "application_failure", "daily_summary"
    ])

class Config:
    """Main configuration class."""

    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[3]
        self.data_dir = self.project_root / "data"
        self.config_dir = self.project_root / "config"

        # Initialize configuration sections
        self.user_profile = UserProfile()
        self.job_search = JobSearchConfig()
        self.database = DatabaseConfig()
        self.ai = AIConfig()
        self.browser = BrowserConfig()
        self.notifications = NotificationConfig()

        # Load configuration from files
        self._load_from_files()
        self._load_from_env()

        # Ensure data directories exist
        self._ensure_directories()

    def _load_from_files(self):
        """Load configuration from JSON files."""
        try:
            # Load user profile if exists
            profile_file = self.config_dir / "user_profile.json"
            if profile_file.exists():
                with open(profile_file) as f:
                    profile_data = json.load(f)
                    for key, value in profile_data.items():
                        if hasattr(self.user_profile, key):
                            setattr(self.user_profile, key, value)

            # Load job search config if exists
            job_config_file = self.config_dir / "job_search.json"
            if job_config_file.exists():
                with open(job_config_file) as f:
                    job_data = json.load(f)
                    for key, value in job_data.items():
                        if hasattr(self.job_search, key):
                            setattr(self.job_search, key, value)

        except Exception as e:
            print(f"Warning: Could not load config files: {e}")

    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Database
        db_path = os.environ.get("DB_PATH")
        if db_path:
            self.database.db_path = db_path
            
        fernet_key = os.environ.get("FERNET_KEY")
        if fernet_key:
            self.database.encryption_key = fernet_key

        # User Profile
        user_name = os.environ.get("USER_NAME")
        if user_name:
            self.user_profile.name = user_name
            
        user_email = os.environ.get("USER_EMAIL")
        if user_email:
            self.user_profile.email = user_email
            
        user_phone = os.environ.get("USER_PHONE")
        if user_phone:
            self.user_profile.phone = user_phone

        # Job Search
        exp_min = os.environ.get("EXPERIENCE_MIN")
        if exp_min and exp_min.isdigit():
            self.job_search.experience_min = int(exp_min)
            
        exp_max = os.environ.get("EXPERIENCE_MAX")
        if exp_max and exp_max.isdigit():
            self.job_search.experience_max = int(exp_max)
            
        max_apps = os.environ.get("MAX_APPLICATIONS_PER_DAY")
        if max_apps and max_apps.isdigit():
            self.job_search.max_applications_per_day = int(max_apps)

        # Browser
        headless = os.environ.get("BROWSER_HEADLESS")
        if headless:
            self.browser.headless = headless.lower() == "true"
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.data_dir / "database",
            self.data_dir / "logs", 
            self.data_dir / "resumes",
            self.data_dir / "temp"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def save_to_file(self, section: str = "all"):
        """Save configuration to JSON files."""
        self.config_dir.mkdir(exist_ok=True)

        if section in ["all", "user_profile"]:
            with open(self.config_dir / "user_profile.json", "w") as f:
                json.dump(self.user_profile.__dict__, f, indent=2)

        if section in ["all", "job_search"]:
            with open(self.config_dir / "job_search.json", "w") as f:
                json.dump(self.job_search.__dict__, f, indent=2)

    def get_resume_path(self) -> Path:
        """Get the path to the user's resume."""
        resume_dir = self.data_dir / "resumes"
        for ext in [".pdf", ".docx", ".doc"]:
            resume_file = resume_dir / f"resume{ext}"
            if resume_file.exists():
                return resume_file
        return resume_dir / "resume.pdf"  # Default

    def get_db_path(self) -> Path:
        """Get the full database path."""
        if Path(self.database.db_path).is_absolute():
            return Path(self.database.db_path)
        return self.project_root / self.database.db_path

# Global configuration instance
config = Config()
