"""
engines — Core deterministic teaching engines for Primer.

Contains:
- problems: problem generator and parallel problem creator
- assessor: deterministic answer assessment and misconception classification
- mastery: explainable confidence updates
- planner: graph-driven pedagogical decision engine
"""
from app.engines.problems import generate_problem, parallel_problem
from app.engines.assessor import assess_answer
from app.engines.mastery import update_confidence, is_weak, is_mastered
from app.engines.planner import plan_next_step, PlannerOutcome

__all__ = [
    "generate_problem",
    "parallel_problem",
    "assess_answer",
    "update_confidence",
    "is_weak",
    "is_mastered",
    "plan_next_step",
    "PlannerOutcome",
]
