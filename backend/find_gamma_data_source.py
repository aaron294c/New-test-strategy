#!/usr/bin/env python3
"""Script to find where the frontend Risk Distance data is coming from."""

import os
import json
from pathlib import Path

def search_for_spx_5400():
    """Search for files containing the SPX $5400 put wall value."""
    root = Path("/workspaces/New-test-strategy")
    
    patterns_to_search = [
        "5400",  # SPX ST put wall
        "st_put_wall",
        "stPutWall", 
        "ST Put",
        "level_data"
    ]
    
    results = []
    
    for pattern in patterns_to_search:
        print(f"\nSearching for: {pattern}")
        
        # Search in frontend
        for file in root.rglob("*"):
            if file.is_file() and file.suffix in ['.ts', '.tsx', '.js', '.jsx', '.json', '.py']:
                try:
                    content = file.read_text()
                    if pattern in content:
                        # Get line numbers
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if pattern in line:
                                results.append((str(file), i+1, line.strip()[:100]))
                except:
                    pass
    
    print("\n" + "="*80)
    print("FILES CONTAINING SPX PUT WALL DATA:")
    print("="*80)
    
    seen_files = set()
    for file, line, content in results:
        if file not in seen_files:
            seen_files.add(file)
            print(f"\n{file}")
        print(f"  Line {line}: {content}")
    
    return results

if __name__ == "__main__":
    search_for_spx_5400()
