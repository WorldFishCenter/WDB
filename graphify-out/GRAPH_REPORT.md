# Graph Report - .  (2026-06-05)

## Corpus Check
- Corpus is ~6,520 words - fits in a single context window. You may not need a graph.

## Summary
- 63 nodes · 83 edges · 7 communities
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.72)
- Token cost: 87,515 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_FASA Feed Formulation Engine|FASA Feed Formulation Engine]]
- [[_COMMUNITY_Peskas Monitoring & Tooling|Peskas Monitoring & Tooling]]
- [[_COMMUNITY_SSF Behaviour-Change Interventions|SSF Behaviour-Change Interventions]]
- [[_COMMUNITY_WIO Data Harmonization|WIO Data Harmonization]]
- [[_COMMUNITY_Nutrition-Sensitive Fisheries (Timor-Leste)|Nutrition-Sensitive Fisheries (Timor-Leste)]]
- [[_COMMUNITY_PondCube Water-Quality Data|PondCube Water-Quality Data]]
- [[_COMMUNITY_Digital Transformation Accelerator|Digital Transformation Accelerator]]

## God Nodes (most connected - your core abstractions)
1. `Peskas Digital Monitoring System` - 12 edges
2. `Fishery Nutrient Profiles for NSFM in Timor-Leste (Nature Food 2026)` - 9 edges
3. `Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026)` - 8 edges
4. `FASA Feed Formulation Engine` - 8 edges
5. `Technical Guidelines for SSF Data Harmonization in the WIO (Context note)` - 7 edges
6. `Digital Feedback on Fisher Behavior & Governance, Kenya (Frontiers 2025)` - 6 edges
7. `PAFF Calculated Composition table` - 6 edges
8. `PAFF Feed Formulations table` - 5 edges
9. `ASNS (Aquaculture Species Nutrition Specification database)` - 5 edges
10. `FICD (Feed Ingredient Composition Database)` - 5 edges

