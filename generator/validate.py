#!/usr/bin/env python3
"""SEO / integrity checks for the built site (the kind of issues Ahrefs and Semrush site audits flag).

    python3 generator/validate.py
"""
import collections
import glob
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.meta = {}
        self.h1 = 0
        self.links = []
        self.imgs = []
        self.ld = []
        self.in_ld = False
        self.canonical = None
        self.ids = set()
        self.words = 0
        self.in_body_text = False

    def handle_starttag(self, tag, a):
        a = dict(a)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "title":
            self.in_title = True
        elif tag == "meta" and a.get("name"):
            self.meta[a["name"]] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "script" and a.get("type") == "application/ld+json":
            self.in_ld = True
            self.ld.append("")
        elif tag in ("source",) and a.get("src"):
            self.links.append(a["src"])

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script":
            self.in_ld = False

    def handle_data(self, d):
        if self.in_title:
            self.title += d
        if self.in_ld:
            self.ld[-1] += d
        else:
            self.words += len(re.findall(r"[A-Za-z]{2,}", d))


def resolve(href, page_dir):
    href = href.split("#")[0].split("?")[0]
    if not href:
        return True
    if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
        return True
    path = href if href.startswith("/") else os.path.normpath(os.path.join(page_dir, href))
    fs = os.path.join(ROOT, path.lstrip("/"))
    if path.endswith("/") and path != "/":
        return os.path.isfile(os.path.join(fs, "index.html"))
    return os.path.isfile(fs) or os.path.isfile(fs.rstrip("/") + ".html") or os.path.isfile(os.path.join(fs, "index.html"))


def main():
    issues = collections.defaultdict(list)
    titles = collections.defaultdict(list)
    descs = collections.defaultdict(list)
    pages = 0
    inbound = collections.Counter()
    all_urls = set()
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = "/" + os.path.relpath(f, ROOT)
        txt = open(f).read()
        if 'http-equiv="refresh"' in txt or rel.endswith("/index.html") and os.path.exists(f[:-11] + ".html"):
            continue
        p = P()
        p.feed(txt)
        robots = p.meta.get("robots", "")
        indexable = robots.startswith("index")
        url = rel[:-5] if rel.endswith(".html") else rel
        url = "/" if url == "/index" else url
        url = url[:-6] if url.endswith("/index") else url
        pages += 1
        if indexable:
            all_urls.add(url)
        t = p.title.strip()
        d = p.meta.get("description", "")
        if indexable:
            titles[t].append(rel)
            descs[d].append(rel)
            if not (25 <= len(t) <= 65):
                issues["title length"].append(f"{rel} ({len(t)}): {t}")
            if not (110 <= len(d) <= 165):
                issues["description length"].append(f"{rel} ({len(d)})")
            if p.h1 != 1:
                issues["h1 count"].append(f"{rel}: {p.h1}")
            if p.words < 300 and "/policies/" not in rel:
                issues["thin content (<300 words)"].append(f"{rel}: {p.words}")
            if not p.canonical:
                issues["missing canonical"].append(rel)
        for img in p.imgs:
            if "alt" not in img:
                issues["img missing alt"].append(f"{rel}: {img.get('src')}")
            if not (img.get("width") and img.get("height")):
                issues["img missing dimensions"].append(f"{rel}: {img.get('src')}")
        for blk in p.ld:
            try:
                json.loads(blk)
            except Exception as e:
                issues["invalid JSON-LD"].append(f"{rel}: {e}")
        page_dir = os.path.dirname(url)
        for h in p.links:
            if h.startswith("#"):
                if h[1:] and h[1:] not in p.ids:
                    issues["broken anchor"].append(f"{rel}: {h}")
                continue
            if not resolve(h, page_dir):
                issues["broken internal link"].append(f"{rel}: {h}")
            elif h.startswith("/"):
                inbound[h.split("#")[0].split("?")[0].rstrip("/") or "/"] += 1
    for t, ps in titles.items():
        if len(ps) > 1:
            issues["duplicate title"].append(f"{t}: {ps}")
    for d, ps in descs.items():
        if len(ps) > 1:
            issues["duplicate description"].append(f"{d[:60]}: {ps}")
    for u in sorted(all_urls):
        key = u.rstrip("/") or "/"
        if inbound[key] == 0:
            issues["orphan page (no internal links)"].append(u)
    # sitemap sanity
    sm = open(os.path.join(ROOT, "sitemap.xml")).read()
    locs = re.findall(r"<loc>https://eldttraining\.us([^<]*)</loc>", sm)
    for loc in locs:
        if not resolve(loc, "/"):
            issues["sitemap URL missing"].append(loc)
    print(f"Checked {pages} pages, {len(locs)} sitemap URLs")
    if not issues:
        print("No issues found.")
    for k, v in issues.items():
        print(f"\n[{k}] {len(v)}")
        for x in v[:25]:
            print("  ", x)
    return 1 if any(k.startswith(("broken", "invalid", "duplicate", "sitemap")) for k in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
