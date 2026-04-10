# TDA-Meta: Topological Evidence Gaps

A Topological Data Analysis (TDA) engine for identifying structural voids in global medical research.

This project maps clinical populations into a high-dimensional space and uses **Persistent Homology** to find "holes" — populations or diseases that have zero transportable evidence from existing trials.

## Features
- **Persistent Homology:** Uses 0-D Vietoris-Rips complexes to track the birth and death of evidence clusters.
- **Topological Isolation Scores:** Ranks evidence gaps from 0 to 100.
- **Interactive Voids Dashboard:** Visualizes the most critically isolated populations.

## Project Structure
- `core/math.py`: TDA and distance matrix functions.
- `core/pipeline.py`: Evidence scanning pipeline.
- `index.html`: Interactive TDA dashboard.

## Target Journals
- *Nature Methods*
- *Biostatistics*
