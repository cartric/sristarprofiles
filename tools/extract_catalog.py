#!/usr/bin/env python3
"""Extract the supplied SRI STAR catalog without changing the website or PDF.

Requires PyMuPDF and Pillow. Run from any directory with Python 3.10+.
The geometry is discovered from this catalog's card borders and image placements;
marketing crops are curated pixel coordinates in the original embedded artwork.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pymupdf as pdf
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/SRI_STAR_Product_Catalogue_Landscape (2).pdf"
OUT = ROOT / "assets/sri-star-catalog"
SCALE = 3  # 216 dpi for page-faithful crops; does not add native image detail.
SERIES = {
    3: "60-casement", 4: "62-sliding", 5: "80-sliding", 6: "80-sliding",
    7: "88-sliding", 8: "88-sliding", 9: "60-casement", 10: "60-casement",
    11: "65-casement", 12: "65-casement",
}
PAGE_COUNTS = {3: 6, 4: 6, 5: 6, 6: 5, 7: 6, 8: 2, 9: 6, 10: 3, 11: 6, 12: 6}
PAGE_TITLES = {1: "Cover", 2: "Technical test report", 13: "Manufacturer details", 14: "Distributor and contact"}
FIELDS = ["S.No.", "Product Description", "Product Code", "Series", "Thickness",
          "Weight (Kgs/Mtr)", "Length/Mtr", "Length Weight", "Pcs/Bag"]


def write_json(name, data):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def coords(rect):
    return [round(v, 3) for v in rect]


def render(page, rect, name, scale=SCALE):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=pdf.Matrix(scale, scale), clip=rect, alpha=False)
    pix.save(path)
    return {"path": name, "width": pix.width, "height": pix.height,
            "source_page": page.number + 1, "bbox_pdf_points": coords(rect),
            "method": "page render", "dpi": int(scale * 72)}


def card_rectangles(page):
    """Pair horizontal border segments, rather than assume identical page grids."""
    lines = set()
    for drawing in page.get_drawings():
        for item in drawing["items"]:
            if item[0] == "re":
                r = item[1]
                if r.width > 180 and r.height < 2:
                    lines.add(tuple(round(v, 2) for v in r))
    columns = defaultdict(list)
    for x0, y0, x1, y1 in sorted(lines):
        columns[(x0, x1)].append((y0, y1))
    cards = []
    for (x0, x1), ys in columns.items():
        assert len(ys) % 2 == 0
        for top, bottom in zip(ys[::2], ys[1::2]):
            cards.append(pdf.Rect(x0 - 1.32, top[0], x1, bottom[1]))
    return sorted(cards, key=lambda r: (r.y0, r.x0))


def parse_card(page, rect):
    tokens = [x.strip() for x in page.get_text("text", clip=rect).splitlines() if x.strip()]
    assert len(tokens) == len(FIELDS) * 3, (page.number + 1, tokens)
    values = {}
    for offset, label in enumerate(FIELDS):
        actual, colon, value = tokens[offset * 3:offset * 3 + 3]
        assert actual == label and colon == ":", (actual, label)
        values[label] = value
    return values


def number(value):
    return None if value == "-" else float(value.replace(" mm", ""))


def contact_sheet(items, name, columns=4, cell=(300, 285)):
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell[0], rows * cell[1]), "#edf2ee")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=13)
    for i, (path, label) in enumerate(items):
        left, top = (i % columns) * cell[0], (i // columns) * cell[1]
        draw.rectangle((left + 5, top + 5, left + cell[0] - 5, top + cell[1] - 5), fill="white")
        with Image.open(OUT / path) as im:
            thumb = im.convert("RGB")
            thumb.thumbnail((cell[0] - 24, cell[1] - 53))
            sheet.paste(thumb, (left + (cell[0] - thumb.width) // 2, top + 10))
        draw.text((left + 12, top + cell[1] - 35), label, fill="#173b28", font=font)
    destination = OUT / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pdf.open(SOURCE)
    assert len(doc) == 14, "This extractor is curated for the supplied 14-page catalog."
    manifest = {"source_pdf": SOURCE.relative_to(ROOT).as_posix(),
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "page_count": len(doc), "page_numbering": "1-based physical PDF pages",
                "pages": [], "embedded_images": [], "assets": [], "products": []}

    # Preserve native embedded streams, deduplicated by content. Tiny scan-line
    # fragments are archived separately; the useful assembled diagram is rendered.
    seen_xrefs, seen_hashes, native_by_page = {}, {}, {}
    (OUT / "originals").mkdir(exist_ok=True)
    with ZipFile(OUT / "originals/page-10-image-fragments.zip", "w", ZIP_DEFLATED) as fragments:
        for page in doc:
            for entry in page.get_images():
                xref = entry[0]
                if xref in seen_xrefs:
                    seen_xrefs[xref]["source_pages"].append(page.number + 1)
                    continue
                embedded = doc.extract_image(xref)
                raw = embedded["image"]
                digest = hashlib.sha256(raw).hexdigest()
                is_fragment = embedded["height"] <= 1
                if digest in seen_hashes:
                    name = seen_hashes[digest]
                elif is_fragment:
                    member = f"xref-{xref:04d}.{embedded['ext']}"
                    fragments.writestr(member, raw)
                    name = f"originals/page-10-image-fragments.zip!{member}"
                    seen_hashes[digest] = name
                else:
                    name = f"originals/xref-{xref:04d}.{embedded['ext']}"
                    (OUT / name).write_bytes(raw)
                    seen_hashes[digest] = name
                record = {"xref": xref, "path": name, "width": embedded["width"],
                          "height": embedded["height"], "source_pages": [page.number + 1],
                          "sha256": digest, "fragment": is_fragment}
                seen_xrefs[xref] = record
                manifest["embedded_images"].append(record)
                if page.number + 1 in PAGE_TITLES:
                    native_by_page[page.number + 1] = (name, Image.open(io.BytesIO(raw)).convert("RGB"))

    # Full pages are reference material, not intended as whole website pages.
    for page in doc:
        n = page.number + 1
        name = f"pages/page-{n:02d}.png"
        title = PAGE_TITLES.get(n, SERIES.get(n, "").replace("-", " ").title() + " Series")
        record = render(page, page.rect, name, scale=2)
        record["title"] = title
        manifest["pages"].append(record)

    for n, series in SERIES.items():
        page = doc[n - 1]
        cards = card_rectangles(page)
        assert len(cards) == PAGE_COUNTS[n], (n, len(cards))
        images = page.get_image_info(xrefs=True)
        for rect in cards:
            raw = parse_card(page, rect)
            serial = int(raw["S.No."])
            code = raw["Product Code"]
            title = raw["Product Description"]
            product_id = f"p{n:02d}-{serial:02d}-{slug(code)}"
            basename = f"products/{series}/{product_id}"
            card_asset = render(page, rect + (-0.7, -0.7, 0.7, 0.7), basename + "-card.png")

            # Union every placed image in the card, including overlapping images
            # and scan-line strips. Native extraction alone would lose the composite.
            placements = [im for im in images if rect.contains(pdf.Rect(im["bbox"]))]
            assert placements, product_id
            bounds = pdf.Rect(placements[0]["bbox"])
            for im in placements[1:]:
                bounds |= pdf.Rect(im["bbox"])
            bounds = (bounds + (-2, -2, 2, 2)) & (rect + (1.7, 1.7, -1.7, -1.7))
            drawing_asset = render(page, bounds, basename + "-diagram.png")
            normalized_title = title.replace("Mullian", "Mullion").replace("Casemnt", "Casement").replace("Cashment", "Casement")
            product = {"id": product_id, "series_group": series, "source_page": n,
                       "source_serial": serial, "product_code": code,
                       "name": normalized_title, "name_as_printed": title,
                       "series_as_printed": raw["Series"],
                       "thickness_mm": number(raw["Thickness"]),
                       "weight_kg_per_m": number(raw["Weight (Kgs/Mtr)"]),
                       "length_m": number(raw["Length/Mtr"]),
                       "length_weight_as_printed": raw["Length Weight"],
                       "pieces_per_bag": int(raw["Pcs/Bag"]),
                       "source_fields": raw, "assets": {"diagram": drawing_asset, "card": card_asset},
                       "embedded_xrefs": sorted(set(im["xref"] for im in placements)),
                       "review_notes": []}
            if normalized_title != title:
                product["review_notes"].append("Display spelling normalized; original spelling retained in name_as_printed.")
            if raw["Thickness"] not in ("-",) and "mm" not in raw["Thickness"]:
                product["review_notes"].append("Thickness unit is omitted in source; mm inferred from other rows.")
            if len(placements) > 1:
                product["review_notes"].append(f"Diagram assembled from {len(placements)} placed images; prefer rendered diagram over raw originals.")
            manifest["products"].append(product)

    by_code = defaultdict(list)
    for product in manifest["products"]:
        by_code[product["product_code"]].append(product)
    duplicate_codes = []
    for code, products in by_code.items():
        if len(products) > 1:
            fields = [field for field in FIELDS[1:] if len({p["source_fields"][field] for p in products}) > 1]
            duplicate_codes.append({"product_code": code, "entry_ids": [p["id"] for p in products],
                                    "differing_source_fields": fields})
            for product in products:
                product["review_notes"].append("Code appears in multiple catalog entries; retain page/serial ID until supplier review.")

    # Native artwork crops preserve the original 1672 x 941 aspect ratio. The PDF
    # stretches these marketing images, so page crops would distort their artwork.
    def crop(n, name, box, title, note=""):
        source_name, im = native_by_page[n]
        assert 0 <= box[0] < box[2] <= im.width and 0 <= box[1] < box[3] <= im.height
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        im.crop(box).save(path)
        manifest["assets"].append({"path": name, "title": title, "source_page": n,
                                   "source_image": source_name, "bbox_native_pixels": list(box),
                                   "width": box[2] - box[0], "height": box[3] - box[1],
                                   "method": "native raster crop", "note": note})

    for n, name in [(1, "cover"), (2, "technical-test-report"), (13, "manufacturer-details"), (14, "distributor-contact")]:
        crop(n, f"marketing/{name}.png", (0, 0, 1672, 941), PAGE_TITLES[n])
    crop(1, "brand/sri-star-profiles-horizontal.png", (28, 23, 844, 214), "SRI STAR Profiles horizontal logo", "Original light background retained; raster artwork, not a vector logo.")
    crop(2, "brand/sri-star-profiles-stacked.png", (70, 3, 447, 195), "SRI STAR Profiles stacked logo", "White background retained.")
    crop(2, "brand/sri-star-symbol.png", (75, 3, 244, 113), "SRI STAR symbol", "Raster crop with original background.")
    for xref, name, title in [(35, "shengda-profiles", "Shengda Profiles logo"), (36, "sri-star-header", "SRI STAR technical-page logo")]:
        raw_path = seen_xrefs[xref]["path"]
        with Image.open(OUT / raw_path) as im:
            im.save(OUT / f"brand/{name}.png")
            manifest["assets"].append({"path": f"brand/{name}.png", "title": title, "source_page": 3,
                                       "source_image": raw_path, "width": im.width, "height": im.height,
                                       "method": "native embedded image", "note": "Native proportions differ from stretched PDF header placement."})
    crop(14, "brand/kalpana-traders-nameplate.png", (42, 289, 634, 378), "Kalpana Traders nameplate", "Original dark background retained.")
    crop(13, "company/hebei-shengda-factory.png", (40, 244, 805, 711), "Hebei Shengda factory image", "Rectangular crop inside the original decorative frame.")
    crop(14, "company/kalpana-traders-warehouse-artwork.png", (689, 0, 1672, 550), "Kalpana Traders warehouse artwork", "Promotional composite; not verified as a photograph of the actual premises.")
    crop(14, "company/kalpana-traders-contact-panel.png", (40, 390, 599, 754), "Kalpana Traders contact details")
    crop(14, "marketing/profile-range-artwork.png", (625, 548, 1672, 865), "Profile range artwork", "Composite crop retains background; not an isolated product cutout.")
    crop(1, "marketing/sliding-window-artwork.png", (1301, 106, 1642, 403), "Sliding window artwork", "Illustrative marketing artwork; no model or product code is supplied.")
    crop(2, "technical/complete-test-parameters.png", (17, 198, 607, 781), "Complete test parameters")
    crop(2, "technical/performance-parameters.png", (610, 202, 1653, 775), "Important performance parameters")
    performance = ["visible-wall-thickness", "non-visible-wall-thickness", "falling-hammer-impact",
                   "density", "vicat-softening-temperature", "tensile-yield-stress", "tensile-fracture-strain",
                   "bending-elastic-modulus", "welded-joint-bending-mean", "welded-joint-bending-minimum",
                   "short-term-welding-coefficient"]
    columns = [(612, 951), (956, 1300), (1304, 1648)]
    rows = [(256, 377), (382, 501), (505, 633), (637, 774)]
    for i, title in enumerate(performance):
        x0, x1 = columns[i % 3]
        y0, y1 = rows[i // 3]
        crop(2, f"technical/{i+1:02d}-{title}.png", (x0, y0, x1, y1), title.replace("-", " ").title())
    benefits = ["durable", "weather-resistant", "eco-friendly", "sound-insulation", "thermal-efficiency", "reliable-performance"]
    for title, x in zip(benefits, [83, 247, 416, 584, 755, 940]):
        crop(2, f"benefits/{title}-icon.png", (x - 39, 801, x + 39, 875), title.replace("-", " ").title() + " icon")
        crop(2, f"benefits/{title}-badge.png", (max(0, x - 77), 797, x + 77, 904), title.replace("-", " ").title() + " badge")
    for title, box in [
        ("production-capacity", (836, 219, 1204, 448)),
        ("industry-memberships", (1213, 219, 1649, 449)),
        ("management-system-certifications", (836, 458, 1204, 665)),
        ("products-and-applications", (1213, 458, 1649, 665)),
        ("testing-and-recognition", (836, 675, 1649, 814)),
    ]:
        crop(13, f"company/{title}.png", box, title.replace("-", " ").title())

    counts = Counter(p["series_group"] for p in manifest["products"])
    manifest["summary"] = {"product_entries": len(manifest["products"]), "distinct_product_codes": len(by_code),
                           "series": dict(sorted(counts.items())), "curated_supporting_assets": len(manifest["assets"]),
                           "embedded_image_objects": len(seen_xrefs), "unique_embedded_images": len(seen_hashes),
                           "fragment_image_objects": sum(r["fragment"] for r in seen_xrefs.values())}
    manifest["duplicate_product_codes"] = duplicate_codes
    write_json("manifest.json", manifest)
    write_json("products.json", manifest["products"])

    text_pages = []
    for page in doc:
        text_pages.append(f"=== PAGE {page.number + 1:02d} ===\n" +
                          (page.get_text() or "[Image-only page. See content.json for reviewed transcription and original artwork.]\n"))
    (OUT / "extracted-text.txt").write_text("\n".join(text_pages))
    for series in counts:
        selected = [p for p in manifest["products"] if p["series_group"] == series]
        contact_sheet([(p["assets"]["diagram"]["path"], f"{p['product_code']} | p{p['source_page']:02d} #{p['source_serial']}") for p in selected],
                      f"contact-sheets/{series}.jpg", columns=3)
    contact_sheet([(p["path"], f"Page {i+1:02d}: {p['title']}") for i, p in enumerate(manifest["pages"])],
                  "contact-sheets/all-pages.jpg", columns=3, cell=(420, 365))
    contact_sheet([(a["path"], Path(a["path"]).stem[:36]) for a in manifest["assets"]],
                  "contact-sheets/supporting-assets.jpg", columns=4)
    create_gallery(manifest)
    # Verify every raster decodes and every reference resolves before reporting success.
    image_count = 0
    for file in OUT.rglob("*"):
        if file.suffix.lower() in (".png", ".jpg", ".jpeg"):
            with Image.open(file) as im:
                im.verify()
            image_count += 1
    assert len(manifest["products"]) == 52
    assert len({p["id"] for p in manifest["products"]}) == 52
    for p in manifest["products"]:
        for a in p["assets"].values():
            assert (OUT / a["path"]).is_file()
    print(json.dumps({**manifest["summary"], "verified_image_files": image_count}, indent=2))


def create_gallery(manifest):
    """Offline review index only; no runtime, remote assets, or site integration."""
    esc = html.escape
    parts = ["""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SRI STAR catalog asset library</title><style>
