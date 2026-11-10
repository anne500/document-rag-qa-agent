# Initial RAG Verification

## Environment
- Python: 3.12.10
- Ollama: 0.40.5
- Chat model: qwen3.5:4b
- Embedding model: nomic-embed-text
- Embedding dimensions: 768
- Corpus: three fictional project documents, three chunks

## Verified behavior
- Dependency imports and pip check passed.
- Local embedding call passed.
- Saved Chroma index reopened successfully.
- At k=1, three direct questions retrieved the correct project document.
- Birch approval and Cedar cloud-provider questions acknowledged missing information.

## Retrieval comparison
Question: Did MAPLE-207 fail because the runner ran out of disk space?

| Retrieval k | Sources in rank order | Answer outcome | Seconds |
| --- | --- | --- | --- |
| 1 | Birch | Abstained; Maple evidence missing | 7.62 |
| 2 | Birch, Maple | Correctly identified expired signing certificate; cited [2] | 11.93 |

## Interpretation
Retrieving a second chunk supplied the evidence needed for this question.
The k=1 answer avoided fabrication but did not resolve the question.
These are manually reviewed smoke checks, not a comprehensive benchmark.
Timings are individual observations, not controlled performance measurements.

## Remaining checks
- PDF ingestion and page citations.
- Retrieval across a larger corpus.
- Questions requiring multiple sources.
- Instructions embedded in retrieved documents.
