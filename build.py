#!/usr/bin/env python3
"""Build the Pan Garden plant manager site.

Usage:

    python3 build.py

Reads one markdown file per plant from plants/ and writes a static site into
site/. Open site/index.html by double clicking it. No server, no npm, no CDN.

PyYAML is used for the frontmatter if it is installed. If it is not, a small
built in parser handles the subset of YAML this project uses, so there is
nothing to install.

Per plant file format:

    ---
    slug: prop-joe               # optional, defaults to the filename
    name: Prop Joe
    species: Monstera deliciosa
    aka: null                    # other name it gets called
    pot_cm: 28
    pot_target_cm: 30            # optional, the pot it is moving to
    location: Living room
    order: 1                     # optional, sorts within a status group
    photos:                      # newest first is not required, build.py sorts
      - file: prop-joe.jpg       # a filename inside photos/
        date: 2026-08-14         # optional, groups the photo into a dated cycle
        note: Before the repot   # optional caption
    status: outstanding          # outstanding | done | rehoming | skipped
    outstanding:
      - text: What still needs doing
        blocked_by: A 21cm pot   # optional
        due: 2027-02-20          # optional
    log:
      - date: 2026-08-05
        note: What was done, in the past tense
    ---
    Freeform care notes in markdown below the frontmatter.

plants/_collection.md uses the same format for jobs that apply to the whole
collection rather than one plant. It becomes the panel on the index page and
the collection.html page.
"""

import html
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLANTS_DIR = ROOT / "plants"
PHOTOS_DIR = ROOT / "photos"
SITE_DIR = ROOT / "site"

# Status groups, in the order they appear on the index.
STATUS_ORDER = ["outstanding", "done", "rehoming", "skipped"]
STATUS_LABEL = {
    "outstanding": "Outstanding",
    "done": "Done",
    "rehoming": "Rehoming",
    "skipped": "Skipped",
}

