This repository contains a reproducibility study and analytical extension of the dataset  
**“Contact Observations from an Intensive Care Unit”** (*Nature Scientific Data*, 2025).

The project analyzes Ultra-Wideband (UWB) sensor data to model spatio-temporal interaction patterns among healthcare professionals in a Medical Intensive Care Unit (MICU), with the goal of identifying potential transmission pathways for Healthcare-Associated Infections (HAIs).

🔗 **https://www.nature.com/articles/s41597-025-05249-5:** 

---

## Project Overview

This work reproduces the original data processing pipeline and extends the analysis by incorporating higher-order interaction modeling. Raw proximity signals are transformed into fine-grained, time-resolved contact histories, enabling both individual-level and group-level exposure analysis.

Unlike traditional pairwise contact networks, this project adopts a **dynamic hypergraph framework** to represent multi-person clinical interactions such as medical rounds, team-based procedures, and shared equipment usage.

---

## Methodological Contributions

- **Automated Data Processing Pipeline**  
  Reproduction of the original preprocessing workflow to generate **1-second–resolution imputed contact histories** across **14 full MICU shifts**.

- **Hypergraph-Based Interaction Modeling (Extension)**  
  Modeling of **group interactions (≥ 3 entities)** to capture higher-order clinical dynamics beyond binary contacts.

- **Exposure Risk Quantification**  
  Identification of **high-risk healthcare providers (HCPs)** and spatial interaction hotspots within the MICU.

---

## Analytical Perspective: Beyond Binary Contacts

Traditional contact network analysis represents interactions as pairwise edges between individuals. While effective for simple proximity tracking, this approach underrepresents the complexity of ICU workflows.

- **Pairwise Graph Models**  
  Fragment simultaneous multi-person events into independent dyadic interactions.

- **Dynamic Hypergraph Models**  
  Represent **n-ary interactions** among multiple staff members and medical assets within the same temporal window, providing a higher-resolution and workflow-aware risk representation.

---

## Key Findings

- **High-Risk Actors**  
  A small subset of individuals (e.g., *pr045* and *pr037*) consistently act as transmission bridges, each participating in **over 50,000 group interaction events**.

- **Spatial Interaction Bottlenecks**  
  The **Main Corridor (b004)** and **Main Nurse Station (b143)** are identified as the most critical interaction hubs.

- **Temporal Stability of Risk Patterns**  
  Exposure risk rankings and spatial hotspots remain consistent across **10–11 of the 14 analyzed shifts**, indicating that risk is largely structural rather than stochastic.

---

## Citation
Vu, Hieu; Herman, Ted; Struble, Roger; Adhikari, Bijaya; Polgreen, Philip M. (2025).  
**Contact Observations from an Intensive Care Unit - Supplementary**. figshare. Dataset.  
[https://doi.org/10.6084/m9.figshare.28826414.v3](https://doi.org/10.6084/m9.figshare.28826414.v3)
