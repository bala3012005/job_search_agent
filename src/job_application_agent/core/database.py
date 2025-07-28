"""
Database operations with encryption support.
"""

import sqlite3
import aiosqlite
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from .encryption import EncryptionManager
from .config import config

logger = logging.getLogger(__name__)

class Database:
    """Database manager with encryption support."""

    def __init__(self):
        self.db_path = config.get_db_path()
        self.encryption_manager = EncryptionManager(config.database.encryption_key) if config.database.encryption_key else None
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensure database file and directory exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create tables if they don't exist
        with sqlite3.connect(self.db_path) as conn:
            self._create_tables(conn)

    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables."""
        cursor = conn.cursor()

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                requirements TEXT,
                salary_range TEXT,
                experience_required TEXT,
                posted_date TEXT,
                source_platform TEXT NOT NULL,
                source_url TEXT,
                match_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'discovered',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                application_id TEXT,
                status TEXT DEFAULT 'pending',
                cover_letter_path TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_received_at TIMESTAMP,
                response_status TEXT,
                notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (job_id)
            )
        """)

        # User credentials (encrypted)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT UNIQUE NOT NULL,
                username_encrypted BLOB,
                password_encrypted BLOB,
                additional_data_encrypted BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("Database tables created/verified")

    async def save_job(self, job_data: Dict[str, Any]) -> bool:
        """Save job information to database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO jobs 
                    (job_id, title, company, location, description, requirements, 
                     salary_range, experience_required, posted_date, source_platform, 
                     source_url, match_score, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_data.get('job_id'),
                    job_data.get('title'),
                    job_data.get('company'),
                    job_data.get('location'),
                    job_data.get('description'),
                    job_data.get('requirements'),
                    job_data.get('salary_range'),
                    job_data.get('experience_required'),
                    job_data.get('posted_date'),
                    job_data.get('source_platform'),
                    job_data.get('source_url'),
                    job_data.get('match_score', 0.0),
                    job_data.get('status', 'discovered'),
                    datetime.now().isoformat()
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save job: {e}")
            return False

    async def get_jobs(self, status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jobs from database with optional status filter."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM jobs"
                params = []
                
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get jobs: {e}")
            return []

    async def save_application(self, application_data: Dict[str, Any]) -> bool:
        """Save application information to database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO applications 
                    (job_id, application_id, status, cover_letter_path, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    application_data.get('job_id'),
                    application_data.get('application_id'),
                    application_data.get('status', 'pending'),
                    application_data.get('cover_letter_path'),
                    application_data.get('notes')
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save application: {e}")
            return False

    async def update_application(self, application_id: str, status: str, response_status: Optional[str] = None) -> bool:
        """Update application status and response."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE applications 
                    SET status = ?, response_status = ?, response_received_at = ?
                    WHERE application_id = ?
                """, (status, response_status, datetime.now().isoformat(), application_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update application: {e}")
            return False

    async def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get application statistics for the specified number of days."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                date_limit = (datetime.now() - timedelta(days=days)).isoformat()

                # Get job stats
                async with db.execute("""
                    SELECT COUNT(*) as total_jobs,
                           SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied_jobs,
                           SUM(CASE WHEN status = 'discovered' THEN 1 ELSE 0 END) as pending_jobs
                    FROM jobs
                    WHERE created_at >= ?
                """, (date_limit,)) as cursor:
                    job_stats_row = await cursor.fetchone()
                    job_stats = {str(k): v for k, v in dict(job_stats_row).items()} if job_stats_row else {}

                # Get application stats
                async with db.execute("""
                    SELECT COUNT(*) as total_applications,
                           SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted_applications,
                           SUM(CASE WHEN response_status = 'accepted' THEN 1 ELSE 0 END) as accepted_applications
                    FROM applications
                    WHERE applied_at >= ?
                """, (date_limit,)) as cursor:
                    app_stats_row = await cursor.fetchone()
                    app_stats = {str(k): v for k, v in dict(app_stats_row).items()} if app_stats_row else {}

                return {**job_stats, **app_stats}

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    async def update_daily_stats(self, jobs_found: int, applications_sent: int) -> None:
        """Update daily statistics."""
        today = datetime.now().date().isoformat()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO daily_stats 
                    (date, jobs_found, applications_sent)
                    VALUES (?, ?, ?)
                """, (today, jobs_found, applications_sent))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update daily stats: {e}")

# ...existing code...

    async def save_credentials(self, platform: str, username: str, password: str, additional_data: Optional[Dict] = None) -> bool:
        """Save encrypted credentials for a platform."""
        if not self.encryption_manager:
            logger.error("Encryption manager not initialized")
            return False

        try:
            username_encrypted = self.encryption_manager.encrypt_string(username)
            password_encrypted = self.encryption_manager.encrypt_string(password)
            additional_data_encrypted = (
                self.encryption_manager.encrypt_string(json.dumps(additional_data))
                if additional_data else None
            )

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO user_credentials 
                    (platform, username_encrypted, password_encrypted, additional_data_encrypted, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    platform,
                    username_encrypted,
                    password_encrypted,
                    additional_data_encrypted,
                    datetime.now().isoformat()
                ))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False

    async def get_credentials(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get decrypted credentials for a platform."""
        if not self.encryption_manager:
            logger.error("Encryption manager not initialized")
            return None

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_credentials WHERE platform = ?",
                    (platform,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return None

                    result = {
                        'username': self.encryption_manager.decrypt_string(row['username_encrypted']),
                        'password': self.encryption_manager.decrypt_string(row['password_encrypted'])
                    }

                    if row['additional_data_encrypted']:
                        additional_data = self.encryption_manager.decrypt_string(row['additional_data_encrypted'])
                        result['additional_data'] = json.loads(additional_data)

                    return result

        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            return None

# Global database instance
db = Database()