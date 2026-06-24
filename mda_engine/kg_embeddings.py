import os
from openai import OpenAI
from access_constants import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "text-embedding-3-small"

# Labels that get canonical + originals embedding
CANONICAL_LABELS = {
    "KeyMechanics",
    "KeyDynamics",
    "KeyAesthetics",
    "MiscGameCharacteristics",
    "MajorGameDesignElements"
}

# Labels that get name-only embedding
NAME_ONLY_LABELS = {
    "Genre",
    "SubGenre",
    "Developer",
    "Publisher",
    "PegiRating"
}


def get_embedding(text):
    response = client.embeddings.create(
        model=MODEL,
        input=text
    )
    return response.data[0].embedding


def build_embedding_text_for_canonical(name, originals):
    originals_str = ", ".join(originals) if originals else ""
    if originals_str:
        return f"{name}: {originals_str}"
    return name


def fetch_canonical_nodes(tx, label):
    result = tx.run(f"MATCH (n:{label}) RETURN n.name AS name, n.originals AS originals")
    return [(record["name"], record["originals"] or []) for record in result]


def fetch_name_only_nodes(tx, label):
    result = tx.run(f"MATCH (n:{label}) RETURN n.name AS name")
    return [record["name"] for record in result]


def fetch_game_nodes(tx):
    result = tx.run("MATCH (n:Game) RETURN n.name AS name, n.gameplay_summary AS summary")
    return [(record["name"], record["summary"] or "") for record in result]


def write_embedding_to_node(tx, label, name, embedding):
    tx.run(f"""
        MATCH (n:{label} {{name: $name}})
        SET n.embedding = $embedding
    """, name=name, embedding=embedding)


def create_vector_index(tx, label, dimensions=1536):
    index_name = f"{label.lower()}_embedding_index"
    tx.run(f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (n:{label}) ON (n.embedding)
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {dimensions},
            `vector.similarity_function`: 'cosine'
        }}}}
    """)


def embed_canonical_label(driver, label):
    print(f"  Embedding {label} nodes...")
    with driver.session() as session:
        nodes = session.execute_read(fetch_canonical_nodes, label)
        for name, originals in nodes:
            text = build_embedding_text_for_canonical(name, originals)
            embedding = get_embedding(text)
            session.execute_write(write_embedding_to_node, label, name, embedding)
    print(f"  Done embedding {label} ({len(nodes)} nodes)")


def embed_name_only_label(driver, label):
    print(f"  Embedding {label} nodes...")
    with driver.session() as session:
        names = session.execute_read(fetch_name_only_nodes, label)
        for name in names:
            embedding = get_embedding(name)
            session.execute_write(write_embedding_to_node, label, name, embedding)
    print(f"  Done embedding {label} ({len(names)} nodes)")


def embed_game_nodes(driver):
    print("  Embedding Game nodes...")
    with driver.session() as session:
        games = session.execute_read(fetch_game_nodes)
        for name, summary in games:
            text = summary if summary else name
            embedding = get_embedding(text)
            session.execute_write(write_embedding_to_node, "Game", name, embedding)
    print(f"  Done embedding Game ({len(games)} nodes)")


def create_all_vector_indexes(driver):
    print("Creating vector indexes...")
    all_labels = CANONICAL_LABELS | NAME_ONLY_LABELS | {"Game"}
    with driver.session() as session:
        for label in all_labels:
            session.execute_write(create_vector_index, label)
    print("Vector indexes created.")


def generate_and_store_embeddings(driver):
    print("Generating embeddings...")
    embed_game_nodes(driver)
    for label in CANONICAL_LABELS:
        embed_canonical_label(driver, label)
    for label in NAME_ONLY_LABELS:
        embed_name_only_label(driver, label)
    create_all_vector_indexes(driver)
    print("All embeddings complete.")