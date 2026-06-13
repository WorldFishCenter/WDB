# Graph Report - .  (2026-06-12)

## Corpus Check
- Corpus is ~15,052 words - fits in a single context window. You may not need a graph.

## Summary
- 173 nodes · 320 edges · 7 communities
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.81)
- Token cost: 380,610 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Peskas Platform & SSF Monitoring|Peskas Platform & SSF Monitoring]]
- [[_COMMUNITY_DTA & CGIAR AI Ecosystem|DTA & CGIAR AI Ecosystem]]
- [[_COMMUNITY_Fisheries Data Harmonization & Standards|Fisheries Data Harmonization & Standards]]
- [[_COMMUNITY_WIO Harmonization Framework (IDHF)|WIO Harmonization Framework (IDHF)]]
- [[_COMMUNITY_Fishery Nutrient Profiling & Nutrition|Fishery Nutrient Profiling & Nutrition]]
- [[_COMMUNITY_PondCube & FAIR Data Ecosystem|PondCube & FAIR Data Ecosystem]]
- [[_COMMUNITY_FASA Aquaculture Feed Formulation|FASA Aquaculture Feed Formulation]]

## God Nodes (most connected - your core abstractions)
1. `Peskas` - 40 edges
2. `Fishery Nutrient Profiles for Nutrition-Sensitive SSF Management in Timor-Leste (Nature Food 2026)` - 22 edges
3. `Digital Transformation Accelerator` - 18 edges
4. `WIO SSF Data Harmonization Initiative` - 16 edges
5. `WorldFish` - 14 edges
6. `How Much Is Too Much Information? Digital Feedback on Fisher Behavior (Kenya)` - 14 edges
7. `Supply and Demand Intervention Increased Fish Consumption Among Rural Women (Timor-Leste RCT)` - 13 edges
8. `FASA Feed Formulation Engine` - 12 edges
9. `FASA` - 11 edges
10. `CGIAR` - 10 edges

## Surprising Connections (you probably didn't know these)
- `CGIAR Data Harmonization Workshop & Guidelines` --conceptually_related_to--> `WIO SSF Data Harmonization Initiative`  [INFERRED]
  digital_transformation_accelerator/Digital_Transformation_Accelerator_2025_TR.pdf → data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md
- `COASTS (Small Scale Fisheries Analysis Platform)` --conceptually_related_to--> `Peskas`  [INFERRED]
  data_harmonization/WIOMSA_harmonization_OCT2025.pdf → peskas/peskas_about.md
- `International Potato Center (CIP)` --part_of--> `CGIAR`  [INFERRED]
  digital_transformation_accelerator/Digital_Transformation_Accelerator_2025_TR.pdf → data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md
- `International Rice Research Institute (IRRI)` --part_of--> `CGIAR`  [INFERRED]
  digital_transformation_accelerator/Digital_Transformation_Accelerator_2025_TR.pdf → data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO_context.md
- `KoboToolbox` --references--> `Functional Requirements for Electronic Data Collection Tools`  [EXTRACTED]
  data_harmonization/WIOMSA_harmonization_OCT2025.pdf → graphify-out/converted/Technical_Guidelines_SSF_Data_Harmonization_WIO_8f7e1b7e.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Integrated Data Harmonization Framework Phases** — data_harmonization_idhf_diagnostic_assessment, data_harmonization_idhf_design_standardization, data_harmonization_idhf_implementation_sustainability [EXTRACTED 0.95]
