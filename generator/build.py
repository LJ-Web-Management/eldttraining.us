#!/usr/bin/env python3
"""Static site generator for eldttraining.us.

    python3 generator/build.py          # builds into ./site

Pages are written as `<path>.html` so GitHub Pages / Cloudflare Pages / Netlify serve them at
extensionless URLs identical to the old Shopify URLs (/products/..., /pages/..., /collections/all).
"""
import glob
import html
import json
import math
import os
import re
import sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "data"))

import md  # noqa: E402
from courses import COURSES, BY_SLUG, BY_HANDLE  # noqa: E402
from states import STATES, BY_ABBR  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "site")
DOMAIN = "https://eldttraining.us"
# Content "last updated" date used for sitemap lastmod / dateModified. Bump when you change content.
TODAY = os.environ.get("SITE_UPDATED", "2026-11-16")
YEAR = date.today().year
BRAND = "ELDT Training"
PHONE = "(866) 429-6742"
PHONE_TEL = "+18664296742"
EMAIL = "info@eldttraining.us"
OG_IMAGE = DOMAIN + "/assets/img/eldt-training-social-share.jpg"
LOGO = "/assets/img/eldt-training-logo.jpg"
SYLLABI = json.load(open(os.path.join(HERE, "data", "syllabi.json")))
ASSET_V = datetime.now().strftime("%Y%m%d%H%M")

# Hosting under a sub-path (e.g. the GitHub Pages preview at lj-web-management.github.io/eldttraining.us/).
# BASE_PATH="/eldttraining.us" prefixes every root-relative link; leave it empty on the real domain.
# Any build served somewhere other than eldttraining.us is marked noindex so it never competes in Google.
BASE = os.environ.get("BASE_PATH", "").strip().rstrip("/")
if BASE and not BASE.startswith("/"):
    BASE = "/" + BASE
SITE_HOST = os.environ.get("SITE_HOST", "").strip().lower()
PREVIEW = bool(BASE) or (SITE_HOST not in ("", "eldttraining.us", "www.eldttraining.us"))

_ATTR_RE = re.compile(r'(\s(?:href|src|action|poster|value)=")/(?!/)')
_SRCSET_RE = re.compile(r'(\s(?:srcset|imagesrcset)=")([^"]*)"')
_ROBOTS_RE = re.compile(r'<meta name="robots" content="[^"]*">')


def finalize(doc):
    """Apply BASE_PATH to root-relative URLs and noindex preview builds."""
    if BASE:
        doc = _ATTR_RE.sub(lambda m: m.group(1) + BASE + "/", doc)
        doc = _SRCSET_RE.sub(lambda m: m.group(1) + re.sub(r'(^|,\s*)/(?!/)', lambda n: n.group(1) + BASE + "/", m.group(2)) + '"', doc)
        doc = doc.replace('content="0; url=/', f'content="0; url={BASE}/')
        doc = doc.replace('<html lang="en">', f'<html lang="en" data-base="{BASE}">', 1)
    if PREVIEW:
        doc = _ROBOTS_RE.sub('<meta name="robots" content="noindex, nofollow">', doc, count=1)
    return doc

TRACKING = """<!-- Google tag (gtag.js): GA4 + Google tag + Google Ads -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NBH7WDL0NG"></script>
<script>
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());
gtag('config','G-NBH7WDL0NG');
gtag('config','G-YFRVXFXTZP');
gtag('config','GT-KF6RLPLB');
gtag('config','AW-16866056315',{'allow_enhanced_conversions':true});
</script>
<!-- Microsoft Clarity -->
<script>
(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","qbr52o2h0g");
</script>"""

SOCIAL = [
    ("Facebook", "https://www.facebook.com/eldttraining.us", '<path d="M18 10.05C18 5.6 14.42 2 10 2s-8 3.6-8 8.05c0 4.02 2.93 7.35 6.75 7.95v-5.62H6.72v-2.33h2.03V8.28c0-2.02 1.2-3.13 3.02-3.13.87 0 1.79.16 1.79.16v1.98h-1.01c-.99 0-1.3.62-1.3 1.26v1.51h2.22l-.36 2.33h-1.86V18c3.83-.6 6.75-3.93 6.75-7.95"/>'),
    ("Instagram", "https://www.instagram.com/hazwoper_osha_training/", '<path d="M10 3.6c2.08 0 2.33 0 3.15.05 2.11.1 3.1 1.1 3.2 3.2.04.82.05 1.07.05 3.15s0 2.33-.05 3.15c-.1 2.1-1.09 3.1-3.2 3.2-.82.04-1.07.05-3.15.05s-2.33 0-3.15-.05c-2.12-.1-3.1-1.1-3.2-3.2C3.61 12.33 3.6 12.08 3.6 10s0-2.33.05-3.15c.1-2.1 1.09-3.1 3.2-3.2.82-.04 1.07-.05 3.15-.05zM10 2c-2.17 0-2.45 0-3.3.05C3.8 2.18 2.18 3.8 2.05 6.7 2 7.55 2 7.83 2 10s0 2.45.05 3.3c.13 2.9 1.75 4.52 4.65 4.65.85.04 1.13.05 3.3.05s2.45 0 3.3-.05c2.9-.13 4.52-1.75 4.65-4.65.04-.85.05-1.13.05-3.3s0-2.45-.05-3.3C17.82 3.8 16.2 2.18 13.3 2.05 12.45 2 12.17 2 10 2zm0 3.9a4.1 4.1 0 1 0 0 8.2 4.1 4.1 0 0 0 0-8.2zm0 6.77a2.67 2.67 0 1 1 0-5.34 2.67 2.67 0 0 1 0 5.34zm4.27-7.9a.96.96 0 1 0 0 1.92.96.96 0 0 0 0-1.92z"/>'),
    ("YouTube", "https://www.youtube.com/@hazwoper-osha", '<path d="M18.16 5.87a2.1 2.1 0 0 0-1.48-1.49C15.37 4 10 4 10 4s-5.37 0-6.68.38a2.1 2.1 0 0 0-1.48 1.49C1.5 7.19 1.5 10 1.5 10s0 2.81.34 4.13a2.1 2.1 0 0 0 1.48 1.49C4.63 16 10 16 10 16s5.37 0 6.68-.38a2.1 2.1 0 0 0 1.48-1.49c.34-1.32.34-4.13.34-4.13s0-2.81-.34-4.13zM8.3 12.56V7.44L12.75 10 8.3 12.56z"/>'),
    ("X (Twitter)", "https://x.com/HazwoperOsha", '<path d="M11.52 8.78 17.2 2h-1.35l-4.93 5.88L6.98 2H2.44l5.96 8.89L2.44 18h1.35l5.21-6.21L13.16 18h4.54l-6.18-9.22zm-1.84 2.2-.6-.88-4.8-7.1h2.07l3.87 5.73.6.88 5.04 7.46h-2.07l-4.11-6.09z"/>'),
]

ORG = {
    "@type": ["EducationalOrganization", "Organization"],
    "@id": DOMAIN + "/#organization",
    "name": BRAND,
    "alternateName": ["ELDTtraining.us", "ELDT Training.us"],
    "url": DOMAIN + "/",
    "logo": {"@type": "ImageObject", "url": DOMAIN + LOGO, "width": 600, "height": 95},
    "image": OG_IMAGE,
    "description": "ELDT Training (eldttraining.us) is an online provider of FMCSA-compliant Entry-Level Driver Training (ELDT) theory courses for Class A and Class B CDLs and the hazmat, passenger, school bus, tanker, and X endorsements. Completions are reported to the FMCSA Training Provider Registry.",
    "email": EMAIL,
    "telephone": "+1-866-429-6742",
    "parentOrganization": {"@type": "Organization", "name": "Industrial Certified Training, LLC"},
    "sameAs": ["https://www.facebook.com/eldttraining.us"],
    "areaServed": {"@type": "Country", "name": "United States"},
    "knowsAbout": ["Entry-Level Driver Training (ELDT)", "Commercial driver's license (CDL)", "FMCSA Training Provider Registry", "49 CFR Part 380",
                   "Hazardous materials endorsement", "Passenger endorsement", "School bus endorsement", "Tank vehicle endorsement", "CDL theory training"],
    "contactPoint": {"@type": "ContactPoint", "telephone": "+1-866-429-6742", "email": EMAIL, "contactType": "customer service",
                     "areaServed": "US", "availableLanguage": "English"},
}
WEBSITE = {"@type": "WebSite", "@id": DOMAIN + "/#website", "url": DOMAIN + "/", "name": BRAND,
           "publisher": {"@id": DOMAIN + "/#organization"}, "inLanguage": "en-US"}

PAGES = []      # (path, title, description, indexable, lastmod, kind)
TEXT_INDEX = {}  # path -> markdown text for llms-full.txt

esc = lambda s: html.escape(str(s), quote=True)


def money(v):
    return f"${v:,.2f}"


def url(path):
    return DOMAIN + path


def ld(obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return '<script type="application/ld+json">' + s.replace("</", "<\\/") + "</script>"


def breadcrumb_ld(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": url(p)} for i, (n, p) in enumerate(items)]}


def breadcrumb_html(items):
    lis = []
    for i, (n, p) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f'<li aria-current="page">{esc(n)}</li>')
        else:
            lis.append(f'<li><a href="{p}">{esc(n)}</a></li>')
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'


def faq_ld(faqs):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": md.strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": md.strip_tags(a)}} for q, a in faqs]}


def faq_html(faqs, open_first=False):
    out = ['<div class="faq">']
    for i, (q, a) in enumerate(faqs):
        body = a if a.strip().startswith("<") else "<p>" + md.inline(a) + "</p>"
        out.append(f'<details{" open" if open_first and i == 0 else ""}><summary>{md.inline(q)}</summary><div class="ans">{body}</div></details>')
    out.append("</div>")
    return "".join(out)


# ---------------------------------------------------------------- layout
NAV = [("Home", "/"), ("Courses", "/collections/all"), ("By State", "/pages/state"), ("Guides", "/guides/"),
       ("FAQ", "/pages/faq-training-entry-level-driver-must-complete"), ("About Us", "/pages/about-us"), ("Contact Us", "/pages/contact")]


def header(active):
    items = "".join(
        f'<li><a href="{p}"{" aria-current=\"page\"" if active == p else ""}>{n}</a></li>' for n, p in NAV)
    return f"""<a class="skip" href="#main">Skip to content</a>
<div class="topbar"><strong>Registered FMCSA Training Provider</strong> · Theory completions reported to the TPR · <a href="tel:{PHONE_TEL}">Call {PHONE}</a></div>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="/" aria-label="ELDT Training home"><img src="{LOGO}" alt="ELDT Training logo" width="200" height="32"></a>
    <nav class="main-nav" id="mainNav" aria-label="Main">
      <ul>{items}</ul>
    </nav>
    <div class="nav-cta">
      <a class="phone-link hide-sm" href="tel:{PHONE_TEL}">{PHONE}</a>
      <a class="btn btn-dark btn-sm" href="/collections/all">Enroll Now</a>
      <button class="nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false" aria-controls="mainNav"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>"""


