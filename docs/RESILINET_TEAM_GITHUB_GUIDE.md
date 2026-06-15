# ResiliNet AI — Team Collaboration & GitHub Workflow Guide

This document covers two things:

1. **Who works on what** — a clear ownership split across the modules from the Master Architecture Guide, so everyone knows their area.
2. **How to use GitHub as a team** — written for people who haven't used branches/PRs before. Every command is explained.

---

## 1. Team & Work Distribution

| Person | Focus Area | Owns |
|---|---|---|
| **Jeevan** | Data layer & Neo4j | **Data layer** — Neo4j schema design (`schema.cypher`), `database.py`, `models.py`, seed/test data, and collaborates with Manish on tuning the GraphRAG context formatting. |
| **Manish** | AI / GraphRAG | **AI/GraphRAG core** — `graphrag.py` (retrieval queries), `llm_service.py` (system prompt + LLM call + JSON parsing). Drives severity-classification logic and prompt iteration. |
| **Vaishnav** | Frontend & AI integration | **React + AI bridge** — works alongside Saurabh on the dispatch feed UI (where AI output is displayed), and collaborates with Manish/Jeevan on how the GraphRAG context is structured and consumed downstream. |
| **Yash Mourya** | Mobile | **Mobile Field App (Part 5)** — entire `resilinet_field_app/` — models, `dispatch_service.dart`, `dispatch_provider.dart`, screens. |
| **Saurabh Mishra** | Web | **Web Command Center (Part 4)** — entire `resilinet-frontend/` — `App.jsx`, `MapView.jsx`, `useDispatchSocket.js`. |
| **You (Yash)** | Backend core & architecture | **Backend core (`main.py`)** — FastAPI app, `/report` endpoint, WebSocket manager, lifespan/config. Also coordinates overall architecture and reviews PRs that touch shared interfaces (the JSON shapes everyone depends on). |

**Why this split works**: Jeevan and Manish together cover both halves of GraphRAG (the reasoning layer and the graph data feeding it) and naturally review each other's work. Vaishnav and Saurabh share ownership of the dashboard, with Vaishnav also connecting into the AI side. Yash Mourya owns a full, self-contained mobile client. You own the "contract" — the API and WebSocket message shapes — since changes there affect everyone else's work.

---

## 2. Repository Structure (Single Monorepo)

One repo, with one top-level folder per major piece. This matches the Master Guide's parts directly, so everyone knows exactly where their code lives.

```
resilinet-ai/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── graphrag.py
│   ├── llm_service.py
│   ├── schema.cypher
│   └── requirements.txt
├── frontend-web/          (Saurabh + Vaishnav)
│   └── src/...
├── frontend-mobile/        (Yash Mourya)
│   └── lib/...
├── docs/
│   └── ResiliNet_AI_Master_Guide.md
├── .gitignore
└── README.md
```

---

## 3. Git Crash Course — Three Concepts You Need

Before any commands, the three ideas everything else builds on:

- **Repository (repo)**: the project folder, tracked by Git, with full history. Lives on GitHub (the "remote") and as a copy on each person's laptop (the "local" copy).
- **Branch**: a separate "timeline" of changes. `main` is the official, always-working timeline. When you start a task, you create your own branch off `main` — so your half-finished work never breaks `main` for everyone else.
- **Commit**: a saved snapshot of your changes, with a message describing what changed. A branch is just a sequence of commits.

The whole workflow is: **branch off main → make commits on your branch → push your branch to GitHub → open a Pull Request (PR) → someone reviews it → merge into main.**

---

## 4. One-Time Setup (everyone does this once)

```bash
# Check Git is installed
git --version

# Tell Git who you are — this name/email shows up on every commit you make
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Clone the repo (downloads it to your laptop)
git clone https://github.com/YASH514131/Resilinet.git
cd Resilinet
```

If you've never connected to GitHub from your laptop before, GitHub will ask you to authenticate — easiest option is to install **GitHub CLI** (`gh auth login`) and follow the prompts, or set up an SSH key (GitHub has a guide for this under Settings → SSH and GPG keys).

> **Access**: Yash needs to add each of you as a **Collaborator** first (repo → Settings → Collaborators and teams → Add people) — otherwise `git push` will fail with a permission error. Do this before anyone else starts Step 1 below.

