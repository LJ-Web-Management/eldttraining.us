"""Tiny Markdown-ish converter for ELDT Training content files.

Supports: front matter (--- key: value ---), ## / ### headings (auto ids), paragraphs,
**bold**, *italic*, `code`, [links](url), - / 1. lists, | tables |, > blockquotes,
:::type ... ::: blocks (answer, tip, warn, info, facts), raw HTML lines, and {{shortcodes}}.
"""
import html
import re


def slugify(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "section"


def parse_front_matter(text):
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        fm = text[3:end].strip("\n")
        body = text[end + 4:].lstrip("\n")
        key = None
        for line in fm.splitlines():
            if not line.strip():
                continue
            m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
            if m and not line.startswith("  "):
                key = m.group(1).strip()
                meta[key] = m.group(2).strip()
            elif key:
                meta[key] += " " + line.strip()
        return meta, body
    return meta, text


def inline(s):
    # protect inline code
    codes = []

    def _code(m):
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", _code, s)

    def _link(m):
        text, url = m.group(1), m.group(2).strip()
        ext = url.startswith("http") and "eldttraining.us" not in url
        attrs = ' rel="noopener"' if ext else ""
        return f'<a href="{html.escape(url, quote=True)}"{attrs}>{text}</a>'

    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)
    return s


def render_table(rows):
    def cells(r):
        r = r.strip()
        if r.startswith("|"):
            r = r[1:]
        if r.endswith("|"):
            r = r[:-1]
        return [c.strip() for c in r.split("|")]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]] if len(rows) > 1 and re.match(r"^\|?\s*:?-{2,}", rows[1].strip()) else [cells(r) for r in rows[1:]]
    out = ['<div class="table-wrap"><table><thead><tr>']
    out += [f"<th scope=\"col\">{inline(h)}</th>" for h in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>")
        for i, c in enumerate(r):
            cls = ""
            low = re.sub(r"<[^>]+>", "", c).strip().lower()
            if low.startswith("yes"):
                cls = ' class="yes"'
            elif low.startswith("no") and len(low) < 40:
                cls = ' class="no"'
            tag = "th scope=\"row\"" if i == 0 and False else "td"
            out.append(f"<{tag}{cls}>{inline(c)}</{tag.split()[0]}>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def to_html(body, shortcode=None, headings=None):
    """Convert body text to HTML. `shortcode(name, arg)` renders {{name:arg}} blocks.
    `headings` (list) collects (level, id, text) for a TOC."""
    if headings is None:
        headings = []
    lines = body.splitlines()
    out = []
    i = 0
    n = len(lines)
    used_ids = set()

    def hid(text):
        base = slugify(text)
        k, j = base, 2
        while k in used_ids:
            k = f"{base}-{j}"
            j += 1
        used_ids.add(k)
        return k

    while i < n:
        line = lines[i]
        st = line.strip()
        if not st:
            i += 1
            continue
        # shortcodes
        m = re.match(r"^\{\{\s*([\w-]+)\s*(?::\s*(.*?))?\s*\}\}$", st)
        if m and shortcode:
            out.append(shortcode(m.group(1), (m.group(2) or "").strip()))
            i += 1
            continue
        # fenced blocks
        m = re.match(r"^:::\s*([\w-]+)\s*(.*)$", st)
        if m:
            kind, title = m.group(1), m.group(2).strip()
            j = i + 1
            buf = []
            while j < n and lines[j].strip() != ":::":
                buf.append(lines[j])
                j += 1
            inner_text = "\n".join(buf)
            if kind == "facts":
                items = []
                for b in buf:
                    if ":" in b:
                        k, v = b.split(":", 1)
                        items.append(f"<div><dt>{inline(k.strip())}</dt><dd>{inline(v.strip())}</dd></div>")
                out.append('<dl class="key-facts">' + "".join(items) + "</dl>")
            elif kind == "answer":
                label = title or "Quick answer"
                out.append(f'<div class="answer-box"><span class="label">{html.escape(label)}</span>{to_html(inner_text, shortcode, [])}</div>')
            else:
                cls = {"tip": "callout", "warn": "callout warn", "info": "callout info"}.get(kind, "callout")
                t = f"<p><strong>{inline(title)}</strong></p>" if title else ""
                out.append(f'<div class="{cls}">{t}{to_html(inner_text, shortcode, [])}</div>')
            i = j + 1
            continue
        # headings
        m = re.match(r"^(#{2,4})\s+(.*)$", st)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            k = hid(text)
            headings.append((level, k, re.sub(r"<[^>]+>", "", inline(text))))
            out.append(f'<h{level} id="{k}">{inline(text)}</h{level}>')
            i += 1
            continue
        # raw html block
        if st.startswith("<"):
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue
        # table
        if st.startswith("|"):
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i])
                i += 1
            out.append(render_table(buf))
            continue
        # blockquote
        if st.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].lstrip())
                i += 1
            out.append("<blockquote>" + to_html("\n".join(buf), shortcode, []) + "</blockquote>")
            continue
        # lists
        if re.match(r"^([-*])\s+", st) or re.match(r"^\d+[.)]\s+", st):
            ordered = bool(re.match(r"^\d+[.)]\s+", st))
            tag = "ol" if ordered else "ul"
            items = []
            while i < n:
                s2 = lines[i].strip()
                if ordered and re.match(r"^\d+[.)]\s+", s2):
                    items.append(re.sub(r"^\d+[.)]\s+", "", s2))
                elif not ordered and re.match(r"^[-*]\s+", s2):
                    items.append(re.sub(r"^[-*]\s+", "", s2))
                elif s2 and lines[i].startswith(("  ", "\t")) and items:
                    items[-1] += " " + s2
                else:
                    break
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        # paragraph
        buf = []
        while i < n:
            s2 = lines[i].strip()
            if not s2 or re.match(r"^(#{2,4}\s|[-*]\s|\d+[.)]\s|\||>|:::|\{\{|<)", s2):
                break
            buf.append(s2)
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    return "\n".join(out)


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def to_text(body):
    """Plain-text-ish (markdown) for llms-full.txt: drop shortcodes and ::: markers."""
    out = []
    for line in body.splitlines():
        st = line.strip()
        if re.match(r"^\{\{.*\}\}$", st):
            continue
        if st.startswith(":::"):
            continue
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
