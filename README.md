# eldttraining.us: static rebuild (SEO + AI-search optimized)

A static replacement for the Shopify version of eldttraining.us: same branding, same homepage video, same analytics (minus Shopify), Stripe checkout through the hazwoper-osha.com course API (same flow as datacentertraining.us), and 115 crawlable pages.

## Layout

```
generator/            build system and content (edit here)
  build.py            renders every page into ./site
  validate.py         audit: titles, descriptions, H1s, broken links/anchors, alt text, JSON-LD, orphans, sitemap
  serve.py            local preview server that resolves URLs like GitHub Pages
  md.py               small Markdown converter used for guides/pages
  data/courses.py     course catalog (hazwoper-osha.com IDs/SKUs, prices, hours, FAQs)
  data/syllabi.json   module/lesson lists pulled from the Shopify product descriptions
  data/states.py      state data for /pages/state/{xx}
  content/guides/*.md 41 guides (front matter + Markdown)
  content/pages/*.md  about, contact, partner, FAQ hub, policies
site/                 built output: deploy this folder (CNAME + .nojekyll included)
  assets/js/config.js Stripe key, API base URL, course IDs, CHECKOUT_DISABLED flag
  assets/js/checkout.js  Stripe → /add_new_user → /add_order → confirmCardPayment
.github/workflows/pages.yml   builds, validates, and deploys site/ to GitHub Pages on push to main
```

## Commands

```bash
python3 generator/build.py      # build into ./site
python3 generator/validate.py   # SEO/integrity audit
python3 generator/serve.py      # preview at http://127.0.0.1:8130
```

## Preview on GitHub Pages (before the domain is connected)

Without a custom domain, Pages serves the site at `https://lj-web-management.github.io/eldttraining.us/`. The workflow reads that sub-path from `actions/configure-pages` and rebuilds with `BASE_PATH=/eldttraining.us`, which prefixes every internal link and asset and marks every page `noindex` so the preview never competes with the real domain in Google. Once `eldttraining.us` is set as the custom domain, the base path is empty and the deployed build is the normal one, with no workflow change needed.

To reproduce the preview locally:

```bash
BASE_PATH=/eldttraining.us python3 generator/build.py
python3 generator/serve.py 8131 /eldttraining.us   # http://127.0.0.1:8131/eldttraining.us/
python3 generator/build.py                          # rebuild normally before committing
```

The preview uses the same live Stripe key, course API, GA4, Google Ads, and Clarity as production. Real card payments there are real orders. Filter GA4/Clarity by hostname to exclude preview traffic.

## URLs preserved from Shopify (no redirects needed)

Pages are written as `<path>.html`, which GitHub Pages, Cloudflare Pages, and Netlify all serve at the extensionless URL:

- `/products/{handle}` for all 8 courses
- `/collections/all` (and `/collections/frontpage` → soft redirect)
- `/pages/state` and `/pages/state/{xx}` for 50 states + DC + PR (these currently rank in Google)
- `/pages/about-us`, `/pages/contact`, `/pages/partner-with-us`, `/pages/faq-training-entry-level-driver-must-complete`, `/pages/data-sharing-opt-out`
- `/policies/privacy-policy`, `/policies/terms-of-service`, `/policies/refund-policy`
- `/blogs/news` → soft redirect to `/guides/`; `/pages/privacy` → `/policies/privacy-policy`

If you host on plain S3/CloudFront instead, you need a function that maps `/x` → `/x.html`.

## Tracking (carried over from the live site, Shopify pixels removed)

- GA4 `G-NBH7WDL0NG` and `G-YFRVXFXTZP`, Google tag `GT-KF6RLPLB`
- Google Ads `AW-16866056315`, purchase conversion `AW-16866056315/qwkRCKWJrp0aEPuwruo-` with enhanced conversions (fired on checkout success)
- Microsoft Clarity `qbr52o2h0g`
- Google Search Console verification meta tag
- GA4 ecommerce events: `view_item_list`, `view_item`, `select_item`, `begin_checkout`, `add_payment_info`, `purchase`; plus `phone_click`, `email_click`, `generate_lead`, `video_start`, `video_complete`

## Checkout / course API

`site/assets/js/config.js` maps each course to its hazwoper-osha.com catalog ID (matched by SKU):

| Course | Checkout slug | Course ID | SKU |
|---|---|---|---|
| Class A | `class-a` | 304 | ELDTClassA |
| Class B | `class-b` | 309 | CDL ELDT C-B |
| Class B to A Upgrade | `b-to-a-upgrade` | 316 | ELDTB-AUpgrade |
| Hazmat (H) | `hazmat-h` | 281 | ELDTHEndorsement |
| Passenger (P) | `passenger-p` | 293 | ELDTPEndorsement |
| School Bus (S) | `school-bus-s` | 299 | CELDTSBS |
| X (Hazmat + Tanker) | `hazmat-tanker-x` | 493 | X Endorsment |
| Tanker (N) | `tanker-n` | 499 | CDL-ELDT-N |

Orders are sent with `order_from: "eldttraining.us"`. The amount charged is decided server-side by `/add_order`.

## AI / search files

- `/llms.txt` summary and `/llms-full.txt` full text for LLMs
- `/agents.md` instructions for AI shopping agents (replaces Shopify's UCP version)
- `/robots.txt` explicitly allows search and AI crawlers; blocks `/checkout`
- `/sitemap.xml` with lastmod for all 113 indexable URLs
- JSON-LD on every page: Organization, WebSite, BreadcrumbList, Course + Product (course pages), Article (guides), FAQPage, VideoObject, ItemList

## Launch checklist

1. Push to a GitHub repo, enable Pages → "GitHub Actions" as the source.
2. Point DNS for eldttraining.us at GitHub Pages (apex A records + `www` CNAME) and disconnect the domain in Shopify.
3. Submit `https://eldttraining.us/sitemap.xml` in Google Search Console and Bing Webmaster Tools.
4. Run an Ahrefs / Semrush site audit after the first crawl.
