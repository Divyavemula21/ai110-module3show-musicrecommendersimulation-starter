"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

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


def print_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5,
                          mode=None) -> None:
    """Print the top-k recommendations for one named taste profile."""
    header = f"{name}  ({user_prefs['genre']} / {user_prefs['mood']} / energy {user_prefs['energy']})"
    print()
    print("=" * len(header))
    print(header)
    print("=" * len(header))

    # Each recommendation is (song, score, reasons) — see recommend_songs().
    for rank, (song, score, reasons) in enumerate(
            recommend_songs(user_prefs, songs, k=k, mode=mode), start=1):
        print()
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   Score: {score:.2f}")
        print("   Reasons:")
        for reason in reasons:
            print(f"     - {reason}")
    print()


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


if __name__ == "__main__":
    main()
