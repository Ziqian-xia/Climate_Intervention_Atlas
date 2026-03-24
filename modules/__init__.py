"""Pipeline modules for Auto-SLR."""

import sys
from pathlib import Path

# Add search-packages to Python path for Phase 2 integration
search_packages_dir = Path(__file__).parent.parent / "Search and full-text packages" / "search-packages"
if search_packages_dir.exists():
    sys.path.insert(0, str(search_packages_dir))
else:
    print(f"Warning: Search packages directory not found at {search_packages_dir}")
