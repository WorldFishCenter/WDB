# Graph Report - .  (2026-06-08)

## Corpus Check
- 5 files · ~12,818 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 171 nodes · 264 edges · 7 communities
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.83)
- Token cost: 39,123 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_FASA Feed Formulation Engine|FASA Feed Formulation Engine]]
- [[_COMMUNITY_WIO SSF Data Harmonization|WIO SSF Data Harmonization]]
- [[_COMMUNITY_Peskas Validated-Trip Data (WIO)|Peskas Validated-Trip Data (WIO)]]
- [[_COMMUNITY_Fisheries Data Standards & Governance|Fisheries Data Standards & Governance]]
- [[_COMMUNITY_Digital Transformation Accelerator & PondCube|Digital Transformation Accelerator & PondCube]]
- [[_COMMUNITY_Blue-Food Nutrition & Peskas Workflow|Blue-Food Nutrition & Peskas Workflow]]
- [[_COMMUNITY_Fisheries Behavior & Nutrition Trials|Fisheries Behavior & Nutrition Trials]]

## God Nodes (most connected - your core abstractions)
1. `Mozambique Validated Trips Dataset` - 22 edges
2. `Kenya Validated Trips Dataset` - 22 edges
3. `FASA Feed Formulation Engine` - 17 edges
4. `Peskas Digital Monitoring System` - 13 edges
5. `Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)` - 13 edges
6. `Zanzibar Validated Trips Dataset` - 12 edges
7. `Technical Guidelines for SSF Data Harmonization in the WIO Region` - 11 edges
8. `Linear programming engine (PuLP + HiGHS)` - 10 edges
9. `Minimum Common Denominator (Minimum Variable Set)` - 9 edges
10. `Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026)` - 8 edges

## Surprising Connections (you probably didn't know these)
- `FAO Ontologies (ASFIS, GAUL administrative layers)` --semantically_similar_to--> `Aquatic Foods Ontology / ASFIS-ISSCAAP classification`  [INFERRED] [semantically similar]
  data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `Technical Guidelines for SSF Data Harmonization in the WIO Region` --conceptually_related_to--> `Peskas Digital Monitoring System`  [INFERRED]
  graphify-out/converted/Technical_Guidelines_SSF_Data_Harmonization_WIO_8f7e1b7e.md → peskas/peskas_automated_analytics_softwarex_2025.pdf
- `Kenya Validated Trips Dataset` --shares_data_with--> `Digital Feedback on Fisher Behavior & Governance, Kenya (Frontiers 2025)`  [EXTRACTED]
  peskas/kenya_validated_trips_dict.md → ssf_research/digital_feedback_fisher_behavior_kenya_2025.pdf
- `Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026)` --conceptually_related_to--> `Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)`  [EXTRACTED]
  ssf_research/fish_consumption_rct_timor_leste_2026.pdf → peskas/kenya_validated_trips_dict.md
- `Data Harmonization: Unified Fisheries Data in East Africa (WIOMSA Slides Oct 2025)` --references--> `Technical Guidelines for SSF Data Harmonization in the WIO Region`  [EXTRACTED]
  data_harmonization/WIOMSA_harmonization_OCT2025.pdf → graphify-out/converted/Technical_Guidelines_SSF_Data_Harmonization_WIO_8f7e1b7e.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **PondCube July 2025 published water-quality CSVs** — pondcube_pondcube_about_pondcube_measurements_long_csv, pondcube_pondcube_about_pondcube_observations_wide_csv, pondcube_pondcube_about_pondcube_tanks_reference_csv, pondcube_pondcube_about_pondcube_data_quality_csv, pondcube_pondcube_data_about_source_workbook [EXTRACTED 1.00]
- **FASA engine reference databases (ASNS/FICD/PAFF)** — fasa_fasa_repo_about_lp_engine, fasa_fasa_repo_about_asns_database, fasa_fasa_repo_about_ficd_database, fasa_fasa_repo_about_paff_database [EXTRACTED 1.00]
- **FASA LP formulation flow (engine, crosswalk, constraints, IIS)** — fasa_fasa_repo_about_lp_engine, fasa_fasa_repo_about_crosswalk, fasa_fasa_repo_about_premix_masking, fasa_fasa_repo_about_toxin_ceilings, fasa_fasa_repo_about_iis_reporting [INFERRED 0.85]

## Communities (7 total, 0 thin omitted)

### Community 0 - "FASA Feed Formulation Engine"
Cohesion: 0.10
Nodes (31): ASNS (Aquaculture Species Nutrition Specification database), African Catfish, Circular economy (waste-to-feed), FASA Initiative, FASA Feed-Formulation App (the engine), Nile Tilapia, ASNS nutrition specification database, Avadí et al. (2022) — Smallholder aquaculture sustainability in Zambia (+23 more)

