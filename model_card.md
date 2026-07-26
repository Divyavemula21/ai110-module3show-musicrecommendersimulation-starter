# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

It matches a listener's "vibe" (their genre, mood, and energy) to songs in a small catalog.

---

## 2. Intended Use  

**Goal / task.** VibeMatch suggests songs a listener will probably like. It looks at a short
taste profile and ranks the songs in the catalog from best match to worst.

**What it is for.** This is a classroom project. It is meant to teach how a simple recommender
turns data into predictions. It works on a tiny, made-up song list.

**What it assumes.** It assumes the user can name one favorite genre, one favorite mood, a
target energy level, and whether they like acoustic music.

**What it should NOT be used for.** It is not for real users or real apps. It should not be
used to make real decisions about people. It is not a replacement for Spotify or YouTube, and
it does not learn from other listeners.

---

## 3. How the Model Works  

The model gives each song a score, then sorts the songs from highest score to lowest.

Here are the scoring rules in plain language:

- If the song's **genre** matches the user's favorite genre, it gets **+2 points**.
- If the song's **mood** matches the user's favorite mood, it gets **+1 point**.
- For **energy**, the closer the song's energy is to what the user wants, the more points it
  gets (up to +1). A song that is far off gets almost nothing.
- For **acoustic taste**, the song gets a small bonus (up to +0.5) if it matches whether the
  user likes acoustic music or not.

The points are added up. The song with the most points is the top recommendation. Each pick
also comes with a short list of reasons, like "genre match: pop (+2.0)," so the user can see
why it was chosen. I started from empty starter functions and built all of this scoring and
ranking logic myself.

---

## 4. Data  

The catalog has **17 songs**. It started with 10, and I added 7 more to get more variety.

Each song has these features: genre, mood, energy, tempo, valence, danceability, and
acousticness. I later added five "advanced" features: popularity (0–100), release decade,
detailed mood tags (like *nostalgic* or *euphoric*), language, and an explicit-content flag.
The scoring uses genre, mood, energy, acousticness, and all five advanced features.

There are **9 genres** (pop, lofi, rock, ambient, jazz, synthwave, indie pop, edm, acoustic)
and **6 moods** (happy, chill, intense, relaxed, moody, focused).

The data has real limits:

- It is very small, so results are just a ranking of a few songs.
- Some genres have four songs (lofi) while others have only one (ambient, synthwave, indie pop).
- There are few songs in the middle energy range (0.55–0.75).
- The songs are made up, and there is no lyrics, language, or artist history.

---

## 5. Strengths  

The system works well in a few clear ways:

- It gives sensible results for listeners with a strong, clear taste. Pop, lofi, and rock
  profiles each got their own genre at the top.
- It explains every pick. Each song comes with reasons and points, so nothing feels like a
  black box.
- It handles brand-new songs. Because it scores songs by their features, a song works even if
  no one has played it yet.
- Different users get different results, which shows the profile settings really matter.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

One clear weakness I found while testing different profiles is that the way I calculate the
"energy gap" (`1 - |song energy - target energy|`) quietly favors listeners with extreme
energy tastes over moderate ones. When I tested a listener who wanted middle-of-the-road
energy (target 0.5), every song in the catalog scored between 0.55 and 0.95 on energy — a
spread of only 0.40 — so the energy feature became almost a constant and barely influenced
their ranking. In contrast, a high-energy listener (target 0.9) saw energy scores spread from
0.38 to 1.00, so energy meaningfully shaped their results. This means the system effectively
"listens to" the energy preference of extreme users but nearly ignores it for moderate ones,
which is unfair and is made worse by a gap in my data (many low- and high-energy songs but few
in the 0.55–0.75 range). It also reflects a broader representation bias: genres like lofi have
four songs while others have only one, so well-represented tastes get rich, varied results
while niche listeners get thin ones.

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

**Profiles I tested.** I ran three very different listeners through the system:

- **High-Energy Pop** — likes pop, happy mood, high energy (0.9), not acoustic
- **Chill Lofi** — likes lofi, chill mood, low energy (0.3), likes acoustic
- **Deep Intense Rock** — likes rock, intense mood, high energy (0.85), not acoustic

For each one I looked at the top 5 songs and checked whether the picks and the "reasons" the
program gave actually made sense for that kind of listener.