def footer():
    course_links = "".join(f'<li><a href="/products/{c["handle"]}">{esc(c["short"])} ELDT</a></li>' for c in COURSES)
    guide_links = "".join(f'<li><a href="/guides/{s}">{esc(t)}</a></li>' for s, t in [
        ("what-is-eldt", "What Is ELDT?"), ("eldt-requirements", "ELDT Requirements"), ("how-to-get-a-cdl", "How to Get a CDL"),
        ("cdl-endorsements", "CDL Endorsements"), ("hazmat-endorsement", "Hazmat Endorsement"), ("training-provider-registry", "Training Provider Registry"),
        ("eldt-cost", "ELDT Cost")])
    social = "".join(f'<a href="{u}" rel="noopener" aria-label="{n}"><svg viewBox="0 0 20 20" aria-hidden="true">{svg}</svg></a>' for n, u, svg in SOCIAL)
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <p class="disclaimer"><strong style="color:#fff">Disclaimer:</strong> Eldttraining.us is a private company providing ELDT online training courses. Our courses align with FMCSA and DOT guidelines, and we are listed as a registered training provider on the FMCSA Training Provider Registry. We are not affiliated with FMCSA, USDOT, or any state licensing agency.</p>
        <p class="disclaimer"><strong style="color:#fff">Subsidiary Partnership:</strong> ELDTtraining.us is a subsidiary of Industrial Certified Training, LLC, a company specializing in DOT safety training. We partner with HAZWOPER OSHA Training, LLC to offer a comprehensive range of safety compliance courses.</p>
      </div>
      <div><h2>ELDT Courses</h2><ul>{course_links}</ul></div>
      <div><h2>Guides</h2><ul>{guide_links}<li><a href="/guides/">All guides →</a></li></ul></div>
      <div>
        <h2>Contact Us</h2>
        <p>Have questions? We're here to help.</p>
        <ul>
          <li><a href="tel:{PHONE_TEL}">{PHONE}</a></li>
          <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
          <li><a href="/pages/about-us">About Us</a></li>
          <li><a href="/pages/partner-with-us">Partner With Us</a></li>
          <li><a href="/pages/state">ELDT by State</a></li>
        </ul>
        <div class="social">{social}</div>
        <a class="footer-badge" href="https://tpp.eldttraining.us/"><img src="/assets/img/fmcsa-compliant-badge-sm.png" alt="FMCSA-compliant ELDT training provider badge" width="90" height="83" loading="lazy"><span>ELDT Training Partner Program →</span></a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© {YEAR}, ELDT Training. All Rights Reserved.</span>
      <span><a href="/policies/privacy-policy">Privacy Policy</a> · <a href="/policies/terms-of-service">Terms of Service</a> · <a href="/policies/refund-policy">Refund Policy</a> · <a href="/pages/data-sharing-opt-out">Your Privacy Choices</a></span>
    </div>
  </div>
</footer>"""


def write_page(path, title, description, body, *, schema=None, robots="index, follow", og_type="website",
               active=None, extra_head="", canonical=None, lastmod=None, kind="page", mobile_cta=True,
               checkout_assets=False, preload=None, also_index=False, include_in_sitemap=True):
    canonical = canonical or url(path)
    graph = [ORG, WEBSITE] + (schema or [])
    head_schema = ld({"@context": "https://schema.org", "@graph": graph})
    css = f'<link rel="stylesheet" href="/assets/css/styles.css?v={ASSET_V}">'
    js = f'<script src="/assets/js/main.js?v={ASSET_V}" defer></script>'
    if checkout_assets:
        css += ('\n<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/intl-tel-input@18.2.1/build/css/intlTelInput.css">'
                f'\n<link rel="stylesheet" href="/assets/css/checkout.css?v={ASSET_V}">')
        js = (f'<script src="/assets/js/config.js?v={ASSET_V}" defer></script>\n<script src="https://js.stripe.com/v3/" defer></script>\n'
              '<script src="https://cdn.jsdelivr.net/npm/intl-tel-input@18.2.1/build/js/intlTelInput.min.js" defer></script>\n'
              f'<script src="/assets/js/checkout.js?v={ASSET_V}" defer></script>')
    pre = preload or ""
    mcta = ""
    if mobile_cta:
        mcta = f'<div class="mobile-cta"><a class="btn btn-outline" href="tel:{PHONE_TEL}">Call</a><a class="btn btn-dark" href="/collections/all">View Courses</a></div>'
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="{robots}{', max-image-preview:large, max-snippet:-1' if robots.startswith('index') else ''}">
<link rel="canonical" href="{canonical}">
<meta name="google-site-verification" content="cqBwJT9TFKTZocNiNmr-ROoZqsRZ6JUsTcM_pfWGM54">
<meta name="theme-color" content="#31393c">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="ELDT Training: FMCSA-compliant online ELDT theory courses">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@HazwoperOsha">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="text/plain" title="LLM summary" href="/llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&family=Open+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap">
{pre}
{css}
{extra_head}
{TRACKING}
{head_schema}
</head>
<body{' class="has-mobile-cta"' if mobile_cta else ''}>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
{mcta}
{js}
</body>
</html>
"""
    doc = finalize(doc)
    if path == "/":
        rel = "index.html"
    elif path.endswith("/"):
        rel = path.strip("/") + "/index.html"
    else:
        rel = path.strip("/") + ".html"
    dest = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as f:
        f.write(doc)
    if also_index:  # also write <path>/index.html for hosts that resolve directories first
        d2 = os.path.join(OUT, path.strip("/"), "index.html")
        os.makedirs(os.path.dirname(d2), exist_ok=True)
        with open(d2, "w") as f:
            f.write(doc)
    PAGES.append(dict(path=path, title=title, description=description, indexable=robots.startswith("index") and include_in_sitemap,
                      lastmod=lastmod or TODAY, kind=kind, canonical=canonical))


def write_redirect(path, target):
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Moved | {BRAND}</title>
<meta name="robots" content="noindex, follow"><link rel="canonical" href="{url(target)}">
<meta http-equiv="refresh" content="0; url={target}"></head>
<body><p>This page has moved to <a href="{target}">{url(target)}</a>.</p></body></html>"""
    dest = os.path.join(OUT, path.strip("/") + ".html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w").write(finalize(doc))


# ---------------------------------------------------------------- shared components
def course_card(c, heading="h3"):
    tag = f'<span class="tag">{esc(c["tag"])}</span>' if c.get("tag") else ""
    was = f'<span class="price-was">{money(c["compare_at"])}</span>' if c.get("compare_at") else ""
    cls = "course-card has-tag" if c.get("tag") else "course-card"
    return f"""<article class="{cls}" data-sku="{esc(c['sku'])}" data-name="{esc(c['name'])}" data-price="{c['price']}">
  {tag}<{heading}><a href="/products/{c['handle']}">{esc(c['name'])}</a></{heading}>
  <p class="sub">{esc(c['card_sub'])}</p>
  <p class="req">{esc(c['card_req'])}</p>
  <div class="price-row"><span class="price">{money(c['price'])}</span>{was}</div>
  <div class="card-actions"><a class="btn btn-outline btn-sm" href="/products/{c['handle']}">Learn More</a><a class="btn btn-dark btn-sm" href="/checkout?item={c['slug']}">Enroll Now</a></div>
</article>"""


def course_grid(slugs=None, list_name="Courses", heading="h3"):
    cs = [BY_SLUG[s] for s in slugs] if slugs else COURSES
    return f'<div class="course-grid" data-item-list="{esc(list_name)}">' + "".join(course_card(c, heading) for c in cs) + "</div>"


def cta_band(c=None):
    if c:
        return f"""<div class="cta-band"><div><h3>{esc(c['short'])} ELDT theory, 100% online</h3><p>{c['hours']} hour{'s' if c['hours'] != 1 else ''} · self-paced · completion reported to the FMCSA TPR · {money(c['price'])}</p></div>
<div class="card-actions"><a class="btn btn-white" href="/products/{c['handle']}">Course details</a><a class="btn btn-green" href="/checkout?item={c['slug']}">Enroll Now</a></div></div>"""
    return """<div class="cta-band"><div><h3>Start your ELDT theory training today</h3><p>FMCSA-compliant, self-paced, audio playback, and reported to the Training Provider Registry when you pass.</p></div>
<div class="card-actions"><a class="btn btn-green" href="/collections/all">See all courses</a></div></div>"""


# (label, checked before, theory cell, theory class, behind-the-wheel cell, btw class, course slug)
# Only courses we sell. Theory classes: yes = required (green), rec = recommended (orange).
# Behind-the-wheel classes: online = no BTW needed, finish 100% online (green); btw = separate BTW (neutral).
ELDT_TABLE_ROWS = [
    ("Class A CDL (first time)", "Checked before your Class A skills test", "Required", "yes", "Yes: range and public road", "btw", "class-a"),
    ("Class B to Class A upgrade", "Checked before your Class A skills test", "Required", "yes", "Yes: range and public road", "btw", "b-to-a-upgrade"),
    ("Class B CDL (first time)", "Checked before your Class B skills test", "Required", "yes", "Yes: range and public road", "btw", "class-b"),
    ("Passenger (P) endorsement", "Checked before your P skills test", "Required", "yes", "Yes: range and/or public road", "btw", "passenger-p"),
    ("School bus (S) endorsement", "Checked before your S skills test", "Required", "yes", "Yes: range and/or public road", "btw", "school-bus-s"),
    ("Hazmat (H) endorsement", "Checked before your H knowledge test", "Required", "yes", "None: finish 100% online", "online", "hazmat-h"),
    ("Hazmat + Tanker (X) endorsement", "Hazmat portion checked before your H knowledge test", "Required (hazmat portion)", "yes", "None: finish 100% online", "online", "hazmat-tanker-x"),
    ("Tanker (N) endorsement", "Prepares you for the state N knowledge test", "Recommended prep|Not a federal ELDT mandate", "rec", "None: finish 100% online", "online", "tanker-n"),
]


def cell_with_note(text):
    """'Main text|small note' -> main text with a muted note underneath."""
    main, _, note = text.partition("|")
    return esc(main) + (f'<span class="cell-note">{esc(note)}</span>' if note else "")


def eldt_table():
    rows = []
    for lic, note, th, cls_t, btw, cls_b, slug in ELDT_TABLE_ROWS:
        c = BY_SLUG[slug]
        tag = ' <span class="tag-inline">Best value</span>' if slug == "hazmat-tanker-x" else ""
        rows.append(
            f'<tr><td><a href="/products/{c["handle"]}"><strong>{esc(lic)}</strong></a>{tag}<span class="cell-note">{esc(note)}</span></td>'
            f'<td class="{cls_t}">{cell_with_note(th)}</td><td class="{cls_b}">{esc(btw)}</td>'
            f'<td class="course-cell"><div class="course-cta"><div><span class="cell-price">{money(c["price"])}</span>'
            f'<span class="cell-note">{c["hours"]} hr{"s" if c["hours"] != 1 else ""}, self-paced</span></div>'
            f'<a class="btn btn-dark btn-sm" href="/checkout?item={slug}">Enroll</a></div></td></tr>')
    return ('<div class="table-wrap eldt-table"><table><thead><tr><th scope="col">License or endorsement</th><th scope="col">ELDT theory</th>'
            '<th scope="col">Behind-the-wheel</th><th scope="col">Our online course</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"
            '<p class="small">Every course is 100% online with audio playback. ELDT completions (Class A, Class B, P, S, and H, including the hazmat portion of X) are reported to the FMCSA Training Provider Registry. '
            'Source: 49 CFR Part 380, Subparts F and G. ELDT applies to applicants who did not already hold the license or endorsement before February 7, 2022.</p>')


def state_grid():
    return '<div class="state-grid">' + "".join(
        f'<a href="/pages/state/{s["abbr"].lower()}" title="ELDT training in {esc(s["name"])}">{s["abbr"]}</a>' for s in STATES) + "</div>"


def state_select():
    opts = "".join(f'<option value="/pages/state/{s["abbr"].lower()}">{esc(s["name"])}</option>' for s in sorted(STATES, key=lambda x: x["name"]))
    return f'<form class="state-select" action="/pages/state" onsubmit="return false"><label class="visually-hidden" for="statePicker">Choose your state</label><select id="statePicker"><option value="">Choose your state…</option>{opts}</select></form>'


US_MAP = json.load(open(os.path.join(HERE, "data", "us_map.json")))  # see generator/tools/make_us_map.cjs
MAP_CALLOUTS = ["VT", "NH", "MA", "RI", "CT", "NJ", "DE", "MD", "DC"]  # too small to tap: labeled boxes to the right
MAP_LABEL_NUDGE = {"FL": (16, 4), "LA": (-12, 0), "MI": (10, 16), "KY": (6, 2), "WV": (-3, 4), "VA": (10, 4), "ID": (0, 16),
                   "HI": (0, -6), "MN": (-6, 6), "CA": (-6, 0), "NC": (8, 0), "SC": (4, 2), "OK": (12, 0), "NY": (6, 4)}


def state_map():
    """Clickable SVG map of the states (Albers USA, 975x610) plus DC and Puerto Rico callouts."""
    by_name = {s["name"]: s for s in STATES}
    shapes = {by_name[x["name"]]["abbr"]: (by_name[x["name"]], x) for x in US_MAP}
    parts, callouts = [], []
    for ab in sorted(shapes):
        s, x = shapes[ab]
        label = ""
        if ab not in MAP_CALLOUTS:
            dx, dy = MAP_LABEL_NUDGE.get(ab, (0, 0))
            size = 13 if x["area"] > 2500 else 10.5
            label = f'<text x="{x["cx"] + dx:.0f}" y="{x["cy"] + dy:.0f}" font-size="{size}">{ab}</text>'
        parts.append(f'<a href="/pages/state/{ab.lower()}" aria-label="ELDT training in {esc(s["name"])}" data-name="{esc(s["name"])}">'
                     f'<path d="{x["d"]}"/>{label}</a>')
    for i, ab in enumerate(MAP_CALLOUTS):
        s, x = shapes[ab]
        y = 200 + i * 30
        callouts.append(f'<a class="callout" href="/pages/state/{ab.lower()}" aria-label="ELDT training in {esc(s["name"])}" data-name="{esc(s["name"])}">'
                        f'<line x1="{x["cx"]}" y1="{x["cy"]}" x2="938" y2="{y}"/><rect x="938" y="{y - 11}" width="46" height="22" rx="6"/>'
                        f'<text x="961" y="{y}" font-size="12">{ab}</text></a>')
    pr = BY_ABBR["PR"]
    callouts.append(f'<a class="callout" href="/pages/state/pr" aria-label="ELDT training in {esc(pr["name"])}" data-name="{esc(pr["name"])}">'
                    '<rect x="872" y="560" width="46" height="22" rx="6"/><text x="895" y="571" font-size="12">PR</text></a>')
    return ('<svg class="us-map" viewBox="0 0 990 612" xmlns="http://www.w3.org/2000/svg" role="group" aria-label="Map of U.S. states. Select your state.">'
            + "".join(parts) + "".join(callouts) + "</svg>")


def state_picker(all_link=True):
    more = ' <a href="/pages/state">See all states and licensing agencies</a>' if all_link else ""
    return (f'<div class="state-picker">{state_select()}<div class="us-map-wrap"><p class="map-readout" aria-hidden="true">Select your state</p>{state_map()}</div>'
            f'<p class="small center map-note">Click your state on the map or choose it from the list.{more}</p></div>')


GUIDES = {}  # slug -> meta (filled by load_guides)


def guide_cards(slugs):
    cards = []
    for s in slugs:
        g = GUIDES.get(s)
        if not g:
            continue
        cards.append(f'<a class="link-card" href="/guides/{s}"><strong>{esc(g["h1"])}</strong><span>{esc(g["description"][:120])}…</span></a>')
    return '<div class="grid-3">' + "".join(cards) + "</div>"


VIDEO_UPLOAD = datetime.fromtimestamp(1788708219, tz=timezone.utc).date().isoformat()
VIDEO_LD = {
    "@type": "VideoObject", "@id": DOMAIN + "/#video",
    "name": "How online ELDT training works with ELDT Training",
    "description": "A short animated overview of Entry-Level Driver Training (ELDT): why new CDL drivers need it, how online theory training works, and how completion is reported to the FMCSA Training Provider Registry.",
    "thumbnailUrl": DOMAIN + "/assets/img/eldt-video-poster.jpg",
    "contentUrl": DOMAIN + "/assets/video/eldt-training-overview.mp4",
    "uploadDate": VIDEO_UPLOAD, "duration": "PT1M32S", "publisher": {"@id": DOMAIN + "/#organization"},
}


def video_block():
    return """<div class="video-wrap"><video controls playsinline preload="none" poster="/assets/img/eldt-video-poster.webp" width="700" height="362" data-track="ELDT overview" aria-label="How online ELDT training works">
