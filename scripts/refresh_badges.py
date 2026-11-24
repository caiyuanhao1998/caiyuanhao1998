"""Refresh local copies of the profile's two dynamic badges."""

from argparse import ArgumentParser
from http.client import HTTPException
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SVG = "{http://www.w3.org/2000/svg}svg"
MAX_BADGE_BYTES = 64 * 1024

SCHOLAR_QUERY = urlencode({
    "url": "https://scholar.google.com/citations?user=3YozQwcAAAAJ&hl=en",
    "query": '//*[@id="gsc_rsb_st"]/tbody/tr[1]/td[2]/text()',
    "label": "Google Scholar",
    "logo": "googlescholar",
    "logoColor": "white",
    "color": "4285F4",
    "suffix": " citations",
})

BADGES = (
    (
        "google-scholar-citations.svg",
        "https://img.shields.io/badge/dynamic/xml?" + SCHOLAR_QUERY,
        r"Google Scholar: [0-9]+(?:,[0-9]{3})* citations",
    ),
    (
        "github-stars.svg",
        "https://img.shields.io/github/stars/caiyuanhao1998?affiliations=OWNER%2CCOLLABORATOR&",
        r"Stars: [0-9]+(?:[.,][0-9]+)*[kMGT]?",
    ),
)


def refresh(filename, url, label_pattern):
    path = ASSETS / filename
    try:
        request = Request(url, headers={
            "Accept": "image/svg+xml",
            "User-Agent": "profile-badge-refresh/1.0 (+https://github.com/caiyuanhao1998/caiyuanhao1998)",
        })
        with urlopen(request, timeout=20) as response:
            if response.headers.get_content_type() != "image/svg+xml":
                raise ValueError("response is not an SVG")
            content = response.read(MAX_BADGE_BYTES + 1)
        if len(content) > MAX_BADGE_BYTES:
            raise ValueError("SVG response is larger than expected")
        root = ElementTree.fromstring(content)
        label = root.get("aria-label", "")
        if root.tag != SVG or not re.fullmatch(label_pattern, label):
            raise ValueError("SVG does not contain a valid count")
    except (OSError, HTTPException, ValueError, ElementTree.ParseError) as error:
        print(f"::warning title=Badge fetch failed::{filename}: {error}")
        return path.is_file()

    if path.is_file() and path.read_bytes() == content:
        print(f"{filename}: {label} (unchanged)")
    else:
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(content)
        temporary.replace(path)
        print(f"{filename}: {label} (updated)")
    return True


def main(scholar_only=False):
    selected = BADGES[:1] if scholar_only else BADGES
    results = [refresh(*badge) for badge in selected]
    if not all(results):
        raise SystemExit("A badge could not be fetched and has no saved copy.")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--scholar-only", action="store_true", help="refresh only Google Scholar")
    main(scholar_only=parser.parse_args().scholar_only)
