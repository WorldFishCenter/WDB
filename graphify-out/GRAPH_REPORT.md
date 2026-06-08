# Graph Report - .  (2026-06-08)

## Corpus Check
- 1 files · ~12,530 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 138 nodes · 214 edges · 8 communities
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.82)
- Token cost: 44,000 input · 5,374 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Peskas SSF Catch Data (WIO)|Peskas SSF Catch Data (WIO)]]
- [[_COMMUNITY_SSF Harmonization Governance|SSF Harmonization Governance]]
- [[_COMMUNITY_FAO Standards & Variables|FAO Standards & Variables]]
- [[_COMMUNITY_Nutrition-Sensitive Fisheries|Nutrition-Sensitive Fisheries]]
- [[_COMMUNITY_Aquaculture Feed Formulation (FASA)|Aquaculture Feed Formulation (FASA)]]
- [[_COMMUNITY_SSF Behavioral RCTs|SSF Behavioral RCTs]]
- [[_COMMUNITY_Digital Accelerator & PondCube|Digital Accelerator & PondCube]]
- [[_COMMUNITY_SSF Data Collection Protocols|SSF Data Collection Protocols]]

## God Nodes (most connected - your core abstractions)
1. `Mozambique Validated Trips Dataset` - 22 edges
2. `Kenya Validated Trips Dataset` - 22 edges
3. `Peskas Digital Monitoring System` - 13 edges
4. `Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)` - 13 edges
5. `Zanzibar Validated Trips Dataset` - 12 edges
6. `Technical Guidelines for SSF Data Harmonization in the WIO Region` - 11 edges
7. `Minimum Common Denominator (Minimum Variable Set)` - 9 edges
8. `Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026)` - 8 edges
9. `FASA Feed Formulation Engine` - 8 edges
10. `Digital Feedback on Fisher Behavior & Governance, Kenya (Frontiers 2025)` - 7 edges

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
- **IDHF Three-Phase Harmonization Process** — concept_integrated_data_harmonization_framework, converted_technical_guidelines_ssf_data_harmonization_wio_8f7e1b7e_diagnostic_survey, concept_minimum_common_denominator, converted_technical_guidelines_ssf_data_harmonization_wio_8f7e1b7e_implementation_roadmap [EXTRACTED 0.90]
- **FAO/International Classification Standards Stack** — concept_fao_isscfg, concept_fao_asfis, concept_fao_gaul, concept_iso_8601, concept_aquatic_food_ontology [EXTRACTED 0.90]
- **Minimum Variable Set — Four Thematic Domains** — concept_minimum_common_denominator, converted_technical_guidelines_ssf_data_harmonization_wio_8f7e1b7e_domain_spatial_temporal, converted_technical_guidelines_ssf_data_harmonization_wio_8f7e1b7e_domain_fishing_effort, converted_technical_guidelines_ssf_data_harmonization_wio_8f7e1b7e_domain_catch_composition, converted_technical_guidelines_ssf_data_harmonization_wio_8f7e1b7e_domain_socioeconomic_environmental [EXTRACTED 0.90]

## Communities (8 total, 0 thin omitted)

### Community 0 - "Peskas SSF Catch Data (WIO)"
Cohesion: 0.15
Nodes (29): Catch Habitat Classification, Digital Feedback & Fisher Behavior Kenya (2025), FAO GAUL Administrative Coding, Harmonized Catch/Effort Data, Kenya (coast), Mozambique (coast), Peskas Monitoring System, Peskas Monitoring System Slides (+21 more)

### Community 1 - "SSF Harmonization Governance"
Cohesion: 0.10
Nodes (27): Integrated Data Harmonization Framework (IDHF), Minimum Common Denominator (Minimum Variable Set), Nairobi Convention, Regional Data Dictionary, SSF Data Harmonization, South West Indian Ocean Fisheries Commission (SWIOFC), Working Group on Data and Statistics (WGDS), Technical Guidelines for SSF Data Harmonization in the WIO Region (+19 more)

### Community 2 - "FAO Standards & Variables"
Cohesion: 0.11
Nodes (23): Aquatic Food Ontology (AQFO), Catch and Effort Data, Food and Agriculture Organization of the United Nations (FAO), FAO ASFIS List and 3-alpha Codes, FAO Global Administrative Unit Layers (GAUL), FAO International Standard Statistical Classification of Fishing Gear (ISSCFG), ISO 8601 Date/Time Standard, Domain 3: Catch Composition (+15 more)

