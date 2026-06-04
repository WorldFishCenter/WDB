# Adding things to the WDB graph — a guide for non-coders

This guide is for team members who have **never used a code editor** and don't write code. It walks you, click by click, through adding something new — a dataset, a PDF, a photo, even just an **idea** — to the WorldFish Digital Brain (WDB) so it becomes part of the shared knowledge graph.

**This is the exact same procedure as the [README protocol](README.md#the-protocol-adding-to-the-brain) — just with screenshots.** Following the same steps as everyone else is what keeps the brain consistent. You never touch the main project directly: you make your changes on your **own copy**, and the maintainer reviews and approves them.

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

## Part 2 — The protocol, step by step

These are the **same six steps as the [README protocol](README.md#the-protocol-adding-to-the-brain)** — here's how to do each by clicking. Repeat them every time you add something.

**Step 1 — Sync & branch.**
- Click the **Source Control** icon on the left (a branching-road shape) → the **"⋯"** menu at the top → **Pull**. Now you have the newest version.
- Look at the **bottom-left corner** — it shows the current branch (probably `main`). Click it → **Create new branch** → name it `yourname/short-topic` (e.g. `maria/kenya-yield-data`). Press Enter. *(This is the golden rule in action — you're now on your own branch.)*

**Step 2 — Pick the initiative folder.**
In the **left sidebar (Explorer)**, open the folder for the initiative your item belongs to (e.g. `project_kenya_pilot/`). We organize **by initiative, not by file type** — everything for one effort lives together. If no folder fits, right-click the empty Explorer space → **New Folder** and name it in `lower_snake_case` (e.g. `genetic_improvement`). **If you're unsure which initiative it belongs to, ask the maintainer — don't guess.**

**Step 3 — Add the file, named by the rule.**
Drag your file into that folder, then rename it (right-click → **Rename**) to follow the rule: **`lower_snake_case`, descriptive, with year/region when they apply** — `kenya_yield_2025.csv`, not `data.csv` or `Final Report.pdf`. Don't change a spreadsheet's column headers; keep a published paper's real title. *(See [Part 3](#part-3--what-you-can-add) for each file type.)*

**Step 4 — Write its context note.** *(Required for datasets, PDFs, and documents.)*
This small note is what lets the graph connect your file.
- Right-click the folder → **New File**. Name it **exactly** `<your-filename>_dict.md` (for spreadsheets) or `<your-filename>_context.md` (for everything else).
- Copy the matching template from the **[README — Section 9](README.md#9-context-notes-your-main-quality-lever)** (it has worked examples), fill in **every** section in plain English, and save (**Ctrl+S** / **Cmd+S**).
- The most important line is **`## Related files`**: list the real files yours relates to — and include files in **other initiative folders** too. Those cross-links are what make the brain valuable.

**Step 5 — Commit (source files only).**
- Click the **Source Control** icon. **Don't include anything from `graphify-out/`** — that folder is generated automatically.
- In the message box, type a short description, e.g. *"Add Kenya 2025 yield dataset + context note."*
- Click **Commit**. If asked to stage all changes, click **Yes**.

**Step 6 — Open a pull request.**
- Click **Publish Branch** (or **Sync Changes**). This uploads *your branch* — not the main project.
- Go to **github.com**, open the WDB repo. You'll see a banner: **"Compare & pull request"** — click it. (Or go to the **Pull requests** tab → **New pull request**.)
- Add a one-line title and a sentence saying what you added, then click **Create pull request**.

**Then: wait for approval.** The maintainer reviews your pull request, may ask for a small change, then merges it. After merging, they refresh the graph for everyone. **You're done — no graph tool to run.**

---

## Before you open the PR — checklist

This is the same checklist the README uses. Tick every box:

- [ ] File is in the correct **initiative folder**
- [ ] Name is **`lower_snake_case`**, descriptive (year/region if relevant)
- [ ] **Context note** added where required, with **every section filled in**
- [ ] **Related files** lists real siblings (+ a cross-initiative link where one exists)
- [ ] Only **source files** committed — nothing from `graphify-out/`
- [ ] You're on **your branch**, opening a **pull request** — not committing to `main`

---

## Part 3 — What you can add

Put it in the right **initiative folder**, give it a **`lower_snake_case`** name, and add the context note the table requires (templates + worked examples are in the **[README — Section 9](README.md#9-context-notes-your-main-quality-lever)**). This table matches the README's "What am I adding?" exactly.

| What you're adding | How to add it | Context note |
|---|---|---|
| **Dataset / spreadsheet** (CSV, Excel) | Drag into the folder. Don't change the column headers. | **Required** — `<file>_dict.md` (Template A). |
| **Report / paper / document** (PDF, Word, text) | Drag it in. Keep a published paper's real title. | **Required** — `<file>_context.md` (Template B). |
| **Image / photo / diagram / screenshot** | Drag it in (e.g. a whiteboard photo or field map). | Required if it carries information — `<file>_context.md` (Template B). |
| **Meeting recording / audio** (MP4, MP3) | Drag the media file in; the maintainer's tools transcribe it. | Required if it's hard to follow — `<file>_context.md` (Template B). |
| **Web link / online paper** | **Don't** paste a URL into a file. Tell the maintainer the link — they add it properly with `/graphify add`. | The maintainer adds it. |
| **An idea, note, or observation** | Right-click the folder → **New File** → name it `idea_<short-topic>.md` and write it in plain English. | The note *is* the content — name any related files/initiatives inside it so the graph links them. |

---

## Quick reference

| You want to… | Do this |
|---|---|
| Open the Command Palette | **Ctrl+Shift+P** (Mac: **Cmd+Shift+P**) |
| Get the latest version | **Source Control → ⋯ → Pull** |
| Start your own branch | Click the branch name (**bottom-left**) → **Create new branch** |
| Save your work | **Source Control →** type a message **→ Commit** |
| Send it for review | **Publish Branch**, then open a **Pull request** on github.com |

> **No-editor shortcut:** You can also do all of this in the browser. On **github.com → WDB → the right initiative folder → "Add file" → "Upload files"** (or "Create new file" for an idea). At the bottom, choose **"Create a new branch for this commit and start a pull request,"** then **Propose changes**. This keeps the golden rule automatically.

## If something goes wrong
- **Don't edit or delete anything inside the `graphify-out/` folder** — that's generated automatically.
- If you don't see **Create new branch**, you may have skipped signing in (Part 1, Step 4).
- Always check the **bottom-left** shows *your* branch, not `main`, before you commit.
- Still stuck? Send the maintainer: (1) which step you're on, (2) the exact error wording, and (3) a screenshot. That's enough to help quickly.
