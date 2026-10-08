# SRI STAR Profiles catalog analysis and asset library

**Website integration update:** The Hugo website now uses these assets and product records directly at `/products/`, with individual series pages, company information, technical data, PDF downloads, and product enquiries. The offline gallery below is retained as an extraction reference. Repository findings and the recommended plan later in this document describe the scaffold before that integration. See the [current project README](../../README.md) for running and maintaining the site.

The supplied 14-page catalog is a useful foundation for a profile supplier's website. It is principally a technical product catalog, with brand, performance, manufacturer, and distributor information around it. It is not a catalog of pipes, sheets, wall panels, or a broad hardware range.

Open **[index.html](index.html)** in a browser to browse and search the extracted assets. Everything is local; the preview makes no external requests. This is an asset review index, not a replacement for the Hugo website.

## Business identity found in the PDF

| Entity | What the catalog says | Source pages |
| --- | --- | --- |
| SRI STAR Profiles | Engineered uPVC profiles for window and door fabrication | 1, 2, 13, 14 |
| Kalpana Traders | Authorised Distributor - Southern Region | 1, 14 |
| Hebei Shengda Company | Manufacturer of SRI STAR uPVC Profiles; based in Baoding, Hebei, China | 13 |

The supplied document spells the names **SRI STAR** and **Kalpana Traders**. It establishes a manufacturer/brand/distributor relationship; it does not establish legal parent-company or subsidiary ownership.

Kalpana Traders' printed contact details are in Podanur, Coimbatore, Tamil Nadu 641023. The catalog lists +91 9865599555, +91 9944541604, and kalpanaupvctraders@gmail.com. The complete address and tax ID are transcribed in [content.json](content.json), alongside the manufacturer and test-report content. These are source transcriptions to confirm before publication.

## Product inventory

| Series | PDF pages | Catalog entries | Suggested product-section URL |
| --- | --- | ---: | --- |
| 60 Casement | 3, 9, 10 | 15 | `/products/60-casement/` |
| 62 Sliding | 4 | 6 | `/products/62-sliding/` |
| 80 Sliding | 5, 6 | 11 | `/products/80-sliding/` |
| 88 Sliding | 7, 8 | 8 | `/products/88-sliding/` |
| 65 Casement | 11, 12 | 12 | `/products/65-casement/` |
| **Total** | **10 product pages** | **52** | |

These are **52 printed entries and 43 distinct code strings**, not 52 confirmed unique SKUs. Shared components and duplicated/conflicting entries explain the difference. The 60 Casement pages are separated in the PDF; the extraction groups them together.

Products include frames, inward/outward sashes, door sashes, mullions, glass beads, bay corners, tube adaptors, sash covers, and screen sashes. Each entry has its printed description, code, series, thickness where specified, weight per metre, length, length weight, and pieces per bag. All printed lengths are 5.8 m, although their decimal formatting varies.

## What was extracted

| Location | Contents |
| --- | --- |
| `products/<series>/` | **52 diagram PNGs and 52 full specification-card PNGs**, named with page, serial number, and product code |
| `brand/` | 6 logo/symbol/nameplate assets, including SRI STAR and Shengda branding |
| `marketing/` | 4 complete marketing-page artworks, profile-range artwork, and sliding-window artwork |
| `company/` | Factory image, warehouse artwork, contact panel, and 5 manufacturer-information panels |
| `technical/` | Complete test table, performance overview, and 11 individual performance cards |
| `benefits/` | 6 benefit icons and 6 corresponding labeled badges |
| `pages/` | All 14 full PDF pages rendered at 144 dpi, for reference |
| `originals/` | 47 distinct non-fragment embedded raster images at their native resolution, plus a ZIP of 298 tiny image fragments from page 10 |
| `contact-sheets/` | One overview per product series, one for all pages, and one for supporting assets |
| `products.json` | Structured product records with original field values and linked assets |
| `content.json` | Reviewed transcription of the image-only business and test-report pages |
| `manifest.json` | Source PDF SHA-256, page numbers, crop coordinates, image dimensions, embedded-image references, duplicates, and review notes |
| `extracted-text.txt` | Extractable PDF text from pages 3-12; image-only pages are explicitly marked |
| `index.html` | Offline searchable asset gallery |

There are **45 curated supporting images**, in addition to the 104 product images and reference/original material. The source PDF remains unchanged at `assets/SRI_STAR_Product_Catalogue_Landscape (2).pdf`.

Example: `products/60-casement/p03-01-sphd60-11-diagram.png` is the first profile drawing on page 3. Its sibling `p03-01-sphd60-11-card.png` includes the printed specifications. Stable page/serial IDs prevent repeated product codes from overwriting each other.

## Image quality and extraction decisions

- Product cards and diagrams are rendered from the PDF at 216 dpi. This preserves the visible dimensions, page proportions, overlaid images, and assembled artwork. All 52 drawings were visually inspected in series contact sheets.
- Most technical drawings are already raster images, often around 250-350 pixels on a side. A higher-resolution render makes the crop convenient to use; it does not recover missing source detail. One frame image has substantially more native detail. The native originals are retained for future use.
- The page 10 bay-corner diagram is stored in 299 image placements backed by 298 distinct one-pixel-high image objects. Rendering reconstructs it correctly. The fragments are archived separately to keep the usable asset folders clear.
- Several drawings contain overlapping source images. Raw originals may contain an underlying drawing different from the visible composite; use the curated `*-diagram.png` for the website.
- The cover, technical report, manufacturer page, and contact page are single flattened 1672 x 941 images. Their reusable elements are cropped from those native images. The PDF stretches these images vertically, so the marketing crops deliberately preserve their native proportions.
- Raster logo crops retain their original backgrounds. No vector logos, transparent cutouts, CAD files, or new product detail have been invented.
- The warehouse and profile marketing images are promotional artwork. The catalog alone does not establish that the warehouse illustration depicts the actual premises.

