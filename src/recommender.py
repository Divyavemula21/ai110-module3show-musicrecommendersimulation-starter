import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# --- Scoring weights ---------------------------------------------------------
# These control how much each attribute matters in the final score.
# Tweak them for the "Experiments You Tried" section of the README:
# e.g. lower GENRE_WEIGHT to 0.5 and watch the ranking shift.
GENRE_WEIGHT = 2.0      # exact-match bonus for genre (biggest signal)
MOOD_WEIGHT = 1.0       # exact-match bonus for mood
ENERGY_WEIGHT = 1.0     # closeness of energy to the user's target
ACOUSTIC_WEIGHT = 0.5   # agreement with the user's acoustic preference (minor factor)

# --- Advanced feature weights (added in the "Advanced Song Features" step) ---
DECADE_WEIGHT = 1.0        # bonus when a song is from the user's favorite decade
TAG_WEIGHT = 0.5           # bonus per matching detailed mood tag (capped at 2 tags)
LANGUAGE_WEIGHT = 0.5      # bonus when the song's language matches the user's
POPULARITY_WEIGHT = 0.5    # bonus scaled by the user's popularity preference
EXPLICIT_PENALTY = 3.0     # penalty when a song is explicit and the user opted out
MAX_MATCHED_TAGS = 2       # cap on how many tags can earn points

# --- Diversity / fairness penalties ------------------------------------------
# Applied at RANK time (not per-song), to avoid filling the top results with the
# same artist or genre. Each already-selected song sharing the candidate's
# artist/genre subtracts these points from the candidate's score.
ARTIST_DIVERSITY_PENALTY = 1.5   # per earlier top-list song by the same artist
GENRE_DIVERSITY_PENALTY = 0.75   # per earlier top-list song of the same genre


# --- Scoring modes (Strategy pattern) ----------------------------------------
# Each "mode" is a strategy: an interchangeable bundle of weights that the ONE
# shared scoring algorithm uses. Swapping the mode swaps the ranking behavior
# without touching the scoring code, which keeps everything modular and DRY.
@dataclass(frozen=True)
class ScoringMode:
    """A named ranking strategy — the set of weights the scorer should use."""
    name: str
    genre_weight: float
    mood_weight: float
    energy_weight: float
    acoustic_weight: float
    decade_weight: float = DECADE_WEIGHT
    tag_weight: float = TAG_WEIGHT
    language_weight: float = LANGUAGE_WEIGHT
    popularity_weight: float = POPULARITY_WEIGHT
    explicit_penalty: float = EXPLICIT_PENALTY


# The default mode mirrors the finalized baseline weights, so scoring with no
# mode selected behaves exactly as before.
BALANCED = ScoringMode("Balanced", GENRE_WEIGHT, MOOD_WEIGHT, ENERGY_WEIGHT, ACOUSTIC_WEIGHT)
GENRE_FIRST = ScoringMode("Genre-First", genre_weight=3.0, mood_weight=1.0,
                          energy_weight=0.5, acoustic_weight=0.5)
MOOD_FIRST = ScoringMode("Mood-First", genre_weight=1.0, mood_weight=3.0,
                         energy_weight=1.0, acoustic_weight=0.5)
ENERGY_FOCUSED = ScoringMode("Energy-Focused", genre_weight=1.0, mood_weight=0.5,
                             energy_weight=3.0, acoustic_weight=0.5)

# Registry so callers (like main.py) can pick a strategy by name.
MODES: Dict[str, "ScoringMode"] = {
    m.name: m for m in (BALANCED, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED)
}


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py

    The first block of fields is the original baseline. The advanced features
    (popularity, release_decade, mood_tags, language, explicit) have defaults so
    older code and tests that build a Song without them still work.
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # --- advanced features ---
    popularity: int = 50                       # 0-100 popularity score
    release_decade: int = 2020                 # e.g. 1980, 2000, 2020
    mood_tags: List[str] = field(default_factory=list)  # e.g. ["nostalgic", "euphoric"]
    language: str = "instrumental"             # e.g. english, spanish, instrumental
    explicit: bool = False                     # explicit content flag


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    Advanced preferences default to "no opinion" (None/empty/allow) so existing
    profiles that only set the baseline four fields behave exactly as before.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # --- advanced preferences ---
    favorite_decade: Optional[int] = None
    preferred_tags: List[str] = field(default_factory=list)
    preferred_language: Optional[str] = None
    prefers_popular: Optional[bool] = None     # True=mainstream, False=niche, None=no opinion
    allow_explicit: bool = True