---

## 5. Branching Strategy — "GitHub Flow"

We're using the simplest possible model, with one rule:

> **Nobody commits directly to `main`. Every change comes in through a Pull Request.**

Branch naming: `feature/<area>-<short-description>`, all lowercase, words separated by hyphens.

| Person | Example branch names |
|---|---|
| Jeevan | `feature/db-neo4j-schema`, `feature/db-models-validation` |
| Manish | `feature/ai-graphrag-retrieval`, `feature/ai-llm-prompt-v2` |
| Vaishnav | `feature/web-dispatch-feed-ui`, `feature/ai-context-review` |
| Yash Mourya | `feature/mobile-dispatch-provider`, `feature/mobile-ui-polish` |
| Saurabh | `feature/web-map-markers`, `feature/web-websocket-hook` |
| You | `feature/backend-report-endpoint`, `feature/backend-websocket-manager` |

One branch = one task. Don't pile five unrelated changes into one branch — it makes review and rollback much harder.

---

## 6. The Daily Workflow — Step by Step

This is the loop every person repeats for every task.

### Step 1 — Start from an up-to-date `main`

```bash
git checkout main          # switch to the main branch
git pull origin main        # download the latest changes from GitHub
```

### Step 2 — Create your feature branch

```bash
git checkout -b feature/ai-graphrag-retrieval
```

`-b` means "create this branch and switch to it in one step." You're now working on your own isolated copy of the project.

### Step 3 — Do your work, then check what changed

```bash
git status
```

This lists every file you've added/modified/deleted — useful before committing, so you don't accidentally commit something you didn't mean to (like a `.env` file).

### Step 4 — Stage and commit your changes

```bash
git add backend/graphrag.py          # stage a specific file
# or
git add .                              # stage everything that changed

git commit -m "feat(ai): add nearby responder retrieval query"
```

**Commit message convention** (keeps history readable):

```
<type>(<area>): <short description>

type  = feat | fix | docs | refactor | test | chore
area  = ai | backend | web | mobile | db
```

Examples: `feat(mobile): add live dispatch list screen`, `fix(backend): handle null responder id in dispatch update`.

### Step 5 — Push your branch to GitHub

```bash
git push -u origin feature/ai-graphrag-retrieval
```

`-u` (short for `--set-upstream`) links your local branch to a new branch on GitHub with the same name. After this first push, you can just type `git push` for future pushes on this branch.

### Step 6 — Open a Pull Request (PR)

1. Go to **https://github.com/YASH514131/Resilinet** — you'll see a yellow banner: *"feature/ai-graphrag-retrieval had recent pushes"* with a **Compare & pull request** button. Click it.
2. Set the base branch to `main` and your branch as the compare branch (usually already correct).
3. Write a short title and description: what you changed, and why.
4. If your change closes a tracked task, add `Closes #12` in the description (this auto-links and auto-closes the GitHub Issue when merged — see Section 10).
5. Click **Create pull request**.

### Step 7 — Wait for Yash's review

- Your PR now shows up on Yash's dashboard for review. He'll check the code, may leave comments or request changes, and once it's good, approves and merges it (see Section 14 for exactly what he does on his end).
- If he requests changes: make the edits on the **same branch**, commit, and `git push` again — the PR updates automatically, no need to open a new one.
- Once merged, you'll see the PR marked "Merged" on GitHub.

### Step 8 — Clean up

```bash
git checkout main
git pull origin main                                  # get your now-merged change
git branch -d feature/ai-graphrag-retrieval            # delete local branch
git push origin --delete feature/ai-graphrag-retrieval # delete remote branch
```

---

## 7. Staying in Sync (Avoiding Painful Conflicts)

If your task takes more than a day, `main` will likely move ahead while you work. Pull those changes into your branch regularly:

```bash
git checkout feature/ai-graphrag-retrieval
git fetch origin
git merge origin/main
```

If Git says it merged automatically — great, keep working. If it reports a **conflict**, see Section 8.

Doing this every morning, *before* you start coding, keeps conflicts small and infrequent.

---

## 8. Handling a Merge Conflict (Don't Panic)

