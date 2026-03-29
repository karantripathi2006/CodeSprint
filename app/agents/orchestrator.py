"""
Multi-Agent Orchestrator
========================
Coordinates the three agents (Parser, Normalizer, Matcher) into a unified pipeline.
Supports single and batch processing with retry logic and partial failure handling.
"""

import logging
import time
import traceback
from typing import Dict, List, Any, Optional

from app.agents.resume_parser import ResumeParserAgent
from app.agents.skill_normalizer import SkillNormalizerAgent
from app.agents.semantic_matcher import SemanticMatcherAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the multi-agent pipeline:
        Resume → Parsing Agent → Normalization Agent → (optionally) Matching Agent
    
    Features:
    - Single and batch resume processing
    - Retry logic with exponential backoff
    - Partial failure handling (returns whatever succeeded)
    - Latency tracking per agent step
    - Structured logging and observability
    """

    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5  # seconds

    def __init__(self):
        """Initialize all agents."""
        self.parser = ResumeParserAgent()
        self.normalizer = SkillNormalizerAgent()
        self.matcher = SemanticMatcherAgent()
        logger.info("AgentOrchestrator initialized with all 3 agents")

    def process_resume(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Full pipeline: Parse → Normalize a single resume.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Dict with parsed_data, normalized_skills, metadata, and any errors
        """
        pipeline_start = time.time()
        result = {
            "status": "success",
            "filename": filename,
            "parsed_data": None,
            "normalized_skills": None,
            "errors": [],
            "metadata": {
                "total_time_ms": 0,
                "parse_time_ms": 0,
                "normalize_time_ms": 0,
            },
        }

        # ── Step 1: Parse Resume ─────────────────────────────────────────
        logger.info(f"[Pipeline] Step 1/2: Parsing {filename}")
        parsed = self._run_with_retry(
            lambda: self.parser.parse(file_content, filename),
            step_name="parse",
        )

        if parsed is None:
            result["status"] = "failed"
            result["errors"].append("Resume parsing failed after retries")
            result["metadata"]["total_time_ms"] = int((time.time() - pipeline_start) * 1000)
            return result

        result["parsed_data"] = parsed
        result["metadata"]["parse_time_ms"] = parsed.get("parsing_time_ms", 0)

        # ── Step 2: Normalize Skills ─────────────────────────────────────
        logger.info(f"[Pipeline] Step 2/2: Normalizing skills from {filename}")
        try:
            normalized = self._run_with_retry(
                lambda: self.normalizer.normalize(
                    parsed.get("skills", []),
                    parsed.get("experience", []),
                ),
                step_name="normalize",
            )

            if normalized:
                result["normalized_skills"] = normalized
                normalize_time = int((time.time() - pipeline_start) * 1000) - result["metadata"]["parse_time_ms"]
                result["metadata"]["normalize_time_ms"] = normalize_time
            else:
                result["errors"].append("Skill normalization failed, raw skills preserved")
                result["normalized_skills"] = {
                    "normalized_skills": parsed.get("skills", []),
                    "inferred_skills": [],
                    "unknown_skills": [],
                    "all_skills": parsed.get("skills", []),
                    "proficiency_map": {},
                    "total_count": len(parsed.get("skills", [])),
                }
                result["status"] = "partial"
        except Exception as e:
            result["errors"].append(f"Normalization error: {str(e)}")
            result["status"] = "partial"

        result["metadata"]["total_time_ms"] = int((time.time() - pipeline_start) * 1000)
        logger.info(f"[Pipeline] Complete for {filename} in {result['metadata']['total_time_ms']}ms "
                     f"(status={result['status']})")
        return result

    def match_candidate(self, candidate_profile: Dict[str, Any],
                        job_description: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a processed candidate profile against a job description.
        
        Args:
            candidate_profile: Output from process_resume or manually constructed
            job_description: Job requirements dict
            
        Returns:
            Match result with scores, gaps, explanation
        """
        logger.info(f"[Pipeline] Matching candidate against: {job_description.get('title', 'Unknown Job')}")
        start = time.time()

        match_result = self._run_with_retry(
            lambda: self.matcher.match(candidate_profile, job_description),
            step_name="match",
        )

        if match_result is None:
            return {
                "status": "failed",
                "overall_score": 0,
                "error": "Matching failed after retries",
                "match_time_ms": int((time.time() - start) * 1000),
            }

        match_result["status"] = "success"
        return match_result

    def process_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process multiple resumes in batch.
        
        Args:
            files: List of {"filename": str, "content": bytes}
            
        Returns:
            Dict with results list, summary statistics
        """
        logger.info(f"[Pipeline] Starting batch processing of {len(files)} resumes")
        batch_start = time.time()

        results = []
        success_count = 0
        failed_count = 0

        for i, file_data in enumerate(files):
            filename = file_data.get("filename", f"resume_{i}")
            content = file_data.get("content", b"")

            logger.info(f"[Batch] Processing {i+1}/{len(files)}: {filename}")
            try:
                result = self.process_resume(content, filename)
                results.append(result)
                if result["status"] in ("success", "partial"):
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"[Batch] Failed to process {filename}: {e}")
                results.append({
                    "status": "failed",
                    "filename": filename,
                    "errors": [str(e)],
                })
                failed_count += 1

        batch_time = int((time.time() - batch_start) * 1000)
        logger.info(f"[Batch] Complete: {success_count} succeeded, {failed_count} failed "
                     f"in {batch_time}ms")

        return {
            "total": len(files),
            "successful": success_count,
            "failed": failed_count,
            "total_time_ms": batch_time,
            "results": results,
        }

    def _run_with_retry(self, func, step_name: str, max_retries: int = None):
        """
        Execute a function with retry logic and exponential backoff.
        
        Args:
            func: Callable to execute
            step_name: Name of the step (for logging)
            max_retries: Override default max retries
            
        Returns:
            Function result or None if all retries fail
        """
        retries = max_retries or self.MAX_RETRIES

        for attempt in range(retries):
            try:
                result = func()
                if attempt > 0:
                    logger.info(f"[Retry] {step_name} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                logger.warning(f"[Retry] {step_name} attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    delay = self.BASE_RETRY_DELAY * (2 ** attempt)
                    logger.info(f"[Retry] Waiting {delay}s before next attempt...")
                    time.sleep(delay)
                else:
                    logger.error(f"[Retry] {step_name} failed after {retries} attempts: "
                                 f"{traceback.format_exc()}")
                    return None
