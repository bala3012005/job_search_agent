"""
Job data model for the application.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Job:
    """Job data model."""
    job_id: str
    title: str
    company: str
    location: str
    source_platform: str
    source_url: str
    description: str = ""
    requirements: str = ""
    salary_range: str = ""
    experience_required: str = ""
    posted_date: str = ""
    match_score: float = 0.0
    status: str = "discovered"  # discovered, applied, rejected, interview, offer
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'job_id': self.job_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'requirements': self.requirements,
            'salary_range': self.salary_range,
            'experience_required': self.experience_required,
            'posted_date': self.posted_date,
            'source_platform': self.source_platform,
            'source_url': self.source_url,
            'match_score': self.match_score,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create Job instance from dictionary."""
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None

        return cls(
            job_id=data['job_id'],
            title=data['title'],
            company=data['company'],
            location=data['location'],
            source_platform=data['source_platform'],
            source_url=data['source_url'],
            description=data.get('description', ''),
            requirements=data.get('requirements', ''),
            salary_range=data.get('salary_range', ''),
            experience_required=data.get('experience_required', ''),
            posted_date=data.get('posted_date', ''),
            match_score=data.get('match_score', 0.0),
            status=data.get('status', 'discovered'),
            created_at=created_at,
            updated_at=updated_at
        )

@dataclass
class Application:
    """Job application data model."""
    application_id: str
    job_id: str
    status: str = "pending"  # pending, submitted, in_review, rejected, interview, offer
    cover_letter_path: str = ""
    applied_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    response_status: str = ""
    notes: str = ""

    def __post_init__(self):
        if self.applied_at is None:
            self.applied_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'application_id': self.application_id,
            'job_id': self.job_id,
            'status': self.status,
            'cover_letter_path': self.cover_letter_path,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'response_received_at': self.response_received_at.isoformat() if self.response_received_at else None,
            'response_status': self.response_status,
            'notes': self.notes
        }