<source src="/assets/video/eldt-training-overview.mp4" type="video/mp4">
Your browser does not support video. <a href="/assets/video/eldt-training-overview.mp4">Download the ELDT overview video</a>.
</video></div>"""


def shortcode(name, arg):
    if name == "courses":
        slugs = [s.strip() for s in arg.split(",") if s.strip()] if arg and arg != "all" else None
        return course_grid(slugs, list_name="Guide courses")
    if name == "cta":
        return cta_band(BY_SLUG.get(arg)) if arg else cta_band()
    if name == "eldt-table":
        return eldt_table()
    if name == "states":
        return state_grid()
    if name == "guides":
        return guide_cards([s.strip() for s in arg.split(",")])
    if name == "video":
        return video_block()
    return ""


# ---------------------------------------------------------------- content loading
def split_faq(body):
    m = re.search(r"^##\s+(Frequently asked questions.*|FAQs?.*)$", body, re.M | re.I)
    if not m:
        return body, []
    main, rest = body[:m.start()], body[m.end():]
    faqs = []
    for block in re.split(r"^###\s+", rest, flags=re.M)[1:]:
        q, _, a = block.partition("\n")
        a = a.strip()
        faqs.append((q.strip(), md.to_html(a, shortcode)))
    return main, faqs


def load_guides():
    for f in sorted(glob.glob(os.path.join(HERE, "content", "guides", "*.md"))):
        slug = os.path.basename(f)[:-3]
        meta, body = md.parse_front_matter(open(f).read())
        meta["slug"] = slug
        meta["body"] = body
        meta.setdefault("h1", meta.get("title"))
        GUIDES[slug] = meta


def reading_time(text):
    return max(2, math.ceil(len(re.findall(r"\w+", text)) / 225))


def toc_html(heads):
    items = [(lvl, hid, txt) for lvl, hid, txt in heads if lvl == 2]
    if len(items) < 3:
        return ""
    return '<nav class="toc" aria-label="On this page"><strong>On this page</strong><ol>' + "".join(
        f'<li><a href="#{hid}">{esc(txt)}</a></li>' for _, hid, txt in items) + "</ol></nav>"


def side_courses(slugs):
    cs = [BY_SLUG[s] for s in slugs if s in BY_SLUG] or COURSES[:3]
    main = cs[0]
    rows = "".join(f'<div class="mini-price"><a href="/products/{c["handle"]}">{esc(c["short"])}</a><b>{money(c["price"])}</b></div>' for c in COURSES)
    return f"""<div class="side-card cta"><h3>{esc(main['short'])} ELDT course</h3><p>{esc(main['card_sub'])}. {main['hours']} hour{'s' if main['hours'] != 1 else ''}, self-paced, reported to the FMCSA TPR.</p>
<p style="margin:0 0 12px"><span class="price" style="color:#9be15d;font-size:2rem">{money(main['price'])}</span></p>
<a class="btn btn-green btn-block" href="/checkout?item={main['slug']}">Enroll Now</a></div>
<div class="side-card"><h3>All ELDT courses</h3>{rows}</div>"""


# ---------------------------------------------------------------- page builders
def build_home():
    faqs = [
        ("What is ELDT?", "ELDT (Entry-Level Driver Training) is a set of federal training requirements established by the Federal Motor Carrier Safety Administration (FMCSA) in 49 CFR Part 380 for individuals seeking a commercial driver's license (CDL) or certain CDL endorsements for the first time. It took effect on February 7, 2022."),
        ("Who needs to complete ELDT?", "<p>ELDT applies to individuals who are:</p><ul><li>Obtaining a <a href=\"/products/entry-level-driver-training-eldt-class-a\">Class A CDL</a> for the first time</li><li>Obtaining a <a href=\"/products/entry-level-driver-training-eldt-class-b\">Class B CDL</a> for the first time</li><li><a href=\"/products/entry-level-driver-training-eldt-class-b-to-a-upgrade\">Upgrading from a Class B to a Class A CDL</a></li><li>Obtaining a <a href=\"/products/cdl-entry-level-driver-training-eldt-passenger-p-endorsement\">Passenger (P) endorsement</a> for the first time</li><li>Obtaining a <a href=\"/products/cdl-entry-level-driver-training-eldt-school-bus-s-endorsement\">School Bus (S) endorsement</a> for the first time</li><li>Obtaining a <a href=\"/products/cdl-entry-level-driver-training-eldt-hazmat-h-endorsement\">Hazardous Materials (H) endorsement</a> for the first time</li></ul>"),
        ("What training must an entry-level driver complete before the CDL skills or knowledge test?", "<p>To be eligible to take the Class A or Class B CDL skills test, the S or P skills test, or the H knowledge test, applicants must complete the applicable entry-level driver training from a <a href=\"/guides/training-provider-registry\">registered training provider</a>. Class A, Class B, P, and S require both theory and behind-the-wheel training; H requires theory only.</p>" + eldt_table()),
        ("When did the ELDT requirements take effect?", "The federal ELDT requirements took effect on February 7, 2022. They are not retroactive: drivers who already held the applicable CDL or endorsement before that date do not need ELDT for it."),
        ("Can I complete ELDT training online?", "Yes, for the theory portion. Theory may be completed online with any provider listed on the FMCSA Training Provider Registry (TPR). For Class A, Class B, P, and S, behind-the-wheel training must still be completed in a vehicle with a qualified, TPR-registered instructor."),
        ("How much does online ELDT cost here?", "Class A is $129.99, Class B is $119.99, the Class B to A upgrade is $99.99, Hazmat (H) is $69.99, Passenger (P) and School Bus (S) are $59.99 each, the X endorsement course is $129.99, and the Tanker (N) course is $49.99."),
        ("How fast is my completion reported to the FMCSA?", "Federal rules give providers until midnight of the second business day after you finish. We submit your completion to the Training Provider Registry as soon as you pass the final theory assessment with 80% or higher."),
        ("Is the course available in Spanish?", "Not currently. Our ELDT courses are available in English only, with audio playback that reads each lesson aloud."),
    ]
    review = "Great ELDT theory course! Everything was clear and well organized, and it made getting my certification straightforward from start to finish."
    feat_icons = {
        "self": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>',
        "flex": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12a8 8 0 0 1 14-5.3M20 12a8 8 0 0 1-14 5.3"/><path d="M18 3v4h-4M6 21v-4h4"/></svg>',
        "support": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/></svg>',
        "mobile": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/></svg>',
        "quiz": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3 8-8"/><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"/></svg>',
        "progress": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/></svg>',
    }
    features = [
        ("self", "Self-Paced Learning", "Learn at your own pace, with the flexibility to revisit lessons as needed until you feel confident in your knowledge."),
        ("flex", "Flexibility", "Access your lessons whenever it suits you. No classroom pressure and no class schedule to meet."),
        ("support", "Dedicated Support", f"Contact us by phone at {PHONE} or by email, and our support team will be ready to assist you."),
        ("mobile", "Mobile-Compatible", "On-the-go learning with a mobile-friendly platform. Access your course from any device with an internet connection."),
        ("quiz", "Interactive Quizzes", "Quizzes reinforce each lesson so you are ready for the final theory assessment (80% to pass)."),
        ("progress", "Progress Tracking", "Your progress saves automatically, so you can pick up exactly where you left off."),
    ]
    feat_html = "".join(f'<div class="feature"><div class="ico">{feat_icons[k]}</div><div><h3>{t}</h3><p>{d}</p></div></div>' for k, t, d in features)
    body = f"""
