"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import textwrap

from src.recommender import load_songs, recommend_songs, MODES, BALANCED

# Switch the ranking strategy here. Options come from recommender.MODES:
# "Balanced", "Genre-First", "Mood-First", "Energy-Focused".
SCORING_MODE = "Balanced"


# A few distinct taste profiles to compare how the recommender responds to
# very different listeners. Each maps to the features the scoring rule reads,
# including the advanced ones: favorite_decade, preferred_tags,
# preferred_language, prefers_popular, and allow_explicit.
USER_PROFILES = {
    "High-Energy Pop": {
        "genre": "pop", "mood": "happy", "energy": 0.9, "likes_acoustic": False,
        "favorite_decade": 2020, "preferred_tags": ["euphoric", "energetic"],
        "preferred_language": "english", "prefers_popular": True,
        "allow_explicit": True,
    },
    "Chill Lofi": {
        "genre": "lofi", "mood": "chill", "energy": 0.3, "likes_acoustic": True,
        "favorite_decade": 2020, "preferred_tags": ["calm", "nostalgic"],
        "preferred_language": "instrumental", "prefers_popular": False,
        "allow_explicit": True,
    },
    "Deep Intense Rock": {
        "genre": "rock", "mood": "intense", "energy": 0.85, "likes_acoustic": False,
        "favorite_decade": 2010, "preferred_tags": ["aggressive", "energetic"],
        "preferred_language": "english", "prefers_popular": None,
        "allow_explicit": True,
    },
    "Clean Nostalgic Synthwave": {
        "genre": "synthwave", "mood": "moody", "energy": 0.7, "likes_acoustic": False,
        "favorite_decade": 1980, "preferred_tags": ["nostalgic", "moody"],
        "preferred_language": "instrumental", "prefers_popular": False,
        "allow_explicit": False,
    },
}


def render_table(rows: list, reason_width: int = 46) -> str:
    """
    Render recommendations as a bordered ASCII table (no external dependency).

    `rows` is a list of (rank, title, artist, score, reasons_list). The Reasons
    column lists each reason on its own line (wrapped to reason_width) so the
    point breakdown behind every score stays visible in the table.

    (A library like `tabulate` could produce a similar table in one call; plain
    ASCII is used here so the app runs with no extra install.)
    """
    headers = ["#", "Title", "Artist", "Score", "Reasons"]
    w_rank = max(len(headers[0]), *(len(str(r[0])) for r in rows))
    w_title = max(len(headers[1]), *(len(r[1]) for r in rows))
    w_artist = max(len(headers[2]), *(len(r[2]) for r in rows))
    w_score = max(len(headers[3]), *(len(f"{r[3]:.2f}") for r in rows))
    w_reason = max(len(headers[4]), reason_width)
    widths = (w_rank, w_title, w_artist, w_score, w_reason)

    def hline() -> str:
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def row(c0, c1, c2, c3, c4) -> str:
        return (f"| {c0:<{w_rank}} | {c1:<{w_title}} | {c2:<{w_artist}} "
                f"| {c3:>{w_score}} | {c4:<{w_reason}} |")

    lines = [hline(), row(*headers), hline()]
    for rank, title, artist, score, reasons in rows:
        reason_lines: list = []
        for reason in reasons:
            reason_lines.extend(textwrap.wrap(reason, w_reason) or [""])
        if not reason_lines:
            reason_lines = [""]
        for i, rline in enumerate(reason_lines):
            if i == 0:
                lines.append(row(str(rank), title, artist, f"{score:.2f}", rline))
            else:
                lines.append(row("", "", "", "", rline))
        lines.append(hline())
    return "\n".join(lines)


def print_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5,
                          mode=None, diversity: bool = False) -> None:
    """Print the top-k recommendations for one named taste profile as a table."""
    header = f"{name}  ({user_prefs['genre']} / {user_prefs['mood']} / energy {user_prefs['energy']})"
    print()
    print("=" * len(header))
    print(header)
    print("=" * len(header))

    # Each recommendation is (song, score, reasons) — see recommend_songs().
    rows = [
        (rank, song["title"], song["artist"], score, reasons)
        for rank, (song, score, reasons) in enumerate(
            recommend_songs(user_prefs, songs, k=k, mode=mode, diversity=diversity), start=1)
    ]
    print(render_table(rows))


def compare_modes(name: str, user_prefs: dict, songs: list, k: int = 3) -> None:
    """Show one profile's top-k under every scoring mode, to see the strategy switch."""
    banner = f"MODE COMPARISON for '{name}'"
    print()
    print("#" * len(banner))
    print(banner)
    print("#" * len(banner))
    for mode_name, mode in MODES.items():
        print(f"\n-- {mode_name} --")
        for rank, (song, score, _) in enumerate(
                recommend_songs(user_prefs, songs, k=k, mode=mode), start=1):
            print(f"  {rank}. {song['title']:<18} ({song['genre']}/{song['mood']})  {score:.2f}")


def compare_diversity(name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Show one profile's top-k with the diversity/fairness penalty off vs on."""
    banner = f"DIVERSITY COMPARISON for '{name}'"
    print()
    print("#" * len(banner))
    print(banner)
    print("#" * len(banner))
    for label, use_div in (("diversity OFF", False), ("diversity ON", True)):
        print(f"\n-- {label} --")
        for rank, (song, score, _) in enumerate(
                recommend_songs(user_prefs, songs, k=k, diversity=use_div), start=1):
            print(f"  {rank}. {song['title']:<18} ({song['artist']}, {song['genre']})  {score:.2f}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Rank every profile using the selected strategy (default: Balanced).
    mode = MODES.get(SCORING_MODE, BALANCED)
    print(f"Scoring mode: {mode.name}")
    for name, user_prefs in USER_PROFILES.items():
        print_recommendations(name, user_prefs, songs, k=5, mode=mode)

    # Show how switching strategies re-ranks a single profile.
    compare_modes("High-Energy Pop", USER_PROFILES["High-Energy Pop"], songs, k=3)

    # Show how the diversity penalty breaks up an artist/genre monopoly.
    compare_diversity("Chill Lofi", USER_PROFILES["Chill Lofi"], songs, k=5)


if __name__ == "__main__":
    main()
