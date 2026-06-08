"""UniOCR Command Line Interface."""

import argparse
import json
import sys
from pathlib import Path

from . import UniOCR, list_available_engines


def cmd_extract(args: argparse.Namespace) -> None:
    """Handle the ``extract`` sub-command."""
    ocr = UniOCR(engine=args.engine)
    engine_cls = ocr.engine.__class__.__name__
    print(f"Processing '{args.input}' with engine: {engine_cls}", file=sys.stderr)

    doc = ocr.extract(args.input)

    if args.format == "json":
        output_text = json.dumps(doc.to_dict(), ensure_ascii=False, indent=2)
    elif args.format == "text":
        output_text = doc.text
    else:  # markdown (default)
        output_text = doc.markdown

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_text, encoding="utf-8")
        print(f"Done. Output written to: {out_path}", file=sys.stderr)
    else:
        print(output_text)


def cmd_engines(args: argparse.Namespace) -> None:
    """Handle the ``engines`` sub-command."""
    available = list_available_engines()
    if args.json:
        print(json.dumps({"available_engines": available}))
    elif available:
        print("Available engines:")
        for name in available:
            print(f"  • {name}")
    else:
        print(
            "No OCR engines detected.\n"
            "  pip install uniocr[paddle]  — PaddleOCR-VL\n"
            "  pip install uniocr[apple]   — Apple Vision (macOS)",
            file=sys.stderr,
        )


def cmd_serve(args: argparse.Namespace) -> None:
    """Handle the ``serve`` sub-command."""
    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn is required: pip install uniocr[api]",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"Starting UniOCR API on http://{args.host}:{args.port}\n"
        f"  Swagger docs → http://{args.host}:{args.port}/docs\n"
        f"  Workers: {args.workers}",
        file=sys.stderr,
    )
    uvicorn.run(
        "uniocr.api:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="uniocr",
        description="UniOCR — Unified multilingual OCR tool.",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- extract ---
    p_ext = sub.add_parser("extract", help="Extract text from a file or URL.")
    p_ext.add_argument("input", help="File path, URL, or data-URI.")
    p_ext.add_argument(
        "--engine", "-e", default="auto",
        help="Engine: auto | paddle | apple  (default: auto)",
    )
    p_ext.add_argument("--output", "-o", help="Write output to file.")
    p_ext.add_argument(
        "--format", "-f", default="markdown",
        choices=["markdown", "text", "json"],
        help="Output format (default: markdown).",
    )
    p_ext.set_defaults(func=cmd_extract)

    # --- engines ---
    p_eng = sub.add_parser("engines", help="List available OCR engines.")
    p_eng.add_argument("--json", action="store_true", help="Output as JSON.")
    p_eng.set_defaults(func=cmd_engines)

    # --- serve ---
    p_srv = sub.add_parser("serve", help="Start the REST API server.")
    p_srv.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    p_srv.add_argument("--port", "-p", type=int, default=8000, help="Port (default: 8000)")
    p_srv.add_argument("--workers", "-w", type=int, default=1, help="Worker count (default: 1)")
    p_srv.add_argument("--reload", action="store_true", help="Auto-reload (dev mode)")
    p_srv.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
