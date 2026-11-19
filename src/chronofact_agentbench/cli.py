"""Command-line interface for ChronoFact-AgentBench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import download_dataset, load_prepared_dataset, prepare_dataset, sha256_file
from .evaluate import run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chronofact",
        description="Tool-augmented temporal fact verification benchmark.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download the pinned TimeStress dataset.")
    download_parser.add_argument("--output", default="data/raw/timestress_train.parquet")
    download_parser.add_argument("--timeout", type=int, default=90)

    prepare_parser = subparsers.add_parser("prepare", help="Prepare labels and date-granularity metadata.")
    prepare_parser.add_argument("--input", default="data/raw/timestress_train.parquet")
    prepare_parser.add_argument("--output", default="data/processed/timestress_prepared.csv")

    run_parser = subparsers.add_parser("run", help="Run baseline and optional Ollama evaluations.")
    run_parser.add_argument("--input", default="data/processed/timestress_prepared.csv")
    run_parser.add_argument("--output", default="reports/run-01")
    run_parser.add_argument("--seed", type=int, default=17)
    run_parser.add_argument("--max-samples", type=int, default=None)
    run_parser.add_argument("--include-ollama", action="store_true")
    run_parser.add_argument("--ollama-model", default="qwen2.5:3b")
    run_parser.add_argument("--ollama-sample-limit", type=int, default=50)
    run_parser.add_argument("--ollama-base-url", default="http://localhost:11434")
    run_parser.add_argument("--agent-conditions", default="text,tool_dates,tool_code,tool_overlap",
                            help="Comma-separated: text, tool_dates, tool_code, tool_overlap.")
    run_parser.add_argument("--structured-output", action="store_true",
                            help="Constrain every model reply to a JSON schema with only the allowed action.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "download":
        result = download_dataset(args.output, timeout=args.timeout)
        print(json.dumps(result, indent=2))
    elif args.command == "prepare":
        result = prepare_dataset(args.input, args.output)
        print(json.dumps(result, indent=2))
    elif args.command == "run":
        frame = load_prepared_dataset(args.input)
        outputs = run_experiment(
            frame=frame,
            output_dir=args.output,
            seed=args.seed,
            max_samples=args.max_samples,
            include_ollama=args.include_ollama,
            ollama_model=args.ollama_model,
            ollama_sample_limit=args.ollama_sample_limit,
            ollama_base_url=args.ollama_base_url,
            conditions=tuple(c.strip() for c in args.agent_conditions.split(",") if c.strip()),
            structured_output=args.structured_output,
            input_sha256=sha256_file(Path(args.input)),
        )
        print(json.dumps(outputs, indent=2))
        print("\nMetrics:")
        print(Path(outputs["metrics"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
