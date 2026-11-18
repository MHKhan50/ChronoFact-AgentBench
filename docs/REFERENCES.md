# References and provenance

## Dataset

- Orange Research. **TimeStress** [dataset]. Hugging Face, <https://huggingface.co/datasets/Orange/TimeStress>.
  CC BY-SA 4.0. Pinned file `train.parquet`, revision `f90d17c`, SHA-256
  `93df1d4782f770b38d1eda00acb5aa9d97c9a863fd6921fecb6f310052ffa59a`.
- Ammar Khodja, H., Béchet, F., Brabant, Q., Nasr, A., & Lecorvé, G. (2025). Factual Knowledge in Language Models:
  Robustness and Anomalies under Simple Temporal Context Variations. *Proceedings of the First Workshop on Large
  Language Model Memorization (L2M2)*, 1–22. <https://doi.org/10.18653/v1/2025.l2m2-1.1>. The paper that introduces
  TimeStress.
- Wikidata, the source of the facts and validity periods in TimeStress: <https://www.wikidata.org/>.

## Related work cited in the paper

- Chen, W., Wang, X., & Wang, W. Y. (2021). A Dataset for Answering Time-Sensitive Questions. *NeurIPS Datasets and
  Benchmarks Track*. <https://arxiv.org/abs/2108.06314>
- Tan, Q., Ng, H. T., & Bing, L. (2023). Towards Benchmarking and Improving the Temporal Reasoning Capability of Large
  Language Models. *ACL 2023*, 14820–14835. <https://doi.org/10.18653/v1/2023.acl-long.828>
- Fatemi, B., et al. (2025). Test of Time: A Benchmark for Evaluating LLMs on Temporal Reasoning. *ICLR 2025*.
  <https://arxiv.org/abs/2406.09170>
- Schick, T., et al. (2023). Toolformer: Language Models Can Teach Themselves to Use Tools. *NeurIPS 2023*.
- Gao, L., et al. (2023). PAL: Program-aided Language Models. *ICML 2023*, PMLR 202, 10764–10799.
- Yao, S., et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*.
- Qwen Team (2025). Qwen2.5 Technical Report. arXiv:2412.15115.
- Grattafiori, A., et al. (2024). The Llama 3 Herd of Models. arXiv:2407.21783.

## Positioning

TimeStress measures whether models recall a fact consistently across temporal contexts when answering from memory.
This repository keeps its labels and asks a different question: what a small local model needs from its tools to
label a time-qualified claim, by changing only what the tool returns.