## Surprising Connections (you probably didn't know these)
- `FAO Ontologies (ASFIS, GAUL administrative layers)` --semantically_similar_to--> `Aquatic Foods Ontology / ASFIS-ISSCAAP classification`  [INFERRED] [semantically similar]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `Technical Guidelines for SSF Data Harmonization in the WIO (Context note)` --conceptually_related_to--> `Peskas Digital Monitoring System`  [INFERRED]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)` --references--> `Fishery Nutrient Profiles for NSFM in Timor-Leste (Nature Food 2026)`  [EXTRACTED]
  peskas/fishery_nutrient_profiles_timor_leste_naturefood_2026_context.md → peskas/fishery_nutrient_profiles_timor_leste_naturefood_2026.pdf
- `Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026)` --conceptually_related_to--> `Fishery Nutrient Profiles for NSFM in Timor-Leste (Nature Food 2026)`  [EXTRACTED]
  ssf_research/fish_consumption_rct_timor_leste_2026.pdf → peskas/fishery_nutrient_profiles_timor_leste_naturefood_2026.pdf
- `Digital Feedback on Fisher Behavior & Governance, Kenya (Frontiers 2025)` --references--> `Peskas Digital Monitoring System`  [EXTRACTED]
  ssf_research/digital_feedback_fisher_behavior_kenya_2025.pdf → peskas/peskas_automated_analytics_softwarex_2025.pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Peskas data system underpinning Timor-Leste fisheries-nutrition research** — peskas_peskas_platform, peskas_peskas_automated_analytics_softwarex_2025, peskas_fishery_nutrient_profiles_timor_leste_naturefood_2026 [EXTRACTED 1.00]
- **Timor-Leste nutrition-sensitive fisheries & fish-consumption interventions** — peskas_fishery_nutrient_profiles_timor_leste_naturefood_2026, ssf_research_fish_consumption_rct_timor_leste_2026, ssf_research_timor_leste_malnutrition_stunting [INFERRED 0.85]
- **FASA least-cost feed formulation pipeline (constraints + ingredients + benchmark)** — fasa_repo_engine, fasa_asns_database, fasa_ficd_database, fasa_paff_calculated_composition [EXTRACTED 1.00]
- **PondCube water-quality dataset family (converted from source workbook)** — pondcube_measurements_long, pondcube_observations_wide, pondcube_tanks_reference, pondcube_data_quality, pondcube_convert_script [EXTRACTED 1.00]

## Communities (7 total, 0 thin omitted)

### Community 0 - "FASA Feed Formulation Engine"
Cohesion: 0.29
Nodes (12): ASNS (Aquaculture Species Nutrition Specification database), FICD (Feed Ingredient Composition Database), PAFF Calculated Composition table, PAFF (Practical Aquaculture Feed Formulation database), PAFF Feed Formulations table, Avadí et al. (2022) smallholder aquaculture in Zambia, Bureau (2014) aquaculture feed formulation optimization, ASNS-to-FICD crosswalk (+4 more)

### Community 1 - "Peskas Monitoring & Tooling"
Cohesion: 0.18
Nodes (12): Aquatic Foods Ontology / ASFIS-ISSCAAP classification, Peskas End-to-End Workflow (ingestion to dashboard), Harvard Dataverse (open data archive), IUU Fishing Monitoring, KoBoToolbox (field data collection), Low-Cost Open-Source Adaptable Template, Pelagic Data Systems (PDS) vessel tracking, Peskas: Automated Analytics for Small-Scale, Data-Deficient Fisheries (SoftwareX 2025) (+4 more)

### Community 2 - "SSF Behaviour-Change Interventions"
Cohesion: 0.18
Nodes (12): Beach Management Units (BMUs), Kenya, Cluster-Randomized 2x2 Factorial Trial (NCT04729829), Digital Feedback on Fisher Behavior & Governance, Kenya (Frontiers 2025), Context note: Digital Feedback Fisher Behavior Kenya (2025), Digital Feedback / Information Provision to Fishers, Nearshore Fish-Aggregating Devices (FADs), Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026), Context note: Fish Consumption RCT Timor-Leste (2026) (+4 more)

### Community 3 - "WIO Data Harmonization"
Cohesion: 0.25
Nodes (9): FAO Ontologies (ASFIS, GAUL administrative layers), Integrated Data Harmonization Framework (IDHF, Tungpantong et al. 2021), Minimum Common Denominator (core variable set), Regional Bodies & Platforms (Nairobi Convention, SWIOFC, WGDS), Technical Guidelines for SSF Data Harmonization in the WIO (Context note), Rationale for SSF Data Harmonization, Western Indian Ocean (WIO) Region / East Africa SSF, Data Harmonization: Unified Fisheries Data in East Africa (WIOMSA Slides Oct 2025) (+1 more)

### Community 4 - "Nutrition-Sensitive Fisheries (Timor-Leste)"
Cohesion: 0.29
Nodes (8): Blue Foods / Nutrient-Dense Aquatic Foods, Complementary Management Pathways, Ecosystem Approach to Fisheries (EAF), Fishery Nutrient Profiles for NSFM in Timor-Leste (Nature Food 2026), Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026), Nutrient Density Score (NDS) / Fishery Nutrient Profiles (FNP), Nutrition-Sensitive Fisheries Management (NSFM), Women of Reproductive Age (WRA) Reference Group

### Community 5 - "PondCube Water-Quality Data"
Cohesion: 0.80
Nodes (6): convert_pondcube.py conversion script, pondcube_data_quality log, pondcube_measurements_long table, pondcube_observations_wide table, pondcube_tanks_reference table, PondCube water-quality dataset (July 2025)

### Community 6 - "Digital Transformation Accelerator"
Cohesion: 0.67
Nodes (4): CGIAR Digital Transformation Accelerator — Annual Technical Report 2025, Asia Digital Hub (WorldFish, Penang), Digital Transformation Accelerator (CGIAR), PondCube (WorldFish genetic-improvement data package)

## Knowledge Gaps
- **26 isolated node(s):** `Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)`, `Nutrient Density Score (NDS) / Fishery Nutrient Profiles (FNP)`, `Blue Foods / Nutrient-Dense Aquatic Foods`, `Women of Reproductive Age (WRA) Reference Group`, `Context note: Peskas Automated Analytics (SoftwareX 2025)` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Peskas Digital Monitoring System` connect `Peskas Monitoring & Tooling` to `SSF Behaviour-Change Interventions`, `WIO Data Harmonization`, `Nutrition-Sensitive Fisheries (Timor-Leste)`?**
  _High betweenness centrality (0.275) - this node is a cross-community bridge._
- **Why does `Fishery Nutrient Profiles for NSFM in Timor-Leste (Nature Food 2026)` connect `Nutrition-Sensitive Fisheries (Timor-Leste)` to `Peskas Monitoring & Tooling`, `SSF Behaviour-Change Interventions`?**
  _High betweenness centrality (0.174) - this node is a cross-community bridge._
- **Why does `Technical Guidelines for SSF Data Harmonization in the WIO (Context note)` connect `WIO Data Harmonization` to `Peskas Monitoring & Tooling`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **What connects `Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)`, `Nutrient Density Score (NDS) / Fishery Nutrient Profiles (FNP)`, `Complementary Management Pathways` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._