# Palette lifted from plants-to-action.html so the site stays familiar.
CSS = """
:root {
  --bg: #faf9f7;
  --text: #1d1c1a;
  --muted: #6b6862;
  --border: #e6e3de;
  --card: #fff;
  --green: #3f7d52;
  --amber: #b5811f;
  --panel: #fdf6e6;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 0 24px 72px;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}

.wrap { max-width: 940px; margin: 0 auto; }
.wrap-narrow { max-width: 760px; margin: 0 auto; }

a { color: var(--green); }

header.top {
  padding: 40px 0 28px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 32px;
}

h1 { font-size: 30px; line-height: 1.2; margin: 0 0 8px; letter-spacing: -0.01em; }
h2 { font-size: 18px; margin: 40px 0 14px; letter-spacing: -0.005em; }
h3 { font-size: 15px; margin: 26px 0 8px; }

.sub { color: var(--muted); font-size: 15px; margin: 0; }
.sub strong { color: var(--text); font-weight: 600; }

.back {
  display: inline-block;
  margin: 32px 0 0;
  font-size: 14px;
  text-decoration: none;
}
.back:hover { text-decoration: underline; }

/* Index cards */

.group-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin: 36px 0 14px;
}
.group-head h2 { margin: 0; }
.group-head .count { color: var(--muted); font-size: 14px; }

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(272px, 1fr));
  gap: 16px;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.card:hover { border-color: #d3cec6; transform: translateY(-1px); }

.card .thumb {
  width: 100%;
  height: 168px;
  object-fit: cover;
  display: block;
  background: #f1efeb;
  border-bottom: 1px solid var(--border);
}
.card .thumb-empty {
  height: 168px;
  background: #f1efeb;
  border-bottom: 1px solid var(--border);
}

.card .body { padding: 14px 16px 16px; flex: 1; display: flex; flex-direction: column; }

.card .name {
  font-weight: 600;
  font-size: 17px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.card .species { color: var(--muted); font-size: 13.5px; font-style: italic; margin-top: 1px; }
.card .meta { color: var(--muted); font-size: 13px; margin-top: 6px; }

.card .next {
  margin-top: 11px;
  padding-top: 11px;
  border-top: 1px solid var(--border);
  font-size: 14px;
}
.card .next .label {
  display: block;
  font-size: 11px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 3px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex: 0 0 9px;
  background: var(--muted);
}
.dot.outstanding { background: var(--amber); }
.dot.done { background: var(--green); }
.dot.rehoming { background: #7a8ba6; }
.dot.skipped { background: #c6c1b8; }

/* Panels */

.panel {
  background: var(--panel);
  border: 1px solid #efe1bf;
  border-radius: 10px;
  padding: 18px 20px;
  margin: 4px 0 8px;
}
.panel h2 { margin: 0 0 10px; font-size: 16px; }
.panel ul { margin: 0; padding-left: 20px; }
.panel li { margin-bottom: 7px; }
.panel .tag { background: #fff; border-color: #eadfc3; }
.panel .more { font-size: 14px; margin: 12px 0 0; }

/* Plant page */

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin: 0 0 30px;
}
.gallery figure { margin: 0; }
.gallery a { display: block; }
.gallery figcaption { color: var(--muted); font-size: 13px; margin-top: 6px; }
h3.cycle {
  font-size: 12px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 24px 0 10px;
}
h3.cycle:first-of-type { margin-top: 0; }
.gallery img {
  width: 100%;
  height: 260px;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid var(--border);
  display: block;
}

.identity {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 20px;
  margin-bottom: 8px;
}
.identity dl { margin: 0; display: grid; grid-template-columns: 132px 1fr; row-gap: 7px; }
.identity dt { color: var(--muted); font-size: 14px; }
.identity dd { margin: 0; font-size: 15px; }
.identity .status-line { display: flex; align-items: center; gap: 8px; }

ul.actions { list-style: none; padding: 0; margin: 0; }
ul.actions li {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--amber);
  border-radius: 8px;
  padding: 12px 15px;
  margin-bottom: 9px;
}
.tag {
  display: inline-block;
  margin-top: 6px;
  margin-right: 8px;
  font-size: 12.5px;
  color: var(--muted);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2px 10px;
}

ul.log { list-style: none; padding: 0; margin: 0; }
ul.log li {
  display: grid;
  grid-template-columns: 128px 1fr;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 15px;
}
ul.log .when { color: var(--muted); font-size: 14px; }

.notes { font-size: 15.5px; }
.notes h2 { font-size: 15.5px; margin: 28px 0 10px; color: var(--muted); }
.notes p { margin: 0 0 12px; }
.notes ul { padding-left: 20px; }
.notes li { margin-bottom: 6px; }

.empty { color: var(--muted); font-size: 15px; margin: 0; }

footer.foot {
  margin-top: 56px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 13.5px;
}

@media (max-width: 560px) {
  body { padding: 0 16px 56px; }
  .identity dl { grid-template-columns: 1fr; row-gap: 2px; }
  .identity dd { margin-bottom: 8px; }
  ul.log li { grid-template-columns: 1fr; gap: 2px; }
}
"""


# ---------------------------------------------------------------- frontmatter


def parse_frontmatter(text):
    """Split a file into (frontmatter dict, markdown body)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        return {}, text
    raw = parts[0][3:]
    body = parts[1].lstrip("-\n")
    try:
        import yaml

        data = yaml.safe_load(raw) or {}
    except ImportError:
        data = mini_yaml(raw)
    return data, body


def mini_yaml(raw):
    """Parse the small slice of YAML this project uses, with no dependencies.

    Handles scalars, inline lists, and lists of nested key/value blocks at a
    two space indent. It is not a general YAML parser and does not try to be.
    """
    root = {}
    current_list = None
    current_item = None
    current_key = None

    for line in raw.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if indent == 0:
            current_list = current_item = None
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            key, value = key.strip(), value.strip()
            current_key = key
            if value == "":
                root[key] = current_list = []
            else:
                root[key] = scalar(value)
                current_list = None
            continue

        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if current_list is None:
                current_list = root.setdefault(current_key, [])
            if ":" in item and not item.startswith(("'", '"')):
                key, _, value = item.partition(":")
                current_item = {key.strip(): scalar(value.strip())}
                current_list.append(current_item)
            else:
                current_list.append(scalar(item))
                current_item = None
            continue

        if current_item is not None and ":" in stripped:
            key, _, value = stripped.partition(":")
            current_item[key.strip()] = scalar(value.strip())

    return root


def scalar(value):
    """Turn a YAML scalar string into a Python value."""
    if value in ("null", "~", ""):
        return None
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [scalar(part.strip()) for part in inner.split(",")]
    if len(value) > 1 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return datetime.strptime(value, "%Y-%m-%d").date()
    return value


# ------------------------------------------------------------------- markdown


def md_to_html(text):
    """Render the markdown used in the notes: headings, lists, bold, italic."""
    out = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for block in text.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")

        if all(line.strip().startswith(("- ", "* ")) for line in lines):
            out.append("<ul>")
            in_list = True
            for line in lines:
                out.append("<li>%s</li>" % inline(line.strip()[2:]))
            close_list()
            continue

        if block.startswith("### "):
            out.append("<h3>%s</h3>" % inline(block[4:]))
            continue
        if block.startswith("## "):
            out.append("<h2>%s</h2>" % inline(block[3:]))
            continue

        out.append("<p>%s</p>" % inline(" ".join(lines)))

    close_list()
    return "\n".join(out)


def inline(text):
    """Escape, then apply bold and italic."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