def _score(
    favorite_genre: str,
    favorite_mood: str,
    target_energy: float,
    likes_acoustic: bool,
    genre: str,
    mood: str,
    energy: float,
    acousticness: float,
    *,
    mode: Optional[ScoringMode] = None,
    # advanced preferences / attributes (keyword-only, all optional)
    favorite_decade: Optional[int] = None,
    preferred_tags: Optional[List[str]] = None,
    preferred_language: Optional[str] = None,
    prefers_popular: Optional[bool] = None,
    allow_explicit: bool = True,
    popularity: int = 50,
    release_decade: Optional[int] = None,
    mood_tags: Optional[List[str]] = None,
    language: Optional[str] = None,
    explicit: bool = False,
) -> Tuple[float, List[str]]:
    """
    Shared scoring rule (the "score ONE song" logic).

    Works on plain values so both the OOP path (Song/UserProfile) and the
    functional path (dicts) can reuse the exact same math. Returns the numeric
    score plus a list of human-readable reasons for the explanation.

    The optional `mode` is a ScoringMode strategy that supplies the weights.
    When it is None, the module-level weight constants are used, so old callers
    behave exactly as before. Different modes (Genre-First, Mood-First,
    Energy-Focused, ...) reuse this same algorithm with different weights.

    Genre/mood matching is case-insensitive, so "Pop" and "pop" behave the same.
    """
    # Pick the weights from the chosen strategy, or fall back to the globals.
    genre_w = GENRE_WEIGHT if mode is None else mode.genre_weight
    mood_w = MOOD_WEIGHT if mode is None else mode.mood_weight
    energy_w = ENERGY_WEIGHT if mode is None else mode.energy_weight
    acoustic_w = ACOUSTIC_WEIGHT if mode is None else mode.acoustic_weight
    decade_w = DECADE_WEIGHT if mode is None else mode.decade_weight
    tag_w = TAG_WEIGHT if mode is None else mode.tag_weight
    language_w = LANGUAGE_WEIGHT if mode is None else mode.language_weight
    popularity_w = POPULARITY_WEIGHT if mode is None else mode.popularity_weight
    explicit_pen = EXPLICIT_PENALTY if mode is None else mode.explicit_penalty

    preferred_tags = preferred_tags or []
    mood_tags = mood_tags or []
    score = 0.0
    reasons: List[str] = []

    # Categorical: case-insensitive exact match or nothing.
    # Each reason records the points it contributed, e.g. "genre match: pop (+2.0)".
    if favorite_genre is not None and genre.lower() == favorite_genre.lower():
        score += genre_w
        reasons.append(f"genre match: {genre} (+{genre_w:.1f})")

    if favorite_mood is not None and mood.lower() == favorite_mood.lower():
        score += mood_w
        reasons.append(f"mood match: {mood} (+{mood_w:.1f})")

    # Numerical: reward closeness, not equality. Same 0-1 scale, so
    # (1 - abs(diff)) is 1.0 for a perfect match and 0.0 at opposite ends.
    energy_closeness = 1 - abs(energy - target_energy)
    energy_points = energy_w * energy_closeness
    score += energy_points
    if energy_closeness >= 0.8:
        reasons.append(f"energy {energy} close to target {target_energy} (+{energy_points:.2f})")

    # Preference: acousticness read in the direction the user prefers.
    if likes_acoustic:
        acoustic_points = acoustic_w * acousticness
        score += acoustic_points
        if acousticness >= 0.6:
            reasons.append(f"acoustic, which you like (+{acoustic_points:.2f})")
    else:
        acoustic_points = acoustic_w * (1 - acousticness)
        score += acoustic_points
        if acousticness <= 0.4:
            reasons.append(f"produced/electronic, which you prefer (+{acoustic_points:.2f})")

    # --- Advanced features ---------------------------------------------------

    # Release decade: exact-match bonus (only if the user named a decade).
    if favorite_decade is not None and release_decade == favorite_decade:
        score += decade_w
        reasons.append(f"from your favorite decade ({release_decade}s) (+{decade_w:.1f})")

    # Detailed mood tags: points per overlapping tag, capped so a heavily
    # tagged song cannot run away with the score.
    if preferred_tags:
        wanted = {t.lower() for t in preferred_tags}
        matched = [t for t in mood_tags if t.lower() in wanted]
        if matched:
            capped = min(len(matched), MAX_MATCHED_TAGS)
            tag_points = tag_w * capped
            score += tag_points
            reasons.append(f"tags match: {', '.join(matched[:MAX_MATCHED_TAGS])} (+{tag_points:.1f})")

    # Language: exact-match bonus (case-insensitive).
    if preferred_language is not None and language is not None and \
            language.lower() == preferred_language.lower():
        score += language_w
        reasons.append(f"language match: {language} (+{language_w:.1f})")

    # Popularity: reward mainstream or niche depending on the user's taste.
    if prefers_popular is True:
        pop_points = popularity_w * (popularity / 100)
        score += pop_points
        if popularity >= 70:
            reasons.append(f"popular ({popularity}/100) (+{pop_points:.2f})")
    elif prefers_popular is False:
        pop_points = popularity_w * (1 - popularity / 100)
        score += pop_points
        if popularity <= 50:
            reasons.append(f"niche ({popularity}/100) (+{pop_points:.2f})")

    # Explicit content: strong down-rank when the user opts out.
    if not allow_explicit and explicit:
        score -= explicit_pen
        reasons.append(f"explicit content, which you excluded (-{explicit_pen:.1f})")

    return score, reasons


