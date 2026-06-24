import pandas as pd
import json
import numpy as np
from access_constants import DB_PASSWORD
from constants import SPLIT_COLUMNS, KG_INDEX_LIST
from kg_functions import KGFunctions
from llm_normalization import build_mapping, apply_mapping
from kg_embeddings import generate_and_store_embeddings, create_all_vector_indexes

kg_functions = KGFunctions()

PROPERTY_COLUMNS = {"gameplay_summary"}
GAME_LABEL = "Game"

# Columns that go through normalization and have originals tracked
CANONICAL_COLUMNS = {
    "key_mechanics",
    "key_dynamics",
    "key_aesthetics",
    "misc_game_characteristics",
    "major_game_design_elements"
}


def read_data():
    df = pd.read_csv('data/games_dataset.csv')
    return df


def process_row(row):
    return {
        col.lower().replace(" ", "_").replace("-", "_"): [v.strip() for v in row[col].split(";")] if col in SPLIT_COLUMNS else row[col]
        for col in row.index
    }


def split_data(df, output_file=None):
    data_dict = df.apply(process_row, axis=1).tolist()
    if output_file is not None:
        with open(output_file, 'w') as outfile:
            json.dump(data_dict, outfile, indent=4)
    return data_dict


def normalize_data(data_dict, columns_to_normalize, output_file=None):
    for column in columns_to_normalize:
        print(f"Normalizing column: {column}")
        mapping = build_mapping(data_dict, column)
        data_dict = apply_mapping(data_dict, mapping, column)
    if output_file is not None:
        with open(output_file, 'w') as outfile:
            json.dump(data_dict, outfile, indent=4)
    return data_dict


def write_record_to_kg(entry):
    for key, value in entry.items():
        if key == "game_title":
            kg_functions.execute_command("add_node", index=GAME_LABEL, value=value)

        elif key in PROPERTY_COLUMNS:
            kg_functions.execute_command(
                "add_property",
                node_index=GAME_LABEL,
                node_name=entry["game_title"],
                property_key=key,
                property_value=value
            )

        elif key in CANONICAL_COLUMNS:
            # Value is a list of {"canonical": ..., "original": ...} dicts
            if isinstance(value, list):
                label = key.replace("_", " ").title().replace(" ", "")
                relationship = f"HAS_{key.upper()}"
                for item in value:
                    if isinstance(item, dict):
                        canonical = item["canonical"]
                        original = item["original"]
                    else:
                        # Fallback in case mapping wasn't applied
                        canonical = item
                        original = item
                    kg_functions.execute_command(
                        "add_node_and_relationship",
                        node_index=GAME_LABEL,
                        node_name=entry["game_title"],
                        label_index=label,
                        relationship=relationship,
                        label_value=canonical,
                        original_value=original
                    )

        else:
            label = key.replace("_", " ").title().replace(" ", "")
            relationship = f"HAS_{key.upper()}"
            if isinstance(value, list):
                for v in value:
                    kg_functions.execute_command(
                        "add_node_and_relationship",
                        node_index=GAME_LABEL,
                        node_name=entry["game_title"],
                        label_index=label,
                        relationship=relationship,
                        label_value=v,
                        original_value=None
                    )
            else:
                if value is not np.nan:
                    kg_functions.execute_command(
                        "add_node_and_relationship",
                        node_index=GAME_LABEL,
                        node_name=entry["game_title"],
                        label_index=label,
                        relationship=relationship,
                        label_value=value,
                        original_value=None
                    )


def create_knowledge_graph(normalized_data):
    print("Creating indexes...")
    for index in KG_INDEX_LIST:
        kg_functions.execute_command("create_index", index=index)

    print("Writing records to KG...")
    for record in normalized_data:
        write_record_to_kg(record)
    print("KG creation complete.")


def create_embeddings():
    print("Creating embeddings...")
    generate_and_store_embeddings(kg_functions.driver)


def write_embeddings_to_kg():
    # Handled inside generate_and_store_embeddings
    pass


if __name__ == "__main__":
    df = read_data()
    processed_data = split_data(df, output_file='data/split_data.json')
    normalized_data = normalize_data(
        processed_data,
        columns_to_normalize=list(CANONICAL_COLUMNS),
        output_file='data/normalized_data.json'
    )
    create_knowledge_graph(normalized_data)
    create_embeddings()