A conflict means Git found two changes to the *same lines* of a file and needs you to pick. Git marks the file like this:

```python
<<<<<<< HEAD
SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
=======
SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "CATASTROPHIC"]
>>>>>>> origin/main
```

- Everything between `<<<<<<< HEAD` and `=======` is **your** version.
- Everything between `=======` and `>>>>>>> origin/main` is the **incoming** version from `main`.

To fix it:

1. Edit the file by hand — delete the `<<<<<<<`, `=======`, `>>>>>>>` markers and keep whichever lines (or a combination) you actually want.
2. Save the file.
3. Tell Git it's resolved and finish the merge:

```bash
git add backend/llm_service.py
git commit -m "merge: resolve severity levels conflict with main"
```

4. Continue working, then push as normal.

If a conflict is in a file that isn't yours (e.g. Saurabh's React code conflicts because of an unrelated shared file), message that person before resolving — don't guess at code you don't own.

---

## 9. `.gitignore` — Files We Never Commit

Create this file at the repo root. It stops dependency folders, build artifacts, and secrets from ever being pushed.

```gitignore
# ── Python (backend) ──────────────────────────────
__pycache__/
*.pyc
.venv/
venv/
.env

# ── Node / React (frontend-web) ───────────────────
node_modules/
dist/
.env.local

# ── Flutter (frontend-mobile) ─────────────────────
**/build/
.dart_tool/
.flutter-plugin-dependencies
*.iml
.idea/

# ── General ────────────────────────────────────────
.DS_Store
*.log
```

**Critical**: `.env` (containing `ANTHROPIC_API_KEY`, `NEO4J_PASSWORD`, etc.) must NEVER be committed. If someone already committed one by accident, rotate that key/password immediately — removing it from a later commit does not remove it from history.

---

## 10. Tracking Tasks — GitHub Issues + Project Board

Rather than coordinating over chat, create one **Issue** per task from Section 1's breakdown:

1. Repo → **Issues** tab → **New issue**.
2. Title it clearly: `[AI] Implement GraphRAG nearby-responder query`.
3. Assign it to the owner (e.g. Manish).
4. Label it: `ai`, `backend`, `web`, `mobile`, or `db`.

Then create a **Project board** (repo → **Projects** → New project → "Board" template) with columns: **To Do → In Progress → In Review → Done**. Drag issues across as work progresses — gives everyone a single glance at who's doing what, without anyone needing to ask.

When you open a PR for an issue, write `Closes #<issue-number>` in the PR description — merging the PR automatically closes the issue and moves the card to Done.

---

## 11. Recommended Repo Settings (do this once, as the repo owner)

Go to **Settings → Branches → Add branch protection rule** for `main`:

- ✅ **Require a pull request before merging**
- ✅ **Require approvals** (set to 1, given the team size)
- ✅ **Do not allow bypassing the above settings** (applies the rule even to admins, including you — keeps everyone honest)

This makes it *impossible* to accidentally push broken code straight to `main` — everything goes through review.

---

## 12. Quick Reference Cheat Sheet

```bash
# Setup
git clone https://github.com/YASH514131/Resilinet.git
git config --global user.name "..."
git config --global user.email "..."

# Start new work
git checkout main && git pull origin main
git checkout -b feature/<area>-<description>

# Save work
git status
git add <file>          # or: git add .
git commit -m "feat(area): description"

# Share work
git push -u origin feature/<area>-<description>   # first push
git push                                            # subsequent pushes

# Stay in sync mid-task
git fetch origin
git merge origin/main

# After PR is merged
git checkout main
git pull origin main
git branch -d feature/<area>-<description>
git push origin --delete feature/<area>-<description>
```

---

## 13. Worked Examples — Each Person's Workflow With Real Changes

The cheat sheet above uses placeholders. Here's what it actually looks like for each person, using their real files. Read your own example, then come back to this section every time you sit down to work — it's the same loop every time.

### Manish — working on `backend/graphrag.py`