<section class="hero">
  <picture>
    <source type="image/webp" srcset="/assets/img/eldt-hero-semi-truck-768.webp 768w, /assets/img/eldt-hero-semi-truck-1200.webp 1200w, /assets/img/eldt-hero-semi-truck-1920.webp 1920w" sizes="100vw">
    <img class="hero-bg" src="/assets/img/eldt-hero-semi-truck-1600.jpg" alt="Semi truck driving on a highway at night" width="1600" height="897" fetchpriority="high">
  </picture>
  <div class="wrap hero-inner">
    <div>
      <div class="hero-badge">
        <img src="/assets/img/fmcsa-compliant-badge.webp" alt="FMCSA Training Provider compliant badge" width="80" height="74">
        <span><span class="t1">Registered FMCSA Training Provider</span><span class="t2">Federal Motor Carrier Safety Administration Provider</span></span>
      </div>
      <h1>Online ELDT Training for Your CDL: <span class="accent">FMCSA-Compliant Theory Courses</span></h1>
      <p class="hero-lead">Complete your federally required Entry-Level Driver Training (ELDT) theory online for a Class A or Class B CDL, a B-to-A upgrade, or the Hazmat, Passenger, School Bus, Tanker, and X endorsements. Our ELDT courses are submitted to the FMCSA Training Provider Registry (TPR) upon completion.</p>
      <div class="hero-actions"><a class="btn btn-white btn-lg" href="/collections/all">Enroll Now</a><a class="btn btn-orange btn-lg" href="#which-course">Which course do I need?</a></div>
      <ul class="hero-trust"><li>✔ From $49.99</li><li>✔ Start instantly</li><li>✔ All 50 states + DC</li><li>✔ Reported to FMCSA</li></ul>
    </div>
    <div class="hero-side">
      <div class="review-card"><img src="/assets/img/cdl-driver-avatar.webp" alt="Smiling CDL driver giving a thumbs up from a truck cab" width="74" height="74"><div><div class="stars" aria-label="5 out of 5 stars">★★★★★</div><p>{review}</p></div></div>
      <div class="feature-box">
        <h2>America's #1 Online ELDT Training Program</h2>
        <ul class="checklist"><li>Immediate Reporting To FMCSA</li><li>Audio Playback: Listen as the Course is Read to You</li><li>Start Your Course Instantly</li><li>Complete on Any Device, Anytime</li><li>Only Available in English</li></ul>
      </div>
    </div>
  </div>
</section>

<div class="notice"><div class="wrap">After completing your online ELDT course, <strong>first-time applicants must obtain Behind-the-Wheel (BTW) training</strong> from an authorized instructor before taking the CDL skills test. If this is not completed, the FMCSA will not be able to access your training records.</div></div>

<section class="section" id="courses">
  <div class="wrap">
    <div class="section-head"><h2>Courses We Offer</h2><p>Every course is an FMCSA-compliant online theory course built on the curricula in 49 CFR Part 380. Pick the license or endorsement you are applying for.</p></div>
    {course_grid(list_name="Homepage courses")}
  </div>
</section>

<section class="section section-soft" id="what-is-eldt">
  <div class="wrap-narrow">
    <span class="eyebrow">ELDT in 60 seconds</span>
    <h2>What is ELDT training?</h2>
    <div class="answer-box"><span class="label">Quick answer</span><p><strong>ELDT (Entry-Level Driver Training) is the FMCSA's federal minimum training standard for new commercial drivers.</strong> Since February 7, 2022, anyone getting a Class A or Class B CDL for the first time, upgrading from Class B to Class A, or adding a first-time Hazmat (H), Passenger (P), or School Bus (S) endorsement must complete training from a provider on the FMCSA Training Provider Registry before the state will let them test.</p></div>
    <p>ELDT has two parts. <strong>Theory</strong> is classroom-style knowledge training that can be completed online; you must score at least 80% on the final assessment. <strong>Behind-the-wheel (BTW)</strong> training happens in a real truck or bus with a qualified instructor and is required for Class A, Class B, P, and S (not H). There is no minimum number of hours for either part. Your training provider reports each completed part to the Training Provider Registry, and your state driver licensing agency checks that record before your skills test (or before the H knowledge test).</p>
    <p><a href="/guides/what-is-eldt">Read the complete guide to ELDT →</a></p>
  </div>
</section>

<section class="section" id="which-course">
  <div class="wrap">
    <div class="section-head"><h2>Which ELDT course do I need?</h2><p>Use the license or endorsement you are applying for. If you need more than one (for example, Class B plus Passenger and School Bus for a school bus job), you need each course.</p></div>
    {eldt_table()}
  </div>
</section>

<section class="section section-soft" id="states">
  <div class="wrap">
    <div class="section-head"><h2>Pick Your State</h2><p>ELDT is a federal rule, so our online theory courses are accepted in every state. See how ELDT and CDL testing work where you live.</p></div>
    {state_picker()}
  </div>
</section>

<section class="section" id="why">
  <div class="wrap why">
    <div>
      <h2 class="why-title">Why Choose ELDT Training.us?</h2>
      {video_block()}
    </div>
    <div>
      <h2>Start Your ELDT Certification Journey Today</h2>
      <p>Follow the steps below to begin your journey to a new career.</p>
      <ol class="steps">
        <li><span class="num">01.</span><div><h3>Quick and Easy Registration</h3><p>Sign up for our online course in just a few minutes and start immediately. Skip the hassle of commuting or waiting for a class to start.</p></div></li>
        <li><span class="num">02.</span><div><h3>Learn at Your Pace, Anywhere</h3><p>Access your course anytime, anywhere, on any device. Progress is saved automatically, so you can pick up where you left off.</p></div></li>
        <li><span class="num">03.</span><div><h3>Complete The Course</h3><p>Pass the final assessment and we'll notify the FMCSA Training Provider Registry of your completion. Then you're set to start your behind-the-wheel training.</p></div></li>
      </ol>
    </div>
  </div>
</section>

<section class="section section-soft">
  <div class="wrap">
    <div class="section-head"><h2>Why We're the Right Choice</h2><p>Elevate your learning experience through expertly designed training solutions.</p></div>
    <div class="grid-2">
      <div class="info-card"><h3>Fully Compliant with Federal Standards</h3><p>Our courses are FMCSA compliant and fulfill the Entry-Level Driver Training (ELDT) theory requirements in 49 CFR Part 380.</p></div>
      <div class="info-card"><h3>Reliable and Easy</h3><p>Built to help you meet ELDT requirements quickly while giving you the knowledge you need on the road and on your CDL tests.</p></div>
      <div class="info-card"><h3>Designed by Industry Experts</h3><p>Our curriculum is developed by seasoned instructors with decades of hands-on commercial driving and safety training experience.</p></div>
      <div class="info-card"><h3>Affordable Pricing</h3><p>Courses start at $49.99, with Class A at $129.99. No hidden fees for reporting your completion to the FMCSA.</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Course Features</h2></div>
    <div class="grid-3">{feat_html}</div>
  </div>
</section>

<section class="section section-soft">
  <div class="wrap">
    <div class="section-head"><h2>ELDT &amp; CDL Guides</h2><p>Plain-English answers to the questions new drivers ask most.</p></div>
    {guide_cards(["what-is-eldt", "eldt-requirements", "how-to-get-a-cdl", "eldt-cost", "hazmat-endorsement", "training-provider-registry", "how-long-is-eldt-training", "cdl-endorsements", "class-a-vs-class-b-cdl"])}
    <p class="center mt-2"><a class="btn btn-outline" href="/guides/">Browse all guides</a></p>
  </div>
</section>

<section class="section" id="faq">
  <div class="wrap">
    <div class="section-head"><h2>FAQs</h2></div>
    {faq_html(faqs)}
    <p class="center mt-2"><a href="/pages/faq-training-entry-level-driver-must-complete">See all ELDT FAQs →</a></p>
  </div>
</section>
"""
    item_list = {"@type": "ItemList", "name": "Online ELDT courses", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": url("/products/" + c["handle"]), "name": c["name"]} for i, c in enumerate(COURSES)]}
    webpage = {"@type": "WebPage", "@id": DOMAIN + "/#webpage", "url": DOMAIN + "/", "name": "Online ELDT Training | FMCSA-Compliant CDL Theory Courses",
               "isPartOf": {"@id": DOMAIN + "/#website"}, "about": {"@id": DOMAIN + "/#organization"}, "primaryImageOfPage": OG_IMAGE,
               "video": {"@id": DOMAIN + "/#video"}, "dateModified": TODAY}
    preload = ('<link rel="preload" as="image" type="image/webp" imagesrcset="/assets/img/eldt-hero-semi-truck-768.webp 768w, '
               '/assets/img/eldt-hero-semi-truck-1200.webp 1200w, /assets/img/eldt-hero-semi-truck-1920.webp 1920w" imagesizes="100vw" fetchpriority="high">')
    write_page("/", "Online ELDT Training | FMCSA-Compliant CDL Theory Courses",
               "America's #1 online ELDT training. FMCSA-compliant Entry-Level Driver Training theory for Class A, Class B, Hazmat, Passenger & School Bus. Reported to the TPR.",
               body, schema=[webpage, item_list, VIDEO_LD, faq_ld([(q, md.strip_tags(a)) for q, a in faqs])], active="/", preload=preload, kind="home")
    TEXT_INDEX["/"] = "# Online ELDT Training (eldttraining.us)\n\n" + "\n\n".join(f"## {q}\n{md.strip_tags(a)}" for q, a in faqs)


def build_course(c):
    syl = SYLLABI[c["handle"]]
    modules = syl["modules"]
    lessons = sum(len(m["lessons"]) for m in modules) or len([m for m in modules if m["title"].lower().startswith("lesson")])
    mod_html = []
    for m in modules:
        n = len(m["lessons"])
        count = f'<span class="count">{n} lesson{"s" if n != 1 else ""}</span>' if n else ""
        topics = ("<p><strong>Key topics:</strong> " + esc(", ".join(m["topics"])) + "</p>") if m["topics"] else ""
        les = ("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in m["lessons"]) + "</ul>") if m["lessons"] else ""
        desc = "".join(f"<p>{esc(d)}</p>" for d in m["desc"])
        mod_html.append(f'<details class="module"><summary>{esc(m["title"])}{count}</summary><div class="body">{desc}{topics}{les}</div></details>')
    save_pct = round((1 - c["price"] / c["compare_at"]) * 100) if c.get("compare_at") else 0
    eldt_label = {"required": "Required by federal ELDT rule", "partial": "Meets the ELDT hazmat requirement", "not-federal": "Prepares you for the N knowledge test"}[c["eldt"]]
    n_only = c["eldt"] == "not-federal"  # Tanker (N): not an ELDT category, so nothing goes to the TPR
    tpr_badge = "✔ No TPR wait: test when ready" if n_only else "✔ Reported to FMCSA TPR"
    tpr_check = "No Training Provider Registry submission needed, so you can test when ready" if n_only else "Completion reported to the FMCSA Training Provider Registry"
    if n_only:
        tpr_step = ("<li><strong>No Training Provider Registry wait.</strong> The N endorsement is not part of the federal ELDT mandate, so there is nothing to submit "
                    "and nothing to wait for.</li>")
        test_step = "<li><strong>Take your state's N endorsement knowledge test</strong> at your licensing agency as soon as you feel ready.</li>"
    else:
        tpr_step = "<li><strong>We report your completion to the FMCSA Training Provider Registry</strong>, within the federal deadline of midnight on the second business day.</li>"
        test_step = (f"<li><strong>{('Complete behind-the-wheel training, then take your ' + esc(c['verify']) + '.') if c['btw'].startswith('Yes') else ('Take your ' + esc(c['verify']) + '.')}</strong> "
                     "Your state licensing agency checks the TPR before testing.</li>")
    faqs = list(c["faqs"])
    for q, ans in syl.get("faqs", []):
        faqs.append((q, " ".join(ans)))
    faqs.append(("What is your refund policy?", "You can cancel for a full refund within 30 days of purchase, unless 65% or more of the course has been completed or a certificate has been issued. See our refund policy for details."))
    related = [x for x in COURSES if x["slug"] != c["slug"]][:3]
    if c["slug"] in ("passenger-p",):
        related = [BY_SLUG["school-bus-s"], BY_SLUG["class-b"], BY_SLUG["hazmat-h"]]
    elif c["slug"] in ("school-bus-s",):
        related = [BY_SLUG["passenger-p"], BY_SLUG["class-b"], BY_SLUG["class-a"]]
    elif c["slug"] in ("hazmat-h", "tanker-n"):
        related = [BY_SLUG["hazmat-tanker-x"], BY_SLUG["class-a"], BY_SLUG["tanker-n" if c["slug"] == "hazmat-h" else "hazmat-h"]]
    elif c["slug"] == "hazmat-tanker-x":
        related = [BY_SLUG["hazmat-h"], BY_SLUG["tanker-n"], BY_SLUG["class-a"]]
    rel_guides = [c["guide"], "what-is-eldt", "eldt-theory-vs-behind-the-wheel", "training-provider-registry", "eldt-cost", "how-long-is-eldt-training"]
    rel_guides = [g for g in dict.fromkeys(rel_guides) if g in GUIDES][:6]
    lesson_txt = f"{lessons} lessons" if lessons else f"{len(modules)} parts"
    crumbs = [("Home", "/"), ("Courses", "/collections/all"), (c["short"], "/products/" + c["handle"])]
    ga_item = json.dumps({"item_id": c["sku"], "item_name": c["name"], "item_brand": BRAND, "item_category": "ELDT Theory Course", "price": c["price"], "quantity": 1})
    who = "".join(f"<li>{md.inline(w)}</li>" for w in c["who"])
    intro = "".join(f"<p>{md.inline(p)}</p>" for p in c["intro"])
    body = f"""