def _explanation_from_reasons(reasons: List[str]) -> str:
    """Turn a list of reasons into a readable sentence."""
    if not reasons:
        return "Recommended as a general match for your profile."
    return "Recommended because " + ", ".join(reasons) + "."


def _diversified_order(
    entries: List[Tuple[object, float, List[str], str, str]],
    k: int,
    artist_penalty: float = ARTIST_DIVERSITY_PENALTY,
    genre_penalty: float = GENRE_DIVERSITY_PENALTY,
) -> List[Tuple[object, float, List[str]]]:
    """
    Greedily build a diverse top-k list (a fairness re-ranker).

    `entries` is a list of (item, base_score, reasons, artist, genre) sorted by
    base_score descending. We repeatedly pick the best *adjusted* candidate,
    where the adjustment subtracts a penalty for every already-chosen song that
    shares the candidate's artist or genre. Because the penalty depends on what
    has already been picked, this cannot be done in per-song scoring — it has to
    happen here, at rank time.

    Returns a list of (item, adjusted_score, reasons); when a song was penalized,
    a "diversity penalty" note is appended to its reasons so the drop is visible.
    """
    selected: List[Tuple[object, float, List[str]]] = []
    chosen_artists: List[str] = []
    chosen_genres: List[str] = []
    remaining = list(entries)

    while remaining and len(selected) < k:
        best_idx = 0
        best_adj = None
        for i, (_item, base, _reasons, artist, genre) in enumerate(remaining):
            a_count = chosen_artists.count(artist)
            g_count = chosen_genres.count(genre)
            adj = base - artist_penalty * a_count - genre_penalty * g_count
            # entries are pre-sorted by base score, so the first max wins ties,
            # keeping the higher base-scored song ahead when penalties are equal.
            if best_adj is None or adj > best_adj:
                best_adj = adj
                best_idx = i

        item, base, reasons, artist, genre = remaining.pop(best_idx)
        a_count = chosen_artists.count(artist)
        g_count = chosen_genres.count(genre)
        penalty = artist_penalty * a_count + genre_penalty * g_count

        reasons = list(reasons)
        if penalty > 0:
            notes = []
            if a_count:
                notes.append(f"{a_count} earlier by {artist}")
            if g_count:
                notes.append(f"{g_count} earlier {genre} song(s)")
            reasons.append(f"diversity penalty ({'; '.join(notes)}) (-{penalty:.2f})")

        selected.append((item, base - penalty, reasons))
        chosen_artists.append(artist)
        chosen_genres.append(genre)

    return selected


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score_song(self, user: UserProfile, song: Song,
                    mode: Optional[ScoringMode] = None) -> Tuple[float, List[str]]:
        """Score one Song against a UserProfile, returning (score, reasons)."""
        return _score(
            user.favorite_genre,
            user.favorite_mood,
            user.target_energy,
            user.likes_acoustic,
            mode=mode,
            favorite_decade=user.favorite_decade,
            preferred_tags=user.preferred_tags,
            preferred_language=user.preferred_language,
            prefers_popular=user.prefers_popular,
            allow_explicit=user.allow_explicit,
            genre=song.genre,
            mood=song.mood,
            energy=song.energy,
            acousticness=song.acousticness,
            popularity=song.popularity,
            release_decade=song.release_decade,
            mood_tags=song.mood_tags,
            language=song.language,
            explicit=song.explicit,
        )

    def recommend(self, user: UserProfile, k: int = 5,
                  mode: Optional[ScoringMode] = None,
                  diversity: bool = False) -> List[Song]:
        """Return the top-k Songs for a user, ranked highest score first.

        Pass a ScoringMode to rank with a different strategy (e.g. GENRE_FIRST).
        Pass diversity=True to apply the artist/genre fairness re-ranker.
        """
        # Ranking rule: score every song, sort by score descending, take top k.
        ranked = sorted(
            self.songs,
            key=lambda song: self._score_song(user, song, mode)[0],
            reverse=True,
        )
        if diversity:
            entries = [
                (song, self._score_song(user, song, mode)[0], [], song.artist, song.genre)
                for song in ranked
            ]
            return [item for item, _adj, _reasons in _diversified_order(entries, k)]
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song,
                               mode: Optional[ScoringMode] = None) -> str:
        """Return a one-sentence, plain-language reason a song was recommended."""
        _, reasons = self._score_song(user, song, mode)
        return _explanation_from_reasons(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py

    Converts numeric columns to numbers, splits the pipe-separated mood_tags
    field into a list, and parses the explicit flag into a real bool, so the
    scoring logic can use every column directly.
    """
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}
    int_fields = {"id", "popularity", "release_decade"}
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = dict(row)
            for f_name in int_fields:
                if f_name in song and song[f_name] != "":
                    song[f_name] = int(song[f_name])
            for f_name in float_fields:
                if f_name in song and song[f_name] != "":
                    song[f_name] = float(song[f_name])
            # mood_tags is a pipe-separated list, e.g. "nostalgic|euphoric".
            if "mood_tags" in song:
                song["mood_tags"] = [
                    t.strip() for t in song["mood_tags"].split("|") if t.strip()
                ]
            # explicit is stored as "True"/"False" text.
            if "explicit" in song:
                song["explicit"] = str(song["explicit"]).strip().lower() == "true"
            songs.append(song)
    return songs


def score_song(user_prefs: Dict, song: Dict,
               mode: Optional[ScoringMode] = None) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences (the "score ONE song" rule).
    Required by recommend_songs() and src/main.py

    Accepts either the short dict keys (genre, mood, energy) or the UserProfile-
    style keys (favorite_genre, favorite_mood, target_energy), so a profile
    written in either style works. Advanced preferences are optional; a song
    dict missing an advanced column falls back to a sensible default. Pass a
    ScoringMode to score with a different strategy's weights.
    """
    favorite_genre = user_prefs.get("genre", user_prefs.get("favorite_genre"))
    favorite_mood = user_prefs.get("mood", user_prefs.get("favorite_mood"))
    target_energy = user_prefs.get("energy", user_prefs.get("target_energy", 0.5))
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    return _score(
        favorite_genre,
        favorite_mood,
        target_energy,
        likes_acoustic,
        song["genre"],
        song["mood"],
        song["energy"],
        song["acousticness"],
        mode=mode,
        favorite_decade=user_prefs.get("favorite_decade"),
        preferred_tags=user_prefs.get("preferred_tags"),
        preferred_language=user_prefs.get("preferred_language"),
        prefers_popular=user_prefs.get("prefers_popular"),
        allow_explicit=user_prefs.get("allow_explicit", True),
        popularity=song.get("popularity", 50),
        release_decade=song.get("release_decade"),
        mood_tags=song.get("mood_tags"),
        language=song.get("language"),
        explicit=song.get("explicit", False),
    )


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    mode: Optional[ScoringMode] = None,
                    diversity: bool = False) -> List[Tuple[Dict, float, List[str]]]:
    """
    Functional implementation of the recommendation logic (the ranking rule).
    Required by src/main.py

    Scores every song, sorts by score descending, returns the top k as
    (song_dict, score, reasons) tuples, where reasons is the list of
    point-annotated strings from score_song (e.g. "genre match: pop (+2.0)").
    Callers can print the reasons individually or join them into a sentence
    with _explanation_from_reasons(). Pass a ScoringMode to rank with a
    different strategy.

    When diversity=True, a fairness re-ranker (`_diversified_order`) penalizes
    songs whose artist or genre already appears higher in the list, so the top
    results are not dominated by one artist or genre.
    """
    scored: List[Tuple[Dict, float, List[str]]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, mode)
        scored.append((song, score, reasons))

    scored.sort(key=lambda item: item[1], reverse=True)

    if diversity:
        entries = [(s, sc, r, s.get("artist", ""), s.get("genre", "")) for s, sc, r in scored]
        return _diversified_order(entries, k)  # type: ignore[return-value]
    return scored[:k]
