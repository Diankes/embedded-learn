---
name: arena
description: Maintain C6 Tactics, the user's rated puzzle arena (claude.ai artifact) for this repo. Use when the user asks how they are doing in the arena, finishes a lab, flags a puzzle, wants new puzzles, or says /arena.
---

# C6 Tactics (the arena)

The page: https://claude.ai/artifact/8dUXVEb9t4pkxkrWdPCsBg (source `arena/index.html`, data `arena/puzzles.json`).
The user only plays. Everything below is Claude's job; never ask the user to run or configure anything.

## How it works (so you can explain it)

- Puzzles are opponents with a fixed rating; the player has a Glicko-2 rating (start 1000). Ranks every 200 points:
  Bit, Nibble, Byte, Word, Register, Bus Master, Kernel, Silicon, with divisions III/II/I.
- Modes: 15-minute rated session racing a ghost (the player's best session, XP over time), Puzzle Rush (5 min,
  3 strikes, rising difficulty, against the best run), ladder (all players + "you 7/30 days ago" ghosts + weekly
  XP league vs past weeks), stats (rating chart, per-concept accuracy, drill buttons). Streak = days with 15 min.
- The picker (`pickNext` in index.html) is X's For You ranking (github.com/xai-org/x-algorithm, home-mixer)
  retargeted: score = closeness to a 70% solve chance + review due + new concept boost + rematch, × current-lab
  factor, × concept diversity decay, × the player's "too easy" feedback.
- Every answer comes from a tool: `arena/gen/gen.py` runs snippets in QEMU, encodes with the ESP assembler, compiles
  with the ESP gcc, parses ESP-IDF headers. Never hand-write an answer; generate it.

## Data (ArtifactData tool, url above)

- `players/<id>`: one doc per player: `r rd vol xp solved tried streak last days{date:{xp,sec,n,ok}} hist[[date,r]]
  wk{week:xp} rush{best,tl,at} best{xp,tl} sess[] cc{concept:[tried,ok]} seen{pid:[ok,day]} cards{concept:[box,due]}
  neg{concept:n} flags{pid:"easy"|"confusing"|"wrong"}`. The page writes it; do not edit it except to fix a
  corrupted field (read it first, pin `if_version`).
- `course/current`: `{lab: N}`. The concepts of lab N are served first. Only the owner writes it.

## Jobs

1. **"How am I doing?"** Read `players`. Report: rating and rank, change this week (`hist`), streak, weakest
   concepts (`cc`, ≥3 tries, lowest accuracy), and puzzles flagged in `flags`. Then one concrete suggestion (drill a
   concept, or go back to a lab section). Short; numbers from the doc only.
2. **A lab is done** (README box ticked): update `course/current` to the next lab (`update`, pin the version).
   If that lab's concepts have few puzzles, do job 3.
3. **New puzzles / a new lab.** Add a generator to `arena/gen/gen.py` (new concept in `CONCEPTS` with its lab,
   answers from a tool, `why` lines, `src` citations checked with rg against
   `~/projects/chip-canvas/sources/text`), run `arena/gen/build.sh` on the host (podman; no sudo), spot-check a few
   puzzles by printing them, then republish: Artifact publish with `file_path` `arena/index.html`, `url` above,
   `files` `{"puzzles.json": "arena/puzzles.json"}`, no `capabilities` (keeps the db rules). Keep puzzle ids stable:
   ids are positional per family, so append new families or keep counts; a changed id resets that puzzle's history.
4. **Flagged puzzles** (`flags`): "wrong" → check the answer with the tool that made it; fix the generator, rebuild,
   republish, then tell the user what was wrong. "confusing" → improve the question text or `why` lines.
5. **Calibration** (when the player has 200+ tries): concepts whose accuracy is far from the 70% target at the
   player's rating have mis-rated puzzles; shift that concept's base rating in gen.py by ~100 per 15% off.

Commit changes to this repo (only your own files; the user may have uncommitted notes), and push.
