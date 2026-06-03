# Graph Report - .  (2026-06-03)

## Corpus Check
- Corpus is ~6,310 words - fits in a single context window. You may not need a graph.

## Summary
- 115 nodes · 155 edges · 9 communities (8 shown, 1 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 26 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Feed Formulation Engine (FASA)|Feed Formulation Engine (FASA)]]
- [[_COMMUNITY_PondCube Monitoring|PondCube Monitoring]]
- [[_COMMUNITY_Nutrition-Sensitive Fisheries & Harmonization|Nutrition-Sensitive Fisheries & Harmonization]]
- [[_COMMUNITY_Fisher Behavior Trials|Fisher Behavior Trials]]
- [[_COMMUNITY_WIO Harmonization Standards|WIO Harmonization Standards]]
- [[_COMMUNITY_Peskas Platform & Nutrient Models|Peskas Platform & Nutrient Models]]
- [[_COMMUNITY_Peskas Data Pipeline|Peskas Data Pipeline]]
- [[_COMMUNITY_Digital Transformation Accelerator|Digital Transformation Accelerator]]
- [[_COMMUNITY_FADs & Small Pelagics|FADs & Small Pelagics]]

## God Nodes (most connected - your core abstractions)
1. `pondcube_measurements_long.csv` - 10 edges
2. `PondCube Data Dictionary (Full)` - 10 edges
3. `FASA Feed Formulation Engine (MVP)` - 10 edges
4. `PondCube System Overview` - 9 edges
5. `A supply and demand intervention increased fish consumption among rural women (PLoS One 2026)` - 8 edges
6. `pondcube_observations_wide.csv` - 7 edges
7. `Peskas Platform` - 7 edges
8. `Six-Module Peskas Workflow (Collection, Preprocessing, Validation, Analytics, Export, Visualisation)` - 7 edges
9. `Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026)` - 7 edges
10. `PAFF Feed Formulations table` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Phase I Airtable Participatory Diagnostic Survey` --semantically_similar_to--> `Airtable Metadata Registry`  [INFERRED] [semantically similar]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `FAO Ontologies and Classifications (ASFIS, GAUL)` --semantically_similar_to--> `FAO 3-Alpha Code Taxonomic Harmonisation`  [INFERRED] [semantically similar]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_monitoring_system_slides.pdf
- `Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026)` --references--> `Peskas Platform`  [INFERRED]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `Data Ecosystem AoW (FAIR / AI-ready data)` --semantically_similar_to--> `Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026)`  [INFERRED] [semantically similar]
  digital_transformation_accelerator/Digital_Transformation_Accelerator_2025_TR_context.md → data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md
- `Terms/Variables Standardisation Across Organisations` --semantically_similar_to--> `Aquatic Foods Ontology`  [INFERRED] [semantically similar]
  data_harmonization/WIOMSA_harmonization_OCT2025.pdf → peskas/peskas_automated_analytics_softwarex_2025.pdf

## Import Cycles
- None detected.

## Communities (9 total, 1 thin omitted)

### Community 0 - "Feed Formulation Engine (FASA)"
Cohesion: 0.11
Nodes (26): ASNS Nutrition Specification database, Restriction type (Minimum/Maximum/Ratio), ASNS spec code (PA/AA/ADAAF/ED/TX prefixes), stage_weight label, Chance-constrained variability handling, ASNS-to-FICD crosswalk, FASA Feed Formulation Engine (MVP), FastAPI surface (/formulate, /supported, /validate-recipe, /health) (+18 more)

### Community 1 - "PondCube Monitoring"
Cohesion: 0.22
Nodes (18): PondCube System Overview, Ammonia NH3 Toxicity Lookup Table, Blank-Equals-Missing Rule, PondCube Data Dictionary (Full), pondcube_data_quality.csv, Data Dictionary: pondcube_data_quality.csv, Exclusion of Derived/Reference Sheets, Forward-Compatible Time-Series/Observation Model (+10 more)

### Community 2 - "Nutrition-Sensitive Fisheries & Harmonization"
Cohesion: 0.12
Nodes (16): Data Collection Heterogeneity (Five Dimensions), Data Harmonization: Unified Fisheries Data in East Africa (WIOMSA 2025 Slide Deck), Tangible Benefits of Harmonization, Nairobi Convention and SWIOFC Regional Platforms, Complementary Management Pathways, Ecosystem Approach to Fisheries (EAF), Fishery Nutrient Profile (FNP), K-means Clustering of Fishing Trips by Nutrient Density (+8 more)

### Community 3 - "Fisher Behavior Trials"
Cohesion: 0.19
Nodes (15): Before-After-Control-Impact (BACI) design, Beach Management Units (BMUs), Three heuristic behavioral models (info deficit, self-interested, neighborhood-interested), Digital feedback on fisher behavior (Kenya 2025), Knowledge-Attitude-Practice (KAP) framework, How much is too much information? Testing digital feedback on fisher behavior (Frontiers 2025), Peskas open-source digital monitoring toolkit, Child stunting and malnutrition in Timor-Leste (+7 more)

### Community 4 - "WIO Harmonization Standards"
Cohesion: 0.17
Nodes (13): Phase I Airtable Participatory Diagnostic Survey, Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026), FAO Ontologies and Classifications (ASFIS, GAUL), Integrated Data Harmonization Framework (IDHF), Scoping Assessment of 26 Institutions Across 10 WIO Countries, Four Candidate Thematic Domains, CGIAR Harmonization Strategy Variable Table, Minimum Common Denominator of Shared Variables (+5 more)

### Community 5 - "Peskas Platform & Nutrient Models"
Cohesion: 0.20
Nodes (10): NutrientFishbase and Global Food Composition Databases, SHAP Feature Importance Analysis, 6-Year Timor-Leste Catch Dataset (77,438 fishing trips), XGBoost Predictive Model of FNPs, Docker, GitHub Actions and Google Cloud Infrastructure, Low-Cost Open-Source Design Principle, Peskas Platform, Shiny Interactive Dashboard (kepler.gl, multilingual) (+2 more)

### Community 6 - "Peskas Data Pipeline"
Cohesion: 0.25
Nodes (8): estimate_fishery_indicators Function, Harvard Dataverse Open Data Portal, KoboToolbox Field Data Collection, MAD Univariate and Multivariate Outlier Detection, Pelagic Data Systems (PDS) Vessel Tracking, validate_pds_data Function, Six-Module Peskas Workflow (Collection, Preprocessing, Validation, Analytics, Export, Visualisation), MongoDB and Google Cloud Data Storage

### Community 7 - "Digital Transformation Accelerator"
Cohesion: 0.43
Nodes (7): CGIAR Digital Transformation Accelerator, Asia Digital Hub (WorldFish, Penang), Data Ecosystem AoW (FAIR / AI-ready data), Digital Transformation Accelerator — Annual Technical Report 2025, Cloud-Based Genetic Data Ecosystem, Genetic Improvement Data Modernization, Multi-Country Hatchery Programs (Bangladesh, Egypt, Zambia)

## Knowledge Gaps
- **31 isolated node(s):** `Data Dictionary: pondcube_measurements_long.csv`, `Data Dictionary: pondcube_tanks_reference.csv`, `Ecosystem Approach to Fisheries (EAF)`, `PERMANOVA Validation of Nutrient Profiles`, `SHAP Feature Importance Analysis` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Technical Guidelines for SSF Data Harmonization in the WIO (v1.0, April 2026)` connect `WIO Harmonization Standards` to `Nutrition-Sensitive Fisheries & Harmonization`, `Peskas Platform & Nutrient Models`, `Digital Transformation Accelerator`?**
  _High betweenness centrality (0.254) - this node is a cross-community bridge._
- **Why does `Peskas Platform` connect `Peskas Platform & Nutrient Models` to `Nutrition-Sensitive Fisheries & Harmonization`, `WIO Harmonization Standards`?**
  _High betweenness centrality (0.206) - this node is a cross-community bridge._
- **Why does `Data Ecosystem AoW (FAIR / AI-ready data)` connect `Digital Transformation Accelerator` to `WIO Harmonization Standards`?**
  _High betweenness centrality (0.175) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `pondcube_measurements_long.csv` (e.g. with `Cloud-Based Genetic Data Ecosystem` and `Tidy Long Format Convention`) actually correct?**
  _`pondcube_measurements_long.csv` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Data Dictionary: pondcube_measurements_long.csv`, `Data Dictionary: pondcube_tanks_reference.csv`, `Exclusion of Derived/Reference Sheets` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Feed Formulation Engine (FASA)` be split into smaller, more focused modules?**
  _Cohesion score 0.1076923076923077 - nodes in this community are weakly interconnected._
- **Should `Nutrition-Sensitive Fisheries & Harmonization` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._