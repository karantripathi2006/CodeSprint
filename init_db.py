"""
Database initialization script.
Run this to create all tables and seed the skill taxonomy.

Usage: python init_db.py
"""
#DATABASE_URL=postgresql://postgres:postgres@postgres:5432/resumatch
import sys
import os
import json
import logging

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Initialize the database and seed data."""
    logger.info("🔧 Initializing ResuMatch AI database...")

    # Create tables
    from app.core.database import init_db, SessionLocal
    init_db()
    logger.info("✅ Database tables created")

    # Seed skills from taxonomy
    try:
        from app.models.skill import Skill
        db = SessionLocal()

        taxonomy_path = os.path.join("data", "skill_taxonomy.json")
        if os.path.exists(taxonomy_path):
            with open(taxonomy_path, "r") as f:
                taxonomy = json.load(f)

            count = 0
            for category, data in taxonomy.get("categories", {}).items():
                for skill_name in data.get("skills", []):
                    existing = db.query(Skill).filter(Skill.name == skill_name).first()
                    if not existing:
                        skill = Skill(name=skill_name, category=category)
                        db.add(skill)
                        count += 1

                # Add child skills
                for parent_name, children in data.get("children", {}).items():
                    parent = db.query(Skill).filter(Skill.name == parent_name).first()
                    for child_name in children:
                        existing = db.query(Skill).filter(Skill.name == child_name).first()
                        if not existing:
                            child = Skill(
                                name=child_name,
                                category=category,
                                parent_skill_id=parent.id if parent else None,
                            )
                            db.add(child)
                            count += 1

            db.commit()
            logger.info(f"✅ Seeded {count} skills from taxonomy")
        else:
            logger.warning("⚠️ Taxonomy file not found, skipping skill seeding")

        db.close()
    except Exception as e:
        logger.error(f"❌ Error seeding skills: {e}")

    # Seed sample jobs
    try:
        from app.models.job import Job
        db = SessionLocal()

        jobs_path = os.path.join("data", "sample_jobs.json")
        if os.path.exists(jobs_path):
            with open(jobs_path, "r") as f:
                jobs = json.load(f)

            count = 0
            for job_data in jobs:
                existing = db.query(Job).filter(Job.title == job_data["title"]).first()
                if not existing:
                    job = Job(
                        title=job_data["title"],
                        company=job_data.get("company", ""),
                        description=job_data["description"],
                        required_skills=job_data.get("required_skills", []),
                        optional_skills=job_data.get("optional_skills", []),
                        experience_min=job_data.get("experience_min", 0),
                        experience_max=job_data.get("experience_max", 0),
                        location=job_data.get("location", ""),
                        job_type=job_data.get("job_type", ""),
                    )
                    db.add(job)
                    count += 1

            db.commit()
            logger.info(f"✅ Seeded {count} sample jobs")
        db.close()
    except Exception as e:
        logger.error(f"❌ Error seeding jobs: {e}")

    # Seed default admin user
    try:
        from app.models.user import User
        from app.core.security_auth import get_password_hash
        db = SessionLocal()

        if not db.query(User).filter(User.username == "admin").first():
            admin = User(username="admin", hashed_password=get_password_hash("password"))
            db.add(admin)
            db.commit()
            logger.info("✅ Default admin user created (username: admin / password: password)")
        else:
            logger.info("ℹ️  Admin user already exists, skipping")

        db.close()
    except Exception as e:
        logger.error(f"❌ Error seeding admin user: {e}")

    logger.info("🎉 Database initialization complete!")


if __name__ == "__main__":
    main()
