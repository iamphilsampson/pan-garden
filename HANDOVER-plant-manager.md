# Handover: build the Pan Garden plant manager

**For:** Claude Code, working in `/Users/phillipsamson/Projects/zpersonal/Pan Garden`
**Date:** 21 August 2026
**Task:** replace `plants-to-action.html` with a generated static site: an index plus one page per plant, tracking outstanding actions and a dated history of what has already been done.

---

## Read these first, do not re-derive them

Everything about the plants themselves already exists. Do not re-identify species, re-decide pot sizes, or re-litigate care advice.

| File | What it is |
|---|---|
| `plant-repot-plan.md` | **The master knowledge doc, v6.** Plant register, soil recipes, feeding order, per-plant reasoning, decisions already made and corrections already issued. This is the source you migrate data from |
| `HANDOVER.md` | Handover from the previous session. Project background, the headline findings, how Phil works. Read the "Working with Phil" section |
| `plants-to-action.html` | The current working surface. **This is what you are replacing.** Steal its palette and card layout; discard its structure |
| `photos/` | Every plant photo, already renamed by plant. Reference these relatively |

## Why this is being built

Phil's annual plant sort-out. The one-big-page format worked while the job was a single afternoon's task list, but he wants it to become a thing he keeps: per-plant state, what is outstanding, and crucially **what he did previously and when**. Next August the history is the valuable part.

His words: "if we had an index page, then a sub page for each plant, we can track what we need to do, and what we have done previously, so we have more of a plant manager, which we then keep up to date."

He explicitly said to build this **assumptively in the background**. Do not interview him about it. Make sensible calls, build it, show him.

---

## Architecture: source of truth, then generate

Do not hand-author the HTML pages. The thing that makes or breaks this is whether updating it is trivial; the pages are the easy part.

```
Pan Garden/
  plants/                 <- source of truth, one markdown file per plant
    prop-joe.md
    philipos.md
    ...
  build.py                <- generates site/ from plants/ + photos/
  site/
    index.html
    prop-joe.html
    ...
  photos/                 <- unchanged, referenced as ../photos/x.jpg
  plant-repot-plan.md     <- stays as the reference/knowledge doc
```

**Per-plant markdown, YAML frontmatter plus freeform notes:**

```yaml
---
slug: prop-joe
name: Prop Joe
species: Monstera deliciosa
aka: null
pot_cm: 28
location: null
photos: [prop-joe-monstera-trunk-aerial-roots.jpg]
status: outstanding        # outstanding | done | skipped | rehoming
outstanding:
  - text: "Repot into the 30cm, bury 20 to 30cm of bare trunk, tuck every reachable aerial root in"
    blocked_by: null
  - text: "Wrap the air layer"
    due: 2027-02-20
log:
  - date: 2026-08-05
    note: "Bottom-watered, 20 to 30 minutes"
---
Freeform care notes in markdown. Pulled from plant-repot-plan.md.
```

Reasons for markdown-plus-frontmatter over a single JSON or `localStorage`:

- Phil edits it directly, or asks an agent to, without a UI
- Git diffs are readable, so the history is real history
- `localStorage` on `file://` is fragile and would silently lose his log

Use PyYAML if present, otherwise write a minimal frontmatter parser rather than adding a dependency. No build tooling, no npm, no CDN.

## What the pages need to show

**Index:** one card per plant. Thumbnail, name, species, pot size, a status dot, the count of outstanding actions, the single next action, and the date last actioned. Sort outstanding first, then done, then skipped. A small header line with counts (currently: 14 plants, 6 outstanding). Link each card to its page.

**Plant page:** photos at the top, identity block (name, what it actually is, pot size), outstanding actions as a list, then the dated log newest first, then the care notes. A back link to the index. If a plant has a `blocked_by`, show what it is waiting on.

## Constraints

- Static, self-contained, opens by double-click from `file://`. No server, no frameworks, no CDN, no build step beyond `python3 build.py`
- Inline CSS in each page, or one shared `site/style.css`. Either is fine
- Palette, taken from the existing HTML so it stays familiar: bg `#faf9f7`, text `#1d1c1a`, muted `#6b6862`, borders `#e6e3de`, cards `#fff`, green `#3f7d52`, amber `#b5811f`, warm panel `#fdf6e6`
- Existing photos are ~1500 to 2000px. Generate thumbnails at build time or use CSS `object-fit`, do not commit duplicates
- **British English. No em dashes. No emoji.** These are hard requirements from Phil's preferences, and the existing docs follow them
- Do not delete `plants-to-action.html` or `plant-repot-plan.md`. Leave both in place

## Migration data

All 14 plants are in the register table in `plant-repot-plan.md` section 4, with their real species, pot sizes and status. The "Done today" list in section 5 gives you log entries dated 2026-08-05. The outstanding six are Prop Joe, Philipos, OG loc, variegated big, variegated small, string of hearts. The Dracaena is `skipped`, the pine is `rehoming` (going to a friend), the Strelitzia, avocado, three trailers and hanging basket are `done`.

**Two changes made after that doc was written, apply them:**

1. **Variegated big now needs a repot**, 18cm to 21cm. Reversal of the "keep the pot" line in the plan. Evidence is `photos/variegated-big-pothos-roots-through-base.jpg`: a dense root mat escaping the base and two roots running a foot across the floor. Blocked on buying a 21cm pot. Keep the metal rod
2. **Prop Joe's 30cm pot has been bought**, and it is a tall one, so more bare trunk goes under the soil line than planned

## Suggested skills

- **`skill-creator`** is the one worth considering, and only after the site exists. If this becomes an annual routine, the audit method (photograph, identify, measure, default to no repot, check light and feed before reaching for a bigger pot) plus this site's update flow would make a solid reusable skill. Do not build it unprompted
- **`dataviz`** only if a chart is later wanted. The site needs none. Status dots are not a data visualisation
- **None of the Tendable skills apply.** This is personal, not work. Do not reach for the Jira, Amplitude, Metabase, release or customer-brief skills

## Working with Phil

Lifted from `HANDOVER.md` and confirmed again this session:

- Fast back-and-forth while he is physically doing the job. Answer, give the next step, stop. Do not pre-build later steps
- **He values being challenged and being told when advice was wrong.** Several recommendations have been reversed mid-project and every reversal was welcomed. Own corrections plainly rather than quietly restating
- Plain language over jargon
- Photos are his main input. HEIC needs converting; `pillow-heif` is the working route
- He wants links to files and folders rather than being made to dig

## Out of scope

He is mid-way through an afternoon of actual potting. **Do not touch the plant work, the running order, or the shopping list.** That is being handled in the Cowork session. Build the site, then stop.
