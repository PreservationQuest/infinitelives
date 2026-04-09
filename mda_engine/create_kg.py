import pandas as pd
import json
import numpy as np

from access_constants import DB_PASSWORD
from constants import SPLIT_COLUMNS, KG_INDEX_LIST
from kg_functions import KGFunctions 

kg_functions = KGFunctions()

def read_data():
    df = pd.read_csv('data/games_dataset.csv')
    return df

def process_row(row):
    return {
        col.lower().replace(" ", "_").replace("-", "_"): [v.strip() for v in row[col].split(";")] if col in SPLIT_COLUMNS else row[col]
        for col in row.index
    }

def split_data(df, output_file = None):
    data_dict = data_dict = df.apply(process_row, axis=1).tolist()
    if output_file is not None:
        with open(output_file, 'w') as outfile:
            json.dump(data_dict, outfile, indent = 4)
    
    return data_dict

def normalize_data(data_dict, fields_to_normalize, output_file = None):
    # Call LLM to normalize the values in the specified fields.
    # Need to create a list of all possible values for those fields, and then cluster them. 
    # Will have to write a separate function to call the LLM/cluster data
    if  output_file is not None:
        with open(output_file, 'w') as outfile:
            json.dump(data_dict, outfile, indent = 4)
    
    return data_dict # Should ideally return the normalized data dict; placeholder

def write_record_to_kg(entry):
    # Create indexes for all relevant fields (if not already created).
    for key, value in entry.items():
        if key == "game_title":
            kg_functions.execute_command("add_node", index = 'game_title', value = value)
        elif key == "gameplay_summary":
            kg_functions.execute_command("add_property", node_index = "game_title", node_name = entry["game_title"], property_key = key, property_value = value)
        else:
            label = key.replace("_", " ").title().replace(" ", "")
            relationship = f"HAS_{key.upper()}"
            if isinstance(value, list):
                for v in value:
                    kg_functions.execute_command("add_node_and_relationship", node_index = "game_title", node_name = entry["game_title"], label_index = label, relationship = relationship, label_value = v)
            else:
                if value is not np.nan:
                    kg_functions.execute_command("add_node_and_relationship", node_index = "game_title", node_name = entry["game_title"], label_index = label, relationship = relationship, label_value = value)

def create_knowledge_graph(normalized_data):
    # Create neo4j graph from data_dict.
    for index in KG_INDEX_LIST:
        kg_functions.execute_command("create_index", index)
    for record in normalized_data:
        write_record_to_kg(record)

def create_embeddings(kg):
    # Experiment with different embeddings techniques.
    pass

def write_embeddings_to_kg(kg, embeddings):
    pass

if __name__ == "__main__":
    df = read_data()
    processed_data = split_data(df, output_file = 'data/split_data.json')
    normalized_data = normalize_data(processed_data, fields_to_normalize=[], output_file = 'data/normalized_data.json')
    kg = create_knowledge_graph(normalized_data)
    # embeddings = create_embeddings(kg)
    # kg = write_embeddings_to_kg(kg, embeddings)

