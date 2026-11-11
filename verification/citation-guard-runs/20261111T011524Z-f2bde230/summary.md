# 🔗 Citation Guard Evaluation

Run status: **complete**.

Mode: **saved_draft_plus_live_repair**. Numeric validation does not establish factual support.

| Saved answer | Initial numeric check | Final guard status | Live calls |
| --- | --- | --- | --- |
| cedar_maple:k2::baseline | pass | accepted | 0 |
| cedar_maple:k2::revised | pass | accepted | 0 |
| cedar_maple:k2::refined | pass | accepted | 0 |
| cedar_maple:k4::revised | pass | accepted | 0 |
| cedar_maple:k4::refined | pass | accepted | 0 |
| cedar_maple:k4::baseline | pass | accepted | 0 |
| atlas_pages:k2::refined | pass | accepted | 0 |
| atlas_pages:k2::baseline | pass | accepted | 0 |
| atlas_pages:k2::revised | pass | accepted | 0 |
| atlas_pages:k4::baseline | pass | accepted | 0 |
| atlas_pages:k4::revised | pass | accepted | 0 |
| atlas_pages:k4::refined | pass | accepted | 0 |
| cedar_birch_missing:k2::revised | pass | accepted | 0 |
| cedar_birch_missing:k2::refined | pass | accepted | 0 |
| cedar_birch_missing:k2::baseline | pass | accepted | 0 |
| cedar_birch_missing:k4::refined | pass | accepted | 0 |
| cedar_birch_missing:k4::baseline | pass | accepted | 0 |
| cedar_birch_missing:k4::revised | pass | accepted | 0 |
| three_unit_approvals:k2::baseline | pass | accepted | 0 |
| three_unit_approvals:k2::revised | pass | accepted | 0 |
| three_unit_approvals:k2::refined | fail | abstained | 1 |
| three_unit_approvals:k4::revised | pass | accepted | 0 |
| three_unit_approvals:k4::refined | pass | accepted | 0 |
| three_unit_approvals:k4::baseline | pass | accepted | 0 |
| four_unit_failures:k2::refined | pass | accepted | 0 |
| four_unit_failures:k2::baseline | pass | accepted | 0 |
| four_unit_failures:k2::revised | pass | accepted | 0 |
| four_unit_failures:k4::baseline | pass | accepted | 0 |
| four_unit_failures:k4::revised | pass | accepted | 0 |
| four_unit_failures:k4::refined | pass | accepted | 0 |
| known_unknown:k2::revised | pass | accepted | 0 |
| known_unknown:k2::refined | pass | accepted | 0 |
| known_unknown:k2::baseline | pass | accepted | 0 |
| known_unknown:k4::refined | fail | accepted | 1 |
| known_unknown:k4::baseline | pass | accepted | 0 |
| known_unknown:k4::revised | pass | accepted | 0 |
| conflicting_approvals:control::baseline | pass | accepted | 0 |
| conflicting_approvals:control::revised | pass | accepted | 0 |
| conflicting_approvals:control::refined | pass | accepted | 0 |

First drafts are replayed from the frozen capture. In offline mode the same invalid draft is replayed on retry to test withholding, not model repair. In live-repair mode only rejected drafts receive a new model call. Review repaired claims separately. No general answer-accuracy or semantic-abstention score is computed.
