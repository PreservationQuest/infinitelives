JUDGE_PERSONA = (
    "You are an expert evaluator of empirical game studies, game mechanics, "
    "player-outcome measurement, intervention evidence, and literature-derived evidence graphs."
)


def judge_prompt(dimension: str, gold: str, prediction: str) -> str:
    return (
        f"{JUDGE_PERSONA}\nEvaluate only this dimension: {dimension}.\n"
        "Do not evaluate other dimensions. Return strict JSON with score, rationale, and evidence.\n"
        f"Gold:\n{gold}\nPrediction:\n{prediction}"
    )
