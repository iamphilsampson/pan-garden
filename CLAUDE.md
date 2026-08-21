# Pan Garden

Houseplant manager. Fourteen plants, per-plant state, outstanding jobs and a dated history.
Started as an annual repotting audit in August 2026, kept as a running record.

## How it works

`plants/*.md` is the source of truth. One file per plant: YAML frontmatter for state, markdown
below it for care notes. `build.py` generates `site/` from those plus `photos/`.

```bash
python3 build.py
```

Static, no server, no npm, no CDN, standard library only.

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

Live at **https://iamphilsampson.github.io/pan-garden/**. Pushing to `main` rebuilds and redeploys
via `.github/workflows/pages.yml`, so there is no deploy step and the hosted copy cannot drift.
It flattens `../photos/` to `photos/` for the hosted copy only, so local `site/index.html` still
works unchanged.

The repo is **public**. Do not put anything in it that should not be.

`site/` is gitignored because `build.py` regenerates it. Photos are committed, they are the
evidence.

## Files

| Path | What it is |
|---|---|
| `plants/` | **Source of truth.** Edit these |
| `build.py` | Generates the site. The frontmatter format is documented in its docstring |
| `site/` | Generated output, safe to delete and rebuild |
| `photos/` | Every plant photo, named by plant. Referenced as `../photos/x.jpg` |
| `plant-repot-plan.md`, `plants-to-action.html` | Historical reference. Superseded, see the precedence rule below |
| `HANDOVER.md`, `HANDOVER-plant-manager.md` | Session handovers from the audit and the build |

## Picking this back up

Nothing is needed to keep it alive. To verify: open the live URL, then run `python3 build.py`.

**If the site has stopped updating**, the Actions workflow has aged out, most likely a deprecated
action version. It fails safe, the last good deploy stays up, so it is never urgent. Bump the
`uses:` versions in `.github/workflows/pages.yml`, and build locally in the meantime.

**Due February 2027:** wrap Prop Joe's air layer around the 20th, and start feeding again in March.
Both are dated on their pages.

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
  fourteen had the same two problems, not enough light and no feed. **Exactly one, Prop Joe, was
  ever proven short of root space.** Roots at the drainage holes has meant out of fresh soil, not
  out of room, every single time it has been checked
- **Do not diagnose roots from a photograph.** Two errors on 21 August came from doing that: a
  root ball attributed to the wrong plant, and "escaped roots" written up as a "dense root mat".
  Get the plant out of the pot and look, or ask Phil what he saw
- Reversals are welcome. Where advice changed, the old position and the reason are kept in the
  plant's notes rather than quietly overwritten
