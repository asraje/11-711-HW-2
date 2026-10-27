# Model policy and implementation references

The implementation uses local open-weight models. The reviewed allow-list contains
Qwen2.5-Instruct 0.5B, 1.5B, 3B, 7B and 14B. Qwen2.5 was released in 2024,
before the assignment's January 1, 2026 cutoff. The default 1.5B variant has
1.54 billion total parameters.

- [Official default model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)
- [Official Qwen2.5 release announcement](https://qwenlm.github.io/blog/qwen2.5/)
- [Official Transformers chat templates](https://huggingface.co/docs/transformers/chat_templating)
- [Official Transformers generation API](https://huggingface.co/docs/transformers/main_classes/text_generation)
- [SQuAD evaluation implementation](https://github.com/rajpurkar/SQuAD-explorer/blob/master/evaluate-v1.1.py)
- [Python robots parser](https://docs.python.org/3/library/urllib.robotparser.html)
- [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)

Review the exact model card, release date, total parameter count, and license
before extending `MODELS` in `cmu_rag/reader.py`. A model name rounded to “32B”
does not establish compliance with a strict 32 billion parameter cap.
`trust_remote_code=False` is used. No training or synthetic data creation occurs.
Pin `--revision` to a Hugging Face commit for reproducible experiments; run
metadata records the resolved revision and device.

The optional local judge uses an explicit rubric stored in the code and output.
It is a diagnostic proxy, not a reproduction of the staff's undisclosed judge.
Small judge models can be unreliable; inspect their scores and keep overlap
metrics and judge scores separate.

The handout allows AI-assisted code and prohibits AI-written report text.
These files document the implementation; they are not a draft of the report.
