"""Command-line interface for the v0 evaluator."""

from __future__ import annotations

import argparse
from pathlib import Path

from .orchestrator import EvaluationConfig, evaluate_csv


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate E2EDev BDD/Selenium tests with a fixed multi-agent pipeline.")
    parser.add_argument("--input", type=Path, default=Path("e2edev_sample.csv"), help="Input E2EDev CSV file.")
    parser.add_argument("--output", type=Path, default=Path("reports/latest"), help="Directory for JSON and Markdown reports.")
    parser.add_argument("--live", action="store_true", help="Enable OpenAI-backed semantic agents. Requires OPENAI_API_KEY in the environment.")
    parser.add_argument("--model", default="gpt-5-mini", help="OpenAI model for --live mode; configurable to match account access.")
    parser.add_argument("--limit", type=int, help="Analyse only the first N CSV records; useful for controlled live runs.")
    parser.add_argument("--max-output-tokens", type=int, default=4_000, help="Maximum output tokens per model call in --live mode.")
    parser.add_argument("--timeout", type=float, default=45.0, help="Per-request OpenAI timeout in seconds for --live mode.")
    parser.add_argument(
        "--mutation-hypotheses",
        action="store_true",
        help="Add the optional static Mutation Hypothesis Agent in --live mode; this is not real mutation testing.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be a positive integer")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    if args.live:
        print("Live mode enabled...")
        if args.limit is None:
            print("Full input selected: this can make roughly 3 calls per test plus 2 calls per requirement suite.")
    else:
        print("Offline mode: only deterministic static checks will run.")

    run = evaluate_csv(
        EvaluationConfig(
            input_path=args.input,
            output_dir=args.output,
            live=args.live,
            model=args.model,
            limit=args.limit,
            max_output_tokens=args.max_output_tokens,
            timeout_seconds=args.timeout,
            mutation_hypotheses=args.mutation_hypotheses,
        )
    )
    print(f"Completed {len(run.tests)} tests across {len(run.requirements)} requirement suites.")
    print(f"Reports written to {args.output / 'summary.md'} and {args.output / 'evaluation.json'}.")


if __name__ == "__main__":
    main()
