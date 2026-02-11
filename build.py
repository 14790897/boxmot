"""
Export a clean copy of the project, excluding private/generated files.

Usage:
    python build.py
    python build.py --output D:/somewhere/boxmot_release

Output:
    dist/boxmot_release/   (or custom path via --output)
"""

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# --- Directories to INCLUDE ---
INCLUDE_DIRS = [
    "boxmot",
    "tracking",
    "new",
    "weights",
    "assets",
]

# --- Files to INCLUDE (relative to project root) ---
INCLUDE_FILES = [
    "app.py",
    "config.json",
    "pyproject.toml",
    "poetry.lock",
    "INSTALL.md",
    "README.md",
    "CITATION.cff",
    "MANIFEST.in",
    # Model weights
    "yolov8-particle-best.pt",
    "yolov8_best.pt",
    "best_model_new_eff1.pth",
    "osnet_x0_25_msmt17.pt",
]

# --- Patterns to SKIP inside included directories ---
IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", ".git", ".pytest_cache", ".mypy_cache",
    "*.mp4", "*.avi", "*.jpg", "*.png", "*.txt", "*.pkl",
    "*.onnx", "*.engine", "*.tflite", "*.torchscript",
    "*_openvino_model",
)

# --- Top-level items to EXCLUDE (not copied at all) ---
EXCLUDE = {
    # Git / IDE
    ".git", ".gitignore", ".vscode", ".venv",
    # Build artifacts
    "build", "dist", "__pycache__", "*.egg-info",
    # Run results / output
    "runs", "runs_x_me",
    "plots", "plots-eff1", "plots-eff1-new", "plots-eff1-new-both", "plots-eff1-new-distribution",
    "processed_video_gradio", "processed_video_gradio2",
    "output_frames", "yolov7_result", "yolov8_tracking",
    "mot_test", "test", "tests", "example", "examples",
    # Private / temp files
    "batch_directories.txt",
    "config_eff1.json", "config_new.json", "config_other.json", "config-750.json",
    "README_SELF.md",
    "gt_true.txt", "gt_predfict.txt", "true_filtered_gt.txt",
    "extract_output.txt", "filelist.txt",
    "botsort_output.json", "bytetrack_output.json",
    "deepocsort_output.json", "ocsort_output.json",
    # Scripts not part of the app
    "0_cleanup.py", "2_cal_draw.py", "check_revolution.py",
    "convert_mot.py", "copy_line.py", "enlarge_gt.py",
    "postprocess.py", "relative_error.py", "run.py",
    "build.py",
    # Unused model files
    "new_best_model.pth", "best_model (10).pth",
    "yolov8n.pt", "yolov8_nano.pt", "yolov8-x.pt", "yolov8-xx.pt",
    "yolov9-particle.pt", "yolov9-particle-100.pt",
    "yolov9-s-50-only-you.pt", "yolov9-200.pt",
    # Videos
    "03_40.mp4", "output_video.mp4", "x_video.mp4", "x_particle_video.avi",
    # Validation data
    "exp20(这个是mot验证需要的)/",
    # Misc
    "renovate.json", "DOCS_INDEX.md",
}


def main():
    parser = argparse.ArgumentParser(description="Export clean project copy")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "dist" / "boxmot_release"))
    args = parser.parse_args()

    output_dir = Path(args.output)

    print("=" * 60)
    print("Exporting clean project copy")
    print("=" * 60)
    print(f"Source : {PROJECT_ROOT}")
    print(f"Output : {output_dir}")
    print("=" * 60)

    # Clean previous export
    if output_dir.exists():
        print("Removing previous export...")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Copy directories
    print("\nCopying directories ...")
    for d in INCLUDE_DIRS:
        src = PROJECT_ROOT / d
        if src.exists():
            print(f"  {d}/")
            shutil.copytree(src, output_dir / d, symlinks=False, ignore=IGNORE, dirs_exist_ok=True)
        else:
            print(f"  SKIP {d}/ (not found)")

    # Copy files
    print("\nCopying files ...")
    for f in INCLUDE_FILES:
        src = PROJECT_ROOT / f
        if src.exists():
            size_mb = src.stat().st_size / 1024 / 1024
            print(f"  {f}  ({size_mb:.1f} MB)")
            shutil.copy2(src, output_dir / f)
        else:
            print(f"  SKIP {f} (not found)")

    # Summary
    total_size = sum(f.stat().st_size for f in output_dir.rglob("*") if f.is_file())
    file_count = sum(1 for f in output_dir.rglob("*") if f.is_file())
    print("\n" + "=" * 60)
    print("Export complete!")
    print(f"Output    : {output_dir}")
    print(f"Files     : {file_count}")
    print(f"Total size: {total_size / 1024 / 1024:.0f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
