# Automatic Startup Index Refresh: Verification

## Implementation
At startup, the agent fingerprints extracted text, source metadata,
embedding model name, chunk settings, and splitter/PDF-reader versions.
Each fingerprint selects a separate index folder under db/.
A completion marker is written after indexing succeeds.

## Observed checks

| Check | Index prefix | Outcome |
| --- | --- | --- |
| Initial build | 8a06fad96141 | Five document/page units and five chunks |
| Unchanged restart | 8a06fad96141 | Reused index; Atlas answer retained its page citation |
| Add Willow | 05797b74eb0a | Six units and six chunks; answered WILLOW-BLUE-42 |
| Edit Willow | 88df46c97812 | Six units and six chunks; answered WILLOW-GREEN-73 |
| Remove Willow | 8a06fad96141 | Reused original index; no Willow source; acknowledged missing information |

The temporary Willow document was removed after verification.

## Scope and limitations
- These are manually reviewed smoke checks.
- Refresh occurs at startup, not while the agent is running.
- A new corpus version rebuilds the complete index.
- Historical indexes remain on disk; removal is not secure erasure.
- Replacing an embedding model under the same model name is not detected.
- Interrupted-build recovery, concurrent startup, index corruption, and
  indexing-setting changes have not been verified.
- No general retrieval or latency improvement is claimed.