# --------------------------------------------------------------------- dates


def to_date(value):
    """Accept a date, a datetime or a YYYY-MM-DD string."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def pretty_date(value):
    """5 August 2026. British order, no leading zero."""
    parsed = to_date(value)
    if parsed is None:
        return str(value) if value else ""
    return "%d %s %d" % (parsed.day, parsed.strftime("%B"), parsed.year)


# --------------------------------------------------------------------- plants


def load_plants():
    plants = []
    collection = None

    for path in sorted(PLANTS_DIR.glob("*.md")):
        data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        data = dict(data or {})
        data["slug"] = data.get("slug") or path.stem.lstrip("_")
        data["notes"] = body.strip()
        data["source"] = path.name
        data["outstanding"] = normalise_actions(data.get("outstanding"))
        data["log"] = sorted(
            [entry for entry in (data.get("log") or []) if entry],
            key=lambda entry: to_date(entry.get("date")) or date.min,
            reverse=True,
        )
        data["photos"] = normalise_photos(data.get("photos"))

        missing = [p for p in data["photos"] if not (PHOTOS_DIR / p["file"]).exists()]
        for photo in missing:
            warn("%s lists a photo that is not in photos/: %s" % (path.name, photo["file"]))
        data["photos"] = [p for p in data["photos"] if p not in missing]

        if path.stem.startswith("_collection"):
            collection = data
            continue

        status = data.get("status") or "outstanding"
        if status not in STATUS_ORDER:
            warn("%s has an unknown status: %s" % (path.name, status))
            status = "outstanding"
        data["status"] = status
        plants.append(data)

    plants.sort(key=lambda p: (STATUS_ORDER.index(p["status"]), p.get("order") or 99, p.get("name") or ""))
    return plants, collection


def normalise_actions(raw):
    """Allow either a plain string or a dict for each outstanding action."""
    actions = []
    for item in raw or []:
        if not item:
            continue
        if isinstance(item, str):
            actions.append({"text": item})
        else:
            actions.append(dict(item))
    return actions


def normalise_photos(raw):
    """Allow either a plain filename or a dict with a date and a caption.

    Sorted newest first, so the most recent state of a plant leads.
    """
    photos = []
    for item in raw or []:
        if not item:
            continue
        if isinstance(item, str):
            photo = {"file": item}
        else:
            photo = dict(item)
        photo.setdefault("date", None)
        photo.setdefault("note", None)
        photos.append(photo)
    photos.sort(key=lambda p: to_date(p.get("date")) or date.min, reverse=True)
    return photos


def last_actioned(plant):
    dates = [to_date(entry.get("date")) for entry in plant["log"]]
    dates = [d for d in dates if d]
    return max(dates) if dates else None


def pot_text(plant):
    pot = plant.get("pot_cm")
    target = plant.get("pot_target_cm")
    if pot and target:
        return "%scm, moving to %scm" % (pot, target)
    if pot:
        return "%scm" % pot
    return "Not measured"


def warn(message):
    print("  note: %s" % message, file=sys.stderr)


# ---------------------------------------------------------------- rendering


def page(title, body, narrow=False):
    return """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="%s">