### Community 1 - "WIO SSF Data Harmonization"
Cohesion: 0.08
Nodes (29): Catch and Effort Data, Integrated Data Harmonization Framework (IDHF), Minimum Common Denominator (Minimum Variable Set), Nairobi Convention, SSF Data Harmonization, Technical Guidelines for SSF Data Harmonization in the WIO Region, CGIAR Harmonization Strategy, Diagnostic Survey of Current Data Collection Practices (Phase I) (+21 more)

### Community 2 - "Peskas Validated-Trip Data (WIO)"
Cohesion: 0.15
Nodes (29): Catch Habitat Classification, Digital Feedback & Fisher Behavior Kenya (2025), FAO GAUL Administrative Coding, Harmonized Catch/Effort Data, Kenya (coast), Mozambique (coast), Peskas Monitoring System, Peskas Monitoring System Slides (+21 more)

### Community 3 - "Fisheries Data Standards & Governance"
Cohesion: 0.09
Nodes (27): Aquatic Food Ontology (AQFO), Food and Agriculture Organization of the United Nations (FAO), FAO ASFIS List and 3-alpha Codes, FAO Global Administrative Unit Layers (GAUL), FAO International Standard Statistical Classification of Fishing Gear (ISSCFG), ISO 8601 Date/Time Standard, Regional Data Dictionary, South West Indian Ocean Fisheries Commission (SWIOFC) (+19 more)

### Community 4 - "Digital Transformation Accelerator & PondCube"
Cohesion: 0.14
Nodes (24): CGIAR Digital Transformation Accelerator — Annual Technical Report 2025, Asia Digital Hub (WorldFish, Penang), AgriLLM (open-source agricultural LLM), Asia Digital Hub at WorldFish (Penang), Carob harmonization framework, CGIAR AI Hub, Data Ecosystem (Area of Work), FAIR-by-design and AI-ready data (+16 more)

### Community 5 - "Blue-Food Nutrition & Peskas Workflow"
Cohesion: 0.12
Nodes (19): Fishery Nutrient Profiles Timor-Leste (Nature Food 2026), Aquatic Foods Ontology / ASFIS-ISSCAAP classification, Blue Foods / Nutrient-Dense Aquatic Foods, Complementary Management Pathways, Ecosystem Approach to Fisheries (EAF), Peskas End-to-End Workflow (ingestion to dashboard), Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026), Harvard Dataverse (open data archive) (+11 more)

### Community 6 - "Fisheries Behavior & Nutrition Trials"
Cohesion: 0.18
Nodes (12): Beach Management Units (BMUs), Kenya, Cluster-Randomized 2x2 Factorial Trial (NCT04729829), Digital Feedback on Fisher Behavior & Governance, Kenya (Frontiers 2025), Context note: Digital Feedback Fisher Behavior Kenya (2025), Digital Feedback / Information Provision to Fishers, Nearshore Fish-Aggregating Devices (FADs), Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026), Context note: Fish Consumption RCT Timor-Leste (2026) (+4 more)

## Knowledge Gaps
- **56 isolated node(s):** `Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)`, `Nutrient Density Score (NDS) / Fishery Nutrient Profiles (FNP)`, `Blue Foods / Nutrient-Dense Aquatic Foods`, `Women of Reproductive Age (WRA) Reference Group`, `Context note: Peskas Automated Analytics (SoftwareX 2025)` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Technical Guidelines for SSF Data Harmonization in the WIO Region` connect `WIO SSF Data Harmonization` to `Peskas Validated-Trip Data (WIO)`, `Blue-Food Nutrition & Peskas Workflow`?**
  _High betweenness centrality (0.248) - this node is a cross-community bridge._
- **Why does `Minimum Common Denominator (Minimum Variable Set)` connect `WIO SSF Data Harmonization` to `Fisheries Data Standards & Governance`?**
  _High betweenness centrality (0.185) - this node is a cross-community bridge._
- **Why does `Kenya Validated Trips Dataset` connect `Peskas Validated-Trip Data (WIO)` to `WIO SSF Data Harmonization`, `Blue-Food Nutrition & Peskas Workflow`, `Fisheries Behavior & Nutrition Trials`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **What connects `Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)`, `Nutrient Density Score (NDS) / Fishery Nutrient Profiles (FNP)`, `Complementary Management Pathways` to the rest of the system?**
  _65 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `FASA Feed Formulation Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.1032258064516129 - nodes in this community are weakly interconnected._
- **Should `WIO SSF Data Harmonization` be split into smaller, more focused modules?**
  _Cohesion score 0.08374384236453201 - nodes in this community are weakly interconnected._
- **Should `Peskas Validated-Trip Data (WIO)` be split into smaller, more focused modules?**
  _Cohesion score 0.14532019704433496 - nodes in this community are weakly interconnected._