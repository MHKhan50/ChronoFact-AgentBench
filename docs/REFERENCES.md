# References and provenance

1. Khodja, H. A., Béchet, F., Brabant, Q., Nasr, A., & Lecorvé, G. (2025). **Factual Knowledge in Language Models: Robustness and Anomalies under Simple Temporal Context Variations.** Proceedings of the First Workshop on Large Language Model Memorization (L2M2), 1–22. DOI: [10.18653/v1/2025.l2m2-1.1](https://doi.org/10.18653/v1/2025.l2m2-1.1). This is the primary paper introducing TimeStress.

2. Zhang, T., Wang, J., Li, Z., Qu, J., Liu, A., Chen, Z., & Zhi, H. (2024). **MusTQ: A Temporal Knowledge Graph Question Answering Dataset for Multi-Step Temporal Reasoning.** Findings of ACL 2024, 11688–11699. DOI: [10.18653/v1/2024.findings-acl.696](https://doi.org/10.18653/v1/2024.findings-acl.696).

3. Soulard, T., Raad, J., & Saïs, F. (2025). **WhenFactsExpire** [Dataset]. Zenodo. DOI: [10.5281/zenodo.15675768](https://doi.org/10.5281/zenodo.15675768). The Zenodo record describes a Wikidata-derived temporal fact-validation dataset; its processed archive is much larger than TimeStress, so it is not the primary dataset for this lightweight release.

4. Orange Research. **TimeStress dataset** [Dataset]. Hugging Face. [Dataset card and files](https://huggingface.co/datasets/Orange/TimeStress). License: CC BY-SA 4.0. Pinned Parquet file revision: `f90d17c`; expected SHA-256: `93df1d4782f770b38d1eda00acb5aa9d97c9a863fd6921fecb6f310052ffa59a`.

5. Orange-OpenSource. **TimeStress source repository.** [GitHub](https://github.com/Orange-OpenSource/TimeStress). The repository documents data generation and the original LLM evaluation pipeline.

6. Wikidata contributors. **Wikidata: a free and open knowledge base.** [Wikidata](https://www.wikidata.org/). TimeStress reports Wikidata as its source of temporal facts.


7. Jiang, P., Liu, Y., Wen, Y., Gan, Y., Liu, L., Zhang, R., Yang, J., Xue, Y., Deng, Y., Guo, X., & Liu, Q. (2026). **DyHist: Query-Aware Historical Dynamics Modeling for Temporal Knowledge Graph Extrapolation.** Findings of the Association for Computational Linguistics: EMNLP 2026. [ACL Anthology](https://aclanthology.org/2026.findings-emnlp.361/).

8. **Temporal Modelling in Cultural Heritage Knowledge Graphs: Use Cases, Requirements, Evaluation, and Decision Support.** Transactions on Graph Data and Knowledge (TGDK), 4(1), 2 (2026). DOI: [10.4230/TGDK.4.1.2](https://doi.org/10.4230/TGDK.4.1.2).

## Literature positioning

TimeStress already evaluates temporal-context robustness across language models and date granularities. MusTQ studies multi-step temporal knowledge-graph QA. WhenFactsExpire studies temporal fact validity with corrupted temporal contexts. ChronoFact-AgentBench therefore positions itself as a small, reproducible **tool-augmented agent evaluation harness** over an existing dataset, not as a replacement for those datasets or a claim that temporal fact validation is a new problem.
