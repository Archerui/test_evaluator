"""Command-line interface for the v0 evaluator."""

from __future__ import annotations

import argparse
from pathlib import Path

from .orchestrator import EvaluationConfig, evaluate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate E2EDev BDD/Selenium tests with a fixed multi-agent pipeline.")
    parser.add_argument("--mode", choices=("basic", "full"), default="basic", help="Evaluation mode.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("e2edev_sample.csv"),
        help="Input E2EDev CSV, JSONL, or requirment_with_tests.json file.",
    )
    parser.add_argument("--e2edev-root", type=Path, help="Cloned E2EDev repository or E2EDev_data directory.")
    parser.add_argument(
        "--projects",
        help="Comma-separated E2EDev project IDs, for example E2ESD_Bench_01,E2ESD_Bench_04.",
    )
    parser.add_argument(
        "--requirements",
        help="Comma-separated requirement IDs or full suite keys.",
    )
    parser.add_argument(
        "--tests",
        help="Comma-separated test IDs or full record keys.",
    )
    parser.add_argument("--max-projects", type=int, help="Limit the number of discovered projects.")
    parser.add_argument("--output", type=Path, default=Path("reports/latest"), help="Directory for JSON and Markdown reports.")
    parser.add_argument("--live", action="store_true", help="Enable OpenAI-backed semantic agents. Requires OPENAI_API_KEY in the environment.")
    parser.add_argument("--model", default="gpt-5-mini", help="OpenAI model for --live mode; configurable to match account access.")
    parser.add_argument(
        "--limit",
        "--max-tests",
        dest="limit",
        type=int,
        help="Analyse only the first N selected records; useful for controlled runs.",
    )
    parser.add_argument(
        "--max-tests-per-project",
        type=int,
        help="Limit selected tests independently within each project.",
    )
    parser.add_argument("--workers", type=int, default=2, help="Maximum concurrent baseline/coverage browser runs.")
    parser.add_argument("--max-output-tokens", type=int, default=4_000, help="Maximum output tokens per model call in --live mode.")
    parser.add_argument("--timeout", type=float, default=45.0, help="Per-request OpenAI timeout in seconds for --live mode.")
    parser.add_argument(
        "--no-llm-cache",
        action="store_true",
        help="Disable the per-call structured-output cache for live semantic agents.",
    )
    parser.add_argument(
        "--runner-timeout",
        type=float,
        default=60.0,
        help="Per-test Behave/Selenium timeout in seconds for full mode.",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run Chrome with a visible window in full mode (headless is the default).",
    )
    parser.add_argument(
        "--runtime-retries",
        type=int,
        default=1,
        help="Retries for full-mode env_error/timeout results (default: 1).",
    )
    parser.add_argument(
        "--stability-runs",
        type=int,
        default=1,
        help="Total unchanged baseline runs per test for flaky detection (default: 1).",
    )
    parser.add_argument(
        "--runtime-budget",
        type=float,
        help="Soft per-stage wall-clock budget in seconds for baseline/stability browser work.",
    )
    parser.add_argument(
        "--mutation-hypotheses",
        action="store_true",
        help="Add the optional static Mutation Hypothesis Agent in --live mode; this is not real mutation testing.",
    )
    parser.add_argument(
        "--mutation",
        action="store_true",
        help="Run real source mutation testing in full mode.",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Collect Chrome DevTools precise JavaScript coverage in full mode.",
    )
    parser.add_argument(
        "--coverage-method",
        choices=("auto", "cdp", "istanbul"),
        default="auto",
        help="Coverage backend when --coverage is enabled (default: auto).",
    )
    parser.add_argument(
        "--browser-stubs",
        help="Optional comma-separated browser stubs: network,speech,clipboard,notification.",
    )
    parser.add_argument(
        "--max-mutants",
        type=int,
        default=30,
        help="Global maximum number of generated mutants (default: 30).",
    )
    parser.add_argument(
        "--max-mutants-per-project",
        type=int,
        default=30,
        help="Per-project mutant limit before applying the global limit (default: 30).",
    )
    parser.add_argument(
        "--mutation-budget",
        type=float,
        help="Soft wall-clock budget in seconds for mutation execution.",
    )
    parser.add_argument(
        "--mutation-operators",
        help=(
            "Optional comma-separated operators: event_name,event_handler,dom_update,api_call,"
            "string_literal,comparison,boolean_literal,numeric_literal,arithmetic."
        ),
    )
    parser.add_argument("--resume", action="store_true", help="Reuse compatible checkpoints from the output directory.")
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Shared JSONL history file for cross-run trend deltas (default: <output>/history.jsonl).",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress per-stage progress lines.")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be a positive integer")
    if args.max_tests_per_project is not None and args.max_tests_per_project <= 0:
        raise SystemExit("--max-tests-per-project must be positive")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    if args.runner_timeout <= 0:
        raise SystemExit("--runner-timeout must be positive")
    if args.runtime_retries < 0:
        raise SystemExit("--runtime-retries cannot be negative")
    if args.stability_runs <= 0:
        raise SystemExit("--stability-runs must be positive")
    if args.runtime_budget is not None and args.runtime_budget <= 0:
        raise SystemExit("--runtime-budget must be positive")
    if args.max_mutants <= 0:
        raise SystemExit("--max-mutants must be positive")
    if args.max_mutants_per_project <= 0:
        raise SystemExit("--max-mutants-per-project must be positive")
    if args.mutation_budget is not None and args.mutation_budget <= 0:
        raise SystemExit("--mutation-budget must be positive")
    if args.max_projects is not None and args.max_projects <= 0:
        raise SystemExit("--max-projects must be positive")
    if args.workers <= 0:
        raise SystemExit("--workers must be positive")
    if args.mode == "full" and args.e2edev_root is None:
        raise SystemExit("--mode full requires --e2edev-root")
    if (args.mutation or args.coverage) and args.mode != "full":
        raise SystemExit("--mutation and --coverage require --mode full")
    if args.live:
        print("Live mode enabled...")
        if args.limit is None:
            print("Full input selected: this can make roughly 3 calls per test plus 2 calls per requirement suite.")
    else:
        print("Offline semantic mode: OpenAI agents are disabled; deterministic and local full-mode stages will still run.")

    projects = tuple(item.strip() for item in (args.projects or "").split(",") if item.strip())
    requirements = tuple(item.strip() for item in (args.requirements or "").split(",") if item.strip())
    tests = tuple(item.strip() for item in (args.tests or "").split(",") if item.strip())
    mutation_operators = tuple(
        item.strip() for item in (args.mutation_operators or "").split(",") if item.strip()
    )
    browser_stubs = tuple(
        item.strip() for item in (args.browser_stubs or "").split(",") if item.strip()
    )
    unknown_stubs = set(browser_stubs).difference({"network", "speech", "clipboard", "notification"})
    if unknown_stubs:
        raise SystemExit(f"Unknown --browser-stubs values: {', '.join(sorted(unknown_stubs))}")
    run = evaluate(
        EvaluationConfig(
            input_path=args.input,
            output_dir=args.output,
            mode=args.mode,
            e2edev_root=args.e2edev_root,
            projects=projects,
            requirements=requirements,
            tests=tests,
            max_projects=args.max_projects,
            workers=args.workers,
            live=args.live,
            model=args.model,
            limit=args.limit,
            max_tests_per_project=args.max_tests_per_project,
            max_output_tokens=args.max_output_tokens,
            timeout_seconds=args.timeout,
            llm_cache=not args.no_llm_cache,
            runner_timeout_seconds=args.runner_timeout,
            headless=not args.no_headless,
            runtime_retries=args.runtime_retries,
            stability_runs=args.stability_runs,
            runtime_budget_seconds=args.runtime_budget,
            mutation=args.mutation,
            max_mutants=args.max_mutants,
            max_mutants_per_project=args.max_mutants_per_project,
            mutation_budget_seconds=args.mutation_budget,
            mutation_operators=mutation_operators,
            coverage=args.coverage,
            coverage_method=(
                "cdp_precise_coverage" if args.coverage_method == "cdp" else args.coverage_method
            ),
            browser_stubs=browser_stubs,
            mutation_hypotheses=args.mutation_hypotheses,
            resume=args.resume,
            progress=not args.quiet,
            history_path=args.history_file,
        )
    )
    print(f"Completed {len(run.tests)} tests across {len(run.requirements)} requirement suites.")
    print(f"Run ID: {run.run_id}")
    print(f"Reports written to {args.output / 'summary.md'} and {args.output / 'evaluation.json'}.")


if __name__ == "__main__":
    main()
