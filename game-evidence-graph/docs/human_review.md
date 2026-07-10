# Human Review

Human review is required for uncertain game matches, mechanic assignments, outcome mappings, missing controls, missing effect evidence, low extraction confidence, inferred mechanic links, event/mechanic confusion, and unsupported edges.

Commands:

```bash
game-evidence review export --output data/review/review_queue.csv
game-evidence review apply --input data/review/review_decisions.csv
game-evidence review ui
```
