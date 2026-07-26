# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked the agent to add "advanced song features" across the whole project: introduce five
new attributes to the dataset and update the scoring logic so recommendations take them into
account. This was a multi-step change that touched the data file, the dataclasses, the CSV
loader, and the scoring rules all at once.

**Prompts used:**

- "Introduce 5 or more complex attributes to my dataset that are not currently present, such
  as Song Popularity (0-100), Release Decade, or detailed mood tags (e.g. nostalgic,
  aggressive, euphoric). Update both data/songs.csv and the scoring logic in
  src/recommender.py so scoring accounts for the new attributes."
- Follow-up: "Make sure the existing tests still pass and that profiles which don't set the new
  preferences behave exactly as before."
- Follow-up: "Verify the explicit-content penalty actually changes a song's score."

**What did the agent generate or change?**

- **data/songs.csv** — added 5 new columns for all 17 songs: `popularity` (0-100),
  `release_decade`, `mood_tags` (pipe-separated detailed tags like `nostalgic|euphoric`),
  `language`, and `explicit`.
- **src/recommender.py** — added new fields to the `Song` and `UserProfile` dataclasses (all
  with defaults), new scoring weights, and new scoring rules: decade match (+1.0), matching
  mood tags (+0.5 each, capped at 2), language match (+0.5), a popularity bonus scaled by a
  "mainstream vs niche" preference, and an explicit-content penalty (−3.0). It updated
  `load_songs` to parse the new columns (ints, a list for tags, a real bool for explicit) and
  wired the new values through both the OOP and functional scoring paths.
- **src/main.py** — enriched the three taste profiles with the new preferences and added a
  fourth profile ("Clean Nostalgic Synthwave") that uses `favorite_decade`, tags, language,
  niche preference, and `allow_explicit=False`.

**What did you verify or fix manually?**

- Ran `pytest` — the two starter tests still pass, confirming the new dataclass fields (added
  with defaults) did not break existing `Song`/`UserProfile` construction.
- Ran `python -m src.main` and read the reason lists to confirm each new feature actually
  awards points (e.g. "from your favorite decade (2020s) (+1.0)", "tags match: euphoric,
  energetic (+1.0)").
- Manually tested the explicit penalty: Basement Riff (an explicit song) scored 4.41 with
  `allow_explicit=True` and 1.41 with `allow_explicit=False` — a clean −3.0 difference, with the
  reason shown.
- Checked the CSV parsing: `mood_tags` loads as a Python list and `explicit` loads as a real
  bool, not strings, so the scoring math and boolean checks work without errors.
- One thing I made sure of: profiles that don't set the advanced preferences (like in the
  starter tests) get zero extra points, so the change is backward-compatible rather than
  silently shifting old results.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern**. I wanted several ranking "modes" (Balanced, Genre-First, Mood-First,
Energy-Focused) that a user can switch between, without copying the scoring code four times.
The Strategy pattern fits because each mode is an interchangeable algorithm variant that the
program can swap in at run time.

**How did AI help you brainstorm or implement it?**

I asked the AI to brainstorm a modular way to support multiple scoring modes. It walked me
through a few options — subclassing a base scorer, passing a scoring function, or bundling the
weights into a "strategy" object — and we discussed the trade-offs. The key insight it offered
was that my modes only differ by their *weights*, not by the steps of the algorithm, so a full
class hierarchy would just duplicate logic. We settled on a lightweight Strategy: a small
frozen `ScoringMode` dataclass that holds one set of weights, with the shared `_score` function
reading its weights from whichever mode is passed in. It also suggested keeping a default
(`mode=None` uses the module constants) so the change stayed backward-compatible and the
existing tests kept passing.

**How does the pattern appear in your final code?**

- The strategy type is the `ScoringMode` dataclass in `src/recommender.py`, with four ready-made
  strategy instances (`BALANCED`, `GENRE_FIRST`, `MOOD_FIRST`, `ENERGY_FOCUSED`) and a `MODES`
  registry that maps a name to a strategy.
- The single algorithm, `_score()`, takes a `mode` argument and pulls its weights from that
  strategy (falling back to the module constants when no mode is given), so there is exactly one
  copy of the scoring math.
- `recommend_songs()` and `Recommender.recommend()` accept a `mode` and pass it straight through.
- `src/main.py` picks a strategy by name (`SCORING_MODE`) and has a `compare_modes()` helper that
  re-ranks one profile under every mode, which shows the strategies are truly interchangeable.

I verified it by running `python -m src.main`: switching to Mood-First pushed happy-mood songs up
and dropped an intense-mood song out of the top 3, while Energy-Focused pulled the highest-energy
songs up — different rankings from the same code, exactly what the pattern is for.
