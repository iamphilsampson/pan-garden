# Pan Garden

Houseplant manager. Fourteen plants, per-plant state, what is outstanding and what was done when.
Started as an annual repotting audit in August 2026 and is now kept as a running record.

## How it works

`plants/*.md` is the source of truth. One file per plant: YAML frontmatter for the structured
state, freeform markdown below it for the care notes. `build.py` generates `site/` from those
files plus `photos/`.

```bash
python3 build.py
```

Then open `site/index.html` by double clicking it. Static, no server, no npm, no CDN. PyYAML is
used if installed and a built in parser covers it if not, so there is nothing to install.

## To update a plant

Edit its file in `plants/`, then rebuild. Nothing else. Concretely:

- **Job done:** delete the item from `outstanding`, add a dated entry to `log`
- **Plant finished:** set `status: done` once `outstanding` is empty
- **New job:** add to `outstanding`, with `blocked_by` if it needs a purchase or `due` for a date

Statuses are `outstanding`, `done`, `rehoming`, `skipped`, and the index groups by them in that
order. `plants/_collection.md` holds jobs that apply to everything rather than one plant, and
becomes the panel on the index plus `site/collection.html`.

## History

Git-backed since 21 August 2026 on `main`, remote `iamphilsampson/pan-garden`, **public**.
The history is the point of the project, so **commit and push after any session that changes a
plant's state.** One commit per session is plenty, and the message should say what actually
happened to the plants rather than which files moved.

Live at **https://iamphilsampson.github.io/pan-garden/**. Pushing to `main` rebuilds and
redeploys it via `.github/workflows/pages.yml`, so there is no deploy step to remember and the
hosted copy cannot drift from `plants/*.md`. The workflow flattens `../photos/` to `photos/` for
the hosted copy only, which is why opening `site/index.html` locally still works unchanged.

The repo is public, so **do not put anything in here that should not be.** Photos are visible to
anyone.

`site/` is gitignored because `build.py` regenerates it. Photos are committed, they are the
evidence.

## Files

| Path | What it is |
|---|---|
| `plants/` | **Source of truth.** Edit these |
| `build.py` | Generates the site. The frontmatter format is documented in its docstring |
| `site/` | Generated output, safe to delete and rebuild |
| `photos/` | Every plant photo, named by plant. Referenced as `../photos/x.jpg` |
| `plant-repot-plan.md` | The v6 knowledge doc. Soil recipes, feeding order, the reasoning behind every decision. Reference only, not the source of truth any more |
| `plants-to-action.html` | The old one-big-page working surface. Superseded by `site/`, kept for reference |
| `HANDOVER.md`, `HANDOVER-plant-manager.md` | Session handovers from the audit and the build |

## Conventions

- **British English, no em dashes, no emoji.** The existing docs follow this
- Palette is lifted from `plants-to-action.html` so it stays familiar. It lives in `CSS` at the
  top of `build.py`
- Do not re-derive the plant identifications, pot sizes or care advice. Four of Phil's plant
  names were wrong and the corrections are recorded
- **Precedence when the docs disagree: `plants/` beats `plants-to-action.html` beats
  `plant-repot-plan.md`**, in that order of recency. The plan doc is 5 August, the HTML is
  14 August. Reconciled on 21 August, when the plan doc's blockers turned out to be gating six
  jobs on materials already in the house. Do not migrate from either older file again
- **The default answer to "should I repot this" in this collection has been no.** Nine of the
  fourteen had the same two problems, not enough light and no feed. Only two genuinely needed a
  bigger pot
- Reversals are welcome. Where advice changed, the old position and the reason are kept in the
  plant's notes rather than quietly overwritten
