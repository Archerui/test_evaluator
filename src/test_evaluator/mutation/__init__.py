"""Lightweight JavaScript/HTML mutation testing pipeline."""

from .analyzer import analyze_mutations
from .generator import generate_mutation_plan
from .runner import run_mutant

__all__ = ["analyze_mutations", "generate_mutation_plan", "run_mutant"]
