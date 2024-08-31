import argparse
import json
import logging
import os
import time

import schwab
import yaml
import pandas as pd
from datetime import datetime, timedelta

import datastructures
import schwab_utils
from datastructures import Config
from account import AccountList
from dbutils import get_engine, bulk_insert_to_db, upsert_to_db, get_latest_date
from transactions import extract_base_transaction_values, extract_additional_transaction_values, process_transaction

APP_DESCRIPTION = """
This script is designed to be a long running background process which pulls data periodically and writes to data base.

This app requires a configuration file (default: ./dbconfig.yaml

NLV and transactions are updated on separate timers in the config file.

Supports getting auth token from AWS dynamodb if enabled.
"""

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_schwab_client(config: Config, useasync=False) -> schwab.client.Client:
    client = schwab.auth.client_from_token_file(
        config.tokenpath,
        config.apikey,
        config.apisecretkey,
        useasync
    )
    return client


def get_log_level(log_level_str):
    # Mapping of string log level names to logging module constants
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    # Convert the string to uppercase to ensure case-insensitivity
    log_level_str = log_level_str.upper()

    # Return the corresponding log level constant, or default to INFO if not found
    return LOG_LEVELS.get(log_level_str, logging.INFO)


def fetch_and_store_transactions(
        client,
        accounts: AccountList,
        engine,
        dbconfig,
        daysback=None,
        save_json=False,
        save_json_path="txjson"
):
    if daysback:
        start_date = datetime.now() - timedelta(days=daysback)
    else:
        latest_date = get_latest_date("transactions", engine)
        if latest_date:
            start_date = datetime.fromtimestamp(latest_date) - timedelta(days=10)
        else:
            start_date = datetime.now() - timedelta(days=365)

    current_date = start_date
    end_date = datetime.now()

    while current_date < end_date:
        next_date = current_date + timedelta(days=1)
        logging.info(f"Fetching {next_date.date()}")

        for account in accounts.accounts:
            logging.info(f"\tFetching account {account.accountNumber}")
            try:
                transactions = client.get_transactions(
                    account_hash=account.hashValue,
                    start_date=current_date,
                    end_date=next_date
                ).json()

                if save_json:
                    file_name = f"{save_json_path}/transactions.{account.accountNumber}.{current_date.strftime('%y%m%d')}.json"
                    with open(file_name, 'w') as file:
                        json.dump(transactions, file, indent=4)

                if transactions:
                    for transaction in transactions:
                        additional_data = process_transaction(transaction)

                        for table_name, data_list in additional_data.items():
                            if data_list:
                                df = pd.DataFrame(data_list)
                                if table_name == 'transactions':
                                    #bulk_insert_to_db(df, "transactions", engine, dbconfig)
                                    upsert_to_db(df, table_name, engine, dbconfig)
                                else:
                                    upsert_to_db(df, table_name, engine, dbconfig)

            except Exception as e:
                print(f"Error fetching transactions for {account.accountNumber}: {e}")

        current_date = next_date


def fetch_and_store_transactions_working(client, accounts: AccountList, engine, dbconfig, daysback):
    primary_keys_dict = {
        "transactions": ["activityId"],
        "optionTx": ["transactionId", "optionSymbol"],
        "equityTx": ["transactionId", "orderId", "symbol"],
        "futureTx": ["transactionId", "symbol"],
        "cashEquivalentTx": ["transactionId", "symbol"],
        "fixedIncomeTx": ["transactionId", "symbol"],
        "txFees": ["activityId", "feeType"],
        "unhandledTx": []
    }

    save_json = dbconfig.get("save_json", False)

    for account in accounts.accounts:
        if daysback is None:
            latest_date = get_latest_date("transactions", engine)
            if latest_date:
                latest_date = datetime.fromtimestamp(latest_date)  # Convert from timestamp
                start_date = latest_date - timedelta(days=3)
            else:
                start_date = datetime.now() - timedelta(days=365)
        else:
            start_date = datetime.now() - timedelta(days=daysback)

        current_date = start_date
        while current_date < datetime.now():
            next_date = current_date + timedelta(days=1)
            try:
                response = client.get_transactions(
                    account_hash=account.hashValue,
                    start_date=current_date.date(),
                    end_date=next_date.date()
                )

                if response.status_code != 200:
                    print(f"Error: Received response code {response.status_code} for account {account.accountNumber}")
                    print(f"Response content: {response.content}")
                    continue

                response_json = response.json()

                if isinstance(response_json, list):
                    transactions = response_json
                elif isinstance(response_json, dict):
                    transactions = response_json.get('transactions', [])
                else:
                    print(f"Unexpected JSON structure: {type(response_json)} for account {account.accountNumber}")
                    continue

                if not transactions:
                    print(f"No transactions found for account {account.accountNumber} on {current_date.date()}")
                    current_date = next_date
                    continue

                if save_json:
                    json_dir = dbconfig['json_save_path']
                    os.makedirs(json_dir, exist_ok=True)
                    json_file_path = os.path.join(
                        json_dir,
                        f'transactions.{account.accountNumber}.{current_date.strftime("%y%m%d")}.json'
                    )
                    with open(json_file_path, 'w') as json_file:
                        json.dump(transactions, json_file, indent=4)

                base_transactions = []
                additional_data = {
                    "optionTx": [],
                    "equityTx": [],
                    "futureTx": [],
                    "cashEquivalentTx": [],
                    "fixedIncomeTx": [],
                    "txFees": [],
                    "unhandledTx": []
                }

                for transaction in transactions:
                    base_data = extract_base_transaction_values(transaction)
                    base_transactions.append(base_data)

                    additional_transaction = extract_additional_transaction_values(transaction, current_date, next_date)
                    for table, data in additional_transaction.items():
                        additional_data[table].extend(data)

                if base_transactions:
                    flat_base_transactions = pd.DataFrame(base_transactions)
                    bulk_insert_to_db(flat_base_transactions, "transactions", engine, dbconfig)

                for table_name, data_list in additional_data.items():
                    if data_list:
                        flat_additional_transactions = pd.DataFrame(data_list)
                        upsert_to_db(flat_additional_transactions, table_name, engine, dbconfig)

            except Exception as e:
                print(f"Error fetching transactions for {account.accountNumber}: {e}")
            current_date = next_date


