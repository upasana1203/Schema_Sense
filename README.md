# SchemaSense

A Streamlit app that lets you upload a database and query it in plain English. Type a question, get back the SQL query Gemini generated for it, and see the results run directly against your data — no manual SQL needed.

## What it does

- Upload a `.db`, `.sqlite`, or `.sql` file
- View the tables and an auto-generated schema diagram before querying
- Type a question like "show me the top 5 orders sorted by date"
- Gemini reads the schema, generates the matching SQL query, and the app runs it and shows you the results

## How it works

1. The uploaded database is parsed and its schema (tables, columns, relationships) is extracted and rendered as a diagram.
2. That schema is passed as context to Gemini along with the user's natural language question.
3. Gemini returns a SQL query, which is extracted and cleaned up before execution.
4. The query runs against the uploaded database, and results are displayed back in the UI.

## Tech Stack

- Python
- Streamlit (UI)
- Google Gemini (query generation)
- SQLite / SQL file parsing

## Setup

```bash
git clone https://github.com/upasana1203/SchemaSense.git
cd SchemaSense
pip install -r requirements.txt
```

Create a `.env` file in the root directory:

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Run it:

```bash
streamlit run main.py
```

## Usage

1. Launch the app and upload a `.db` or `.sql` file from the Home tab.
2. Check the Schema Diagram tab to see the table structure.
3. Switch to Query Editor, type your question in plain English, and hit the query button.
4. View the generated SQL and the query results.

## Project Structure

```
.
├── main.py                     # App entry point and UI flow
├── TTS/
│   ├── base_tts.py             # Streamlit UI wrapper/view layer
│   ├── db_management.py         # Database loading and query execution
│   ├── retrieve_schema.py       # Schema extraction and diagram rendering
│   └── text_to_sql_gemini.py    # Gemini prompt + query generation logic
├── requirements.txt
└── .env                          # Your API key (not committed)
```

## Notes

Built on top of an open-source Gemini-based text-to-SQL starter project, extended with:
- Query safety validation — only read-only `SELECT` statements are allowed to run; chained statements and destructive keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, etc.) are blocked before execution, using word-boundary matching so legitimate column names like `updated_at` aren't falsely flagged
- CSV export for query results
- Basic per-session rate limiting to prevent API quota abuse
- Temp file cleanup after each upload, instead of leaving uploaded databases on disk indefinitely
- A capped upload size (25MB) to prevent oversized file uploads
- Updated to the current Gemini model (`gemini-2.5-flash`)
- Removed a bug in query cleanup that stripped every occurrence of the substring "sql" from generated queries, which could silently corrupt queries touching tables/columns containing that substring

This project is licensed under the Apache 2.0 License — see `LICENSE` for details.
