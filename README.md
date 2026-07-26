# 🎵 Music Recommender Simulation

## Project Summary

In this project I will build and explain a small music recommender system.

MY goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders


---

## How The System Works

My recommender works in two clear steps: a **scoring rule** that rates one song, and a
**ranking rule** that sorts all the songs and returns the best few.

**What each `Song` stores:** genre, mood, energy, tempo (BPM), valence, danceability,
acousticness, plus the advanced features `popularity` (0–100), `release_decade`, `mood_tags`
(detailed tags like *nostalgic*, *euphoric*), `language`, and `explicit`.

**What the `UserProfile` stores:** the listener's `favorite_genre`, `favorite_mood`,
`target_energy` (0–1), and `likes_acoustic` (true/false), plus optional advanced preferences:
`favorite_decade`, `preferred_tags`, `preferred_language`, `prefers_popular`, and
`allow_explicit`. The advanced preferences default to "no opinion," so a profile that only sets
the baseline four fields behaves exactly as before.

### My Algorithm Recipe

This is the finalized set of rules my program uses to decide what to recommend.

**Scoring rule — how one song earns points.** Each song starts at `0` and gains points:

| Feature | Rule | Points |
| --- | --- | --- |
| **Genre** | exact match with the user's favorite genre (case-insensitive) | **+2.0** |
| **Mood** | exact match with the user's favorite mood (case-insensitive) | **+1.0** |
| **Energy** | closeness to the user's target, not equality | **+1.0 × (1 − \|song energy − target energy\|)** |
| **Acousticness** | agrees with `likes_acoustic`: `+0.5 × acousticness` if true, else `+0.5 × (1 − acousticness)` | **±0.5** (minor factor) |
| **Release decade** | song is from the user's `favorite_decade` | **+1.0** |
| **Mood tags** | each of the user's `preferred_tags` found on the song (capped at 2) | **+0.5 each** |
| **Language** | song's `language` matches `preferred_language` | **+0.5** |
| **Popularity** | scaled by `prefers_popular` (mainstream vs niche) | **up to +0.5** |
| **Explicit** | song is explicit but the user set `allow_explicit=False` | **−3.0** |

The baseline four features (genre, mood, energy, acousticness) always apply. The advanced
features only add points when the user actually expresses that preference, so old profiles are
unaffected. Categorical features (genre, mood, decade, language) answer *"is this the right kind
of song?"* while numeric features (energy, popularity) fine-tune *"which of these is the best
match?"* Energy rewards *closeness* — a song at 0.82 when the user wants 0.80 scores nearly full
points. The weights live as named constants at the top of `recommender.py`, so I can experiment
by changing one line.

**Ranking rule — how songs are chosen.** I run the scoring rule on every song, sort them from
highest to lowest score, and return the top `k`. Each recommendation comes with a plain-language
explanation built from the same reasons that produced its score.

### Scoring Modes (Strategy pattern)

The recommender supports interchangeable ranking strategies, built with a simple **Strategy
pattern**: each mode is a `ScoringMode` object holding one set of weights, and the single
scoring algorithm reads whichever mode it is given. Switch modes in `main.py` via `SCORING_MODE`:

- **Balanced** (default) — the finalized weights above.
- **Genre-First** — genre dominates (genre 3.0), energy matters less.
- **Mood-First** — mood dominates (mood 3.0), so same-mood songs rise even across genres.
- **Energy-Focused** — energy dominates (energy 3.0), favoring the closest energy match.

Running the app prints a mode-comparison for one profile so you can see the same code produce
different rankings — for example, Mood-First drops an `intense` song out of the top 3 for a
listener who wants `happy`, while Energy-Focused pulls the highest-energy songs up.

### Diversity & Fairness Penalty

To avoid a single artist or genre dominating the results, `recommend_songs(..., diversity=True)`
applies a fairness re-ranker. Because a song's penalty depends on what is *already* in the list,
this happens at rank time (not in per-song scoring): the top-k is built greedily, and each
candidate loses points for every already-chosen song that shares its **artist** (−1.5 each) or
**genre** (−0.75 each). For the Chill Lofi profile this breaks up a LoRoom "monopoly" — with the
penalty on, two LoRoom tracks drop and an ambient and a jazz song rise into the top 5. The
penalty is shown in the song's reasons so the drop stays explainable, and it is off by default.

### Potential Biases I Expect

