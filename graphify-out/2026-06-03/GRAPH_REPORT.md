# Graph Report - .  (2026-06-03)

## Corpus Check
- Corpus is ~5,881 words - fits in a single context window. You may not need a graph.

## Summary
- 108 nodes · 141 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Feed Formulation Engine (FASA)|Feed Formulation Engine (FASA)]]
- [[_COMMUNITY_Nutrient Profiling & Peskas Platform|Nutrient Profiling & Peskas Platform]]
- [[_COMMUNITY_PondCube Monitoring|PondCube Monitoring]]
- [[_COMMUNITY_Peskas Pipeline & Harmonization|Peskas Pipeline & Harmonization]]
- [[_COMMUNITY_Fisher Behavior Trials|Fisher Behavior Trials]]
- [[_COMMUNITY_WIO Harmonization Standards|WIO Harmonization Standards]]
- [[_COMMUNITY_LP Solver Internals|LP Solver Internals]]
- [[_COMMUNITY_FADs & Small Pelagics|FADs & Small Pelagics]]

## God Nodes (most connected - your core abstractions)
1. `PondCube Data Dictionary (Full)` - 10 edges
2. `FASA Feed Formulation Engine (MVP)` - 10 edges
3. `pondcube_measurements_long.csv` - 9 edges
4. `A supply and demand intervention increased fish consumption among rural women (PLoS One 2026)` - 8 edges
5. `pondcube_observations_wide.csv` - 7 edges
6. `PondCube System Overview` - 7 edges
7. `Peskas Platform` - 7 edges
8. `Six-Module Peskas Workflow (Collection, Preprocessing, Validation, Analytics, Export, Visualisation)` - 7 edges
9. `PAFF Feed Formulations table` - 7 edges
10. `ASNS Nutrition Specification database` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Phase I Airtable Participatory Diagnostic Survey` --semantically_similar_to--> `Airtable Metadata Registry`  [INFERRED] [semantically similar]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `FAO Ontologies and Classifications (ASFIS, GAUL)` --semantically_similar_to--> `FAO 3-Alpha Code Taxonomic Harmonisation`  [INFERRED] [semantically similar]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_monitoring_system_slides.pdf
- `Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026)` --references--> `Peskas Platform`  [INFERRED]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `Terms/Variables Standardisation Across Organisations` --semantically_similar_to--> `Aquatic Foods Ontology`  [INFERRED] [semantically similar]
  data_harmonization/WIOMSA_harmonization_OCT2025.pdf → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `Data Collection Heterogeneity (Five Dimensions)` --semantically_similar_to--> `Challenges in SSF Data Collection`  [INFERRED] [semantically similar]
  data_harmonization/WIOMSA_harmonization_OCT2025.pdf → peskas/peskas_monitoring_system_slides.pdf

## Import Cycles
- None detected.

## Communities (8 total, 1 thin omitted)

### Community 0 - "Feed Formulation Engine (FASA)"
Cohesion: 0.13
Nodes (23): ASNS Nutrition Specification database, Restriction type (Minimum/Maximum/Ratio), ASNS spec code (PA/AA/ADAAF/ED/TX prefixes), stage_weight label, Chance-constrained variability handling, ASNS-to-FICD crosswalk, FASA Feed Formulation Engine (MVP), FastAPI surface (/formulate, /supported, /validate-recipe, /health) (+15 more)

### Community 1 - "Nutrient Profiling & Peskas Platform"
Cohesion: 0.11
Nodes (19): Complementary Management Pathways, Ecosystem Approach to Fisheries (EAF), NutrientFishbase and Global Food Composition Databases, Fishery Nutrient Profile (FNP), K-means Clustering of Fishing Trips by Nutrient Density, Nutrition-Sensitive Fisheries Management (NSFM), Fishery Nutrient Profiles for NSFM in Timor-Leste (Nature Food 2026), PERMANOVA Validation of Nutrient Profiles (+11 more)

### Community 2 - "PondCube Monitoring"
Cohesion: 0.22
Nodes (18): PondCube System Overview, Ammonia NH3 Toxicity Lookup Table, Blank-Equals-Missing Rule, PondCube Data Dictionary (Full), pondcube_data_quality.csv, Data Dictionary: pondcube_data_quality.csv, Exclusion of Derived/Reference Sheets, Forward-Compatible Time-Series/Observation Model (+10 more)

### Community 3 - "Peskas Pipeline & Harmonization"
Cohesion: 0.13
Nodes (15): Data Collection Heterogeneity (Five Dimensions), Data Harmonization: Unified Fisheries Data in East Africa (WIOMSA 2025 Slide Deck), Tangible Benefits of Harmonization, Nairobi Convention and SWIOFC Regional Platforms, estimate_fishery_indicators Function, Harvard Dataverse Open Data Portal, KoboToolbox Field Data Collection, MAD Univariate and Multivariate Outlier Detection (+7 more)

### Community 4 - "Fisher Behavior Trials"
Cohesion: 0.19
Nodes (15): Before-After-Control-Impact (BACI) design, Beach Management Units (BMUs), Three heuristic behavioral models (info deficit, self-interested, neighborhood-interested), Digital feedback on fisher behavior (Kenya 2025), Knowledge-Attitude-Practice (KAP) framework, How much is too much information? Testing digital feedback on fisher behavior (Frontiers 2025), Peskas open-source digital monitoring toolkit, Child stunting and malnutrition in Timor-Leste (+7 more)

### Community 5 - "WIO Harmonization Standards"
Cohesion: 0.17
Nodes (13): Phase I Airtable Participatory Diagnostic Survey, Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026), FAO Ontologies and Classifications (ASFIS, GAUL), Integrated Data Harmonization Framework (IDHF), Scoping Assessment of 26 Institutions Across 10 WIO Countries, Four Candidate Thematic Domains, CGIAR Harmonization Strategy Variable Table, Minimum Common Denominator of Shared Variables (+5 more)

### Community 6 - "LP Solver Internals"
Cohesion: 0.67
Nodes (3): Hard-fail with IIS reporting (deletion filter), Linear programming engine (PuLP + HiGHS), Premix-aware constraint masking

## Knowledge Gaps
- **30 isolated node(s):** `Data Dictionary: pondcube_measurements_long.csv`, `Data Dictionary: pondcube_tanks_reference.csv`, `Ecosystem Approach to Fisheries (EAF)`, `PERMANOVA Validation of Nutrient Profiles`, `SHAP Feature Importance Analysis` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Peskas Platform` connect `Nutrient Profiling & Peskas Platform` to `WIO Harmonization Standards`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026)` connect `WIO Harmonization Standards` to `Nutrient Profiling & Peskas Platform`, `Peskas Pipeline & Harmonization`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `Six-Module Peskas Workflow (Collection, Preprocessing, Validation, Analytics, Export, Visualisation)` connect `Peskas Pipeline & Harmonization` to `Nutrient Profiling & Peskas Platform`, `WIO Harmonization Standards`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **What connects `Data Dictionary: pondcube_measurements_long.csv`, `Data Dictionary: pondcube_tanks_reference.csv`, `Exclusion of Derived/Reference Sheets` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Feed Formulation Engine (FASA)` be split into smaller, more focused modules?**
  _Cohesion score 0.12648221343873517 - nodes in this community are weakly interconnected._
- **Should `Nutrient Profiling & Peskas Platform` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Should `Peskas Pipeline & Harmonization` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._