```bash
# Start of day: get the latest main
git checkout main
git pull origin main

# Create a branch for today's task
git checkout -b feature/ai-graphrag-retrieval

# ... open graphrag.py, write/edit the nearby-responder query function ...

# Check what changed
git status
# -> shows: modified backend/graphrag.py

# Stage and commit
git add backend/graphrag.py
git commit -m "feat(ai): add nearby responder retrieval query"

# Keep working — maybe you also tweak the infrastructure query
# ... edit graphrag.py again ...
git add backend/graphrag.py
git commit -m "feat(ai): add nearby infrastructure retrieval query"

# Push your branch to GitHub (first time on this branch, use -u)
git push -u origin feature/ai-graphrag-retrieval
```

Now go to GitHub → open the PR (Section 6, Step 6). Tag Jeevan as reviewer since the query depends on the schema he's building.

If Jeevan's schema changes land in `main` while you're still working:

```bash
git fetch origin
git merge origin/main
# if no conflicts, just continue working and push again:
git push
```

---

### Jeevan — working on `backend/schema.cypher` and `backend/database.py`

```bash
git checkout main
git pull origin main
git checkout -b feature/db-neo4j-schema

# ... edit schema.cypher to add a new constraint or index ...
git add backend/schema.cypher
git commit -m "feat(db): add point index for responder coordinates"

# ... edit database.py to add a helper function ...
git add backend/database.py
git commit -m "feat(db): add get_driver helper for session reuse"

git push -u origin feature/db-neo4j-schema
```

Open the PR. Since Manish's GraphRAG queries assume certain node properties, mention in the PR description exactly which properties/labels changed, so he can check his queries still match.

---

### Vaishnav — working on `frontend-web/src/DispatchFeed.jsx` (paired with the AI context format)

```bash
git checkout main
git pull origin main
git checkout -b feature/web-dispatch-feed-ui

# ... build/edit the component that renders each dispatch card ...
git add frontend-web/src/DispatchFeed.jsx
git commit -m "feat(web): add dispatch feed card component"

# After looking at a sample GraphRAG context with Manish and noticing
# the severity field needs a fallback for older messages:
git add frontend-web/src/DispatchFeed.jsx
git commit -m "fix(web): handle missing severity field gracefully"

git push -u origin feature/web-dispatch-feed-ui
```

Open the PR, tag Saurabh (since this lives inside his `frontend-web/` area) for review.

---

### Yash Mourya — working on `frontend-mobile/lib/providers/dispatch_provider.dart`

```bash
git checkout main
git pull origin main
git checkout -b feature/mobile-dispatch-provider

# ... write the ChangeNotifier class ...
git add frontend-mobile/lib/providers/dispatch_provider.dart
git commit -m "feat(mobile): add DispatchProvider with websocket listener"

# ... wire it into a screen ...
git add frontend-mobile/lib/screens/dispatch_screen.dart
git commit -m "feat(mobile): connect dispatch screen to provider"

git push -u origin feature/mobile-dispatch-provider
```

Open the PR. This branch doesn't depend on anyone else's files, so it can usually be reviewed and merged quickly.

---

### Saurabh — working on `frontend-web/src/MapView.jsx`

```bash
git checkout main
git pull origin main
git checkout -b feature/web-map-markers

# ... add CircleMarker rendering for each dispatch ...
git add frontend-web/src/MapView.jsx
git commit -m "feat(web): render severity-colored markers on map"

git push -u origin feature/web-map-markers
```

If you and Vaishnav are both editing files inside `frontend-web/src/` at the same time, pull `main` more often (every couple hours, not just once a day) — small, frequent merges are much easier than one big one at the end of the week:

```bash
git fetch origin
git merge origin/main
```

---

### You — working on `backend/main.py`

```bash
git checkout main
git pull origin main
git checkout -b feature/backend-report-endpoint

# ... add/adjust the POST /report endpoint ...
git add backend/main.py
git commit -m "feat(backend): add POST /report endpoint with background AI task"

# ... add the GET /dispatches endpoint the mobile app needs ...
git add backend/main.py
git commit -m "feat(backend): add GET /dispatches endpoint for history load"

git push -u origin feature/backend-report-endpoint
```

Since `main.py` is the shared contract everyone's code talks to, open the PR with a clear note on any changed request/response shapes (e.g. "added a new field `recommended_infrastructure_id` to the WebSocket payload") so Saurabh and Yash Mourya know to update their parsing code.

---

### The One Rule That Prevents Most Problems

