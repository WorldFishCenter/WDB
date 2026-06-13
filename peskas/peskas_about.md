---
source_url: https://peskas.org/
captured_at: 2026-06-11
---

# Peskas

Peskas is an open-source, near-real-time digital platform that automates the collection, analysis, and visualization of small-scale fisheries data to overcome severe data scarcity and inform sustainable marine resource management.

## Aim
Small-scale fisheries (SSFs) are critical for global food security, livelihoods, and poverty eradication, yet they remain chronically data-deficient due to their diverse, dispersed, and informal nature. Peskas exists to solve this problem by providing a low-cost, adaptable digital infrastructure that transforms raw catch and effort data into actionable, decision-ready insights. Its ultimate goal is to empower a wide range of stakeholders—from local fishers and enumerators to national policymakers—with transparent, trustworthy evidence to support co-management, enhance equitable ocean governance, and optimize the nutritional and economic benefits of aquatic food systems.

## Scope (current state)
Peskas originated as the flagship national fisheries monitoring system for **Timor-Leste** and has since scaled to multiple countries across Asia and East Africa, including **Malaysia, Kenya, Zanzibar, Mozambique, and Malawi**. The initiative covers the entire data lifecycle from landing site to national dashboard:

* **Data Collection Methods**: Utilizes community enumerators equipped with digital survey tools (e.g., KoBoToolbox) at landing sites to record catch volume, species composition, pricing, and gear type. This is integrated with high-resolution GPS vessel tracking (e.g., Pelagic Data Systems) to monitor fishing effort and spatial distribution.
* **Harmonization & Validation**: Raw data is preprocessed, reshaped, and harmonized against international standards, including the Aquatic Foods Ontology and FAO ASFIS 3-alpha codes. It features an automated validation engine using univariate and multivariate statistical methods to flag outliers and errors in near-real time.
* **Nutrition-Sensitive Analytics**: Incorporates advanced data-mining and machine learning (XGBoost) to model **Fishery Nutrient Profiles (FNPs)**. By linking catch data with databases like FishBase, it analyzes the yield of essential micronutrients (calcium, iron, omega-3, etc.) across different gear types and habitats to guide public health and nutrition-oriented interventions.
* **Dissemination Components**: Outputs are distributed via interactive, multilingual web portals, automated dynamic reports, an open-data export pipeline to the Harvard Dataverse, and the **Peskas Tracks** app, which allows fishers to log and view their own trip and catch data.

Key concepts associated with this initiative include **small-scale fisheries (SSF)**, **near-real-time monitoring**, **Fishery Nutrient Profiles (FNPs)**, **co-management**, and the **ecosystem approach to fisheries (EAF)**.

## Related files
- peskas_timeline_about.md — child of this hub; the full 2013–present history, co-development, and global-scaling chronology of Peskas. This overview delegates the year-by-year timeline to it.
- ../data_harmonization/Technical_Guidelines_SSF_Data_Harmonization_WIO.docx — Peskas country data follows the WIO SSF harmonization conventions these guidelines define (FAO ASFIS species codes, GAUL administrative layers); Peskas is a working implementation of that proposed standard.
- ../data_harmonization/WIOMSA_harmonization_OCT2025.pdf — conference deck making the East-Africa SSF harmonization case that Peskas operationalizes in practice.
- ../ssf_research/digital_feedback_fisher_behavior_kenya_2025.pdf — studies digital feedback to small-scale fishers in Kenya, the same fisher-facing information loop the Peskas Tracks app provides; shares WorldFish authorship.
- ../ssf_research/fish_consumption_rct_timor_leste_2026.pdf — Timor-Leste nutrition-sensitive intervention (nearshore FADs + social behaviour change); shares Peskas's nutrition-and-SSF agenda and Timor-Leste setting.
- peskas_automated_analytics_softwarex_2025.pdf — the peer-reviewed SoftwareX paper describing the Peskas pipeline (ingestion → analysis → decision dashboard) this hub overviews.
- peskas_monitoring_system_slides.pdf — slide-deck overview of the Peskas digital monitoring system.
- fishery_nutrient_profiles_timor_leste_naturefood_2026.pdf — Nature Food paper deriving Fishery Nutrient Profiles from six years of Timor-Leste catch data collected through Peskas.
- kenya_validated_trips.csv — validated Kenya landing/trip records produced by Peskas (East Africa scaling).
- zanzibar_validated_trips.csv — validated Zanzibar landing/trip records produced by Peskas (East Africa scaling).
- mozambique_validated_trips.csv — validated Mozambique landing/trip records produced by Peskas (East Africa scaling).