%s
</div>
</body>
</html>
""" % (html.escape(title), "wrap-narrow" if narrow else "wrap", body)


def alt_text(filename):
    return Path(filename).stem.replace("-", " ").replace("_", " ")


def render_card(plant):
    photos = plant["photos"]
    if photos:
        thumb = '<img class="thumb" src="../photos/%s" alt="%s">' % (
            html.escape(photos[0]["file"]),
            html.escape(alt_text(photos[0]["file"])),
        )
    else:
        thumb = '<div class="thumb-empty"></div>'

    meta = [pot_text(plant)]
    if plant.get("location"):
        meta.append(plant["location"])
    when = last_actioned(plant)
    meta.append("Last actioned %s" % pretty_date(when) if when else "Nothing logged yet")

    count = len(plant["outstanding"])
    if count:
        next_action = (
            '<div class="next"><span class="label">Next, %d outstanding</span>%s</div>'
            % (count, inline(plant["outstanding"][0]["text"]))
        )
    else:
        next_action = (
            '<div class="next"><span class="label">%s</span>Nothing outstanding</div>'
            % html.escape(STATUS_LABEL[plant["status"]])
        )

    species = plant.get("species") or ""
    return """<a class="card" href="%s.html">
  %s
  <div class="body">
    <div class="name"><span class="dot %s"></span>%s</div>
    <div class="species">%s</div>
    <div class="meta">%s</div>
    %s
  </div>
</a>""" % (
        html.escape(plant["slug"]),
        thumb,
        plant["status"],
        html.escape(plant.get("name") or plant["slug"]),
        html.escape(species),
        html.escape(" · ".join(meta)),
        next_action,
    )


def render_index(plants, collection):
    total = len(plants)
    outstanding_plants = [p for p in plants if p["outstanding"]]
    outstanding_jobs = sum(len(p["outstanding"]) for p in plants)
    dates = [last_actioned(p) for p in plants]
    dates = [d for d in dates if d]

    head = ['<header class="top">', "<h1>Pan Garden</h1>"]
    line = "<strong>%d plants</strong>, %d with something outstanding, %d jobs in total." % (
        total,
        len(outstanding_plants),
        outstanding_jobs,
    )
    if dates:
        line += " Last worked on %s." % pretty_date(max(dates))
    head.append('<p class="sub">%s</p>' % line)
    head.append("</header>")

    body = ["\n".join(head)]

    if collection:
        items = "".join(
            "<li>%s%s</li>" % (inline(action["text"]), action_tags(action))
            for action in collection["outstanding"]
        )
        body.append(
            """<div class="panel">
<h2>%s</h2>
<ul>%s</ul>
<p class="more"><a href="collection.html">Feeding order and collection notes</a></p>
</div>"""
            % (html.escape(collection.get("name") or "Whole collection"), items)
        )

    for status in STATUS_ORDER:
        group = [p for p in plants if p["status"] == status]
        if not group:
            continue
        body.append(
            '<div class="group-head"><h2>%s</h2><span class="count">%d</span></div>'
            % (html.escape(STATUS_LABEL[status]), len(group))
        )
        body.append('<div class="cards">\n%s\n</div>' % "\n".join(render_card(p) for p in group))

    body.append(
        """<footer class="foot">
