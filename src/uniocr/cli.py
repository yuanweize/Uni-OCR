import argparse
from pathlib import Path
from . import UniOCR

def main():
    parser = argparse.ArgumentParser(description="UniOCR Command Line Interface")
    parser.add_argument("input", help="Input file path or URL to process.")
    parser.add_argument("--engine", default="auto", help="Engine to use: 'auto', 'paddle', 'apple'.")
    parser.add_argument("--output", "-o", help="Optional output markdown file path.")
    
    args = parser.parse_args()
    
    ocr = UniOCR(engine=args.engine)
    
    print(f"Processing '{args.input}' using engine: {ocr.engine.__class__.__name__}")
    
    doc = ocr.extract(args.input)
    
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(doc.markdown, encoding="utf-8")
        print(f"Extraction complete. Results written to: {out_path}")
    else:
        print("\n=== Extracted Markdown ===\n")
        print(doc.markdown)
        print("\n==========================\n")

if __name__ == "__main__":
    main()
