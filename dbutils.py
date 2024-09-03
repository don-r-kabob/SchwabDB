import logging

import pandas as pd
from sqlalchemy import create_engine, inspect, text, Table, MetaData
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, Integer, String, Float, DateTime, text
import traceback

def get_engine(dbconfig):
    engine_type = dbconfig['engine']
    db_url = dbconfig['path']

    if engine_type == 'sqlite':
        engine = create_engine(f'sqlite:///{db_url}')
    else:
        raise ValueError(f"Unsupported database engine: {engine_type}")

    return engine

from pathlib import Path
import os

def ensure_dir_and_create_file_path(directory, filename):
    # Ensure the directory exists; if not, create it
    Path(directory).mkdir(parents=True, exist_ok=True)

    # Create the full file path
    file_path = os.path.join(directory, filename)

    return file_path
def create_table_from_sql(engine, table_name, dbconfig):
    sql_file_name = f'{table_name}.sql'
    #sql_file_path = f'sql/{dbconfig["engine"]}/{table_name}.sql'
    sql_file_path = os.path.join("sql", dbconfig['engine'], sql_file_name)
    logging.info(f"Creating table {table_name} in {sql_file_path}")
    with engine.connect() as conn:
        with open(sql_file_path, 'r') as file:
            conn.execute(text(file.read()))

def infer_sqlalchemy_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return Integer
    elif pd.api.types.is_float_dtype(dtype):
        return Float
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return DateTime
    else:
        return String

def bulk_insert_to_db(df, table_name, engine, dbconfig, ignore=True):
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        create_table_from_sql(engine, table_name, dbconfig)

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    data = df.to_dict(orient='records')
    if ignore:
        insert_statement = table.insert().prefix_with('OR IGNORE')
    else:
        insert_statement = table.insert()

    with engine.begin() as conn:
        try:
            conn.execute(insert_statement, data)
        except Exception as e:
            print(f"Error inserting data into {table_name}: {e}")



def upsert_to_db(df, table_name, engine, dbconfig):
    try:
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            logging.info(f"Creating table {table_name}")
            create_table_from_sql(engine, table_name, dbconfig)

        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        with engine.begin() as conn:
            for index, row in df.iterrows():
                insert_statement = sqlite_insert(table).values(row.to_dict())
                update_statement = {c.name: insert_statement.excluded[c.name] for c in insert_statement.table.c if c.name not in primary_keys_dict[table_name]}
                conn.execute(insert_statement.on_conflict_do_update(index_elements=primary_keys_dict[table_name], set_=update_statement))
    except Exception as e:
        print(f"Error in upsert_to_db: {e}")
        traceback.print_exc()


def get_latest_date_orig(table_name, engine):
    query = f"SELECT MAX(tradeDate) FROM {table_name}"
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
    return result[0] if result[0] else None

def get_latest_date(table_name, engine):
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return None

    query = f"SELECT MAX(tradeDate) FROM {table_name}"
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
    return result[0] if result[0] else None

def print_top_entries(table_name, engine, limit=5):
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        if rows:
            columns = result.keys()
            df = pd.DataFrame(rows, columns=columns)
            print(f"Top {limit} entries from {table_name}:")
            print(df)
        else:
            print(f"No entries found in {table_name}")


primary_keys_dict = {
    "transactions": ["activityId"],
    "optionTx": ["transactionId", "optionSymbol"],
    "equityTx": ["transactionId", "orderId", "symbol"],
    "futureTx": ["transactionId", "symbol"],
    "cashEquivalentTx": ["transactionId", "symbol"],
    "fixedIncomeTx": ["transactionId", "symbol"],
    "txFees": ["activityId", "feeType"]
}