- **FAO Standards Adopted for SSF Data Harmonization** — shared_fao_asfis, shared_fao_gaul, shared_fao_isscfg, shared_aquatic_food_ontology [EXTRACTED 0.95]
- **Four Thematic Domains of the Minimum Variable Set** — data_harmonization_thematic_domain_spatial_temporal, data_harmonization_thematic_domain_fishing_effort, data_harmonization_thematic_domain_catch_composition, data_harmonization_thematic_domain_socioeconomic_environmental [EXTRACTED 0.95]
- **DTA Four Areas of Work** — dta_aow_data_ecosystem, dta_aow_action_lab, dta_aow_digital_futures, dta_aow_enabling_environment [EXTRACTED 1.00]
- **CGIAR AI Hub Product Suite** — shared_agrillm, dta_genebank_ai, dta_hydrology_ai, shared_cgiar_ai_hub [EXTRACTED 0.85]
- **FAIR Data Ecosystem Stack** — shared_carob_framework, shared_gardian_platform, shared_terminag_vocabulary, shared_fair_ai_ready_data [INFERRED 0.85]
- **PondCube July 2025 Water-Quality Dataset Artifacts** — pondcube_measurements_long, pondcube_observations_wide, pondcube_tanks_reference, pondcube_data_quality [EXTRACTED 0.95]
- **FASA Reference Database Family (ASNS / FICD / PAFF)** — fasa_asns_database, fasa_ficd_database, fasa_paff_feed_formulations, fasa_paff_calculated_composition [EXTRACTED 0.95]
- **FASA Feed-Formulation Pipeline (engine consumes ASNS specs + FICD composition)** — fasa_repo, fasa_asns_database, fasa_ficd_database, fasa_crosswalk [EXTRACTED 0.95]
- **PAFF Correctness Gate (engine recomputes PAFF recipes from FICD)** — fasa_paff_benchmark_gate, fasa_paff_feed_formulations, fasa_paff_calculated_composition, fasa_ficd_database [EXTRACTED 0.95]
- **Peskas end-to-end six-module workflow (ingestion to dashboard)** — peskas_ingestion_pipeline, peskas_validation_engine, peskas_dashboard, peskas_harvard_dataverse [EXTRACTED 0.85]
- **Peskas multi-source data integration** — peskas_ingestion_pipeline, peskas_kobotoolbox, peskas_pelagic_data_systems, peskas_fishbase [EXTRACTED 0.85]
- **Peskas AABS East-Africa scaling** — peskas_hub, shared_aabs, shared_kenya, shared_zanzibar, shared_mozambique [EXTRACTED 0.85]
- **Peskas East-Africa validated-trips datasets (Kenya, Mozambique, Zanzibar)** — peskas_kenya_validated_trips_kenya_validated_trips, peskas_mozambique_validated_trips_mozambique_validated_trips, peskas_zanzibar_validated_trips_zanzibar_validated_trips, peskas_hub [EXTRACTED 0.95]
- **FNP modelling method stack (k-means clustering, PERMANOVA, XGBoost, SHAP)** — shared_kmeans_clustering, shared_permanova, shared_xgboost, shared_shap_values [EXTRACTED 0.85]
- **Nutrition-sensitive SSF management framework (FNP, NDS, NSFM, blue foods)** — shared_fishery_nutrient_profile, shared_nutrient_density_score, shared_nutrition_sensitive_fisheries_management, shared_blue_foods [EXTRACTED 0.85]
- **Integrated Supply-and-Demand Food-System Intervention (FAD + SBC, Timor-Leste RCT)** — ssf_research_fish_consumption_rct_timor_leste_2026_paper, ssf_research_timor_leste_rct_fad, ssf_research_timor_leste_rct_sbc, ssf_research_timor_leste_rct_2x2_factorial [EXTRACTED 0.95]
- **Peskas-Driven Digital-Feedback Experiment Across Kenyan BMUs (KAP + BACI)** — ssf_research_digital_feedback_fisher_behavior_kenya_2025_paper, peskas_hub, ssf_research_digital_feedback_kenya_bmu, ssf_research_digital_feedback_kenya_kap_framework, ssf_research_digital_feedback_kenya_baci_design [EXTRACTED 0.95]

## Communities (7 total, 0 thin omitted)

### Community 0 - "Peskas Platform & SSF Monitoring"
Cohesion: 0.07
Nodes (42): Centralized Tool-Agnostic Data Pipeline, COASTS (Small Scale Fisheries Analysis Platform), Dataverse Project, Functional Requirements for Electronic Data Collection Tools, FishBase, Phased Implementation Roadmap (2026-2030), KoboToolbox, Paper vs. Digital Data Collection (+34 more)

### Community 1 - "DTA & CGIAR AI Ecosystem"
Cohesion: 0.09
Nodes (35): Digital Transformation Accelerator — Annual Technical Report 2025, Digital Transformation Accelerator — Overview (about), CGIAR AI Co-Scientist, Action Lab (AoW2), Digital Futures (AoW3), Enabling Environment (AoW4), Asia Digital Hub at WorldFish (Penang), Genebank AI (+27 more)

