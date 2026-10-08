#!/usr/bin/env python3
"""Check the generated Hugo catalogue, links, and branding with the stdlib.

Usage: python3 tools/check_site.py public [--base-path /repository-name/]
"""
import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.links, self.products, self.images = [], [], [], []
        self.h1 = 0
        self.refresh = False
        self.canonical = ""
        self.text = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            self.refresh = True
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href", "")
        if "data-product" in attrs:
            self.products.append(attrs["id"])
        if tag == "img":
            self.images.append(attrs)
        for name in ("href", "src"):
            if name in attrs:
                self.links.append(attrs[name])

    def handle_data(self, text):
        self.text.append(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--base-path", default="/")
    args = parser.parse_args()
    root = args.directory.resolve()
    base_path = "/" + args.base_path.strip("/") + "/" if args.base_path.strip("/") else "/"
    pages = {path: Page(path.read_text()) for path in root.rglob("*.html")}
    assert pages, f"No generated HTML in {root}"
    home = pages[root / "index.html"]
    host = urlsplit(home.canonical).netloc
    failures = []
    checked_links = 0
    for path, page in pages.items():
        label = path.relative_to(root).as_posix()
        duplicates = [key for key, count in Counter(page.ids).items() if count > 1]
        if duplicates:
            failures.append(f"{label}: repeated IDs: {duplicates}")
        if not page.refresh and page.h1 != 1:
            failures.append(f"{label}: expected one H1, got {page.h1}")
        visible = " ".join(page.text)
        if re.search(r"PrimePlast|Your City|YOUR_FORM_ID|sales@primeplast", visible, re.I):
            failures.append(f"{label}: old placeholder content")
        if not page.refresh and "Kalpana Traders" not in visible:
            failures.append(f"{label}: missing business identity")
        for image in page.images:
            if "alt" not in image or not image.get("width") or not image.get("height"):
                failures.append(f"{label}: image lacks alt or dimensions: {image.get('src')}")
        source_url = f"https://{host}{base_path}{label}"
        for link in page.links:
            url = urlsplit(urljoin(source_url, link))
            if url.scheme not in ("http", "https") or url.netloc != host:
                continue
            location = unquote(url.path)
            if not location.startswith(base_path):
                failures.append(f"{label}: link escapes configured base path: {link}")
                continue
            target = root / location[len(base_path):]
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                failures.append(f"{label}: missing target: {link}")
                continue
            if target in pages and url.fragment and unquote(url.fragment) not in pages[target].ids:
                failures.append(f"{label}: missing anchor: {link}")
            checked_links += 1
    source = Path(__file__).resolve().parents[1] / "assets/sri-star-catalog/products.json"
    products = json.loads(source.read_text())
    expected = {p["id"] for p in products}
    actual = pages[root / "products/index.html"].products
    if len(actual) != 52 or set(actual) != expected:
        failures.append("Product index does not contain all 52 source entries exactly once")
    for series in {p["series_group"] for p in products}:
        expected_series = {p["id"] for p in products if p["series_group"] == series}
        page = pages[root / f"products/{series}/index.html"]
        if set(page.products) != expected_series or len(page.products) != len(expected_series):
            failures.append(f"{series}: incorrect product coverage")
    pdf = root / "downloads/sri-star-product-catalogue.pdf"
    original_pdf = source.parent.parent / "SRI_STAR_Product_Catalogue_Landscape (2).pdf"
    if not pdf.is_file() or pdf.read_bytes() != original_pdf.read_bytes():
        failures.append("Catalogue download missing or invalid")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(pages)} HTML pages, {checked_links} internal references, all 52 products across 5 series, and the PDF download.")


if __name__ == "__main__":
    main()
