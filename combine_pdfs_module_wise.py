import argparse
import re
from pathlib import Path

try:
    from pypdf import PdfMerger
except ImportError:
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        raise ImportError(
            "Please install either pypdf or PyPDF2. "
            "Use 'pip install pypdf' for the latest compatibility."
        )


def natural_sort_key(text: str):
    """Generate a natural sort key for strings containing numbers."""
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r"(\d+)", text)]


def find_module_folders(base_dir: Path):
    """Return module folders in alphabetical/natural order."""
    return sorted(
        [path for path in base_dir.iterdir() if path.is_dir()],
        key=lambda path: natural_sort_key(path.name),
    )


def find_pdf_files(module_dir: Path):
    """Return all PDF files inside a module folder in natural order."""
    pdf_files = sorted(
        module_dir.rglob("*.pdf"),
        key=lambda path: natural_sort_key(str(path.relative_to(module_dir))),
    )
    return pdf_files


def merge_pdfs(pdf_paths, destination: Path):
    """Merge PDF files into a single destination PDF."""
    if not pdf_paths:
        raise ValueError("No PDF files provided to merge.")

    merger = PdfMerger()
    try:
        for pdf_path in pdf_paths:
            merger.append(str(pdf_path))
        destination.parent.mkdir(parents=True, exist_ok=True)
        merger.write(str(destination))
    finally:
        merger.close()


def main():
    parser = argparse.ArgumentParser(
        description="Combine PDFs module-wise in order from a base directory."
    )
    parser.add_argument(
        "base_dir",
        nargs="?",
        default=".",
        help="Base directory containing module folders (default: current directory).",
    )
    parser.add_argument(
        "--output-dir",
        default="combined_pdfs",
        help="Output directory for generated combined PDFs.",
    )
    parser.add_argument(
        "--module",
        nargs="+",
        help="Only combine PDFs for a specific module folder name. Multi-word names are supported.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print file merge order without writing output files.",
    )
    args = parser.parse_args()

    if args.module:
        args.module = " ".join(args.module)

    base_dir = Path(args.base_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not base_dir.exists() or not base_dir.is_dir():
        raise SystemExit(f"Base directory does not exist or is not a folder: {base_dir}")

    modules = find_module_folders(base_dir)
    if args.module:
        modules = [m for m in modules if m.name.lower() == args.module.lower()]
        if not modules:
            raise SystemExit(f"No module folder named '{args.module}' found under {base_dir}")

    if not modules:
        raise SystemExit(f"No module folders found under {base_dir}")

    for module_dir in modules:
        pdf_files = find_pdf_files(module_dir)
        if not pdf_files:
            print(f"Skipping module '{module_dir.name}': no PDF files found.")
            continue

        destination = output_dir / f"{module_dir.name}_combined.pdf"
        print(f"Module: {module_dir.name}")
        for pdf_path in pdf_files:
            print(f"  - {pdf_path.relative_to(base_dir)}")

        if args.dry_run:
            continue

        merge_pdfs(pdf_files, destination)
        print(f"Combined PDF created: {destination}\n")


if __name__ == "__main__":
    main()
