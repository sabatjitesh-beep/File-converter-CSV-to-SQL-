import streamlit as st
import csv
import sqlite3
import os
from io import StringIO, BytesIO

def quote_value(val):
    if not val:
        return 'NULL'
    try:
        float(val)
        return str(val)
    except ValueError:
        return "'" + str(val).replace("'", "''") + "'"

def csv_to_sql(csv_file, table_name):
    try:
        reader = csv.reader(StringIO(csv_file.getvalue().decode("utf-8")))
        headers = next(reader)
        inserts = []
        for row in reader:
            values = ', '.join(quote_value(val) for val in row)
            inserts.append(f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({values});")
        sql_output = '\n'.join(inserts)
        return sql_output, None
    except Exception as e:
        return None, str(e)

def sql_input_to_csv(sql_text):
    try:
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.executescript(sql_text)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if not tables:
            raise ValueError("No table found in SQL input.")
        table_name = tables[0][0]
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        conn.close()
        return output.getvalue(), None
    except Exception as e:
        return None, str(e)

# ---------- Streamlit UI ----------
st.title("📄 CSV ↔ SQL Converter")

tab1, tab2 = st.tabs(["File Conversion", "SQL Input to CSV"])

with tab1:
    st.subheader("Upload CSV or SQL file")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "sql"])
    table_name = st.text_input("Table Name (for CSV → SQL)")
    if uploaded_file:
        st.write(f"Selected file: {uploaded_file.name}")
        if uploaded_file.name.endswith(".csv"):
            if st.button("Convert CSV to SQL"):
                if not table_name:
                    st.error("Please enter a table name.")
                else:
                    sql_output, error = csv_to_sql(uploaded_file, table_name)
                    if error:
                        st.error(f"Conversion failed: {error}")
                    else:
                        st.success("Conversion successful!")
                        st.download_button("Download SQL", sql_output, file_name="output.sql")
        elif uploaded_file.name.endswith(".sql"):
            if st.button("Convert SQL to CSV"):
                sql_text = uploaded_file.getvalue().decode("utf-8")
                csv_output, error = sql_input_to_csv(sql_text)
                if error:
                    st.error(f"Conversion failed: {error}")
                else:
                    st.success("Conversion successful!")
                    st.download_button("Download CSV", csv_output, file_name="output.csv")
        else:
            st.error("Unsupported file type.")

with tab2:
    st.subheader("Paste SQL to convert to CSV")
    sql_text_input = st.text_area("Enter SQL (CREATE TABLE + INSERTs)")
    if st.button("Convert SQL Text to CSV"):
        if not sql_text_input.strip():
            st.error("Please enter SQL text.")
        else:
            csv_output, error = sql_input_to_csv(sql_text_input)
            if error:
                st.error(f"Conversion failed: {error}")
            else:
                st.success("Conversion successful!")
                st.download_button("Download CSV", csv_output, file_name="output.csv")

