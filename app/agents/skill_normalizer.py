"""
Skill Normalization Agent
=========================
Normalizes extracted skills against a taxonomy, resolves synonyms/abbreviations,
infers parent skills, and estimates proficiency levels.
"""

import json
import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Path to taxonomy data file ───────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
TAXONOMY_FILE = os.path.join(DATA_DIR, "skill_taxonomy.json")


class SkillNormalizerAgent:
    """
    Agent responsible for normalizing skills extracted from resumes.
    
    Features:
    - Synonym resolution (JS → JavaScript, React.js → React)
    - Abbreviation expansion (K8s → Kubernetes, ML → Machine Learning)
    - Parent skill inference (TensorFlow → Deep Learning → Machine Learning)
    - Proficiency estimation based on years/context
    - Unknown skill detection
    """

    def __init__(self):
        """Load skill taxonomy and build lookup tables."""
        self.taxonomy = self._load_taxonomy()
        self.synonym_map = self._build_synonym_map()
        self.parent_map = self._build_parent_map()
        self.all_known_skills = set(s.lower() for s in self.synonym_map.values())
        logger.info(f"SkillNormalizerAgent initialized with {len(self.all_known_skills)} known skills")

    def _load_taxonomy(self) -> Dict:
        """Load skill taxonomy from JSON file."""
        try:
            with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Taxonomy file not found at {TAXONOMY_FILE}, using built-in defaults")
            return self._default_taxonomy()

    def _default_taxonomy(self) -> Dict:
        """Built-in fallback taxonomy when JSON file is missing."""
        return {
            "categories": {
                "Programming Languages": {
                    "skills": ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R"],
                    "synonyms": {
                        "JS": "JavaScript", "TS": "TypeScript",
                        "C Sharp": "C#", "Golang": "Go",
                        "Python3": "Python", "Python 3": "Python",
                    }
                },
                "Web Frameworks": {
                    "skills": ["React", "Angular", "Vue.js", "Next.js", "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot", "Laravel", "Rails"],
                    "synonyms": {
                        "React.js": "React", "ReactJS": "React",
                        "Angular.js": "Angular", "AngularJS": "Angular",
                        "Vue": "Vue.js", "VueJS": "Vue.js",
                        "NextJS": "Next.js", "Nextjs": "Next.js",
                        "NodeJS": "Node.js", "Node": "Node.js",
                        "ExpressJS": "Express.js", "Express": "Express.js",
                        "Spring": "Spring Boot",
                        "Ruby on Rails": "Rails",
                    }
                },
                "Data Science & ML": {
                    "skills": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Analysis", "Data Engineering"],
                    "children": {
                        "Machine Learning": ["Scikit-learn", "XGBoost", "LightGBM"],
                        "Deep Learning": ["TensorFlow", "PyTorch", "Keras"],
                        "NLP": ["spaCy", "NLTK", "Hugging Face", "LangChain"],
                        "Data Analysis": ["Pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter"],
                    },
                    "synonyms": {
                        "ML": "Machine Learning", "DL": "Deep Learning",
                        "Natural Language Processing": "NLP",
                        "CV": "Computer Vision",
                        "sklearn": "Scikit-learn", "scikit learn": "Scikit-learn",
                        "tf": "TensorFlow", "Tensor Flow": "TensorFlow",
                    }
                },
                "Cloud & DevOps": {
                    "skills": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "CI/CD", "Jenkins", "GitHub Actions"],
                    "synonyms": {
                        "Amazon Web Services": "AWS",
                        "Google Cloud": "GCP", "Google Cloud Platform": "GCP",
                        "Microsoft Azure": "Azure",
                        "K8s": "Kubernetes", "k8s": "Kubernetes",
                        "CICD": "CI/CD",
                    }
                },
                "Databases": {
                    "skills": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite", "Cassandra", "DynamoDB"],
                    "synonyms": {
                        "Postgres": "PostgreSQL", "PG": "PostgreSQL",
                        "Mongo": "MongoDB",
                        "ES": "Elasticsearch", "Elastic Search": "Elasticsearch",
                    }
                },
                "Soft Skills": {
                    "skills": ["Leadership", "Communication", "Problem Solving", "Teamwork", "Time Management", "Agile", "Scrum", "Project Management"],
                    "synonyms": {
                        "Team Player": "Teamwork",
                        "PM": "Project Management",
                    }
                }
            }
        }

    def _build_synonym_map(self) -> Dict[str, str]:
        """Build a flat lookup: synonym (lowercase) -> canonical name."""
        mapping = {}
        for category_name, category_data in self.taxonomy.get("categories", {}).items():
            # Map each skill to itself
            for skill in category_data.get("skills", []):
                mapping[skill.lower()] = skill
            # Map synonyms
            for syn, canonical in category_data.get("synonyms", {}).items():
                mapping[syn.lower()] = canonical
            # Map children
            for parent, children in category_data.get("children", {}).items():
                for child in children:
                    mapping[child.lower()] = child
        return mapping

    def _build_parent_map(self) -> Dict[str, str]:
        """Build child -> parent skill mapping for inference."""
        parent_map = {}
        for category_name, category_data in self.taxonomy.get("categories", {}).items():
            for parent, children in category_data.get("children", {}).items():
                for child in children:
                    parent_map[child.lower()] = parent
        return parent_map

    # ═══════════════════════════════════════════════════════════════════════
    #  MAIN NORMALIZATION PIPELINE
    # ═══════════════════════════════════════════════════════════════════════

    def normalize(self, raw_skills: List[str], experience_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Normalize a list of raw skills extracted from a resume.
        
        Args:
            raw_skills: List of skill strings from the resume parser
            experience_data: Work experience data for proficiency estimation
            
        Returns:
            Dict with normalized_skills, inferred_skills, unknown_skills, proficiency_map
        """
        logger.info(f"Normalizing {len(raw_skills)} raw skills")

        normalized = []
        inferred_skills = []
        unknown_skills = []
        proficiency_map = {}
        seen = set()

        for raw in raw_skills:
            canonical, is_known = self._resolve_skill(raw)

            if canonical.lower() in seen:
                continue
            seen.add(canonical.lower())

            if is_known:
                normalized.append(canonical)
                # Estimate proficiency
                prof = self._estimate_proficiency(canonical, raw, experience_data)
                proficiency_map[canonical] = prof

                # Infer parent skills
                parent = self._infer_parent(canonical)
                if parent and parent.lower() not in seen:
                    seen.add(parent.lower())
                    inferred_skills.append(parent)
                    proficiency_map[parent] = max(0.3, prof - 0.1)  # Slightly lower proficiency for inferred
            else:
                unknown_skills.append(raw)
                # Still add unknown skills with lower confidence
                proficiency_map[raw] = 0.3

        result = {
            "normalized_skills": sorted(normalized),
            "inferred_skills": sorted(inferred_skills),
            "unknown_skills": sorted(unknown_skills),
            "all_skills": sorted(normalized + inferred_skills + unknown_skills),
            "proficiency_map": proficiency_map,
            "total_count": len(normalized) + len(inferred_skills) + len(unknown_skills),
        }

        logger.info(f"Normalization complete: {len(normalized)} normalized, "
                     f"{len(inferred_skills)} inferred, {len(unknown_skills)} unknown")
        return result

    def _resolve_skill(self, raw_skill: str) -> Tuple[str, bool]:
        """
        Resolve a raw skill string to its canonical form.
        Returns (canonical_name, is_known).
        """
        cleaned = raw_skill.strip()
        lower = cleaned.lower()

        # Direct match in synonym map
        if lower in self.synonym_map:
            return self.synonym_map[lower], True

        # Fuzzy matching: try removing common suffixes/prefixes
        for variant in [lower, lower.replace(".", ""), lower.replace("-", " "), lower.replace(" ", "")]:
            if variant in self.synonym_map:
                return self.synonym_map[variant], True

        # Word-boundary substring match — skip very short known skills (e.g. "R", "Go")
        # to prevent "R" matching "React", "Go" matching "Django", etc.
        for known_lower, canonical in self.synonym_map.items():
            if len(known_lower) <= 3:
                continue
            if re.search(r'\b' + re.escape(known_lower) + r'\b', lower):
                return canonical, True

        return cleaned, False

    def _infer_parent(self, skill: str) -> Optional[str]:
        """Infer parent/higher-level skill from a specific skill."""
        return self.parent_map.get(skill.lower())

    def _estimate_proficiency(self, skill: str, raw: str, experience_data: List[Dict] = None) -> float:
        """
        Estimate proficiency level (0.0 - 1.0) based on context.
        
        Heuristics:
        - Mentioned in many experience entries → higher proficiency
        - Recent usage → higher proficiency
        - Mentioned as "expert/advanced" → higher proficiency
        - Default → 0.5 (intermediate)
        """
        proficiency = 0.5  # Default: intermediate

        if experience_data:
            # Count how many experience entries mention this skill
            mentions = 0
            for exp in experience_data:
                responsibilities = " ".join(exp.get("responsibilities", []))
                if re.search(re.escape(skill), responsibilities, re.IGNORECASE):
                    mentions += 1

            # More mentions → higher proficiency (up to 0.9)
            proficiency = min(0.9, 0.4 + (mentions * 0.15))

        # Check for proficiency indicators in raw text
        context_lower = raw.lower()
        if any(word in context_lower for word in ["expert", "advanced", "senior", "lead"]):
            proficiency = max(proficiency, 0.85)
        elif any(word in context_lower for word in ["intermediate", "proficient", "familiar"]):
            proficiency = max(proficiency, 0.6)
        elif any(word in context_lower for word in ["beginner", "basic", "learning", "exposure"]):
            proficiency = min(proficiency, 0.3)

        return round(proficiency, 2)

    def get_taxonomy(self) -> Dict:
        """Return the full skill taxonomy for the API."""
        return self.taxonomy

    def get_category_for_skill(self, skill: str) -> Optional[str]:
        """Find which category a skill belongs to."""
        skill_lower = skill.lower()
        for cat_name, cat_data in self.taxonomy.get("categories", {}).items():
            all_skills = [s.lower() for s in cat_data.get("skills", [])]
            children = []
            for child_list in cat_data.get("children", {}).values():
                children.extend([c.lower() for c in child_list])
            if skill_lower in all_skills or skill_lower in children:
                return cat_name
        return "Other"
