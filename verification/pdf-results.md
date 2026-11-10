# PDF Ingestion and Page Citation Verification

## Observed setup
- Corpus: three Markdown documents and one two-page PDF.
- Loader reported five text documents/PDF pages.
- Indexer reported five chunks.
- RETRIEVAL_K: 2.
- Atlas is a fictional test fixture.

## Manually reviewed results

| Question | Supporting page | Observed answer | Seconds |
| --- | --- | --- | --- |
| Who approves ATLAS-R12? | Atlas PDF page 1 | Quality lead and operations lead; cited [1] | 57.28 |
| Why did ATLAS-418 fail, and what should happen next? | Atlas PDF page 2 | Expired registry token; rotate token and verify runner authentication; cited [1] | 10.37 |
| When is Atlas scheduled for production deployment? | Atlas PDF page 2 | Acknowledged that the date is unspecified; cited [1] | 9.79 |

## Findings
- Text from both PDF pages was available to the agent.
- Retrieved source labels preserved the correct page numbers.
- Answer citations mapped to supporting PDF pages in these examples.
- The build-failure answer used Atlas evidence despite also retrieving Birch.

## Limits
These are three manually reviewed smoke checks.
They do not establish general PDF accuracy or citation reliability.
The timing observations are not a controlled benchmark.
Scanned PDFs, complex layouts, tables, and OCR remain unverified.
Visual inspection of the generated PDF is not recorded here.