*{box-sizing:border-box}body{font:16px/1.5 system-ui,sans-serif;color:#193b2c;background:#f1f4f0;margin:0;padding:32px;max-width:1500px;margin:auto}
h1{font-size:36px;line-height:1.15}h2{margin-top:42px}a{color:#126443}nav{display:flex;gap:14px;flex-wrap:wrap;margin:24px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px}.card{background:white;border:1px solid #d9e2d9;border-radius:10px;padding:16px;overflow:hidden}
.card img{width:100%;height:235px;object-fit:contain}.card h3{font-size:17px;margin:10px 0}.meta{font-size:14px;color:#546458}.links{display:flex;gap:16px;margin-top:12px}
.note{padding:16px;background:#fff7e5;border-left:4px solid #e9a22b}details{font-size:13px;margin-top:12px}summary{cursor:pointer}table{width:100%;border-collapse:collapse}td{padding:3px;vertical-align:top;border-bottom:1px solid #edf0ed}input{width:100%;padding:13px;border:1px solid #a8bcae;border-radius:6px;font:inherit}
[hidden]{display:none!important}@media(max-width:600px){body{padding:16px}h1{font-size:28px}}</style>
<h1>SRI STAR Profiles<br>Catalog asset library</h1>
<p>Kalpana Traders · 14 source pages · 52 catalog entries · 5 profile series</p>
<p class="note">Review library extracted from the supplied PDF. Duplicate codes and source inconsistencies are preserved. Diagram crops reproduce the PDF; enlarging a crop does not increase its original detail. Marketing artwork retains its original backgrounds.</p>
<nav><a href="README.md">Analysis and extraction notes</a><a href="products.json">Product data</a><a href="content.json">Company and technical content</a><a href="manifest.json">Source manifest</a><a href="#supporting">Supporting artwork</a><a href="#pages">All pages</a></nav>
<label for="search">Find a product by name, series, or code</label><input id="search" type="search" placeholder="For example: SPHD60-11 or glass beading">
"""]
    for series in sorted(manifest["summary"]["series"]):
        parts.append(f'<section class="product-section"><h2>{esc(series.replace("-", " ").title())} Series</h2><div class="grid">')
        for p in manifest["products"]:
            if p["series_group"] != series:
                continue
            diagram, card = p["assets"]["diagram"]["path"], p["assets"]["card"]["path"]
            search = esc(f'{series} {p["name"]} {p["product_code"]}'.lower(), quote=True)
            parts.append(f'<article class="card product" data-search="{search}"><a href="{diagram}"><img loading="lazy" src="{diagram}" alt="{esc(p["name"])} dimensional profile drawing"></a><h3>{esc(p["name"])}</h3><strong>{esc(p["product_code"])}</strong><div class="meta">Page {p["source_page"]}, entry {p["source_serial"]} · {p["source_fields"]["Thickness"]} · {p["weight_kg_per_m"]} kg/m</div><div class="links"><a href="{diagram}">Drawing</a><a href="{card}">Full card</a></div><details><summary>Specifications and review notes</summary><table>')
            parts.extend(f'<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>' for k, v in p["source_fields"].items())
            parts.append('</table>' + ''.join(f'<p>{esc(note)}</p>' for note in p['review_notes']) + '</details></article>')
        parts.append('</div></section>')
    parts.append('<h2 id="supporting">Brand, company, and technical artwork</h2><div class="grid">')
    for asset in manifest["assets"]:
        parts.append(f'<article class="card"><a href="{asset["path"]}"><img loading="lazy" src="{asset["path"]}" alt="{esc(asset["title"])}"></a><h3>{esc(asset["title"])}</h3><div class="meta">Page {asset["source_page"]} · {asset["width"]} × {asset["height"]} pixels</div><p class="meta">{esc(asset.get("note", ""))}</p></article>')
    parts.append('</div><h2 id="pages">Full catalog pages</h2><div class="grid">')
    for page in manifest["pages"]:
        parts.append(f'<article class="card"><a href="{page["path"]}"><img loading="lazy" src="{page["path"]}" alt="{esc(page["title"])}"></a><h3>Page {page["source_page"]}: {esc(page["title"])}</h3></article>')
    parts.append('''</div><script>document.getElementById('search').addEventListener('input',event=>{const term=event.target.value.toLowerCase().trim();document.querySelectorAll('.product').forEach(card=>{card.hidden=!card.dataset.search.includes(term)});document.querySelectorAll('.product-section').forEach(section=>{section.hidden=!section.querySelector('.product:not([hidden])')})});</script></html>''')
    (OUT / "index.html").write_text("\n".join(parts))


if __name__ == "__main__":
    main()
