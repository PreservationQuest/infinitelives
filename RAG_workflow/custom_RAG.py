import json
import os

import boto3
import openai
import pandas as pd
from fuzzywuzzy import process  # Install this with `pip install fuzzywuzzy`

from VG_assistant_manager import get_response_from_assistant
from config import ASSISTANT_ID, OPENAI_KEY
from templates import FINAL_PROMPT_TEMPLATES, OUTPUT_TEMPLATES, CONTEXT_SETTING_PROMPT_TEMPLATES, EXTRACT_INFORMATION_INSTRUCTIONS


client = boto3.client('s3')
# Initialize OpenAI API
openai.api_key = os.environ[OPENAI_KEY]


def load_input_csv(filepath):
    df = pd.read_csv(filepath)
    return df

def sort_semicolon_strings(df, column_name):
    df[column_name] = df[column_name].apply(lambda x: ';'.join(sorted(x.split(';'))))
    return df


def prepare_input_file_data(filepath):
    df = load_input_csv(filepath)
    df = sort_semicolon_strings(df, column_name = "Subject of Effect")
    return df

def get_first_issue(input_string: str) -> str:
    """
    Returns the first word in a semicolon-separated string.
    
    Args:
        input_string (str): The input string to process.
        
    Returns:
        str: The first word before the first semicolon.
    """
    if not input_string:
        return ""
    
    # Split the string by semicolon and strip any extra whitespace
    first_issue = input_string.split(";")[0].strip()
    return first_issue

def get_template_detailed_prompt_query(
    category, content_text, column_name
):

    base_instruction_template = (
        f"Paper section: {column_name}\n"
        f"Category: {category}\n"
        f"Input text: {content_text}\n\n"
    )
    category_based_query = CONTEXT_SETTING_PROMPT_TEMPLATES[category]
    detailed_content_based_instruction = EXTRACT_INFORMATION_INSTRUCTIONS
    query = category_based_query + base_instruction_template + detailed_content_based_instruction

    return query

def get_parser_format():
    parser = OUTPUT_TEMPLATES
    return parser


def get_structured_output(query, verify_and_correct=False):
    parser = get_parser_format()
    content = query
    instructions = f"Answer the query in the format specified below: \nformat = {parser.get_format_instructions()}\n"
    response = get_response_from_assistant(ASSISTANT_ID, content, instructions, temperature=0, verify_and_correct=verify_and_correct)

    return response

def check_for_failed_responses(output_text, query, ID):
    check_string_for_query_text = "answer the query"
    if output_text.lower() == query.lower() or output_text == "" or output_text.lower().startswith(check_string_for_query_text):
        print(f"Failed response generation for {ID}. Check rate limit or credit amount in the account.")

        return ID
    else:
        run = "Pass"
        return run


def get_paperwise_sectionwise_summary(content_text, category, column_name, paper_ID, verify_and_correct=True):
    api_response_with_metadata = []
    if (str(content_text) != "[nan]") or (str(content_text) != ""):
        query = get_template_detailed_prompt_query(
                    category, content_text, column_name
                )

        api_response = get_structured_output(query, verify_and_correct=verify_and_correct)

        #check response for failure
        response_check = check_for_failed_responses(api_response, query, paper_ID)

        # Convert dictionary to JSON string
        # api_response_dumps = json.dumps(api_response)
        api_response_with_metadata.append([content_text, api_response, category, column_name])
    else:
        content_text = str(content_text)
        api_response = "Input text was empty. No summaries are generated."
        response_check = paper_ID
        api_response_with_metadata.append([content_text, api_response, category, column_name])

    return api_response_with_metadata, response_check

# Function to map attributes with concatenation
def map_and_concatenate_attributes_if_empty(row, ref_df, target_column="Game_attributes"):
    """
    Maps and concatenates attributes to the target DataFrame only if the target column is empty.

    Args:
        row (pd.Series): A row of the target DataFrame.
        ref_df (pd.DataFrame): The reference DataFrame with game attributes.
        target_column (str): The column in the target DataFrame to update.

    Returns:
        str: The updated value for the target column.
    """
    # If the target column is already filled, return the existing value
    if pd.notna(row.get(target_column)):
        return row[target_column]
    
    # Split the comma-separated game names and normalize
    game_list = [game.strip().lower() for game in row["Game_names"].split(",")]
    
    # Perform fuzzy matching for each game in the list
    matched_attributes = []
    for game in game_list:
        match, score = process.extractOne(game, ref_df["Game_name_normalized"])
        if score > 80:  # Adjust the threshold as needed
            matched_row = ref_df[ref_df["Game_name_normalized"] == match].iloc[0]
            
            # Concatenate the values of the three columns
            concatenated = f"{matched_row['Key_Mechanics']}, {matched_row['Key_Dynamics']}, {matched_row['Key_Aesthetics']}"
            matched_attributes.append(concatenated)
    
    # Join the concatenated attributes into a single string
    return "; ".join(matched_attributes) if matched_attributes else None

def json_to_dataframe(json_dict):
    """
    Converts a JSON dictionary into a DataFrame, where each key becomes a column.

    Args:
        json_dict (dict): The JSON dictionary to convert. Each key is a column name, and its value is a list or scalar.

    Returns:
        pd.DataFrame: A DataFrame with keys as columns and values as rows.
    """
    # Ensure the input is a dictionary
    if not isinstance(json_dict, dict):
        raise ValueError("Input must be a dictionary.")

    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(json_dict)
    
    return df

def get_reference_df(filepath):
    reference_df = load_input_csv(filepath)
    return reference_df

def apply_paperwise_sectionwise_summary_to_row(filepath):
    df = prepare_input_file_data(filepath)
    reference_df = get_reference_df("games_dataset.csv")
    df["first_issue"] = df["Subject of Effect"].apply(get_first_issue, axis=1)
    columns_to_process = ["Abstract", "Introduction", "Methods", "Conclusion"]
    for row in df.itertuples():
        for col_i in columns_to_process:
            content_text = row[col_i]
            category = row["first_issue"]
            column_name = col_i
            paper_ID = row["ID"]
            api_response_with_metadata, response_check = get_paperwise_sectionwise_summary(content_text, category, column_name, paper_ID, verify_and_correct=True)
            row["sectional_summary"] = api_response_with_metadata[0][1]
            response_df = json_to_dataframe(api_response_with_metadata[0][1])
            # Combine the DataFrames by columns
            df_combined = pd.concat([row, response_df], axis=1)
            # Apply the function only if the target column is empty
            row["Game_attributes"] = df_combined.apply(
                map_and_concatenate_attributes_if_empty, axis=1, ref_df=reference_df, target_column="Game_attributes"
                )












