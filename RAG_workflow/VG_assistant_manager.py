import os
import time

import openai
from openai import OpenAI

from config import MODEL_NAME, OPENAI_KEY

# Initialize OpenAI API
openai.api_key = OPENAI_KEY
openai_client = OpenAI(organization='org-QYLV5ByGzWg3rl4MalRgn5nj')

def create_openai_assistant(model_name=MODEL_NAME):
    """
    Create an OpenAI assistant for the Video game data
    """
    print(f"Creating OpenAI assistant with model {model_name}...")
    openai_client = OpenAI(api_key= OPENAI_KEY)

    # Create a new Assistant with Filer Search enabled
    assistant = openai_client.beta.assistants.create(
        instructions=(
            "You are an gaming design data analyst who is responsible for going through a corpus of research papers on video games solving relevant problems. "
            "Your role is to scan row by row of the input data to find information form the huge corpus of data and return it in the template formats given to you."
        ),
        model=model_name,
        tools=[{"type": "file_search"}],
    )
    print(f"Assistant created with ID: {assistant.id}")

    vector_store = openai_client.beta.vector_stores.create(name="Video Game research vector store")
    print(f"Vector store created with ID: {vector_store.id}")

    file_paths = [
        "./supporting_documents/Detailed_Instructions.docx",
        "./supporting_documents/Video_Game_Attributes.docx",
    ]
    file_streams = [open(path, "rb") for path in file_paths]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    print("Batch processing of files started. This may take a few minutes...")
    file_batch = openai_client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    while file_batch.status != "completed":
        time.sleep(10)
        file_batch = openai_client.beta.vector_stores.file_batches.get(
            file_batch_id=file_batch.id
        )
    print("Batch processing completed.")
    print(f"Status: {file_batch.status}")
    print(f"File counts: {file_batch.file_counts}")

    # Update the assistant to use the new Vector Store
    assistant = openai_client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    print(f"Assistant {assistant.id} updated with Vector Store {vector_store.id}.")

    return assistant


def wait_on_run(openai_client, run, thread_id):
    """
    Waits for a run to complete by continuously checking its status.
    """
    start_time = time.time()
    while run.status == "queued" or run.status == "in_progress":
        current_time = time.time()
        elapsed_time = current_time - start_time

        print(
            f"Waiting for run to complete. "
            f"Current status: {run.status}; time elapsed: {elapsed_time:.2f} seconds."
        )
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(5)
    return run


def verify_and_correct_output(
    openai_client,
    thread_id,
    assistant_id,
    content,
    instructions,
    output_message,
    temperature=0,
):
    """
    Verify the output message from the OpenAI assistant and correct it if necessary.
    """
    corrected_run = openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=(
            f"Given the following content:\n{content}\n\n"
            f"The instructions:\n{instructions}\n\n"
            f"The response provided by the LLM:\n{output_message}\n\n"
            "Review each line of the output and compare it against the input text and the Video Game Attributes. "
            "Identify any instances where:\n"
            "a. The output does not follow the given instructions\n"
            "b. The output contains information or metrics inconsistent with the input\n"
            "c. The output references the Video Game Attributes inconsistently with the input\n\n"
            "Based on the identified problems, write an improved version of the output that corrects any errors. "
            "Keep all correct information and make minimal changes to the format, style, and detail of the output."
        ),
        temperature=temperature,
    )

    wait_on_run(openai_client, corrected_run, thread_id)

    corrected_messages = openai_client.beta.threads.messages.list(thread_id=thread_id)
    return corrected_messages.data[0].content[0].text.value


def get_response_from_assistant(
    assistant_id, content, instructions, temperature=0, verify_and_correct=True
):
    """
    Get response from the OpenAI assistant with the given ID.
    """
    openai_client = OpenAI()
    thread = openai_client.beta.threads.create()

    openai_client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content
    )
    run = openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id,
        instructions=instructions,
        temperature=temperature,
    )

    wait_on_run(openai_client, run, thread.id)
    # to avoid erratic assistant behavior where response takes longer to populate and returns the prompt as response
    time.sleep(25)
    messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
    message_content = messages.data[0].content[0].text

    output_message = message_content.value
    if verify_and_correct:
        corrected_message = verify_and_correct_output(
            openai_client,
            thread.id,
            assistant_id,
            content,
            instructions,
            output_message,
        )

    openai_client.beta.threads.delete(thread_id=thread.id)

    if verify_and_correct:
        return corrected_message
    else:
        return output_message


def get_list_of_assistants():
    """
    Get a list of all OpenAI assistants.
    """
    openai_client = OpenAI(api_key= OPENAI_KEY)
    assistants = openai_client.beta.assistants.list()
    return assistants.data


def list_uploaded_documents():
    """
    List all documents uploaded to OpenAI.
    """
    # Fetch all files uploaded to OpenAI
    openai_client = OpenAI(api_key= OPENAI_KEY)
    files = openai_client.files.list()

    # Check if there are any files
    if files.data:
        for file in files.data:
            print(f"ID: {file.id}, Filename: {file.filename}, Purpose: {file.purpose}")
    else:
        print("No documents have been uploaded.")
