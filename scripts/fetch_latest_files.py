#!/usr/bin/env python3
"""
Fetch latest files from KB API and generate updated mock data.

This script fetches the latest 50 files from the KB API and outputs
Python code that can be used to update mock_data.py

Usage:
    # Set credentials first
    export KB_API_BASE_URL="https://your-kb-api.example.com/api/v1/"
    export KB_API_USERNAME="your_username"
    export KB_API_PASSWORD="your_password"

    # Run script
    python scripts/fetch_latest_files.py
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.kb_client import KBClient, KBClientError


def fetch_latest_files(count: int = 50) -> list:
    """Fetch the latest files from KB API."""
    client = KBClient()

    if not client.is_configured():
        print("Error: KB API not configured. Set environment variables:")
        print("  KB_API_BASE_URL")
        print("  KB_API_USERNAME")
        print("  KB_API_PASSWORD")
        return []

    try:
        print(f"Fetching latest {count} files from API...")
        result = client.list_files(page=1, page_size=count)
        files = result.get("results", [])
        print(f"Fetched {len(files)} files.")
        return files
    except KBClientError as e:
        print(f"API Error: {e.message}")
        return []


def generate_mock_entry(file: dict, index: int) -> dict:
    """Generate a mock data entry from a file record."""
    file_id = file.get("id", 10000 + index)
    title = file.get("file_name", file.get("title", "Unknown"))
    source = file.get("source", "")
    uploaded_at = file.get("uploaded_at", "")

    # Parse date
    date = ""
    if uploaded_at:
        try:
            dt = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
            date = dt.strftime("%Y-%m-%d")
        except:
            date = uploaded_at[:10] if len(uploaded_at) >= 10 else uploaded_at

    # Determine source type
    source_type = "AlphaEngine"  # Default
    if "twitter" in source.lower():
        source_type = "Twitter推文"
    elif "substack" in source.lower():
        source_type = "Substack"
    elif "expert" in source.lower():
        source_type = "专家访谈"
    elif "ace" in source.lower():
        source_type = "AceCampTech"

    # Extract author if available
    author = file.get("author", file.get("uploader", {}).get("username", ""))

    # Build content preview
    content = file.get("content", file.get("summary", ""))
    if len(content) > 500:
        content = content[:500] + "..."

    # Build snippet
    snippet = content[:100] + "..." if len(content) > 100 else content

    return {
        "file_id": file_id,
        "title": title,
        "source_type": source_type,
        "date": date,
        "author": author,
        "content": content,
        "snippet": snippet,
        "url": f"#preview-{file_id}"
    }


def categorize_files(files: list) -> dict:
    """Categorize files by potential query topics."""
    categories = {
        "nvidia": [],
        "kkr": [],
        "dell": [],
        "hbm": [],
        "ai_agent": [],
        "tsmc": [],
        "tesla": [],
        "anthropic": [],
        "smci": [],
        "fed_rate": [],
        "other": []
    }

    keywords_map = {
        "nvidia": ["nvidia", "nvda", "英伟达", "blackwell", "gpu", "ai芯片"],
        "kkr": ["kkr", "apollo", "blackstone", "另类资管", "pe", "私募"],
        "dell": ["dell", "戴尔", "服务器", "isg"],
        "hbm": ["hbm", "海力士", "sk hynix", "高带宽内存", "存储"],
        "ai_agent": ["ai agent", "palantir", "salesforce", "agentforce"],
        "tsmc": ["tsmc", "台积电", "cowos", "先进封装"],
        "tesla": ["tesla", "特斯拉", "musk", "马斯克", "fsd", "robotaxi"],
        "anthropic": ["anthropic", "claude", "ai大模型"],
        "smci": ["smci", "超微", "super micro"],
        "fed_rate": ["fed", "美联储", "降息", "利率", "fomc"]
    }

    for file in files:
        title = (file.get("file_name", "") + " " + file.get("title", "")).lower()
        content = file.get("content", "").lower()[:500]
        text = title + " " + content

        categorized = False
        for category, keywords in keywords_map.items():
            for kw in keywords:
                if kw in text:
                    categories[category].append(file)
                    categorized = True
                    break
            if categorized:
                break

        if not categorized:
            categories["other"].append(file)

    return categories


def print_mock_data_update(files: list):
    """Print Python code to update mock data."""

    print("\n" + "=" * 70)
    print("LATEST FILES FROM API")
    print("=" * 70)

    categories = categorize_files(files)

    for category, cat_files in categories.items():
        if not cat_files:
            continue

        print(f"\n# Category: {category} ({len(cat_files)} files)")
        print("-" * 50)

        for i, file in enumerate(cat_files[:5]):  # Show top 5 per category
            entry = generate_mock_entry(file, i)
            print(f"\n{i+1}. [{entry['source_type']}] {entry['date']}")
            print(f"   Title: {entry['title']}")
            print(f"   ID: {entry['file_id']}")

    # Generate actual Python code
    print("\n\n" + "=" * 70)
    print("GENERATED MOCK DATA CODE")
    print("=" * 70)
    print("\n# Copy this to mock/mock_data.py MOCK_SEARCH_RESULTS\n")

    for category, cat_files in categories.items():
        if not cat_files or category == "other":
            continue

        print(f'    "{category}": [')
        for i, file in enumerate(cat_files[:4]):  # Top 4 per category
            entry = generate_mock_entry(file, i)
            print(f'        {{')
            print(f'            "file_id": {entry["file_id"]},')
            print(f'            "title": "{entry["title"]}",')
            print(f'            "source_type": "{entry["source_type"]}",')
            print(f'            "date": "{entry["date"]}",')
            print(f'            "author": "{entry["author"]}",')
            print(f'            "content": """{entry["content"][:200]}...""",')
            print(f'            "snippet": "{entry["snippet"]}"')
            print(f'        }},')
        print(f'    ],')

    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total = sum(len(v) for v in categories.values())
    print(f"\nTotal files fetched: {total}")
    for cat, files in categories.items():
        if files:
            print(f"  {cat}: {len(files)} files")


def main():
    files = fetch_latest_files(50)
    if files:
        print_mock_data_update(files)
    else:
        print("\nNo files fetched. Check your API credentials.")
        print("\nTo configure:")
        print("  export KB_API_BASE_URL='https://your-kb-api.example.com/api/v1/'")
        print("  export KB_API_USERNAME='your_username'")
        print("  export KB_API_PASSWORD='your_password'")


if __name__ == "__main__":
    main()
