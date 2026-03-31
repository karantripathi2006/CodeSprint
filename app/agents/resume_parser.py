"""
Resume Parsing Agent
====================
Extracts structured data from resumes in PDF, DOCX, and plain text formats.
Uses PyMuPDF, pdfplumber, and python-docx for file parsing, and regex/heuristics
for section detection and data extraction.
"""

import re
import io
import logging
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ResumeParserAgent:
    """
    Agent responsible for parsing resumes and extracting structured data.
    Supports PDF, DOCX, and plain text formats.
    """

    # ── Section Headers (regex patterns for detecting resume sections) ────
    SECTION_PATTERNS = {
        "education": r"(?i)\b(education|academic|qualification|degree|university|college)\b",
        "experience": r"(?i)\b(experience|employment|work\s*history|professional\s*background|career)\b",
        "skills": r"(?i)\b(skills|technical\s*skills|competencies|technologies|proficiencies|tools)\b",
        "projects": r"(?i)\b(projects|personal\s*projects|academic\s*projects|portfolio)\b",
        "certifications": r"(?i)\b(certifications?|certificates?|licenses?|credentials?)\b",
        "summary": r"(?i)\b(summary|objective|profile|about\s*me|introduction|overview)\b",
        "contact": r"(?i)\b(contact|personal\s*info|details)\b",
    }

    # ── Contact Extraction Patterns ──────────────────────────────────────
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
    LINKEDIN_PATTERN = re.compile(r"(?:linkedin\.com/in/|linkedin:\s*)([\w-]+)", re.IGNORECASE)

    # ── Experience Duration Patterns ─────────────────────────────────────
    # Matches "Jan 2020 – Dec 2022" or "Jan 2020 – Present"
    DATE_RANGE_PATTERN = re.compile(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4})\s*[-–—to]+\s*"
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|[Pp]resent|[Cc]urrent)",
        re.IGNORECASE,
    )
    # Matches "2020 – 2023" or "2020 – Present"
    YEAR_RANGE_PATTERN = re.compile(
        r"\b(20\d{2}|19\d{2})\s*[-–—to]+\s*(20\d{2}|19\d{2}|[Pp]resent|[Cc]urrent)\b"
    )

    YEAR_PATTERN = re.compile(r"\b(20\d{2}|19\d{2})\b")

    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Main entry point: parse a resume file and return structured data.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename (used to detect format)
            
        Returns:
            Dict with keys: name, email, phone, location, summary, education,
            experience, skills, projects, certifications, raw_text
        """
        start_time = time.time()
        logger.info(f"Parsing resume: {filename}")

        # 1. Extract raw text based on file type
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        raw_text = self._extract_text(file_content, ext)

        if not raw_text or len(raw_text.strip()) < 50:
            logger.warning(f"Very little text extracted from {filename}")
            return self._empty_result(raw_text or "", time.time() - start_time)

        # 2. Extract structured data
        result = {
            "name": self._extract_name(raw_text),
            "email": self._extract_email(raw_text),
            "phone": self._extract_phone(raw_text),
            "location": self._extract_location(raw_text),
            "linkedin": self._extract_linkedin(raw_text),
            "summary": "",
            "education": [],
            "experience": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "raw_text": raw_text,
            "parsing_time_ms": 0,
        }

        # 3. Split into sections and extract data from each
        sections = self._split_into_sections(raw_text)

        result["summary"] = self._extract_summary(sections.get("summary", ""), raw_text)
        result["education"] = self._extract_education(sections.get("education", ""))
        result["experience"] = self._extract_experience(sections.get("experience", ""))
        result["skills"] = self._extract_skills(sections.get("skills", ""), raw_text)
        result["projects"] = self._extract_projects(sections.get("projects", ""))
        result["certifications"] = self._extract_certifications(sections.get("certifications", ""))

        result["parsing_time_ms"] = int((time.time() - start_time) * 1000)
        logger.info(f"Parsed {filename} in {result['parsing_time_ms']}ms — "
                     f"found {len(result['skills'])} skills, "
                     f"{len(result['experience'])} experiences, "
                     f"{len(result['education'])} education entries")
        return result

    # ═══════════════════════════════════════════════════════════════════════
    #  TEXT EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════

    def _extract_text(self, content: bytes, ext: str) -> str:
        """Extract text from file based on extension."""
        try:
            if ext == "pdf":
                return self._extract_pdf_text(content)
            elif ext == "docx":
                return self._extract_docx_text(content)
            else:
                # Assume plain text with various encodings
                for encoding in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                return content.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Error extracting text from .{ext} file: {e}")
            return ""

    def _extract_with_docling(self, content: bytes, ext: str) -> str:
        """
        Primary extraction using Docling (IBM) — handles complex layouts,
        tables, and multi-column PDFs much better than rule-based parsers.
        Returns empty string if Docling is not installed or fails.
        """
        try:
            import tempfile, os
            from docling.document_converter import DocumentConverter

            suffix = f".{ext}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            converter = DocumentConverter()
            result = converter.convert(tmp_path)
            os.unlink(tmp_path)

            # Export to markdown — preserves section structure better than plain text
            text = result.document.export_to_markdown()
            logger.info(f"Docling extracted {len(text)} chars from .{ext} file")
            return text
        except ImportError:
            logger.debug("Docling not installed; using PyMuPDF/pdfplumber fallback")
            return ""
        except Exception as e:
            logger.warning(f"Docling failed: {e}; using fallback")
            return ""

    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF: Docling → PyMuPDF → pdfplumber."""
        # Try Docling first (best quality for complex layouts)
        text = self._extract_with_docling(content, "pdf")
        if text and len(text.strip()) > 100:
            return text

        # Fallback: PyMuPDF
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"
            doc.close()
            if text.strip():
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}, trying pdfplumber")

        # Fallback: pdfplumber
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"pdfplumber also failed: {e}")

        return text

    def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX: Docling → python-docx."""
        # Try Docling first
        text = self._extract_with_docling(content, "docx")
        if text and len(text.strip()) > 50:
            return text

        # Fallback: python-docx
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Error reading DOCX: {e}")
            return ""

    # ═══════════════════════════════════════════════════════════════════════
    #  SECTION SPLITTING
    # ═══════════════════════════════════════════════════════════════════════

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Split resume text into named sections based on header detection.
        Returns dict like {"education": "...", "experience": "...", ...}
        """
        lines = text.split("\n")
        sections: Dict[str, str] = {}
        current_section = "header"
        current_lines: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_lines.append("")
                continue

            # Check if this line is a section header
            detected = self._detect_section(stripped)
            if detected and detected != current_section:
                # Save previous section
                sections[current_section] = "\n".join(current_lines)
                current_section = detected
                current_lines = []
            else:
                current_lines.append(line)

        # Save last section
        sections[current_section] = "\n".join(current_lines)
        return sections

    def _detect_section(self, line: str) -> Optional[str]:
        """Detect if a line is a section header. Returns section name or None."""
        # Section headers are usually short, possibly uppercase or bold-formatted
        clean = re.sub(r"[^a-zA-Z\s]", "", line).strip()
        if len(clean) > 50 or len(clean) < 3:
            return None

        for section, pattern in self.SECTION_PATTERNS.items():
            if re.search(pattern, clean):
                return section
        return None

    # ═══════════════════════════════════════════════════════════════════════
    #  FIELD EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════

    def _extract_name(self, text: str) -> str:
        """Extract candidate name from resume text."""
        # Strategy 1: explicit label anywhere near the top
        label_match = re.search(r"(?:^|\n)\s*(?:name|full\s*name)\s*[:\-]\s*([A-Za-z][A-Za-z\s\.\-']{1,40})", text[:2000], re.IGNORECASE)
        if label_match:
            return label_match.group(1).strip().title()

        lines = text.strip().split("\n")
        candidates = []

        for line in lines[:10]:  # Scan first 10 lines
            cleaned = line.strip()
            if not cleaned or len(cleaned) < 2:
                continue
            # Skip contact info lines
            if self.EMAIL_PATTERN.search(cleaned) or self.PHONE_PATTERN.search(cleaned):
                continue
            if re.search(r"http|linkedin|github|twitter|@|www\.", cleaned, re.IGNORECASE):
                continue
            # Skip lines that are obviously not names (addresses, titles, dates)
            if re.search(r"\d{4}|street|avenue|road|#|\||/", cleaned, re.IGNORECASE):
                continue
            # Skip single-word all-caps lines that look like section headers
            if cleaned.isupper() and len(cleaned.split()) == 1 and len(cleaned) > 6:
                continue

            # Accept lines that are mostly alphabetic (≥70% alpha+space chars)
            alpha_ratio = sum(1 for c in cleaned if c.isalpha() or c == ' ') / max(len(cleaned), 1)
            if alpha_ratio >= 0.70 and 2 <= len(cleaned) <= 50:
                candidates.append(cleaned)

        # Strategy 2: prefer the first candidate that looks like 2–4 words (a real full name)
        for c in candidates:
            words = c.split()
            if 2 <= len(words) <= 4 and all(len(w) >= 2 for w in words):
                return c.title()

        # Strategy 3: fall back to any candidate found
        if candidates:
            return candidates[0].title()

        return ""

    def _extract_email(self, text: str) -> str:
        """Extract first email address found."""
        match = self.EMAIL_PATTERN.search(text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        """Extract first phone number found."""
        match = self.PHONE_PATTERN.search(text)
        return match.group(0).strip() if match else ""

    def _extract_location(self, text: str) -> str:
        """Extract location from early lines of resume."""
        # Common location patterns
        location_pattern = re.compile(
            r"(?:location|address|city|based\s*in)[\s:]+(.+)",
            re.IGNORECASE,
        )
        match = location_pattern.search(text[:1000])
        if match:
            return match.group(1).strip().split("\n")[0]

        # Look for city, state patterns in first few lines
        city_state = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2}|[A-Za-z]+)\b")
        for line in text.split("\n")[:8]:
            match = city_state.search(line)
            if match:
                return match.group(0)
        return ""

    def _extract_linkedin(self, text: str) -> str:
        """Extract LinkedIn profile URL."""
        match = self.LINKEDIN_PATTERN.search(text)
        if match:
            return f"linkedin.com/in/{match.group(1)}"
        return ""

    def _extract_summary(self, section_text: str, full_text: str) -> str:
        """Extract professional summary/objective."""
        if section_text and len(section_text.strip()) > 20:
            return section_text.strip()[:500]
        return ""

    def _extract_education(self, section_text: str) -> List[Dict[str, str]]:
        """Extract education entries from the education section."""
        if not section_text.strip():
            return []

        education = []
        # Common degree patterns
        degree_pattern = re.compile(
            r"(B\.?S\.?c?\.?|M\.?S\.?c?\.?|B\.?A\.?|M\.?A\.?|B\.?Tech|M\.?Tech|Ph\.?D\.?|"
            r"Bachelor|Master|MBA|Diploma|Associate|Doctor)['\s]*(?:of|in|,|\.|\s)?\s*(.*?)(?:\n|$)",
            re.IGNORECASE,
        )

        lines = section_text.strip().split("\n")
        current_entry: Dict[str, str] = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    education.append(current_entry)
                    current_entry = {}
                continue

            deg_match = degree_pattern.search(line)
            if deg_match:
                if current_entry:
                    education.append(current_entry)
                current_entry = {
                    "degree": deg_match.group(0).strip(),
                    "institution": "",
                    "year": "",
                    "gpa": "",
                }

            # Extract year
            years = self.YEAR_PATTERN.findall(line)
            if years and current_entry:
                current_entry["year"] = years[-1]

            # Extract GPA
            gpa_match = re.search(r"(?:GPA|CGPA|Grade)[\s:]+(\d+\.?\d*)", line, re.IGNORECASE)
            if gpa_match and current_entry:
                current_entry["gpa"] = gpa_match.group(1)

            # If no degree found yet, this might be the institution
            if not deg_match and current_entry and not current_entry.get("institution"):
                current_entry["institution"] = line

        if current_entry:
            education.append(current_entry)

        return education if education else [{"degree": section_text.strip()[:200], "institution": "", "year": "", "gpa": ""}]

    def _extract_experience(self, section_text: str) -> List[Dict[str, Any]]:
        """Extract work experience entries."""
        if not section_text.strip():
            return []

        experiences = []
        lines = section_text.strip().split("\n")
        current_exp: Dict[str, Any] = {}
        responsibilities: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_exp:
                    current_exp["responsibilities"] = responsibilities
                    experiences.append(current_exp)
                    current_exp = {}
                    responsibilities = []
                continue

            # Check for date ranges (indicator of a new experience entry)
            date_match = self.DATE_RANGE_PATTERN.search(stripped) or self.YEAR_RANGE_PATTERN.search(stripped)
            if date_match:
                if current_exp:
                    current_exp["responsibilities"] = responsibilities
                    experiences.append(current_exp)
                    responsibilities = []

                current_exp = {
                    "company": "",
                    "role": "",
                    "duration": date_match.group(0),
                    "start_date": date_match.group(1),
                    "end_date": date_match.group(2),
                    "responsibilities": [],
                }
                # The rest of the line might have company/role
                remaining = stripped[:date_match.start()].strip().rstrip("|-–,")
                if remaining:
                    parts = re.split(r"\s*[|–—at@]\s*", remaining, maxsplit=1)
                    current_exp["role"] = parts[0].strip()
                    if len(parts) > 1:
                        current_exp["company"] = parts[1].strip()

            elif stripped.startswith(("•", "-", "●", "▪", "*", "→")):
                # This is a responsibility bullet point
                clean = stripped.lstrip("•-●▪*→ ").strip()
                if clean:
                    responsibilities.append(clean)
            elif current_exp and not current_exp.get("role"):
                current_exp["role"] = stripped
            elif current_exp and not current_exp.get("company"):
                current_exp["company"] = stripped

        # Save last entry
        if current_exp:
            current_exp["responsibilities"] = responsibilities
            experiences.append(current_exp)

        return experiences

    def _extract_skills(self, section_text: str, full_text: str) -> List[str]:
        """Extract skills from skills section and full text."""
        skills = set()

        # Tracks canonical lowercase versions already added to avoid case duplicates
        seen_lower: set = set()

        def _add_skill(s: str):
            s = s.strip().strip("•-●▪*→ ").strip()
            if not s or not (1 < len(s) < 50):
                return
            # Strip proficiency/level suffixes: "Python: Advanced", "Python (3 yrs)", "Python - Expert"
            s = re.sub(
                r'\s*[(:]\s*(?:expert|advanced|senior|intermediate|proficient|familiar|beginner|basic|'
                r'learning|exposure|\d+\+?\s*(?:years?|yrs?|months?))[^,;|•]*$',
                '', s, flags=re.IGNORECASE
            ).strip()
            # Strip trailing parenthetical: "React.js (v18)", "Python (3.9)"
            s = re.sub(r'\s*\([^)]{1,30}\)\s*$', '', s).strip()
            if s and s.lower() not in seen_lower:
                seen_lower.add(s.lower())
                skills.add(s)

        # Extract from skills section
        if section_text.strip():
            for line in section_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Skip pure sub-header lines like "Programming Languages:" with nothing after
                if re.match(r"^(Technical|Soft|Programming|Languages?|Frameworks?|Tools?|Databases?)\s*:?\s*$",
                            line, re.IGNORECASE):
                    continue
                # If line has "Category: skill1, skill2" format, drop category prefix first
                colon_split = re.match(r"^[\w\s&/]+:\s*(.+)$", line)
                if colon_split:
                    line = colon_split.group(1)
                # Split by comma, pipe, bullet, semicolon
                for part in re.split(r"[,|;•●▪]\s*", line):
                    _add_skill(part)

        # Also scan full text for common technology keywords
        tech_keywords = [
            "Python", "JavaScript", "TypeScript", "Java", "C\\+\\+", "C#", "Go", "Rust", "Ruby", "PHP",
            "Swift", "Kotlin", "Scala", "R", "MATLAB",
            "React", "Angular", "Vue", "Next\\.js", "Node\\.js", "Express", "Django", "Flask", "FastAPI",
            "Spring", "Laravel", "Rails",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            "Git", "CI/CD", "Jenkins", "GitHub Actions",
            "REST", "GraphQL", "gRPC", "Microservices",
            "Linux", "Agile", "Scrum", "Jira",
            "HTML", "CSS", "SASS", "Tailwind",
            "SQL", "NoSQL", "Firebase", "Supabase",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        ]

        for kw in tech_keywords:
            if re.search(r"\b" + kw + r"\b", full_text, re.IGNORECASE):
                clean_kw = kw.replace("\\+", "+").replace("\\.", ".")
                if clean_kw.lower() not in seen_lower:
                    seen_lower.add(clean_kw.lower())
                    skills.add(clean_kw)

        return sorted(list(skills))

    def _extract_projects(self, section_text: str) -> List[Dict[str, str]]:
        """Extract projects from the projects section."""
        if not section_text.strip():
            return []

        projects = []
        lines = section_text.strip().split("\n")
        current_project: Dict[str, str] = {}
        description_lines: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_project:
                    current_project["description"] = " ".join(description_lines)
                    projects.append(current_project)
                    current_project = {}
                    description_lines = []
                continue

            # Lines that start with bullet points are descriptions
            if stripped.startswith(("•", "-", "●", "▪", "*", "→")):
                desc = stripped.lstrip("•-●▪*→ ").strip()
                if desc:
                    description_lines.append(desc)
            elif not current_project:
                current_project = {"name": stripped, "description": "", "technologies": ""}
            elif not description_lines:
                description_lines.append(stripped)

        if current_project:
            current_project["description"] = " ".join(description_lines)
            projects.append(current_project)

        return projects

    def _extract_certifications(self, section_text: str) -> List[str]:
        """Extract certifications from the certifications section."""
        if not section_text.strip():
            return []

        certs = []
        for line in section_text.strip().split("\n"):
            cleaned = line.strip().lstrip("•-●▪*→0123456789.) ").strip()
            if cleaned and len(cleaned) > 3:
                certs.append(cleaned)
        return certs

    def _empty_result(self, raw_text: str, elapsed: float) -> Dict[str, Any]:
        """Return an empty result when parsing fails."""
        return {
            "name": "", "email": "", "phone": "", "location": "",
            "linkedin": "", "summary": "",
            "education": [], "experience": [], "skills": [],
            "projects": [], "certifications": [],
            "raw_text": raw_text,
            "parsing_time_ms": int(elapsed * 1000),
        }