Generated from <code>plants/*.md</code> by <code>build.py</code>. Edit the markdown, run
<code>python3 build.py</code> again. The reasoning behind every decision is in
<code>plant-repot-plan.md</code>.
</footer>"""
    )

    return page("Pan Garden", "\n\n".join(body))


def action_tags(action):
    """The pills that hang off an action: what it waits on, and when it is due."""
    tags = []
    if action.get("blocked_by"):
        tags.append("Waiting on %s" % inline(str(action["blocked_by"])))
    if action.get("due"):
        tags.append("Due %s" % html.escape(pretty_date(action["due"])))
    return "".join('<span class="tag">%s</span>' % tag for tag in tags)


def render_actions(plant):
    if not plant["outstanding"]:
        return '<p class="empty">Nothing outstanding.</p>'
    items = [
        "<li>%s%s</li>" % (inline(action["text"]), action_tags(action))
        for action in plant["outstanding"]
    ]
    return '<ul class="actions">\n%s\n</ul>' % "\n".join(items)


def render_log(plant):
    if not plant["log"]:
        return '<p class="empty">Nothing logged yet.</p>'
    items = [
        '<li><span class="when">%s</span><span>%s</span></li>'
        % (html.escape(pretty_date(entry.get("date"))), inline(str(entry.get("note") or "")))
        for entry in plant["log"]
    ]
    return '<ul class="log">\n%s\n</ul>' % "\n".join(items)


def render_gallery(plant):
    """Photos grouped into dated sessions, newest first. This is the timeline."""
    if not plant["photos"]:
        return ""

    groups = []
    for photo in plant["photos"]:
        when = to_date(photo.get("date"))
        if groups and groups[-1][0] == when:
            groups[-1][1].append(photo)
        else:
            groups.append((when, [photo]))

    out = []
    for when, photos in groups:
        out.append(
            '<h3 class="cycle">%s</h3>' % html.escape(pretty_date(when) if when else "Undated")
        )
        tiles = []
        for photo in photos:
            caption = ""
            if photo.get("note"):
                caption = '<figcaption>%s</figcaption>' % inline(str(photo["note"]))
            tiles.append(
                '<figure><a href="../photos/%s"><img src="../photos/%s" alt="%s"></a>%s</figure>'
                % (
                    html.escape(photo["file"]),
                    html.escape(photo["file"]),
                    html.escape(alt_text(photo["file"])),
                    caption,
                )
            )
        out.append('<div class="gallery">\n%s\n</div>' % "\n".join(tiles))
    return "\n".join(out)


def render_plant(plant):
    gallery = render_gallery(plant)

    rows = [("What it is", html.escape(plant.get("species") or "Not identified"))]
    if plant.get("aka"):
        rows.append(("Also called", html.escape(str(plant["aka"]))))
    rows.append(("Pot", html.escape(pot_text(plant))))
    if plant.get("location"):
        rows.append(("Where", html.escape(str(plant["location"]))))
    rows.append(
        (
            "Status",
            '<span class="status-line"><span class="dot %s"></span>%s</span>'
            % (plant["status"], html.escape(STATUS_LABEL[plant["status"]])),
        )
    )
    when = last_actioned(plant)
    rows.append(("Last actioned", html.escape(pretty_date(when)) if when else "Nothing logged yet"))

    identity = '<div class="identity"><dl>\n%s\n</dl></div>' % "\n".join(
        "<dt>%s</dt><dd>%s</dd>" % (label, value) for label, value in rows
    )

    notes = md_to_html(plant["notes"]) if plant["notes"] else '<p class="empty">No notes yet.</p>'

    body = """<header class="top">
<h1>%s</h1>
<p class="sub">%s</p>
</header>

%s

%s

<h2>Outstanding</h2>
%s

<h2>History</h2>
%s

<h2>Care notes</h2>
<div class="notes">
%s
</div>

<a class="back" href="index.html">Back to all plants</a>
""" % (
        html.escape(plant.get("name") or plant["slug"]),
        html.escape(plant.get("species") or ""),
        gallery,
        identity,
        render_actions(plant),
        render_log(plant),
        notes,
    )

    return page("%s, Pan Garden" % (plant.get("name") or plant["slug"]), body, narrow=True)


def render_collection(collection):
    body = """<header class="top">
<h1>%s</h1>
<p class="sub">Jobs and notes that apply to the collection rather than one plant.</p>
</header>

<h2>Outstanding</h2>
%s

<h2>History</h2>
%s

<h2>Notes</h2>
<div class="notes">
%s
</div>

<a class="back" href="index.html">Back to all plants</a>
""" % (
        html.escape(collection.get("name") or "Whole collection"),
        render_actions(collection),
        render_log(collection),
        md_to_html(collection["notes"]) if collection["notes"] else '<p class="empty">No notes yet.</p>',
    )
    return page("Whole collection, Pan Garden", body, narrow=True)


# ---------------------------------------------------------------------- main


def main():
    if not PLANTS_DIR.exists():
        sys.exit("No plants/ directory found next to build.py.")

    plants, collection = load_plants()
    if not plants:
        sys.exit("No plant files found in plants/.")

    if SITE_DIR.exists():
        for old in SITE_DIR.glob("*.html"):
            old.unlink()
    SITE_DIR.mkdir(exist_ok=True)

    (SITE_DIR / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (SITE_DIR / "index.html").write_text(render_index(plants, collection), encoding="utf-8")
    for plant in plants:
        (SITE_DIR / ("%s.html" % plant["slug"])).write_text(render_plant(plant), encoding="utf-8")
    if collection:
        (SITE_DIR / "collection.html").write_text(render_collection(collection), encoding="utf-8")

    jobs = sum(len(p["outstanding"]) for p in plants)
    print("Built %d plants, %d outstanding jobs" % (len(plants), jobs))
    print("Open: %s" % (SITE_DIR / "index.html"))


if __name__ == "__main__":
    main()