<div class="wrap">{breadcrumb_html(crumbs)}</div>
<div class="wrap product-top">
  <div>
    <div class="badges"><span class="badge green">{tpr_badge}</span><span class="badge">100% online</span><span class="badge">Audio playback</span><span class="badge orange">{esc(eldt_label)}</span></div>
    <h1>{esc(c['h1'])}</h1>
    {intro}
    <dl class="key-facts">
      <div><dt>Price</dt><dd>{money(c['price'])}</dd></div>
      <div><dt>Duration</dt><dd>{c['hours']} hour{'s' if c['hours'] != 1 else ''}, self-paced</dd></div>
      <div><dt>Content</dt><dd>{lesson_txt}</dd></div>
      <div><dt>Passing score</dt><dd>80% final assessment</dd></div>
      <div><dt>Verified before</dt><dd>{esc(c['verify'])}</dd></div>
      <div><dt>Behind-the-wheel</dt><dd>{esc(c['btw'].split(',')[0])}</dd></div>
      <div><dt>Access</dt><dd>3-month completion, 1-year access</dd></div>
      <div><dt>Language</dt><dd>English (with audio)</dd></div>
    </dl>
  </div>
  <aside class="buy-box" aria-label="Enroll">
    <div class="price-row" style="justify-content:flex-start"><span class="price">{money(c['price'])}</span><span class="price-was">{money(c['compare_at'])}</span>{f'<span class="save">Save {save_pct}%</span>' if save_pct else ''}</div>
    <p class="small" style="margin-top:-6px">{esc(c['name'])}</p>
    <a class="btn btn-dark btn-lg btn-block" href="/checkout?item={c['slug']}">Enroll Now</a>
    <ul class="checklist" style="margin-top:16px">
      <li>Start instantly after checkout</li>
      <li>{tpr_check}</li>
      <li>Audio playback reads every lesson aloud</li>
      <li>Works on phone, tablet, or computer</li>
      <li>30-day refund policy</li>
    </ul>
    <p class="small">Questions? Call <a href="tel:{PHONE_TEL}">{PHONE}</a></p>
  </aside>
</div>

<section class="section-sm">
  <div class="wrap article-layout" style="padding-top:0">
    <div class="prose">
      <h2 id="who-needs-it">Who needs this course?</h2>
      <ul>{who}</ul>
      <div class="callout info"><p><strong>You do not need this course if:</strong> {md.inline(c['not_for'])}</p></div>

      <h2 id="syllabus">Course syllabus</h2>
      <p>The {esc(c['short'])} course contains {lesson_txt} with quizzes along the way and a final theory assessment. Lessons must be completed in order.</p>
      {''.join(mod_html)}

      <h2 id="how-it-works">How it works after you enroll</h2>
      <ol>
        <li><strong>Enroll and get your login.</strong> Your account is created at checkout and login details are emailed to you right away.</li>
        <li><strong>Complete the lessons at your own pace.</strong> Use audio playback, pause anytime, and switch between devices.</li>
        <li><strong>Pass the final theory assessment with 80% or higher.</strong> You can review the material before you test.</li>
        {tpr_step}
        {test_step}
      </ol>

      <h2 id="eldt-requirements">Where this course fits in the ELDT rules</h2>
      {eldt_table()}

      <h2 id="faq">Frequently asked questions</h2>
      {faq_html(faqs)}

      <h2 id="related-courses">Related courses</h2>
      {course_grid([r['slug'] for r in related], list_name='Related courses')}

      <h2 id="related-guides">Helpful guides</h2>
      {guide_cards(rel_guides)}
    </div>
    <aside class="sidebar"><div class="sticky">
      <div class="side-card cta"><h3>Ready to start?</h3><p>{esc(c['short'])} ELDT theory · {c['hours']} hrs · {money(c['price'])}</p><a class="btn btn-green btn-block" href="/checkout?item={c['slug']}">Enroll Now</a></div>
      <div class="side-card"><h3>On this page</h3><ul><li><a href="#who-needs-it">Who needs it</a></li><li><a href="#syllabus">Syllabus</a></li><li><a href="#how-it-works">How it works</a></li><li><a href="#eldt-requirements">ELDT rules</a></li><li><a href="#faq">FAQ</a></li></ul></div>
      <div class="side-card"><h3>Find your state</h3>{state_select()}</div>
    </div></aside>
  </div>
</section>
<script type="application/json" id="ga-view-item">{ga_item}</script>
"""
    offer = {"@type": "Offer", "url": url("/products/" + c["handle"]), "price": f"{c['price']:.2f}", "priceCurrency": "USD",
             "availability": "https://schema.org/InStock", "priceValidUntil": f"{YEAR + 1}-12-31", "category": "Paid",
             "seller": {"@id": DOMAIN + "/#organization"},
             "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "US", "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                                         "merchantReturnDays": 30, "returnMethod": "https://schema.org/ReturnByMail", "returnFees": "https://schema.org/FreeReturn"}}
    course_ld = {
        "@type": "Course", "@id": url("/products/" + c["handle"]) + "#course", "name": c["name"], "description": c["description"],
        "url": url("/products/" + c["handle"]), "provider": {"@id": DOMAIN + "/#organization"}, "inLanguage": "en",
        "courseCode": c["sku"], "isAccessibleForFree": False, "educationalLevel": "Beginner", "teaches": [m["title"].split(": ", 1)[-1] for m in modules if m["title"].lower().startswith(("module", "lesson"))],
        "educationalCredentialAwarded": ("Tank vehicle (N) endorsement training completion" if c["eldt"] == "not-federal"
                                          else "ELDT theory training certification submitted to the FMCSA Training Provider Registry"),
        "about": ["Entry-Level Driver Training", c["short"]],
        "offers": [{"@type": "Offer", "category": "Paid", "price": f"{c['price']:.2f}", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": url("/products/" + c["handle"])}],
        "hasCourseInstance": [{"@type": "CourseInstance", "courseMode": "Online", "courseWorkload": f"PT{c['hours']}H", "inLanguage": "en",
                               "courseSchedule": {"@type": "Schedule", "repeatFrequency": "P1D", "repeatCount": 90}}],
        "image": OG_IMAGE,
    }
    product_ld = {"@type": "Product", "@id": url("/products/" + c["handle"]) + "#product", "name": c["name"], "description": c["description"],
                  "sku": c["sku"], "mpn": str(c["id"]), "brand": {"@type": "Brand", "name": BRAND}, "image": OG_IMAGE, "category": "Online Courses > Driver Training",
                  "offers": offer}
    write_page("/products/" + c["handle"], c["title"], c["description"], body,
               schema=[course_ld, product_ld, faq_ld([(q, md.strip_tags(a)) for q, a in faqs]), breadcrumb_ld(crumbs)],
               og_type="product", active="/collections/all", kind="course")
    TEXT_INDEX["/products/" + c["handle"]] = (f"# {c['name']}\n\nPrice: {money(c['price'])} (regular {money(c['compare_at'])}) · Duration: {c['hours']} hours · "
                                              f"{lesson_txt} · 80% passing score · Verified before: {c['verify']} · Behind-the-wheel: {c['btw']}\n\n"
                                              + "\n\n".join(md.strip_tags(md.inline(p)) for p in c["intro"]) + "\n\nWho needs it:\n" +
                                              "\n".join("- " + w for w in c["who"]) + "\n\nSyllabus:\n" +
                                              "\n".join("- " + m["title"] + (": " + "; ".join(m["lessons"]) if m["lessons"] else "") for m in modules) +
                                              "\n\nEnroll: " + url("/checkout?item=" + c["slug"]))


def build_collection():
    rows = "".join(
        f'<tr><td><a href="/products/{c["handle"]}">{esc(c["short"])}</a></td><td>{esc(c["verify"])}</td>'
        f'<td class="{"yes" if c["btw"].startswith("Yes") else "no"}">{esc(c["btw"].split(",")[0])}</td><td>{c["hours"]} hrs</td><td><strong>{money(c["price"])}</strong></td>'
        f'<td><a class="btn btn-dark btn-sm" href="/checkout?item={c["slug"]}">Enroll</a></td></tr>' for c in COURSES)
    faqs = [
        ("Which ELDT course should I take?", "Match the course to the license or endorsement you are applying for: Class A for tractor-trailers and combination vehicles, Class B for straight trucks and buses, the B-to-A upgrade if you already hold a Class B, and the H, P, or S course for each first-time endorsement."),
        ("Do I need more than one course?", "Possibly. Each license class and each ELDT endorsement is a separate training type. A new school bus driver, for example, typically needs Class B, Passenger (P), and School Bus (S)."),
        ("Are these courses accepted in my state?", "Yes. ELDT is a federal requirement and every state checks the same FMCSA Training Provider Registry. Online theory from a registered provider counts nationwide."),
        ("Do the courses include behind-the-wheel training?", "No. These are theory courses. Class A, Class B, P, and S also require behind-the-wheel training with a registered BTW provider, such as a CDL school or a carrier's training program."),
    ]
    body = f"""
<div class="wrap">{breadcrumb_html([("Home", "/"), ("Courses", "/collections/all")])}</div>
<section class="page-hero"><div class="wrap"><h1>Online ELDT Courses: FMCSA-Compliant CDL Theory Training</h1>
<p class="lead">All eight of our online Entry-Level Driver Training courses in one place. Each one is self-paced, includes audio playback, and is reported to the FMCSA Training Provider Registry when you pass.</p></div></section>
<section class="section"><div class="wrap">{course_grid(list_name="All courses")}</div></section>
<section class="section section-soft"><div class="wrap">
  <div class="section-head"><h2>Compare ELDT courses</h2><p>Duration, price, and what each course unlocks.</p></div>
  <div class="table-wrap"><table><thead><tr><th scope="col">Course</th><th scope="col">Lets you take</th><th scope="col">BTW also required?</th><th scope="col">Duration</th><th scope="col">Price</th><th scope="col"><span class="visually-hidden">Enroll</span></th></tr></thead><tbody>{rows}</tbody></table></div>
</div></section>
<section class="section"><div class="wrap-narrow prose">
  <h2>How to choose the right course</h2>
  <ul>
    <li><strong>Tractor-trailer, OTR, regional, flatbed, or tanker trucking:</strong> <a href="/products/entry-level-driver-training-eldt-class-a">Class A</a>.</li>
    <li><strong>Dump truck, box truck, cement mixer, garbage truck, or bus:</strong> <a href="/products/entry-level-driver-training-eldt-class-b">Class B</a> (add P for buses).</li>
    <li><strong>Already hold a Class B and want tractor-trailer work:</strong> <a href="/products/entry-level-driver-training-eldt-class-b-to-a-upgrade">Class B to A Upgrade</a>.</li>
    <li><strong>Hauling placarded hazardous materials:</strong> <a href="/products/cdl-entry-level-driver-training-eldt-hazmat-h-endorsement">Hazmat (H)</a>, or <a href="/products/entry-level-driver-training-eldt-hazmat-and-tank-vehicle-endorsement">X (Hazmat + Tanker)</a> for hazmat in tanks.</li>
    <li><strong>Driving a bus or vehicle designed for 16+ passengers:</strong> <a href="/products/cdl-entry-level-driver-training-eldt-passenger-p-endorsement">Passenger (P)</a>.</li>
    <li><strong>Driving a school bus:</strong> <a href="/products/cdl-entry-level-driver-training-eldt-passenger-p-endorsement">Passenger (P)</a> + <a href="/products/cdl-entry-level-driver-training-eldt-school-bus-s-endorsement">School Bus (S)</a>.</li>
    <li><strong>Non-hazmat liquid tankers:</strong> <a href="/products/cdl-entry-level-driver-training-eldt-tanker-n-endorsement">Tanker (N)</a>.</li>
  </ul>
  {eldt_table()}
  <h2>Frequently asked questions</h2>
  {faq_html(faqs)}
