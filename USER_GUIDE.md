# Adding things to the WDB graph — a guide for non-coders

This guide is for team members who have **never used a code editor** and don't write code. It walks you, click by click, through adding something new — a dataset, a PDF, a photo, even just an **idea** — to the WorldFish Digital Brain (WDB) so it becomes part of the shared knowledge graph.

You don't need to understand any code. You will never touch the main project directly: you make your changes on your **own copy**, and the maintainer reviews and approves them.

**A few words you'll see (in plain English):**
- **Repo / repository** — the project's shared folder on GitHub. For us it's called **WDB**.
- **Clone** — download a copy of the repo onto your laptop so you can add things.
- **Branch** — your own private workspace inside the repo where you make changes without affecting everyone else.
- **Commit** — save a snapshot of your change, with a short note describing it.
- **Push / Publish** — send your saved change up to GitHub.
- **Pull request (PR)** — a request asking the maintainer to review your change and add it to the main project.
- **Pull** — get the latest version of the project onto your laptop.

> ## ⚠️ The golden rule
> **Never add your files to the main project directly.** Always work on **your own branch** and open a **pull request**. The maintainer reviews every pull request and approves it — that's how your work gets into WDB. The steps below do this for you; just follow them in order.

---

## Part 1 — One-time setup (do this once)

Do this with a colleague nearby the first time if you can. After it's done, you never repeat it. **You do not need to install the graph tool** — the maintainer refreshes the graph after approving your change.

**1. Get access to the repo.**
Ask the WDB maintainer to invite your GitHub username to the repo. You'll get an email invitation — click the link and accept it.

**2. Install a code editor.** Pick one (they all work the same here):
- **VS Code** — free, most common: https://code.visualstudio.com
- **Cursor** — https://cursor.com
- **Antigravity**, or any other — fine too.

Download it, install it like a normal app, and open it.

**3. Install Git.**
The editor needs a tool called Git to talk to GitHub. Get it from https://git-scm.com (on a Mac it's often already there). Install it, then restart the editor.

**4. Sign in to GitHub inside the editor.**
Find the **Accounts** icon (a little person, usually bottom-left), click it, and sign in to GitHub.

**5. Download (clone) the repo.**
- Press **Ctrl+Shift+P** (Mac: **Cmd+Shift+P**) to open the **Command Palette** — a search box at the top.
- Type **Git: Clone** and select it.
- Paste the WDB repo address (ask the maintainer; it looks like `https://github.com/your-org/WDB.git`).
- Choose a folder on your laptop (e.g. Documents), then click **Open** when prompted.

You'll now see the WDB folders in the **left sidebar** (the Explorer). That's the repo.

---

## Part 2 — Every time you want to add something

Repeat these steps each time.

**Step 1 — Get the latest version.**
Click the **Source Control** icon on the left (a branching-road shape). Click the **"⋯"** menu at the top of that panel → **Pull**. Now you have the newest version.

**Step 2 — Create your own branch.** *(This is the golden rule in action.)*
- Look at the **bottom-left corner** of the editor — it shows the current branch (probably `main`).
- Click it. A menu opens at the top → choose **Create new branch**.
- Give it a short name describing your change, like `yourname/kenya-yield-data`. Press Enter.

You're now on your own branch. Anything you do stays separate from the main project until it's approved.

**Step 3 — Add your file.**
In the **left sidebar (Explorer)**, open the folder for the project your item belongs to (e.g. `project_kenya_pilot/`) and add your item there. **What exactly to do depends on the type — see [Part 3](#part-3--what-you-can-add).** Two rules always apply:
- We organize **by project, not by file type** — everything for one initiative goes in that initiative's folder.
- Use a **clear, descriptive name**: `kenya_yield_data_2025.csv`, not `data.csv`.

**Step 4 — (Recommended) Add a short context note.**
A small note next to your item helps the graph connect it. Right-click the project folder → **New File**, name it per Part 3, copy the matching template from the repo's **[README — Section 9](README.md#9-optional-context-notes)**, fill in the blanks in plain English, and save (**Ctrl+S** / **Cmd+S**).

**Step 5 — Save your change (commit).**
- Click the **Source Control** icon.
- In the message box, type a short description, e.g. *"Add Kenya 2025 yield dataset + context note."*
- Click **Commit**. If asked to stage all changes, click **Yes**.

**Step 6 — Send it for review (publish branch + open pull request).**
- Click **Publish Branch** (or **Sync Changes**). This uploads *your branch* — not the main project.
- Go to **github.com**, open the WDB repo. You'll see a banner: **"Compare & pull request"** — click it. (Or go to the **Pull requests** tab → **New pull request**.)
- Add a one-line title and a sentence saying what you added, then click **Create pull request**.

**Step 7 — Wait for approval.**
The maintainer reviews your pull request. They may approve it, or leave a comment asking for a small change. Once they approve and merge it, your item is part of WDB and the graph is refreshed for everyone. **You're done — no graph tool to run.**

---

## Part 3 — What you can add

You can populate WDB with **almost anything** — not just files. The table below summarizes the process for each type. In every case the basics are the same: put it in the right **project folder**, give it a **clear, descriptive name**, and add a context note where the table says so (templates are in the repo's **[README — Section 9](README.md#9-optional-context-notes)**).

| Element type | How to add it | Context note to include |
|---|---|---|
| **Dataset / spreadsheet** (CSV, Excel) | Drag the file into the project folder. Don't change the column headers. | **Yes** — `<filename>_dict.md` (Template A). |
| **Report, paper, or document** (PDF, Word, text) | Drag it in. Keep a published paper's original title. | **Yes** — `<filename>_context.md` (Template B). |
| **Image / photo / diagram / screenshot** | Drag it in (e.g. a whiteboard photo or field map). | Recommended if it has text or needs explaining — `_context.md`. |
| **Meeting recording / audio** (MP4, MP3) | Drag the media file in; the maintainer's tools transcribe it. | Optional — only if the recording is hard to follow. |
| **Web link / online paper** | Don't paste a URL into a file. Tell the maintainer the link so they can add it properly. | A short `.md` note with the link and why it matters. |
| **An idea, note, or observation** | Right-click the project folder → **New File** → name it `idea_<short-description>.md` and write it in plain English. Name any related files/projects so the graph links them. | None — the note itself is the content. |

---

## Quick reference

| You want to… | Do this |
|---|---|
| Open the Command Palette | **Ctrl+Shift+P** (Mac: **Cmd+Shift+P**) |
| Get the latest version | **Source Control → ⋯ → Pull** |
| Start your own workspace | Click the branch name (**bottom-left**) → **Create new branch** |
| Save your work | **Source Control →** type a message **→ Commit** |
| Send it for review | **Publish Branch**, then open a **Pull request** on github.com |

> **No-editor shortcut:** You can also do all of this in the browser. On **github.com → WDB → the right project folder → "Add file" → "Upload files"** (or "Create new file" for an idea). At the bottom, choose **"Create a new branch for this commit and start a pull request,"** then **Propose changes**. This keeps the golden rule automatically.

## If something goes wrong
- **Don't edit or delete anything inside the `graphify-out/` folder** — that's generated automatically.
- If you don't see **Create new branch**, you may have skipped signing in (Part 1, Step 4).
- Always check the **bottom-left** shows *your* branch, not `main`, before you commit.
- Still stuck? Send the maintainer: (1) which step you're on, (2) the exact error wording, and (3) a screenshot. That's enough to help quickly.