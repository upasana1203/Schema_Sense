import sqlite3
import re
import pandas as pd
from .base_tts import View


class Database(View):

    # Statements that must never reach execute() when the SQL came from an LLM
    BLOCKED_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
        "TRUNCATE", "CREATE", "REPLACE", "ATTACH"
    ]

    def __init__(self):
        pass

    def is_query_safe(self, query: str) -> tuple[bool, str]:
        """
        Only allow read-only SELECT queries to run.
        Returns (is_safe, reason_if_blocked).
        """
        if not query or not query.strip():
            return False, "Empty query."

        cleaned = query.strip().rstrip(";")

        # Block multiple statements chained with ';' (basic injection guard)
        if ";" in cleaned:
            return False, "Multiple statements are not allowed."

        first_word = cleaned.split(None, 1)[0].upper()
        if first_word != "SELECT":
            return False, "Only SELECT queries are allowed."

        upper_query = cleaned.upper()
        for keyword in self.BLOCKED_KEYWORDS:
            # Word-boundary match so column/table names like "updated_at"
            # or "created_by" aren't wrongly flagged as containing UPDATE/CREATE.
            if re.search(rf"\b{keyword}\b", upper_query):
                return False, f"Query contains a blocked keyword: {keyword}"

        return True, ""

    def sql_handling(self, file_path):

        # Create an in-memory SQLite database
        conn = sqlite3.connect(':memory:')
        sql_script = file_path.read().decode("utf-8")

        if sql_script.strip():

            try:
                # Execute the SQL script
                conn.executescript(sql_script)
                self.success("SQL script executed successfully.")
            except sqlite3.Error as sql_error:
                self.error(f"Error executing SQL script: {sql_error}")

        else:
            self.warning(
                "The SQL file is empty. Please provide valid SQL statements.")

        return conn

    def db_handling(self, file_path):
        return sqlite3.connect(file_path)

    def fetch_table_details(self, conn):
        # Retrieve and display table names
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        return tables

    def return_first_5_row(self, table_name, conn):
        data = pd.read_sql_query(
            f"SELECT * FROM {table_name} LIMIT 5", conn)
        View().write(data)

    def execute_db_query(self, query, conn):
        is_safe, reason = self.is_query_safe(query)
        if not is_safe:
            self.error(f"Query blocked: {reason}")
            return None
        try:
            result = pd.read_sql(query, conn)
            self.write(result)
            return result
        except Exception as e:
            self.error(f"Error executing query: {e}")
            return None

    def execute_sql_query(self, query, conn):
        is_safe, reason = self.is_query_safe(query)
        if not is_safe:
            self.error(f"Query blocked: {reason}")
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(f"{query}")
            data = cursor.fetchall()

            column_names = [description[0] for description in cursor.description]
            df = pd.DataFrame(data, columns=column_names)
            View().table(df)
            return df
        except Exception as e:
            self.error(f"Error executing query: {e}")
            return None

    def define_schema(self, tables, conn):
        schema = {}
        cursor = conn.cursor()
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema[table_name] = [
                {"name": col[1], "type": col[2]} for col in columns]
        return schema

    def display_table_data(self, tables, conn):
        View().header("Available Tables")
        if tables:
            View().write("Tables in the uploaded SQL file:")
            for table_name in tables:
                View().write(f"- {table_name[0]}")

                # Optional: Display first 5 rows from each table
                data = self.return_first_5_row(table_name, conn)
                View().write(data)
        else:
            View().warning("No tables found in the SQL script.")