</div></section>
"""
    item_list = {"@type": "ItemList", "name": "Online ELDT courses", "numberOfItems": len(COURSES), "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "item": {"@type": "Course", "name": c["name"], "url": url("/products/" + c["handle"]), "description": c["description"],
                                                          "provider": {"@id": DOMAIN + "/#organization"},
                                                          "offers": {"@type": "Offer", "price": f"{c['price']:.2f}", "priceCurrency": "USD", "category": "Paid"},
                                                          "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "Online", "courseWorkload": f"PT{c['hours']}H"}}}
        for i, c in enumerate(COURSES)]}
    write_page("/collections/all", "All Online ELDT Courses | Class A, B, Hazmat, P, S, N, X",
               "Compare all 8 online ELDT theory courses: Class A ($129.99), Class B, B-to-A upgrade, Hazmat, Passenger, School Bus, Tanker and X. FMCSA TPR reporting included.",
               body, schema=[item_list, faq_ld(faqs), breadcrumb_ld([("Home", "/"), ("Courses", "/collections/all")])], active="/collections/all", kind="collection")


def build_state(s):
    ab = s["abbr"].lower()
    name = s["name"]
    agency = s["agency"]
    agency_short = re.sub(r".*\(([^)]+)\).*", r"\1", agency) if "(" in agency else agency
    the = "" if name.startswith("District") else ""
    in_name = "the District of Columbia" if s["abbr"] == "DC" else name
    path = f"/pages/state/{ab}"
    crumbs = [("Home", "/"), ("ELDT by State", "/pages/state"), (name, path)]
    cities = ", ".join(s["cities"][:-1]) + (" and " + s["cities"][-1] if len(s["cities"]) > 1 else s["cities"][0])
    roads = ", ".join(s["roads"])
    neighbors = [BY_ABBR[n] for n in s["neighbors"] if n in BY_ABBR]
    nb_html = ('<div class="pill-links">' + "".join(f'<a href="/pages/state/{n["abbr"].lower()}">ELDT in {esc(n["name"])}</a>' for n in neighbors) + "</div>") if neighbors else ""
    faqs = [
        (f"Can I take ELDT theory training online in {name}?",
         f"Yes. ELDT is a federal requirement under 49 CFR Part 380, and theory training may be completed online with any provider listed on the FMCSA Training Provider Registry. {agency_short} checks the same national registry as every other state, so online theory from ELDT Training counts for a {name} CDL."),
        (f"Does {agency_short} verify my ELDT before the skills test?",
         f"Yes. Before administering the Class A or Class B skills test, the P or S skills test, or the H knowledge test, {agency_short} must confirm through the Training Provider Registry that you completed the required ELDT."),
        (f"Do I need behind-the-wheel training in {name}?",
         "For Class A, Class B, Passenger (P), and School Bus (S), yes. Behind-the-wheel training must be completed with a TPR-registered provider in a representative vehicle. The Hazmat (H) endorsement is theory only."),
        (f"Can I do behind-the-wheel training outside {in_name}?",
         f"Federal rules allow you to train with any registered BTW provider, but a provider giving in-person training must meet the rules of the state where the training takes place, and your home state may add requirements. Confirm with {agency_short} before you book out-of-state BTW."),
        ("How quickly will my completion show up?",
         "Training providers must submit your completion to the TPR by midnight of the second business day after you finish. We submit as soon as you pass the final assessment."),
    ]
    note = f'<div class="callout info"><p><strong>{esc(name)} note:</strong> {esc(s["note"])}</p></div>' if s.get("note") else ""
    body = f"""
<div class="wrap">{breadcrumb_html(crumbs)}</div>
<section class="page-hero"><div class="wrap"><span class="eyebrow">{esc(name)} CDL applicants</span>
<h1>ELDT Training in {esc(name)}: Online CDL Theory Courses</h1>
<p class="lead">Complete your federally required Entry-Level Driver Training theory online and get ready for your {esc(name)} CDL skills test. Our courses meet FMCSA requirements and are reported to the Training Provider Registry that {esc(agency_short)} checks before testing.</p>
<div class="hero-actions" style="margin:14px 0 0"><a class="btn btn-dark" href="#courses">View Courses</a><a class="btn btn-outline" href="/checkout?item=class-a">Enroll in Class A</a></div></div></section>
<div class="wrap article-layout">
  <div class="prose">
    <div class="answer-box"><span class="label">Quick answer</span><p>Yes, you can complete ELDT theory online in {esc(in_name)}. If you are getting a Class A or Class B CDL for the first time, upgrading from B to A, or adding a first-time H, P, or S endorsement, you must finish ELDT with an FMCSA-registered provider before {esc(agency_short)} will give you the skills test (or the H knowledge test). Theory can be done online; Class A, B, P, and S also need behind-the-wheel training.</p></div>
    <dl class="key-facts">
      <div><dt>Licensing agency</dt><dd><a href="{s['url']}" rel="noopener">{esc(agency_short)}</a></dd></div>
      <div><dt>ELDT in effect since</dt><dd>February 7, 2022</dd></div>
      <div><dt>Online theory accepted?</dt><dd>Yes, from TPR providers</dd></div>
      <div><dt>Interstate CDL minimum age</dt><dd>21 (federal)</dd></div>
    </dl>
    {note}
    <h2 id="steps">How to get your CDL in {esc(name)} with ELDT</h2>
    <ol>
      <li><strong>Meet the basic requirements.</strong> You need a valid {esc(name)} driver's license, proof of identity and residency, and a DOT medical examiner's certificate from a provider on the FMCSA National Registry. Federal rules require you to be 21 to drive across state lines; most states allow intrastate-only CDLs from age 18.</li>
      <li><strong>Get your commercial learner's permit (CLP).</strong> Pass the general knowledge test (plus any endorsement knowledge tests) with {esc(agency)}. You must hold the CLP for at least 14 days before the skills test.</li>
      <li><strong>Complete ELDT theory online.</strong> Take the <a href="/products/entry-level-driver-training-eldt-class-a">Class A</a> or <a href="/products/entry-level-driver-training-eldt-class-b">Class B</a> course (and any <a href="/guides/cdl-endorsements">endorsement</a> courses), score 80% or higher, and we report it to the Training Provider Registry. You can do this before or after getting your CLP.</li>
      <li><strong>Complete behind-the-wheel training.</strong> Train on a range and on public roads with a TPR-registered BTW provider such as a CDL school or a carrier's training program.</li>
      <li><strong>Take the CDL skills test.</strong> {esc(agency_short)} confirms your ELDT records in the TPR, then you take the vehicle inspection, basic control, and road test.</li>
    </ol>
    <h2 id="courses">Which ELDT course do {esc(name)} drivers need?</h2>
    {eldt_table()}
    {course_grid(list_name=f"{name} courses")}
    <h2 id="driving-in-{ab}">Commercial driving in {esc(name)}</h2>
    <p>{esc(s['industry'])} Major freight routes include {esc(roads)}, and the largest CDL job markets are in and around {esc(cities)}.</p>
    <p>Whether you plan to drive regionally inside {esc(in_name)} or run interstate routes, the federal ELDT requirement is the same: finish theory and (where required) behind-the-wheel training with a registered provider before your test.</p>
    <h2 id="faq">Frequently asked questions</h2>
    {faq_html(faqs)}
    {f'<h2 id="nearby">Nearby states</h2>{nb_html}' if nb_html else ''}
    <p class="small mt-2">State procedures, fees, and office locations change. Always confirm current requirements with <a href="{s['url']}" rel="noopener">{esc(agency)}</a>.</p>
  </div>
  <aside class="sidebar"><div class="sticky">{side_courses(["class-a"])}
  <div class="side-card"><h3>Popular guides</h3><ul><li><a href="/guides/how-to-get-a-cdl">How to get a CDL</a></li><li><a href="/guides/eldt-requirements">ELDT requirements</a></li><li><a href="/guides/cdl-permit-clp">CDL permit (CLP)</a></li><li><a href="/guides/eldt-theory-vs-behind-the-wheel">Theory vs behind-the-wheel</a></li><li><a href="/guides/how-much-does-it-cost-to-get-a-cdl">CDL cost</a></li></ul></div>
  </div></aside>
</div>
"""
    wp = {"@type": "WebPage", "@id": url(path) + "#webpage", "url": url(path), "name": f"ELDT Training in {name}",
          "about": {"@type": "State", "name": name}, "isPartOf": {"@id": DOMAIN + "/#website"}, "dateModified": TODAY}
    title = f"ELDT Training {name}: Online CDL Theory Course" if len(name) <= 12 else f"ELDT Training in {name} | Online CDL Theory"
    if len(title) > 62:
        title = f"{name} ELDT Training | Online CDL Theory"
    desc = f"Online ELDT theory training for {name} CDL applicants. FMCSA-compliant Class A, Class B, Hazmat, Passenger & School Bus courses, reported to the TPR that {agency_short} checks."
    if len(desc) > 160:
        desc = f"Online ELDT theory for {name} CDL applicants: FMCSA-compliant Class A, Class B, Hazmat, P & S courses reported to the Training Provider Registry."
    write_page(path, title, desc, body, schema=[wp, faq_ld(faqs), breadcrumb_ld(crumbs)], active="/pages/state", kind="state")


def build_state_index():
    rows = "".join(f'<tr><td><a href="/pages/state/{s["abbr"].lower()}">{esc(s["name"])}</a></td><td><a href="{s["url"]}" rel="noopener">{esc(s["agency"])}</a></td></tr>'
                   for s in sorted(STATES, key=lambda x: x["name"]))
    faqs = [
        ("Is ELDT different in each state?", "The core ELDT rules are federal and identical everywhere: the same curricula, the same Training Provider Registry, and the same test-verification step. States can add requirements, especially for behind-the-wheel training delivered within their borders, so always check with your licensing agency."),
        ("Can I use an online ELDT provider based in another state?", "Yes. Online theory training is not tied to a state. What matters is that the provider is listed on the FMCSA Training Provider Registry and reports your completion there."),
    ]
    body = f"""
<div class="wrap">{breadcrumb_html([("Home", "/"), ("ELDT by State", "/pages/state")])}</div>
<section class="page-hero"><div class="wrap"><h1>ELDT Training by State: Online CDL Theory in All 50 States</h1>
<p class="lead">We offer FMCSA-compliant ELDT training that meets your state's requirements, making it easy to get certified from anywhere. Choose your state for licensing-agency details, steps to your CDL, and local freight information.</p></div></section>
<section class="section"><div class="wrap">{state_picker(all_link=False)}</div></section>
<section class="section section-soft"><div class="wrap-narrow prose">
<h2>State CDL licensing agencies</h2>
<div class="table-wrap"><table><thead><tr><th scope="col">State</th><th scope="col">Agency that issues CDLs and checks ELDT</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Frequently asked questions</h2>{faq_html(faqs)}
</div></section>
<section class="section"><div class="wrap"><div class="section-head"><h2>Courses We Offer</h2></div>{course_grid(list_name="State index courses")}</div></section>
"""
    write_page("/pages/state", "ELDT Training by State | Online CDL Theory in All 50 States",
               "Find ELDT training requirements for your state. Online FMCSA-compliant CDL theory courses accepted in all 50 states, DC and Puerto Rico, with licensing agency links.",
               body, schema=[faq_ld(faqs), breadcrumb_ld([("Home", "/"), ("ELDT by State", "/pages/state")])], active="/pages/state", kind="state-index", also_index=True)


CATEGORIES = ["ELDT Basics", "Getting Your CDL", "CDL Endorsements", "Tests & Skills", "Careers & Employers"]


def build_guide(g):
    slug = g["slug"]
    path = f"/guides/{slug}"
    main, faqs = split_faq(g["body"])
    heads = []
    body_html = md.to_html(main, shortcode, heads)
    toc = toc_html(heads)
    if toc:
        if '<div class="answer-box">' in body_html:
            # insert TOC after the first answer box
            idx = body_html.find('<div class="answer-box">')
            depth, j = 0, idx
            while j < len(body_html):
                if body_html.startswith("<div", j):
                    depth += 1
                elif body_html.startswith("</div>", j):
                    depth -= 1
                    if depth == 0:
                        j += 6
                        break
                j += 1
            body_html = body_html[:j] + toc + body_html[j:]
        else:
            body_html = toc + body_html
    courses = [s.strip() for s in g.get("courses", "class-a").split(",") if s.strip()]
    related = [s.strip() for s in g.get("related", "").split(",") if s.strip() and s.strip() in GUIDES and s.strip() != slug]
    if len(related) < 3:
        related += [s for s, x in GUIDES.items() if x.get("category") == g.get("category") and s != slug and s not in related][:6 - len(related)]
    sources = [x.split("|", 1) for x in g.get("sources", "").split(";;") if "|" in x]
    src_html = ""
    if sources:
        src_html = '<div class="sources"><strong>Sources</strong><ol>' + "".join(
            f'<li><a href="{esc(u.strip())}" rel="noopener">{esc(t.strip())}</a></li>' for t, u in sources) + "</ol></div>"
    faq_block = f'<h2 id="faq">Frequently asked questions</h2>{faq_html(faqs)}' if faqs else ""
    updated = g.get("updated", TODAY)
    published = g.get("published", "2026-11-16")
    rt = reading_time(g["body"])
    crumbs = [("Home", "/"), ("Guides", "/guides/"), (g.get("crumb") or g["h1"], path)]
    body = f"""