- **Genre over-prioritization.** Genre is the heaviest weight (2.0), so the system can favor a
  genre match and overlook great songs that match the user's *mood* but sit in a different genre.
- **Popular-vibe bias.** Because a single genre match (2.0) outweighs the whole numeric range,
  a listener who names a broadly-represented genre gets many strong matches, while someone whose
  favorite genre has only one or two songs in the catalog gets thin results.
- **Filter bubble.** Scoring only rewards *similarity* to the stated profile, so it keeps
  recommending more of the same and never surfaces something pleasantly unexpected.
- **Case/format sensitivity (mitigated).** Matching is now case-insensitive and accepts both
  `genre`/`favorite_genre` key styles, but the system still trusts whatever preferences it is
  given — a mood the catalog doesn't contain simply scores nothing, with no warning.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

The recommendations are printed as a formatted ASCII table (Challenge 4) that includes the
song, artist, final score, and the specific **reasons** (with point values) behind each score.
`python -m src.main` prints one table per profile; the **High-Energy Pop** table below is a
representative example (the other three profiles render the same way).

```
+---+----------------+---------------+-------+------------------------------------------------+
| # | Title          | Artist        | Score | Reasons                                        |
+---+----------------+---------------+-------+------------------------------------------------+
| 1 | Sunrise City   | Neon Echo     |  6.75 | genre match: pop (+2.0)                        |
|   |                |               |       | mood match: happy (+1.0)                       |
|   |                |               |       | energy 0.82 close to target 0.9 (+0.92)        |
|   |                |               |       | produced/electronic, which you prefer (+0.41)  |
|   |                |               |       | from your favorite decade (2020s) (+1.0)       |
|   |                |               |       | tags match: euphoric (+0.5)                    |
|   |                |               |       | language match: english (+0.5)                 |
|   |                |               |       | popular (85/100) (+0.42)                       |
+---+----------------+---------------+-------+------------------------------------------------+
| 2 | Gym Hero       | Max Pulse     |  5.89 | genre match: pop (+2.0)                        |
|   |                |               |       | energy 0.93 close to target 0.9 (+0.97)        |
|   |                |               |       | produced/electronic, which you prefer (+0.47)  |
|   |                |               |       | from your favorite decade (2020s) (+1.0)       |
|   |                |               |       | tags match: energetic (+0.5)                   |
|   |                |               |       | language match: english (+0.5)                 |
|   |                |               |       | popular (88/100) (+0.44)                       |
+---+----------------+---------------+-------+------------------------------------------------+
| 3 | Festival Sky   | Aurora Drop   |  4.93 | mood match: happy (+1.0)                       |
|   |                |               |       | energy 0.9 close to target 0.9 (+1.00)         |
|   |                |               |       | produced/electronic, which you prefer (+0.47)  |
|   |                |               |       | from your favorite decade (2020s) (+1.0)       |
|   |                |               |       | tags match: euphoric (+0.5)                    |
|   |                |               |       | language match: english (+0.5)                 |
|   |                |               |       | popular (92/100) (+0.46)                       |
+---+----------------+---------------+-------+------------------------------------------------+
| 4 | Neon Pulse     | Voltage Kids  |  4.38 | energy 0.95 close to target 0.9 (+0.95)        |
|   |                |               |       | produced/electronic, which you prefer (+0.48)  |
|   |                |               |       | from your favorite decade (2020s) (+1.0)       |
|   |                |               |       | tags match: euphoric, energetic (+1.0)         |
|   |                |               |       | language match: english (+0.5)                 |
|   |                |               |       | popular (90/100) (+0.45)                       |
+---+----------------+---------------+-------+------------------------------------------------+
| 5 | Rooftop Lights | Indigo Parade |  3.54 | mood match: happy (+1.0)                       |
|   |                |               |       | energy 0.76 close to target 0.9 (+0.86)        |
|   |                |               |       | produced/electronic, which you prefer (+0.33)  |
|   |                |               |       | tags match: euphoric (+0.5)                    |
|   |                |               |       | language match: english (+0.5)                 |
|   |                |               |       | popular (70/100) (+0.35)                       |
+---+----------------+---------------+-------+------------------------------------------------+
```

The app also prints a **mode comparison** and a **diversity comparison** (compact lists) after
the tables, so you can see how switching strategies or enabling the fairness penalty re-ranks
the results.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

