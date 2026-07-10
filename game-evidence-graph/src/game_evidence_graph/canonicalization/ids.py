from __future__ import annotations


def sequential_id(prefix: str, index: int, width: int = 3) -> str:
    return f"{prefix}{index:0{width}d}"


def next_game_id(existing: list[str]) -> str:
    nums = [int(x[1:]) for x in existing if x.startswith("g") and x[1:].isdigit()]
    return f"g{(max(nums) + 1 if nums else 1):02d}"


def next_mechanic_id(existing: list[str]) -> str:
    nums = [int(x[1:]) for x in existing if x.startswith("m") and x[1:].isdigit()]
    return f"m{(max(nums) + 1 if nums else 1):03d}"
