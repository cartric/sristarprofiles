# SRI STAR Profiles | Kalpana Traders

A Hugo website for SRI STAR uPVC profile systems, supplied by Kalpana Traders, authorised distributor for the Southern Region in Coimbatore. It retains the Lotus Docs / Bootstrap template and uses the branding, imagery, product specifications, and company information from the supplied catalogue.

## Run locally

Use Hugo Extended and Go for the Hugo module dependency. GitHub Actions installs Hugo Extended v0.167.0 separately. On macOS, you can install the development tools with `brew install hugo go`.

```sh
hugo server --disableFastRender
```

Open **http://localhost:1313/**. Hugo rebuilds when content, data, layouts, or assets change. Press **Ctrl+C** to stop the server.

If this working copy already has `tools/hugo`, you can still run `./tools/hugo server --disableFastRender`. That local executable is intentionally ignored by Git and is not included in a fresh clone.

## Build

```sh
hugo --minify --cleanDestinationDir
```

The generated site is written to `public/`. Use `--cleanDestinationDir` after removing or renaming pages so stale output does not remain.

Commit the source files, original catalogue, extracted assets, and theme. `.gitignore` excludes `public/`, Hugo's generated cache, the local Hugo binary, and local dependency and environment files. GitHub Pages builds the site from source; generated output does not need to be committed.

For a production domain, set `baseURL` in `hugo.toml` or pass it at build time:

```sh
hugo --minify --cleanDestinationDir --baseURL 'https://your-domain.example/'
```

No production domain is configured yet. The GitHub Pages workflow obtains the deployment base URL from GitHub's Pages configuration. Configure **Settings → Pages → Source → GitHub Actions** in the repository used for deployment. If using a custom domain, add its actual hostname to `static/CNAME`.

## Pages

- `/` — company introduction, product series, benefits, and manufacturer overview.
- `/products/` — all 52 printed catalogue entries, with search and series filters.
- `/products/60-casement/`, `/products/65-casement/`, `/products/62-sliding/`, `/products/80-sliding/`, `/products/88-sliding/` — individual series.
- `/about/` — Kalpana Traders and Hebei Shengda Company.
- `/quality/` — catalogue technical data and attributed manufacturer information.
- `/downloads/` — original PDF and technical resources.
- `/contact/` — printed business details and an email-enquiry draft form.
- `/services/` — how to prepare a product requirement.

The old generic product URLs redirect to `/products/`. Catalogue pages render through Hugo; visitors do not need the separate extraction gallery.

## Content and assets

```text
content/                         Page titles, descriptions, and editorial content
hugo.toml                        Brand, navigation, site configuration
data/landing.yaml               Home-page copy and selected artwork
data/catalog/series.yaml        Series descriptions and representative profiles
assets/sri-star-catalog/          Source artwork, extracted product JSON, and provenance
assets/css/site.css              Brand and responsive styling
assets/scss/style.scss           Brand variables plus retained theme SCSS imports
assets/js/catalog.js             Navigation, product filtering, and enquiry drafts
layouts/catalog/                 Hugo product templates
layouts/partials/catalog/        Shared product, image, data, and download helpers
layouts/_default/                Shared shell and company/quality/contact pages
themes/lotusdocs/                Retained upstream theme; not edited
```

`assets/sri-star-catalog/products.json` is the single source for the 52 product records. `content.json` in the same folder holds company details and transcribed technical information. Hugo imports them at build time, publishes only referenced imagery, generates WebP versions, and publishes the original PDF at `/downloads/sri-star-product-catalogue.pdf`.

Repeated product codes are retained with unique page-and-entry references. Display values preserve catalogue specifications, including differences between entries. Missing thickness is shown as unspecified. See the [extraction analysis](assets/sri-star-catalog/README.md) and [manifest](assets/sri-star-catalog/manifest.json) for source issues that need supplier clarification.

The original [offline asset gallery](assets/sri-star-catalog/index.html) remains a development reference. Recreate the extracted images with `tools/extract_catalog.py` and the dependencies in `tools/catalog-requirements.txt`.

## Enquiries

Phone and email links work directly. The enquiry form prepares a draft with the selected product code, series, catalogue reference, quantities, and contact information. The visitor reviews it and opens their email app, or copies it into another email service. It does not submit, store, or send messages on a server, and it does not claim an enquiry was sent.

No form-service account or backend is required for this workflow. A hosted submission service can be connected later if desired. WhatsApp links are not assumed from the printed mobile numbers.

## Validation

```sh
hugo --minify --cleanDestinationDir
python3 tools/check_site.py public
node --check assets/js/catalog.js
```

The output check verifies product coverage, image and download references, internal links and anchors, shared branding, unique element IDs, and the absence of the old placeholder company content. Browser QA remains a separate visual/interaction check.

Optional DOM integration checks for search, filters, navigation state, and enquiry drafts:

```sh
npm install --prefix /tmp/upvc-site-qa --no-fund --no-audit jsdom
NODE_PATH=/tmp/upvc-site-qa/node_modules node tools/check_interactions.cjs public
```
