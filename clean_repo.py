"""
Script to clean Python cache files and temporary files
Run this script to clean __pycache__ directories and .pyc files
"""
import os
import shutil
from pathlib import Path


def clean_pycache(root_dir: str = "."):
    """Remove all __pycache__ directories and .pyc files"""
    root = Path(root_dir)
    removed_dirs = []
    removed_files = []
    
    # Find and remove __pycache__ directories
    for pycache_dir in root.rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                removed_dirs.append(str(pycache_dir))
                print(f"✓ Removed: {pycache_dir}")
            except Exception as e:
                print(f"✗ Error removing {pycache_dir}: {e}")
    
    # Find and remove .pyc files
    for pyc_file in root.rglob("*.pyc"):
        if pyc_file.is_file():
            try:
                pyc_file.unlink()
                removed_files.append(str(pyc_file))
                print(f"✓ Removed: {pyc_file}")
            except Exception as e:
                print(f"✗ Error removing {pyc_file}: {e}")
    
    # Find and remove .pyo files
    for pyo_file in root.rglob("*.pyo"):
        if pyo_file.is_file():
            try:
                pyo_file.unlink()
                removed_files.append(str(pyo_file))
                print(f"✓ Removed: {pyo_file}")
            except Exception as e:
                print(f"✗ Error removing {pyo_file}: {e}")
    
    print(f"\n✓ Cleanup complete!")
    print(f"  - Removed {len(removed_dirs)} __pycache__ directories")
    print(f"  - Removed {len(removed_files)} .pyc/.pyo files")


if __name__ == "__main__":
    print("Cleaning Python cache files...")
    print("=" * 50)
    clean_pycache()