## Source issues to resolve before a public product catalog

| Item | What needs checking |
| --- | --- |
| `SPHD60-21` | Page 3 entries 2 and 5 repeat the same printed specifications. Both retained. Thickness is printed as `2.5` with no unit; normalized data infers mm. |
| `SPHD65-21-1` | Page 11 entry 3 and page 12 entry 7 share a code and weight but show different thicknesses (2.6/2.5 mm) and different drawings. Do not merge automatically. |
| `SPHD60-41` | Page 9 identifies 19 Glass Beading; page 12 identifies 21 Frame Glass Beading with different weight, bag quantity, and drawing. Confirm the intended code. |
| `STHD88-47` | Page 4 lists 50 pieces/bag; page 8 lists 30. |
| `STHD88-20` | Appears in both 62 and 88 Sliding series with different description prefixes. Could be a shared component; confirm applicability. |
| Shared bead codes | Some pages omit thickness while other pages specify 1.4 mm. The extracted data preserves each occurrence. |
| Text versus drawing | Page 12's 21 Frame Glass Beading drawing is dimensioned 20.5; page 10's 80 Tube Adaptor drawing shows a 60.2 overall dimension. Preserve both labels and drawings pending clarification. |
| Source spelling | `Mullian`, `Casemnt`, and `Cashment` are normalized only in display names. Original wording remains in `name_as_printed` and `source_fields`. |
| Test report | Several results omit units, including `1.01` for main profile quality and `3.29` for tensile fracture strain. Retain the printed numbers rather than reinterpret them. |
| Certification and capacity | The catalog lists claims but no supporting certificate documents, report number, test date, or specimen scope. Capacity figures have no explicit annual period. Attribute claims to the catalog until supported. |

The manifest also lists every repeated code and every differing printed field, including harmless differences in decimal formatting. An omitted thickness is `null`, not zero. `length_weight_as_printed` retains its original string because the source field does not explicitly state a unit. Standard numeric fields are provided for filtering; the original decimal precision remains in `source_fields`.

## Original repository findings (before integration)

- The project is a static Hugo site using the vendored Lotus Docs theme. The home page is driven by `data/landing.yaml`, with site settings in `hugo.toml`, Markdown content under `content/`, and custom layouts under `layouts/`.
- Existing branding is **PrimePlast UPVC Traders**, with placeholder city, phone, email, domain, and imagery. It is scaffold content, not the catalog's business identity.
- Existing product pages include windows, doors, pipes, profiles, sheets, and hardware. The PDF supports a focused profile-system catalog. Other categories need separate business confirmation and source content.
- Existing promises about stock, same-week delivery, an owned fleet, trade credit, best prices, and cutting services are not established by this PDF.
- The contact form still points to `https://formspree.co/f/YOUR_FORM_ID`; it is not configured to deliver enquiries.
- The landing data refers to two comparison placeholder SVGs that are absent from the project's placeholder directory. That section also lacks actual before/after material from this PDF.
- `layouts/_default/list.html` shows child-page cards instead of section body content when child pages exist. A series index should deliberately account for that when introducing catalog descriptions and drawings.
- The existing site built successfully using its vendored Hugo v0.167.0 into a temporary output directory. It emits existing deprecation warnings for `languageCode`, `.Site.Data`, and `.Site.LanguageCode`.
- This workspace has no `.git` directory, although it includes a GitHub Pages workflow. No commit or deployment was performed.

## Website plan used for integration

1. **Home:** Kalpana Traders as the supplier, SRI STAR Profiles as the product brand, a concise fabrication-focused introduction, five series cards, and a quote CTA. Use the catalog's green/orange identity while keeping the page text readable and searchable.
2. **Products:** A five-series index and a page for each series. Each product card can show the extracted drawing, code, name, and compact specifications. Detail views can expose the complete table and original card. Use the structured records rather than embedding full PDF pages.
3. **About / manufacturer:** Clearly separate the local distributor from Hebei Shengda. Reuse the factory artwork and attributed manufacturer information.
4. **Quality / technical:** Show verified, appropriately scoped test information with the source document available for download. Resolve ambiguous values before promoting them as proof of performance.
5. **Contact / enquiry:** Confirm the printed contact details, configure an enquiry endpoint, and carry the selected product code into quote requests. Add WhatsApp only after confirming the intended number supports it.
6. **Downloads:** Offer the original catalog and, where helpful, individual technical cards. Keep the source document accessible as a reference.

Hugo can use `products.json` through a data import or by moving the reviewed records under `data/`. Images are already under `assets/`, so templates can use `resources.Get` and create appropriately sized delivery formats. No change to the production website is required to review this library.

## Reproduce the extraction

From the repository root, with Python 3.10+:

```sh
python3 -m venv /tmp/upvc-catalog-venv
/tmp/upvc-catalog-venv/bin/python -m pip install -r tools/catalog-requirements.txt
/tmp/upvc-catalog-venv/bin/python tools/extract_catalog.py
```

The script checks the 14-page source structure, detects card borders, parses all nine specification fields per card, renders crops, preserves native images, and generates the JSON, gallery, and contact sheets. It verifies that each raster decodes and each product image reference resolves. `content.json` and this analysis are reviewed companion files, preserved when the extractor is rerun.
