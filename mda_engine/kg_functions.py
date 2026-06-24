from neo4j import GraphDatabase
from access_constants import DB_PASSWORD, DB_NAME


driver = GraphDatabase.driver("neo4j://127.0.0.1:7687", auth=("neo4j", DB_PASSWORD))


class KGFunctions:
    def __init__(self):
        self.driver = driver

    def create_index(self, tx, index):
        tx.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{index}) ON (n.name)")

    def add_node(self, tx, index, value):
        tx.run(f"MERGE (n:{index} {{name: $value}})", value=value)

    def add_property(self, tx, node_index, node_name, property_key, property_value):
        tx.run(f"""
            MERGE (n:{node_index} {{name: $name}})
            SET n.{property_key} = $value
        """, name=node_name, value=property_value)

    def add_node_and_relationship(self, tx, node_index, node_name, label_index, relationship, label_value, original_value=None):
        tx.run(f"""
            MERGE (n:{label_index} {{name: $value}})
            SET n.originals = CASE
                WHEN $original IS NOT NULL AND NOT $original IN coalesce(n.originals, [])
                THEN coalesce(n.originals, []) + $original
                ELSE coalesce(n.originals, [])
            END
            MERGE (g:{node_index} {{name: $name}})-[:{relationship}]->(n)
        """, name=node_name, value=label_value, original=original_value)

    def execute_command(self, function_name, *args, **kwargs):
        function = getattr(self, function_name)
        with self.driver.session(database=DB_NAME) as session:
            session.execute_write(lambda tx: function(tx, *args, **kwargs))