<div class="wrap">{breadcrumb_html(crumbs)}</div>
<section class="page-hero"><div class="wrap"><span class="eyebrow">{esc(g.get('category', 'Guide'))}</span>
<h1>{esc(g['h1'])}</h1>
{f'<p class="lead">{md.inline(g["lead"])}</p>' if g.get('lead') else ''}
<div class="meta"><span>Updated <time datetime="{updated}">{datetime.fromisoformat(updated).strftime('%B %-d, %Y')}</time></span><span>{rt} min read</span><span>Reviewed by the ELDT Training curriculum team</span></div></div></section>
<div class="wrap article-layout">
  <article class="prose">
    {body_html}
    {faq_block}
    {src_html}
    <div class="author-box"><img src="/assets/img/favicon-32.png" alt="" width="56" height="56" loading="lazy"><div><strong>About ELDT Training</strong><br>ELDT Training (eldttraining.us) is a registered provider on the FMCSA Training Provider Registry offering online ELDT theory courses for Class A, Class B, and CDL endorsements. Guides are written and reviewed by our curriculum team against 49 CFR Parts 380 and 383 and FMCSA guidance. <a href="/pages/about-us">More about us</a>.</div></div>
  </article>
  <aside class="sidebar"><div class="sticky">{side_courses(courses)}
    <div class="side-card"><h3>Related guides</h3><ul>{''.join(f'<li><a href="/guides/{r}">{esc(GUIDES[r]["h1"])}</a></li>' for r in related[:6])}</ul></div>
  </div></aside>
</div>
<section class="section section-soft"><div class="wrap"><div class="section-head"><h2>Keep reading</h2></div>{guide_cards(related[:6])}</div></section>
"""
    article = {"@type": "Article", "@id": url(path) + "#article", "headline": g["h1"][:110], "description": g["description"],
               "datePublished": published, "dateModified": updated, "author": {"@id": DOMAIN + "/#organization"},
               "publisher": {"@id": DOMAIN + "/#organization"}, "image": OG_IMAGE, "mainEntityOfPage": url(path),
               "inLanguage": "en-US", "articleSection": g.get("category", "Guide"), "keywords": g.get("keyword", ""),
               "about": [{"@type": "Thing", "name": "Entry-Level Driver Training"}], "isAccessibleForFree": True}
    if sources:
        article["citation"] = [u.strip() for _, u in sources]
    schema = [article, breadcrumb_ld(crumbs)]
    if faqs:
        schema.append(faq_ld([(q, md.strip_tags(a)) for q, a in faqs]))
    write_page(path, g["title"], g["description"], body, schema=schema, og_type="article", active="/guides/", lastmod=updated, kind="guide")
    TEXT_INDEX[path] = f"# {g['h1']}\n\nURL: {url(path)}\nUpdated: {updated}\n\n" + md.to_text(g["body"])


def build_guides_hub():
    sections = []
    for cat in CATEGORIES:
        items = [(s, g) for s, g in GUIDES.items() if g.get("category") == cat]
        if not items:
            continue
        items.sort(key=lambda x: int(x[1].get("order", 50)))
        cards = "".join(f'<a class="link-card" href="/guides/{s}"><strong>{esc(g["h1"])}</strong><span>{esc(g["description"][:130])}…</span></a>' for s, g in items)
        sections.append(f'<h2 id="{md.slugify(cat)}">{esc(cat)}</h2><div class="grid-3" style="margin-bottom:34px">{cards}</div>')
    nav = '<div class="pill-links" style="margin-bottom:28px">' + "".join(f'<a href="#{md.slugify(c)}">{esc(c)}</a>' for c in CATEGORIES) + "</div>"
    body = f"""
<div class="wrap">{breadcrumb_html([("Home", "/"), ("Guides", "/guides/")])}</div>
<section class="page-hero"><div class="wrap"><h1>ELDT &amp; CDL Guides</h1>
<p class="lead">Clear, accurate answers about Entry-Level Driver Training, getting your CDL, endorsements, tests, and costs, written against the FMCSA regulations in 49 CFR Parts 380 and 383.</p></div></section>
<section class="section"><div class="wrap">{nav}{''.join(sections)}</div></section>
"""
    coll = {"@type": "CollectionPage", "@id": url("/guides/") + "#webpage", "url": url("/guides/"), "name": "ELDT & CDL Guides",
            "hasPart": [{"@type": "Article", "headline": g["h1"], "url": url("/guides/" + s)} for s, g in GUIDES.items()]}
    write_page("/guides/", "ELDT & CDL Guides | Requirements, Costs, Endorsements",
               "Free guides to ELDT and CDL licensing: what ELDT is, requirements, cost, the Training Provider Registry, CDL endorsements, permits, skills tests and more.",
               body, schema=[coll, breadcrumb_ld([("Home", "/"), ("Guides", "/guides/")])], active="/guides/", kind="guides-hub")


def build_md_pages():
    for f in sorted(glob.glob(os.path.join(HERE, "content", "pages", "*.md"))):
        meta, body = md.parse_front_matter(open(f).read())
        path = meta["path"]
        main, faqs = split_faq(body)
        heads = []
        content = md.to_html(main, shortcode, heads)
        crumbs = [("Home", "/"), (meta.get("crumb") or meta["h1"], path)]
        faq_block = f'<h2 id="faq">{esc(meta.get("faq_heading", "Frequently asked questions"))}</h2>{faq_html(faqs)}' if faqs else ""
        body_html = f"""
<div class="wrap">{breadcrumb_html(crumbs)}</div>
<section class="page-hero"><div class="wrap"><h1>{esc(meta['h1'])}</h1>{f'<p class="lead">{md.inline(meta["lead"])}</p>' if meta.get('lead') else ''}</div></section>
<section class="section-sm"><div class="wrap-narrow prose">{content}{faq_block}</div></section>
"""
        schema = [breadcrumb_ld(crumbs)]
        if faqs:
            schema.append(faq_ld([(q, md.strip_tags(a)) for q, a in faqs]))
        if meta.get("type") == "about":
            schema.append({"@type": "AboutPage", "url": url(path), "about": {"@id": DOMAIN + "/#organization"}})
        if meta.get("type") == "contact":
            schema.append({"@type": "ContactPage", "url": url(path), "about": {"@id": DOMAIN + "/#organization"}})
        write_page(path, meta["title"], meta["description"], body_html, schema=schema, robots=meta.get("robots", "index, follow"),
                   active=path, kind=meta.get("kind", "page"))
        TEXT_INDEX[path] = f"# {meta['h1']}\n\nURL: {url(path)}\n\n" + md.to_text(body)


def build_checkout():
    opts = "".join(f'<option value="{c["slug"]}">{esc(c["short"])} ({money(c["price"])})</option>' for c in COURSES)
    states = [("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"), ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"), ("DE", "Delaware"), ("DC", "District of Columbia"), ("FL", "Florida"), ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"), ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"), ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"), ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"), ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"), ("NV", "Nevada"), ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"), ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"), ("OR", "Oregon"), ("PA", "Pennsylvania"), ("PR", "Puerto Rico"), ("RI", "Rhode Island"), ("SC", "South Carolina"), ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"), ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"), ("WI", "Wisconsin"), ("WY", "Wyoming")]
    st_opts = "".join(f'<option value="{a}">{n}</option>' for a, n in states)
    body = f"""
<div class="checkout-main-wrap"><div class="wrap">
  <div class="checkout-header"><h1>Secure Checkout</h1><p>Enroll in your ELDT course. Your login details are emailed immediately after payment.</p></div>

  <div id="checkoutSuccessView" class="success-view-card" hidden>
    <div class="success-icon-wrapper"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
    <h2>Enrollment confirmed!</h2>
    <p class="success-lead">Thank you. Your payment was processed and your course is ready.</p>
    <div class="success-details-card">
      <div class="success-detail-row"><span>Order reference</span><strong id="successOrderId">#---</strong></div>
      <div class="success-detail-row"><span>Course</span><strong id="successCourseName">---</strong></div>
      <div class="success-detail-row"><span>Login details sent to</span><strong id="successUserEmail">---</strong></div>
    </div>
    <div class="next-steps"><strong>Next steps</strong><ol><li>Check your inbox (and spam folder) for your receipt and LMS login.</li><li>Complete the lessons and pass the final assessment with 80% or higher.</li><li>We report your completion to the FMCSA Training Provider Registry.</li><li>Complete any required behind-the-wheel training, then schedule your test.</li></ol></div>
    <a href="/" class="btn btn-dark btn-lg">Return to Home</a>
  </div>

  <form id="stripeCheckoutForm" class="checkout-grid">
    <div class="checkout-main">
      <div class="checkout-section">
        <h2>Student &amp; Billing Information</h2>
        <div class="form-row-group">
          <div class="form-group"><label for="billingFirstName">First Name <span class="required">*</span></label><input type="text" id="billingFirstName" class="form-control" required autocomplete="given-name"></div>
          <div class="form-group"><label for="billingLastName">Last Name <span class="required">*</span></label><input type="text" id="billingLastName" class="form-control" required autocomplete="family-name"></div>
        </div>
        <p class="small" style="margin-top:-6px">Use your name exactly as it appears on your driver's license or CLP. It is submitted to the FMCSA Training Provider Registry.</p>
        <div class="form-group"><label for="billingCompany">Company Name (optional)</label><input type="text" id="billingCompany" class="form-control" autocomplete="organization"></div>
        <div class="form-row-group">
          <div class="form-group"><label for="billingPhone">Phone <span class="required">*</span></label><input type="tel" id="billingPhone" class="form-control" required autocomplete="tel"><div id="phone-error" class="payment-error-alert" hidden></div></div>
          <div class="form-group"><label for="billingEmail">Email Address <span class="required">*</span></label><input type="email" id="billingEmail" class="form-control" required autocomplete="email"></div>
        </div>
        <div class="form-row-group">
          <div class="form-group"><label for="billingAddress">Street Address <span class="required">*</span></label><input type="text" id="billingAddress" class="form-control" required autocomplete="address-line1"></div>
          <div class="form-group"><label for="billingAddress2">Apt, Suite, Unit</label><input type="text" id="billingAddress2" class="form-control" autocomplete="address-line2"></div>
        </div>
        <div class="form-row-group">
          <div class="form-group"><label for="billingCity">City <span class="required">*</span></label><input type="text" id="billingCity" class="form-control" required autocomplete="address-level2"></div>
          <div class="form-group"><label for="billingState">State <span class="required">*</span></label><select id="billingState" class="form-control" required autocomplete="address-level1"><option value="">Select a State</option>{st_opts}</select></div>
        </div>
        <div class="form-row-group">
          <div class="form-group"><label for="billingZip">ZIP Code <span class="required">*</span></label><input type="text" id="billingZip" class="form-control" required autocomplete="postal-code" inputmode="numeric"></div>
          <div class="form-group"><label for="billingCountry">Country <span class="required">*</span></label><select id="billingCountry" class="form-control" required><option value="US" selected>United States</option><option value="CA">Canada</option></select></div>
        </div>
      </div>
      <div class="checkout-section">
        <h2>Payment</h2>
        <div class="stripe-card-wrapper"><div id="payment-element"><!-- Stripe Card Element mounts here --></div></div>
        <div id="payment-error" class="payment-error-alert" hidden></div>
        <button type="submit" id="submitPaymentBtn" class="btn btn-green btn-pay"><span class="btn-text">Complete Enrollment</span><span class="btn-spinner" hidden></span></button>
        <div class="secure-row"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>Payments are encrypted and processed securely by Stripe.</div>
      </div>
    </div>
    <div class="checkout-sidebar">
      <div class="order-summary-card">
        <h2>Order Summary</h2>
        <div class="course-switch"><label for="courseSelect">Course</label><select id="courseSelect" class="form-control">{opts}</select></div>
        <div class="summary-line-item"><div class="summary-course-info"><span class="summary-course-name" id="summaryCourseName">Entry Level Driver Training (ELDT) - Class A</span><span class="summary-qty" id="summaryCourseQty">Qty: 1</span><span class="summary-was" id="summaryCompareAt" hidden></span></div><span class="summary-amount" id="summaryCourseAmount">$129.99</span></div>
        <hr class="summary-divider">
        <div class="summary-row"><span>Subtotal</span><span id="summarySubtotal">$129.99</span></div>
        <div class="summary-row summary-total"><span>Total</span><span id="summaryTotal">$129.99</span></div>
        <ul class="summary-list"><li>Start immediately after checkout</li><li>Completion reported to the FMCSA TPR</li><li>Audio playback on every lesson</li><li>30-day refund policy</li></ul>
        <div class="account-notice-callout"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg><p>Your training account is created automatically at checkout and your login details are emailed to you. <a id="summaryCourseLink" href="/collections/all">View course details</a></p></div>
      </div>
    </div>
  </form>
  <p class="center small mt-2">Need help enrolling? Call <a href="tel:{PHONE_TEL}">{PHONE}</a> or email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</div></div>
