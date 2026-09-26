import time
import streamlit as st

from TTS.base_tts import View
from TTS.retrieve_schema import schemaRetrieve
from TTS.text_to_sql_gemini import GenerateQuery
from TTS.db_management import Database

# Minimum seconds a user must wait between two query submissions
MIN_SECONDS_BETWEEN_QUERIES = 5


def is_rate_limited() -> bool:
    """Simple per-session cooldown so one user can't spam the Gemini API."""
    last_call = st.session_state.get("last_query_time", 0)
    elapsed = time.time() - last_call
    if elapsed < MIN_SECONDS_BETWEEN_QUERIES:
        wait = round(MIN_SECONDS_BETWEEN_QUERIES - elapsed, 1)
        st.warning(f"Please wait {wait}s before submitting another query.")
        return True
    st.session_state["last_query_time"] = time.time()
    return False


def main():
    st.set_page_config(page_title="SchemaSense", page_icon="🗃️", layout="wide")
    view = View()  # Initialize the view with the dark theme
    view.title("🗃️ SchemaSense")
    Home, QueryEditor = view.tabs(["Home", "Query Editor"])

    with Home:
        db_file = view.file_uploader(
            "Upload file", type=["sqlite", "db", "sql"])
        Tables, Schema = view.tabs(["Tables List", "Schema Diagram"])

        with Tables:
            if db_file:
                schema_retrieve = schemaRetrieve(db_file=db_file)
                schema = schema_retrieve.db_to_schema()
                if schema:
                    schema_context = schema_retrieve.transform_schema(
                        schema=schema)
            else:
                view.subheader("Please Upload the SQL file to view the tables")

        with Schema:
            try:
                schema_retrieve.display_schema_diagram(schema_context)
            except Exception as e:
                view.subheader(
                    "Please Upload the SQL file to view the schema diagram")

    with QueryEditor:
        view.header("SQL Query Tester")
        nlp_input = view.text_area("Write your NLP Input here:", "")

        if view.button("SQL Query Tester"):
            if not schema_context:
                view.error("Please Upload the Database file")
            elif is_rate_limited():
                pass  # warning already shown by is_rate_limited()
            else:
                sql_query = GenerateQuery().generate_sql_query_with_gemini(nlp_input, schema_context)
                view.write(sql_query)

                sql_query = view.extract_sql_query(sql_query)

                if schema_retrieve.extension == 'sql':
                    result_df = Database().execute_sql_query(sql_query, schema_retrieve.conn)
                else:
                    result_df = Database().execute_db_query(sql_query, schema_retrieve.conn)

                if result_df is not None and not result_df.empty:
                    csv_data = result_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download results as CSV",
                        data=csv_data,
                        file_name="query_results.csv",
                        mime="text/csv",
                    )


main()
