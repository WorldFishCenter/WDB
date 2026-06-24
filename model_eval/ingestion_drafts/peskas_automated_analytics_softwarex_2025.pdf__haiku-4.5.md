# Peskas

## Summary

Peskas is an automated analytics platform designed to address data collection and interpretation challenges in small-scale fisheries, particularly in data-deficient contexts. Developed by WorldFish and published in SoftwareX (2025), Peskas provides a low-cost, adaptable workflow for ingesting fisheries data and producing near-real-time decision support through a dashboard interface. The system targets the 90% of global fisheries employment represented by small-scale operations, which land over 40% of the world's fish catch but face logistical, financial, and capacity barriers to data gathering—especially in Least Developed Countries.

## Key concepts

**Peskas** implements a modular pipeline architecture comprising two primary components: peskas.timor.portal (v1.0.0), the decision dashboard interface, and peskas.timor.data.pipeline (v3.1.0), the automated ingestion and analysis engine. Together they form a template workflow that accepts diverse, dispersed, and informal fisheries data and produces actionable intelligence.

The platform addresses near-real-time monitoring of small-scale fisheries catch, enabling stock assessment and IUU (illegal, unreported, unregulated) fishing detection—capabilities previously unavailable at the operational scale required for informal sectors.

**Peskas** is designed for contextual adaptation, allowing deployment in different settings and regulatory environments while maintaining a consistent analytical backbone. This modularity acknowledges the heterogeneity of small-scale fisheries globally.

The software is released under the Apache License 2.0 and version-controlled via GitHub (WorldFish Center repositories); both major components have permanent DOI citations via Zenodo, enabling reproducibility and long-term reference.

## Related files

- peskas.timor.portal (dashboard/visualization interface) — distributed component of Peskas
- peskas.timor.data.pipeline (ETL and analytics engine) — distributed component of Peskas
- [Other Peskas deployment or validation datasets or field studies, if present in the repository]