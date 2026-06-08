# FASA

**FASA — The Development and Scaling of Sustainable Feeds for Resilient Aquatic Food Systems in
Sub-Saharan Africa** is a five-year (2022–2027) WorldFish research-and-development initiative
developing low-cost, nutritious fish feeds from locally available ingredients, so that
smallholder aquaculture in Sub-Saharan Africa becomes affordable, sustainable, and resilient.

## Aim

Develop low-cost, highly nutritious fish feeds based on **novel, locally available ingredients**,
and promote a **circular economy** by turning unexploited agricultural and livestock waste into
feed. The end goal is long-lasting sustainable aquaculture that raises farmer incomes, improves
food security, and reduces environmental pollution across the region.

## Why it exists

Aquaculture in Sub-Saharan Africa faces cost and sustainability barriers that conventional feeds
cannot meet:

- **Feed cost dominates.** Feed is **40–70% of total variable production cost**, and the price of
  fishmeal — the traditional staple ingredient — has surged from roughly **$500 to over $1,600 per
  metric ton**, putting conventional feeds out of reach for small-scale farmers.
- **Environmental pressure.** Heavy reliance on imported marine ingredients strains wild fish
  stocks and marine ecosystems.
- **Knowledge & infrastructure gaps.** Baseline surveys of farmers and feed processors reveal
  limited feed-formulation expertise, quality control by visual inspection rather than lab testing,
  inadequate storage, and poor access to finance.

## Where & who

- **Where:** field research and implementation in **Kenya, Nigeria, and Zambia**.
- **Lead & funding:** led by **WorldFish**, funded by a **NOK 80 million (≈ USD 8 million) grant
  from Norad** (Norwegian Agency for Development Cooperation).
- **Partners:** ICIPE (International Centre of Insect Physiology and Ecology), CORAF (West and
  Central African Council for Agricultural Research and Development), SLU (Swedish University of
  Agricultural Sciences), IITA (International Institute of Tropical Agriculture), Aller Aqua Zambia,
  and NRDC (Natural Resources Development College).
- **Beneficiaries:** 5,000 smallholder aquatic-food producers (target **30% women, 40% youth**) and
  local feed millers.

## What FASA delivers (current state)

In its final phase the central deliverable has shifted to a scalable, digitally-driven feed tool,
backed by the scientific work that makes it trustworthy:

- **The FASA feed-formulation app (the "engine").** A least-cost feed calculator for local feed
  millers that finds the cheapest **biologically safe** recipe from ingredients available at the
  local market, under strict nutritional and toxin-safety constraints drawn from FASA's reference
  databases (ASNS and FICD). It is built to push formulations toward cheaper, local, plant-based
  alternatives instead of expensive imported marine ingredients. *How the engine works — the
  optimization model, ingredient inclusion limits, cost/safety caps, and individual toxin ceilings —
  is documented in `fasa_repo_about.md`.*
- **Scientific research & ingredient optimization.** Wet-lab digestibility trials and on-farm pilots
  establish the nutrient requirements of improved **Nile Tilapia** and **African Catfish** strains;
  partners such as SLU research processing techniques — physical processing, soaking, and
  solid-state fermentation — to improve the nutritional profile of at least **15 local ingredients**.
  These trials define the biological boundaries the app's constraints rely on.

## Related files

- `fasa_repo_about.md` — the optimization **engine / compute core**, one of FASA's deliverables (this hub is its parent).
- `ASNS_nutrition_specification_database_dict.md` — the **nutritional specifications** (constraints by species/stage/system) the engine enforces.
- `FICD_feed_ingredient_composition_database_dict.md` — the **ingredient nutrient composition** the engine draws on.
- `PAFF_practical_aquaculture_feed_formulation_database_Feed_Formulations_dict.md` and `PAFF_practical_aquaculture_feed_formulation_database_Calculated_Composition_dict.md` — **reference formulations** the engine reproduces as its correctness gate.