### Community 3 - "Nutrition-Sensitive Fisheries"
Cohesion: 0.12
Nodes (19): Fishery Nutrient Profiles Timor-Leste (Nature Food 2026), Aquatic Foods Ontology / ASFIS-ISSCAAP classification, Blue Foods / Nutrient-Dense Aquatic Foods, Complementary Management Pathways, Ecosystem Approach to Fisheries (EAF), Peskas End-to-End Workflow (ingestion to dashboard), Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026), Harvard Dataverse (open data archive) (+11 more)

### Community 4 - "Aquaculture Feed Formulation (FASA)"
Cohesion: 0.29
Nodes (12): ASNS (Aquaculture Species Nutrition Specification database), FICD (Feed Ingredient Composition Database), PAFF Calculated Composition table, PAFF (Practical Aquaculture Feed Formulation database), PAFF Feed Formulations table, Avadí et al. (2022) smallholder aquaculture in Zambia, Bureau (2014) aquaculture feed formulation optimization, ASNS-to-FICD crosswalk (+4 more)

### Community 5 - "SSF Behavioral RCTs"
Cohesion: 0.18
Nodes (12): Beach Management Units (BMUs), Kenya, Cluster-Randomized 2x2 Factorial Trial (NCT04729829), Digital Feedback on Fisher Behavior & Governance, Kenya (Frontiers 2025), Context note: Digital Feedback Fisher Behavior Kenya (2025), Digital Feedback / Information Provision to Fishers, Nearshore Fish-Aggregating Devices (FADs), Supply & Demand Intervention Increasing Fish Consumption RCT, Timor-Leste (PLoS One 2026), Context note: Fish Consumption RCT Timor-Leste (2026) (+4 more)

### Community 6 - "Digital Accelerator & PondCube"
Cohesion: 0.38
Nodes (10): CGIAR Digital Transformation Accelerator — Annual Technical Report 2025, Asia Digital Hub (WorldFish, Penang), Digital Transformation Accelerator (CGIAR), convert_pondcube.py conversion script, pondcube_data_quality log, pondcube_measurements_long table, pondcube_observations_wide table, PondCube (WorldFish genetic-improvement data package) (+2 more)

### Community 7 - "SSF Data Collection Protocols"
Cohesion: 0.33
Nodes (6): Centralized Data Pipelines, Functional Requirements for Electronic Data Collection Tools, Fishery-level Contextual Information for Scaling Up, Quality Assurance and Quality Control (QA/QC) Procedures, Raising Procedures (sample to total estimates), Standardized Sampling Methodologies

## Knowledge Gaps
- **42 isolated node(s):** `Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)`, `Nutrient Density Score (NDS) / Fishery Nutrient Profiles (FNP)`, `Blue Foods / Nutrient-Dense Aquatic Foods`, `Women of Reproductive Age (WRA) Reference Group`, `Context note: Peskas Automated Analytics (SoftwareX 2025)` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Technical Guidelines for SSF Data Harmonization in the WIO Region` connect `SSF Harmonization Governance` to `Peskas SSF Catch Data (WIO)`, `Nutrition-Sensitive Fisheries`?**
  _High betweenness centrality (0.382) - this node is a cross-community bridge._
- **Why does `Minimum Common Denominator (Minimum Variable Set)` connect `SSF Harmonization Governance` to `FAO Standards & Variables`?**
  _High betweenness centrality (0.286) - this node is a cross-community bridge._
- **Why does `Kenya Validated Trips Dataset` connect `Peskas SSF Catch Data (WIO)` to `SSF Harmonization Governance`, `Nutrition-Sensitive Fisheries`, `SSF Behavioral RCTs`?**
  _High betweenness centrality (0.281) - this node is a cross-community bridge._
- **What connects `Context note: Fishery Nutrient Profiles Timor-Leste (Nature Food 2026)`, `Nutrient Density Score (NDS) / Fishery Nutrient Profiles (FNP)`, `Complementary Management Pathways` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Peskas SSF Catch Data (WIO)` be split into smaller, more focused modules?**
  _Cohesion score 0.14532019704433496 - nodes in this community are weakly interconnected._
- **Should `SSF Harmonization Governance` be split into smaller, more focused modules?**
  _Cohesion score 0.09686609686609686 - nodes in this community are weakly interconnected._
- **Should `FAO Standards & Variables` be split into smaller, more focused modules?**
  _Cohesion score 0.1067193675889328 - nodes in this community are weakly interconnected._