### Community 2 - "Fisheries Data Harmonization & Standards"
Cohesion: 0.16
Nodes (25): Data Collection Heterogeneity (five dimensions), Data Governance & Institutional Arrangements, Data-Information-Knowledge-Insight Integration, WIO SSF Data Harmonization Initiative, Regional Data Dictionary, Species List & Taxonomic Resolution Heterogeneity, Technical Guidelines for SSF Data Harmonization in the WIO Region, Terms/Variable Standardization (+17 more)

### Community 3 - "WIO Harmonization Framework (IDHF)"
Cohesion: 0.12
Nodes (19): Airtable Diagnostic Survey Form, Participatory Diagnostic Survey of Data Collection Practices, Design and Standardization Phase, Diagnostic Assessment Phase, Implementation and Sustainability Phase, Integrated Data Harmonization Framework (IDHF), ISO 8601 Date/Time Standard, Minimum Common Denominator (+11 more)

### Community 4 - "Fishery Nutrient Profiling & Nutrition"
Cohesion: 0.14
Nodes (18): Fishery Nutrient Profiles for Nutrition-Sensitive SSF Management in Timor-Leste (Nature Food 2026), Blue Foods / Aquatic Foods for Nutrition, Ecosystem Approach to Fisheries (EAF), FAO/INFOODS Global Food Composition Database for Fish and Shellfish, Fish Aggregating Devices (FADs), Fishery Nutrient Profile (FNP), k-means Clustering, Micronutrient Deficiency in LMICs (+10 more)

### Community 5 - "PondCube & FAIR Data Ecosystem"
Cohesion: 0.24
Nodes (17): Data Ecosystem (AoW1), CGIAR Data Harmonization Workshop & Guidelines, convert_pondcube.py, pondcube_data_quality.csv, WorldFish Genetic Improvement Programs, PondCube, pondcube_measurements_long.csv, pondcube_observations_wide.csv (+9 more)

### Community 6 - "FASA Aquaculture Feed Formulation"
Cohesion: 0.24
Nodes (17): ASNS Nutrition Specification Database, ASNS to FICD Crosswalk, FICD Feed Ingredient Composition Database, FASA, Least-Cost Linear Programming Formulation Model, PAFF Benchmark Gate, PAFF Calculated Composition Database, PAFF Feed Formulations Database (+9 more)

## Knowledge Gaps
- **53 isolated node(s):** `Tungpantong et al. (2021)`, `Minimum Common Denominator`, `Domain 4: Socio-economic and Environmental Context`, `Airtable Diagnostic Survey Form`, `Regional Scoping Assessment (26 institutions, 10 WIO countries)` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Peskas` connect `Peskas Platform & SSF Monitoring` to `DTA & CGIAR AI Ecosystem`, `Fisheries Data Harmonization & Standards`, `Fishery Nutrient Profiling & Nutrition`, `FASA Aquaculture Feed Formulation`?**
  _High betweenness centrality (0.373) - this node is a cross-community bridge._
- **Why does `WorldFish` connect `DTA & CGIAR AI Ecosystem` to `Peskas Platform & SSF Monitoring`, `Fisheries Data Harmonization & Standards`, `Fishery Nutrient Profiling & Nutrition`, `PondCube & FAIR Data Ecosystem`, `FASA Aquaculture Feed Formulation`?**
  _High betweenness centrality (0.279) - this node is a cross-community bridge._
- **Why does `Fishery Nutrient Profiles for Nutrition-Sensitive SSF Management in Timor-Leste (Nature Food 2026)` connect `Fishery Nutrient Profiling & Nutrition` to `Peskas Platform & SSF Monitoring`, `DTA & CGIAR AI Ecosystem`, `Fisheries Data Harmonization & Standards`, `FASA Aquaculture Feed Formulation`?**
  _High betweenness centrality (0.196) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Peskas` (e.g. with `COASTS (Small Scale Fisheries Analysis Platform)` and `Peskas COASTS (regional analysis platform)`) actually correct?**
  _`Peskas` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Digital Transformation Accelerator` (e.g. with `WIO SSF Data Harmonization Initiative` and `Aquaculture`) actually correct?**
  _`Digital Transformation Accelerator` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `WIO SSF Data Harmonization Initiative` (e.g. with `Digital Transformation Accelerator` and `FAIR / AI-ready Data`) actually correct?**
  _`WIO SSF Data Harmonization Initiative` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Tungpantong et al. (2021)`, `Minimum Common Denominator`, `Domain 4: Socio-economic and Environmental Context` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._