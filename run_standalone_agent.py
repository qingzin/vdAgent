"""Launch the standalone vdAgent window."""

import argparse
import sys

from agent.standalone_window import run_standalone_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch standalone vdAgent UI.")
    parser.add_argument(
        "--llm-url",
        default="http://127.0.0.1:8080",
        help="OpenAI-compatible llama-server base URL.",
    )
    args = parser.parse_args()
    return run_standalone_agent(llm_url=args.llm_url)


if __name__ == "__main__":
    sys.exit(main())