**Experiment 1 — Lowering the genre weight (2.0 → 0.5).**
With the default `GENRE_WEIGHT = 2.0` and the profile `genre=pop, mood=happy, energy=0.8`,
the top three were **Sunrise City** (pop), **Gym Hero** (pop), then **Rooftop Lights**
(indie pop). After lowering `GENRE_WEIGHT` to `0.5`, the ranking shifted:

```
Sunrise City (pop) - 3.39
Rooftop Lights (indie pop) - 2.79   <- moved up
Gym Hero (pop) - 1.85               <- moved down
Storm Runner (rock) - 1.34
Night Drive Loop (synthwave) - 1.34
```

**Rooftop Lights** jumped above **Gym Hero**. That makes sense: once genre matters less,
the *mood* match dominates — Rooftop Lights is `happy` (matching the user) while Gym Hero is
`intense`. This showed me how sensitive recommendations are to the weights I choose.

**What I noticed about different users:** a user who wants low energy and likes acoustic gets
completely different results (lofi, jazz, ambient tracks rise to the top), which confirmed the
energy-closeness and acoustic-preference parts of the score are actually doing work.

**Experiment 2 — Sensitivity test: double energy weight, halve genre weight**
(`ENERGY_WEIGHT` 1.0 → 2.0, `GENRE_WEIGHT` 2.0 → 1.0). I temporarily changed the two
constants in `recommender.py` and re-ran the three profiles:

| Profile | Baseline top 3 | After the shift |
| --- | --- | --- |
| High-Energy Pop | Sunrise City > Gym Hero > Festival Sky | Sunrise City > **Festival Sky** > Gym Hero |
| Chill Lofi | Library Rain > Midnight Coding > Sleepy Static | Library Rain > Midnight Coding > **Spacewalk Thoughts** |
| Deep Intense Rock | Basement Riff > Storm Runner > Gym Hero | Basement Riff > Storm Runner > Gym Hero |

The #1 pick stayed the same in every profile, but the **2nd and 3rd slots reshuffled toward
whichever song best matched the target energy**, even across genres: Festival Sky (edm) climbed
above Gym Hero for the pop listener, and Spacewalk Thoughts (ambient) broke into the lofi
listener's top 3. I verified the math still adds up — e.g. Basement Riff's energy term doubled
from `+0.97` to `+1.94`, and the reported total matched a manual recompute exactly. This showed
that energy is a strong *tie-breaker* but genre + mood together still anchor the top result.
I reverted to the finalized weights (`GENRE_WEIGHT = 2.0`, `ENERGY_WEIGHT = 1.0`) afterward.

---

## Limitations and Risks

My recommender is intentionally simple, so it has real limitations:

- **Tiny catalog.** It only works on the 17 songs in `data/songs.csv`, so "recommendations"
  are really just a ranking of a handful of tracks.
- **No cross-user learning (content-based only).** Unlike Spotify, it never learns from other
  listeners, so it can't surprise you with something outside your stated profile — this is the
  classic *filter bubble*.
- **Only knows the attributes I measure.** It ignores lyrics, language, artist history, and
  release year, and doesn't use tempo, valence, or danceability in the score yet.
- **Can over-favor one genre or mood.** Because genre carries the largest weight, a user's
  favorite genre can dominate the top results and crowd out good matches from other genres.
- **Underrepresented tastes.** Some genres appear only once in the catalog, so a user who loves,
  say, classical or hip-hop would get poor results simply because the data isn't there.

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this

Real-world recommenders like Spotify and YouTube predict what you'll enjoy next by
combining two main strategies: *collaborative filtering*, which learns from other users' behavior ("people with taste like yours also played this"), and *content-based filtering*, which matches the attributes of items — genre, mood, tempo, energy — to what you've already
liked. At scale they blend both, layering in signals like skips, saves, playlist adds, and time of day, then score every candidate and rank the top few to show you. My version is a simplified, purely content-based recommender: it doesn't know about other users, so instead
it builds a profile of the listener's taste (favorite genre, favorite mood, target energy, and acoustic preference) and scores each song by how well its attributes match. I prioritize genre and mood as the strongest signals, reward songs whose energy is closest to the user's target, and factor in the acoustic preference — then rank all songs by that score and return
the best matches, each with a plain-language explanation of *why* it was recommended. This means my system is transparent and handles brand-new songs well, but it can fall into a "filter bubble" of very similar recommendations, since it has no way to learn from a wider
community of listeners.