def fetch_and_store_account_info(client, dbconfig):
    logging.debug("Fetching and storing account Info")
    data = []
    resj = client.get_accounts().json()
    ts = datetime.now().timestamp()
    for accdata in resj:
        sa = accdata['securitiesAccount']
        account_num = sa['accountNumber']
        ib = sa['initialBalances']
        initial_nlv = ib['liquidationValue']
        ab = accdata['aggregatedBalance']
        agg_nlv = ab['liquidationValue']
        cb = sa['currentBalances']
        curr_nlv = cb['liquidationValue']
        initial_bp = ib.get('buyingPower', 0.0)
        current_bp = cb.get('buyingPower', 0.0)
        logging.debug("Current timestamp:" + str(ts))

        data.append(
            {
                'timestamp': ts,
                'accountNumber': account_num,
                'initialNLV': initial_nlv,
                'currentNLV': curr_nlv,
                'aggregateNLV': agg_nlv,
                'initialBP': initial_bp,
                'currentBP': current_bp
            }
        )
    df = pd.DataFrame(data)
    engine = get_engine(dbconfig)
    bulk_insert_to_db(df, "nlv", engine, dbconfig, ignore=False)

def main(appconfig, dbconfig, daysback, dashconfig, **kwargs):
    schwab_conf = Config()
    schwab_conf.read_config(appconfig)
    dbconfig = load_config(dbconfig)
    client = schwab_utils.get_schwab_client(schwab_config=schwab_conf, appconfig=dashconfig)
    acc_json = client.get_account_numbers().json()
    accounts = AccountList(jdata=acc_json)

    logging.debug(accounts.to_json())
    next_nlv_update = datetime.now().timestamp()
    next_tx_update = datetime.now().timestamp()

    while True:
        nowts = datetime.now().timestamp()
        engine = get_engine(dbconfig)
        if nowts > next_nlv_update:
            logging.info("Updating account info")
            fetch_and_store_account_info(client, dbconfig)
            next_nlv_update = (datetime.fromtimestamp(next_nlv_update)+timedelta(seconds=dbconfig['refresh']['accountinfo'])).timestamp()
            logging.info(f"Finished account info - next at: {next_nlv_update}")
        if nowts > next_tx_update:
            logging.info("Updating transactions")
            fetch_and_store_transactions(client, accounts, engine, dbconfig, daysback)
            next_tx_update = (datetime.fromtimestamp(next_tx_update)+timedelta(seconds=dbconfig['refresh']['transactions'])).timestamp()
            logging.info(f"Finished transaction update - next at: {next_nlv_update}")
        time.sleep(dbconfig['refresh']['sleep'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=APP_DESCRIPTION)
    parser.add_argument(
        '--appconfig',
        dest="appconfig",
        default="schwab.app_config.json",
        type=str,
        help='Path to the configuration file',
        metavar='[schwab.app_config.json]'
    )
    parser.add_argument(
        '--dbconfig',
        dest="dbconfig",
        type=str,
        default="dbconfig.yaml",
        help='Path to the DB configuration file. No need to change this unless you really want to',
        metavar='[dbconfig.yaml]'
    )
    parser.add_argument(
        '--daysback',
        dest="daysback",
        type=int,
        default=14,
        help='Number of days back to start fetching transactions from',
        metavar="[14]"
    )
    parser.add_argument(
        "--dashconfig",
        dest="dashconfig",
        default="dashboard_config.yaml",
        metavar='[dashboard_config.yaml]',
        help="App config file. This file will be copied from the default if there is not one"

    )
    args = parser.parse_args()
    setattr(args, 'dashconfig', datastructures.read_dashconfig_file(args.dashconfig))
    log_level = get_log_level(args.dashconfig.get('app').get('logging', "info"))
    logging.basicConfig(
        level=log_level,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the format of the log messages
        datefmt='%Y-%m-%d %H:%M:%S',  # Set the date format
    )
    main(**vars(args))
