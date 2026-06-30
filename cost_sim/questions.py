"""Representative WDB question set for session cost simulation.

Designed to exercise the router realistically across all three modes. The router's
own signal-matching (wdb_router/routing.py) decides which modes activate per question.
Questions are drawn from or inspired by the proof fixtures and the real WDB corpus —
they are known to be meaningful to the graph and CSVs.

Expected mode mix for this set:
  Mode A alone:  #1 #2 #3 #4 #5
  Mode B alone:  #6 #7 #8 #9
  Mode C alone:  #10 #11 #12
  Blended A+B:   #13 #14
  Blended A+C:   #15
  Blended A+B+C: #16

That gives roughly 1 : 0.7 : 0.7 A : B : C call ratio — adjust the list to
shift the mix if you want to model a different query profile.
"""

QUESTIONS: list[str] = [
    # ── Mode A — graph / enumeration ────────────────────────────────────── #
    "What initiatives are present in Kenya?",
    "Which datasets are related to Peskas?",
    "List all papers that reference the Peskas platform.",
    "What projects operate in small-scale fisheries research?",
    "Which initiatives are connected to data harmonization?",

    # ── Mode B — passage synthesis ───────────────────────────────────────── #
    "How does Peskas validate its catch data?",
    "What are the main challenges in collecting small-scale fisheries data?",
    "Why is trip-level aggregation important for fisheries monitoring?",
    "Describe the approach Peskas uses for outlier detection.",

    # ── Mode C — structured query over tidy CSVs ────────────────────────── #
    "What is the average total catch per trip in Kwale?",       # proof_c Q4 (grain trap)
    "What is the average CPUE in the Kenya fishing survey?",    # proof_c Q2 (derived metric)
    "How many distinct fishing trips are in the Zanzibar dataset?",

    # ── Blended ─────────────────────────────────────────────────────────── #
    "What initiatives work in Kenya and what are their key findings?",   # A+B
    "Which related datasets exist for Peskas and what do they describe?",  # A+B
    "What initiatives are connected to Zanzibar and what is the average catch per trip there?",  # A+C
    "What data does the Kenya fishing survey collect and what is the average catch per trip?",   # A+B+C
]