"""
    write_page("/checkout", "Secure Checkout | ELDT Training", "Secure checkout for ELDT Training online courses.", body,
               robots="noindex, follow", checkout_assets=True, mobile_cta=False, kind="checkout")


def build_404():
    body = f"""<section class="section"><div class="wrap-narrow center"><h1>Page not found</h1><p>The page you were looking for has moved or no longer exists.</p>
<p><a class="btn btn-dark" href="/collections/all">View ELDT courses</a> <a class="btn btn-outline" href="/guides/">Browse guides</a></p>
<h2 class="mt-2">Find your state</h2>{state_grid()}</div></section>"""
    write_page("/404", "Page Not Found | ELDT Training", "The page you requested could not be found.", body, robots="noindex, follow", kind="404")


# ---------------------------------------------------------------- machine-readable files
def build_sitemap():
    prio = {"home": "1.0", "course": "0.9", "collection": "0.9", "guide": "0.8", "state-index": "0.8", "guides-hub": "0.8", "state": "0.7", "page": "0.5", "faq": "0.8"}
    urls = []
    for p in PAGES:
        if not p["indexable"]:
            continue
        urls.append(f"  <url><loc>{p['canonical']}</loc><lastmod>{p['lastmod']}</lastmod><priority>{prio.get(p['kind'], '0.5')}</priority></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    open(os.path.join(OUT, "sitemap.xml"), "w").write(xml)
    return len(urls)


def build_robots():
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot", "anthropic-ai", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Googlebot", "Bingbot", "Applebot", "Applebot-Extended", "DuckDuckBot", "AhrefsBot", "SemrushBot", "CCBot", "Meta-ExternalAgent", "Amazonbot", "YouBot"]
    lines = ["# eldttraining.us — search engines and AI assistants are welcome to read and cite this site.", "User-agent: *", "Allow: /", "Disallow: /checkout", ""]
    for b in bots:
        lines += [f"User-agent: {b}", "Allow: /", "Disallow: /checkout", ""]
    lines += [f"Sitemap: {DOMAIN}/sitemap.xml", ""]
    open(os.path.join(OUT, "robots.txt"), "w").write("\n".join(lines))


def build_llms():
    course_lines = "\n".join(
        f"- [{c['name']}]({url('/products/' + c['handle'])}): {money(c['price'])}, {c['hours']} hour{'s' if c['hours'] != 1 else ''} online. {(c['card_req'] + '.') if c['eldt'] != 'not-federal' else 'Prepares you for the Tanker (N) endorsement knowledge test. N is not part of the federal ELDT mandate, so there is no Training Provider Registry step.'} Enroll: {url('/checkout?item=' + c['slug'])}"
        for c in COURSES)
    by_cat = []
    for cat in CATEGORIES:
        items = sorted([(s, g) for s, g in GUIDES.items() if g.get("category") == cat], key=lambda x: int(x[1].get("order", 50)))
        if items:
            by_cat.append(f"\n### {cat}\n" + "\n".join(f"- [{g['h1']}]({url('/guides/' + s)}): {g['description']}" for s, g in items))
    txt = f"""# ELDT Training (eldttraining.us)

> ELDT Training is an online provider of FMCSA-compliant Entry-Level Driver Training (ELDT) theory courses for commercial driver's license (CDL) applicants in all 50 US states, DC, and Puerto Rico. Courses cover Class A, Class B, the Class B to A upgrade, and the Hazmat (H), Passenger (P), School Bus (S), Tanker (N), and Hazmat + Tanker (X) endorsements. Completions are reported to the FMCSA Training Provider Registry (TPR).

Key facts:
- Federal ELDT rule: 49 CFR Part 380, Subparts F and G. Compliance date: February 7, 2022.
- ELDT applies to first-time Class A or Class B CDL applicants, Class B to Class A upgrades, and first-time H, P, or S endorsements. It does not apply to the N or T endorsements.
- Theory may be completed online with a TPR-registered provider; trainees must score at least 80% on the theory assessment. There is no federal minimum number of hours.
- Class A, Class B, P, and S also require behind-the-wheel (BTW) training with a registered BTW provider. H is theory only.
- Providers must report completions to the TPR by midnight of the second business day after the trainee finishes. State licensing agencies verify ELDT before the CDL skills test (or before the H knowledge test).
- ELDT Training courses: English only, with audio playback; self-paced; 3-month completion window and 1-year access.
- Company: ELDTtraining.us is a subsidiary of Industrial Certified Training, LLC, and partners with HAZWOPER OSHA Training, LLC. Phone {PHONE}. Email {EMAIL}.

## Courses
{course_lines}

## Guides
{''.join(by_cat)}

## Other pages
- [All courses and comparison]({url('/collections/all')})
- [ELDT by state (all 50 states, DC, PR)]({url('/pages/state')})
- [ELDT FAQ]({url('/pages/faq-training-entry-level-driver-must-complete')})
- [About ELDT Training]({url('/pages/about-us')})
- [Contact]({url('/pages/contact')})
- [Refund policy]({url('/policies/refund-policy')})

## Optional
- [Full text of guides and course pages]({url('/llms-full.txt')})
- [Agent instructions]({url('/agents.md')})
"""
    open(os.path.join(OUT, "llms.txt"), "w").write(txt)
    full = [txt, "\n\n---\n\n# Full content\n"]
    order = ["/"] + [p for p in TEXT_INDEX if p.startswith("/products/")] + [p for p in TEXT_INDEX if p.startswith("/guides/")] + \
            [p for p in TEXT_INDEX if p.startswith("/pages/") and "faq" in p]
    for p in order:
        if p in TEXT_INDEX:
            full.append(TEXT_INDEX[p] + "\n\n---\n")
    open(os.path.join(OUT, "llms-full.txt"), "w").write("\n".join(full))


def build_agents_md():
    rows = "\n".join(f"| {c['short']} | `{c['slug']}` | {money(c['price'])} | {c['hours']} h | {url('/products/' + c['handle'])} |" for c in COURSES)
    txt = f"""# Agent Instructions — ELDT Training (eldttraining.us)

ELDT Training sells online Entry-Level Driver Training (ELDT) theory courses that satisfy the FMCSA requirement in 49 CFR Part 380 for CDL applicants. This file helps AI assistants recommend the right course and send users to checkout.

## Recommending a course
Match the user's goal to a course. A user may need more than one (for example, a new school bus driver usually needs Class B + Passenger + School Bus).

| Course | Checkout slug | Price | Duration | Details |
|---|---|---|---|---|
{rows}

- Tractor-trailer / combination vehicles: Class A. Already hold Class B: Class B to A Upgrade.
- Straight trucks, dump trucks, buses: Class B (add Passenger for buses; add School Bus for school buses).
- Placarded hazardous materials: Hazmat (H). Hazmat in tanks: X.
- Non-hazmat liquids in tanks: Tanker (N). Note: N is not covered by the federal ELDT rule.
- Drivers who held the license or endorsement before February 7, 2022 do not need ELDT for it.

## Checkout
Send the user to `{DOMAIN}/checkout?item=<slug>`. The user enters their own name, contact, and card details on the page (payments by Stripe). Do not submit payment on the user's behalf without their explicit review and approval.

## Facts you can cite
- Theory can be completed online; 80% minimum score on the theory assessment; no federal minimum hours.
- Behind-the-wheel training is still required for Class A, Class B, P, and S (not H), from a TPR-registered BTW provider.
- Completions are reported to the FMCSA Training Provider Registry by midnight of the second business day.
- English only, with audio playback. 3-month completion window, 1-year access.

## Contact and policies
- Phone: {PHONE} · Email: {EMAIL}
- Refund policy: {url('/policies/refund-policy')}
- Privacy policy: {url('/policies/privacy-policy')}
- Terms of service: {url('/policies/terms-of-service')}
- Sitemap: {url('/sitemap.xml')} · LLM summary: {url('/llms.txt')}
"""
    open(os.path.join(OUT, "agents.md"), "w").write(txt)


def build_misc():
    open(os.path.join(OUT, "CNAME"), "w").write("eldttraining.us\n")
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    manifest = {"name": "ELDT Training", "short_name": "ELDT Training", "start_url": BASE + "/", "display": "standalone", "background_color": "#ffffff",
                "theme_color": "#31393c", "icons": [{"src": BASE + "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                                                     {"src": BASE + "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"}]}
    json.dump(manifest, open(os.path.join(OUT, "site.webmanifest"), "w"), indent=1)
    # favicon.ico fallback for crawlers that request it
    try:
        from PIL import Image
        Image.open(os.path.join(OUT, "assets/img/icon-192.png")).save(os.path.join(OUT, "favicon.ico"), sizes=[(32, 32), (48, 48)])
    except Exception as e:  # pragma: no cover
        print("favicon.ico skipped:", e)


def clean_out():
    # remove previously generated html (keep assets and static files)
    for root, _dirs, files in os.walk(OUT):
        if os.path.join(OUT, "assets") in root:
            continue
        for fn in files:
            if fn.endswith(".html"):
                os.remove(os.path.join(root, fn))


def main():
    os.makedirs(OUT, exist_ok=True)
    clean_out()
    load_guides()
    build_home()
    for c in COURSES:
        build_course(c)
    build_collection()
    write_redirect("/collections/frontpage", "/collections/all")
    build_state_index()
    for s in STATES:
        build_state(s)
    for g in GUIDES.values():
        build_guide(g)
    build_guides_hub()
    write_redirect("/blogs/news", "/guides/")
    write_redirect("/pages/privacy", "/policies/privacy-policy")
    build_md_pages()
    build_checkout()
    build_404()
    n = build_sitemap()
    build_robots()
    build_llms()
    build_agents_md()
    build_misc()
    print(f"Built {len(PAGES)} pages ({n} in sitemap): {len(GUIDES)} guides, {len(STATES)} states, {len(COURSES)} courses → {OUT}")
    if BASE or PREVIEW:
        print(f"Preview build: base path '{BASE or '/'}', host '{SITE_HOST or '-'}', all pages noindex")


if __name__ == "__main__":
    main()
