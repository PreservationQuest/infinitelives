# Query Examples

```bash
game-evidence query \
  --target-outcome empathy \
  --current-mechanics exploration,puzzle_solving \
  --population adolescents \
  --context classroom
```

Query responses use `support_score`, not estimated causal effects. If no evidence exists, the query engine returns:

```text
No sufficiently supported recommendation found.
```