**Before you start work each day**: `git checkout main && git pull origin main`, then branch from there.
**Before you open your PR**: `git fetch origin && git merge origin/main` one more time, so your branch already includes the latest `main` and your PR is conflict-free when reviewed.

---

## 14. Yash's Role — Reviewing, Verifying, and Merging PRs

Everyone else's instructions end with "open a PR and wait." Here's exactly what you do when that PR lands — this is what keeps `main` always working and makes the whole setup feel professional.

### 14.1 One-time setup (do this first, before anyone pushes)

1. **Add collaborators**: repo → **Settings → Collaborators and teams → Add people** → add Jeevan, Manish, Vaishnav, Yash Mourya, and Saurabh by their GitHub usernames. Without this, their `git push` will fail.
2. **Push the initial structure**: clone your own repo, add the `backend/`, `frontend-web/`, `frontend-mobile/`, `docs/` folders (with `docs/ResiliNet_AI_Master_Guide.md` and this guide), commit, and push directly to `main` — this is the *only* time anyone pushes to `main` directly, since the repo is still empty.
3. **Turn on branch protection** (Section 11): repo → **Settings → Branches → Add branch protection rule** for `main` — require a PR before merging, require 1 approval.
4. **Create Issues + Project board** (Section 10): one Issue per row in Section 1's table, assigned to the right person, so everyone has a starting task.

### 14.2 When a PR comes in

You'll get a GitHub notification (and email, if enabled) whenever someone opens a PR or pushes new commits to an open PR.

1. **Open the PR** on GitHub → click the **Files changed** tab. This shows exactly what lines were added (green) and removed (red) — you don't need to pull the branch locally just to look.
2. **Read the PR description** first — it should tell you *what* changed and *why*. If it doesn't, comment asking for it (good habit to build early).
3. **Review the diff**:
   - Hover over any line and click the **+** that appears to leave an inline comment (e.g. "this query will fail if `availableBeds` is null — handle that case").
   - Check it doesn't touch files outside that person's area without a good reason (e.g. Vaishnav's PR shouldn't be editing `backend/main.py`).
   - Check no secrets crept in — search the diff for `API_KEY`, `PASSWORD`, `.env`.
4. **Submit your review** — top right of the Files changed tab, click **Review changes**:
   - **Comment** — general feedback, nothing blocking.
   - **Request changes** — something needs fixing before merge. The person fixes it on the same branch and pushes again; the PR updates automatically and re-requests your review.
   - **Approve** — looks good, ready to merge.

### 14.3 Merging

Once approved (and no conflicts shown by GitHub):

1. Click **Squash and merge** (keeps `main`'s history as one clean commit per feature, instead of every small "wip" commit).
2. Edit the merge commit message if needed — keep it matching the convention (`feat(ai): add nearby responder retrieval query`).
3. Click **Confirm squash and merge**.
4. GitHub will offer a **Delete branch** button right after — click it. This deletes the remote branch (the person still has their local copy until they run the cleanup commands in Step 8 / Section 12).
5. If the PR description had `Closes #12`, the linked Issue auto-closes and moves to **Done** on the Project board.

### 14.4 After merging — keep your own local `main` in sync

```bash
git checkout main
git pull origin main
```

Do this regularly so when *you* start work on `backend/main.py` (your own area), you're always branching from the latest merged code.

### 14.5 Quick mental checklist for every PR

- Does the description explain *what* and *why*?
- Is the change inside that person's owned area (Section 1)? If not, did they flag it for you?
- Any secrets, `.env`, or `node_modules`/`build/` files accidentally included? (`.gitignore` in Section 9 should prevent most of this, but double-check on new files.)
- Does it change a shared shape (API response, WebSocket payload, Cypher schema)? If yes, did they note who else needs to update their code?
- All good → **Approve → Squash and merge → Delete branch**.
---

## Suggested First Week

1. **You**: complete Section 14.1 (add collaborators, push initial structure, branch protection, Issues + Project board).
2. **Everyone**: clone the repo, do one tiny "hello world" branch+PR each (e.g. add your name to a `CONTRIBUTORS.md`) — purely to practice the branch → commit → push → PR → merge loop before touching real code.
3. After that, each person picks up their first real Issue from Section 1 and follows Section 6.
