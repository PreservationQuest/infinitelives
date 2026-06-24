# llm_normalization.py

import json
from openai import OpenAI
from access_constants import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o-mini"
CHUNK_SIZE = 50


def get_unique_values(data_dict, column):
    unique = set()
    for entry in data_dict:
        value = entry.get(column)
        if isinstance(value, list):
            for v in value:
                if v and isinstance(v, str):
                    unique.add(v.strip())
        elif isinstance(value, str) and value:
            unique.add(value.strip())
    return list(unique)


def chunk_values(values, chunk_size=CHUNK_SIZE):
    for i in range(0, len(values), chunk_size):
        yield values[i:i + chunk_size]


def cluster_chunk(values, column_name):
    values_str = "\n".join(f"- {v}" for v in values)
    prompt = f"""You are a video game design expert. Below is a list of phrases describing "{column_name}" from various video games.

Your task:
1. Group semantically equivalent phrases together, even if worded very differently
2. Assign each group a short, canonical name (2-4 words max, title case)
3. Return a JSON object mapping each original phrase exactly to its canonical name

Rules:
- Every phrase must appear as a key in the output
- Canonical names should be concise and domain-appropriate (e.g. "Teamwork", "Resource Management", "Map Control")
- Do not include any explanation, only return valid JSON

Phrases:
{values_str}

Return format:
{{"original phrase": "Canonical Name", ...}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def merge_canonical_names(chunk_mappings):
    # Collect all unique canonical names across chunks
    all_canonicals = set()
    for mapping in chunk_mappings:
        all_canonicals.update(mapping.values())

    canonicals_str = "\n".join(f"- {c}" for c in all_canonicals)
    prompt = f"""You are a video game design expert. Below is a list of canonical game design terms that were independently generated from different batches of data.

Some may be duplicates or near-duplicates referring to the same concept (e.g. "Teamwork" and "Team Coordination").

Your task:
1. Merge any duplicates or near-duplicates into a single preferred canonical name
2. Return a JSON object mapping each original canonical name to the preferred one
3. If a name is already unique and correct, map it to itself

Rules:
- Every canonical name in the input must appear as a key
- Do not include any explanation, only return valid JSON

Canonical names:
{canonicals_str}

Return format:
{{"original canonical": "preferred canonical", ...}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def build_mapping(data_dict, column):
    print(f"Building mapping for column: {column}")
    unique_values = get_unique_values(data_dict, column)
    print(f"  {len(unique_values)} unique values found")

    # First pass: cluster each chunk independently
    chunk_mappings = []
    for i, chunk in enumerate(chunk_values(unique_values)):
        print(f"  Clustering chunk {i + 1}...")
        mapping = cluster_chunk(chunk, column)
        chunk_mappings.append(mapping)

    # Second pass: merge canonical names across chunks
    print(f"  Merging canonical names across chunks...")
    canonical_merge_map = merge_canonical_names(chunk_mappings)

    # Combine: original -> merged canonical
    final_mapping = {}
    for chunk_mapping in chunk_mappings:
        for original, canonical in chunk_mapping.items():
            final_mapping[original] = canonical_merge_map.get(canonical, canonical)

    return final_mapping


def apply_mapping(data_dict, mapping, column):
    for entry in data_dict:
        value = entry.get(column)
        if isinstance(value, list):
            entry[column] = [mapping.get(v, v) for v in value]
        elif isinstance(value, str):
            entry[column] = mapping.get(value, value)
    return data_dict