**What surprised me.** I expected each profile to mostly return its own genre, and it did — but
I was surprised how often a song from a *different* genre snuck into the top of the list just
because it had the right energy. The clearest example is that "Gym Hero" keeps showing up for
people who asked for Happy Pop. In plain language: Gym Hero is a pop song (so it earns the big
genre bonus) and it is very high-energy, almost exactly the energy this listener wants — so
even though its mood is "intense" and not "happy," those two strong matches are enough to push
it all the way to #2. The lesson is that a song does not have to match *everything* to rank
high; nailing the two heaviest factors (genre and energy) can beat a song that only matches the
mood.

**Comparing the profiles (what changed between each pair, and why it makes sense):**

- **High-Energy Pop vs. Chill Lofi.** These two are near opposites and the output shows it.
  The pop listener gets loud, produced, upbeat songs (Sunrise City, Gym Hero, Festival Sky),
  while the lofi listener gets quiet, acoustic, low-energy tracks (Library Rain, Midnight
  Coding, Sleepy Static). This makes sense because their energy targets (0.9 vs 0.3) and their
  acoustic preference (no vs yes) pull in completely different directions, so almost no songs
  overlap.

- **High-Energy Pop vs. Deep Intense Rock.** These two look *similar* at first, and that also
  makes sense: both want high energy and non-acoustic music, so energetic crossover songs like
  Gym Hero and Festival Sky appear in both lists. The difference is at the very top — the pop
  listener's #1 is Sunrise City (pop, happy) and the rock listener's #1 is Basement Riff (rock,
  intense). The genre and mood bonuses decide the winner, while the shared taste for high energy
  explains the overlap further down.

- **Chill Lofi vs. Deep Intense Rock.** This pair changes the most dramatically. The lofi
  listener's top songs are calm and acoustic (energy around 0.3), while the rock listener's top
  songs are aggressive and produced (energy around 0.9). It makes sense because their energy
  targets sit at opposite ends and their acoustic preferences are flipped, so the two lists
  share essentially no songs.

Overall, the comparisons confirmed the system is testing for the right things: genre and mood
decide the very top pick, while energy and the acoustic preference explain why certain songs
cross over between similar profiles and disappear between opposite ones.

No numeric metrics were used — this was a hands-on comparison of whether the rankings and their
explanations matched what each type of listener would reasonably want.

---

## 8. Future Work  

If I kept building this, here are the changes I would make:

- **Group similar genres.** Right now genre is all-or-nothing. I would let close genres (like
  lofi, ambient, and jazz) earn partial credit, so a listener gets good near-matches too.
- **Add an artist limit.** One artist filled three of five slots for the lofi listener. I would
  cap how many songs one artist can take so the list has more variety.
- **Balance and grow the catalog.** I would add more songs to the rare genres and the middle
  energy range, so niche and moderate listeners get better results.

---

## 9. Personal Reflection  

**My biggest learning moment.** The biggest moment for me was seeing how much the *weights*
control everything. When I doubled the energy weight and halved the genre weight, the top pick
often stayed the same but the songs below it reshuffled, and songs from other genres jumped up.
That is when it clicked that a recommender is really just a set of choices about what matters
most, and I am the one making those choices.

**How AI tools helped, and when I double-checked them.** Using an AI coding assistant helped me
move fast. It helped me turn my scoring recipe into working code, format the terminal output
cleanly, and think through edge cases. But I learned I still have to check its work. A few times
the profile I wrote quietly did nothing because the dictionary keys were wrong (`favorite_genre`
instead of `genre`), and I only caught it by running the code and seeing the scores collapse. I
also found real bugs, like the energy score going negative when I gave it an out-of-range value,
and a trailing space breaking a genre match. The AI could suggest fixes, but I had to run the
program, check the math by hand, and confirm the results actually made sense.

**What surprised me.** I was surprised that such simple math could "feel" like a real
recommendation. There is no fancy AI inside it — just adding up points and sorting — yet the top
songs genuinely fit each listener, and the reasons made the picks feel thoughtful. It made me
realize that a lot of what feels smart in real apps might be simpler than it looks.

**What I would try next.** If I kept going, I would let similar genres share credit instead of
using exact matches, add a limit so one artist cannot fill the whole list, and grow the catalog
so niche and middle-energy listeners get better results. I would also like to add a little
"surprise" song outside the user's usual taste, to fight the filter bubble.
