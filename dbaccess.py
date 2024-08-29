import logging
from datetime import datetime

import pandas as pd
import sqlalchemy
import streamlit as st


def get_option_transactions(
        engine: sqlalchemy.Engine = None,
        trade_start_dt: datetime = None,
        trade_end_dt: datetime = None,
        exp_start_dt: datetime = None,
        exp_end_dt: datetime = None,
        accounts: list = None
):
    df = __get_options_transactions(_engine=engine)
    if trade_start_dt is not None:
        start_ts = trade_start_dt.timestamp()
        df = df.loc[df['tradeDate'] >= start_ts, :]
    if trade_end_dt is not None:
        end_ts = trade_end_dt.timestamp()
        df = df.loc[df['tradeDate'] <= end_ts, :]
    if exp_start_dt is not None:
        start_ts = exp_start_dt.timestamp()
        df = df.loc[df['expiration'] >= start_ts, :]
    if exp_end_dt is not None:
        end_ts = exp_end_dt.timestamp()
        df = df.loc[df['expiration'] <= end_ts, :]
    if accounts is not None:
        if isinstance(accounts, str):
            accounts = [accounts]
        elif isinstance(accounts, int):
            accounts = [str(accounts)]
        df = df.loc[~df['accountNumber'].isin(accounts), :]
    return df


def get_equity_option_transactions(
        engine: sqlalchemy.Engine =None,
        trade_start_dt: datetime = None,
        trade_end_dt: datetime = None,
        exp_start_dt: datetime = None,
        exp_end_dt: datetime = None,
        accounts: list = None
):
    df = get_option_transactions(
        engine=engine,
        trade_start_dt=trade_start_dt,
        trade_end_dt=trade_end_dt,
        exp_start_dt=exp_start_dt,
        exp_end_dt=exp_end_dt,
        accounts=accounts
    )
    df = df.loc[df['deliverableType']=="EQUITY",:]
    return df


@st.cache_data(ttl=1)
def __get_options_transactions(
        _engine = None,
) -> pd.DataFrame:
    if _engine is None:
        logging.exception("no db engine")
    q = """
    SELECT otx.*, tx.accountNumber, tx.totalFees, tx.tradeDate
    FROM transactions tx, optionTx otx
    WHERE tx.activityId = otx.transactionId and otx.assetType="OPTION"
    """
    df = pd.read_sql_query(q, _engine)
    df['tradedt'] = pd.to_datetime(df['tradeDate'], unit='s')
    df['tradedtDate'] = pd.to_datetime(df['tradedt']).dt.date
    df['tradeMonth'] = df['tradedt'].dt.month
    df['tradeMonthDate'] = df['tradedt'].dt.strftime('%y-%m')
    df['tradeYearWeek'] = df['tradedt'].dt.strftime('%y-%U')
    df['expirationDt'] = pd.to_datetime(df['expiration'], unit='s')
    df['expirationYear'] = (df['expirationDt'].dt.isocalendar().year)
    df['expirationWeek'] = df['expirationDt'].dt.isocalendar().week
    df['expirationWeekStr'] = [str(x).zfill(2) for x in df['expirationDt'].dt.isocalendar().week]
    df['expirationYearStr'] = [str(x).zfill(2) for x in df['expirationDt'].dt.isocalendar().year]
    #df['expYearWeek'] = df[['expirationYearStr', 'expirationWeekStr']].agg('-'.join, axis=1)
    df['expYearWeek'] = df['expirationYearStr'] + "-" + df['expirationWeek'].astype(str).str.zfill(2)
    #df['expYearWeek'] = df['expirationWeek'].astype(str).str.zfill(2)
    return df


@st.cache_data
def get_option_types(
        _engine: sqlalchemy.Engine = None
):
    if not _engine:
        raise Exception("No db engine")
    q = """
    SELECT distinct deliverableType FROM optionTx
    """
    df = pd.read_sql_query(q, _engine)
    return list(df['deliverableType'])

@st.cache_data
def get_min_option_expiration_timestamp(_engine=None):
    q = "SELECT min(expiration) as expiration FROM optionTx"
    df = pd.read_sql_query(q, _engine)
    return df['expiration'].values[0]


@st.cache_data
def get_max_option_expiration_timestamp(_engine=None):
    q = "SELECT max(expiration) as expiration FROM optionTx"
    df = pd.read_sql_query(q, _engine)
    return df['expiration'].values[0]


@st.cache_data(ttl=3600)
def get_account_numbers(_engine: sqlalchemy.Engine = None):
    if not _engine:
        raise Exception()
    q = "SELECT distinct accountNumber from transactions"
    df = pd.read_sql_query(q, _engine)
    return list(df['accountNumber'])
@st.cache_data
def get_min_option_transaction_timestamp(_engine=None):
    q = "SELECT min(tradeDate) as expiration FROM transactions"
    df = pd.read_sql_query(q, _engine)
    return df['expiration'].values[0]


@st.cache_data
def get_max_option_transaction_timestamp(_engine=None):
    q = "SELECT max(tradeDate) as expiration FROM transactions"
    df = pd.read_sql_query(q, _engine)
    return df['expiration'].values[0]


def get_nlv(engine, start_dt=None, end_dt=None, accounts=None):
    wflag = False
    q = """
    SELECT *
    FROM nlv
    """
    if start_dt is not None:
        start_ts = start_dt.timestamp()
        if wflag is False:
            q += "\nWHERE"
            wflag = True
        q += f"""
        timestamp >= {start_ts}
        """
    if end_dt is not None:
        end_ts = end_dt.timestamp()
        if wflag is False:
            q += "\nWHERE"
            wflag = True
        q += f"""
           timestamp <= {end_ts}
           """
    if accounts is not None:
        awlist = []
        if wflag is False:
            q += "\nWHERE"
            wflag = True
        if isinstance(accounts, str) or isinstance(accounts, int):
            accounts = [accounts]
        for acc in accounts:
            awlist.append(
                f"accountNumber={acc}"
            )
        q += f"\n{'OR'.join(awlist)}"


    q += """
    ORDER BY timestamp
    """
    df = pd.read_sql_query(q, engine)
    df['timestamp'] = df['timestamp']
    df['dt'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] =pd.to_datetime(df['dt']).dt.date
    return df

def get_futures_tx(_engine: sqlalchemy.Engine=None):
    if not _engine:
        raise Exception()
    return __get_futures_transactions(_engine)

@st.cache_data(ttl=1)
def __get_futures_transactions(
        _engine = None,
) -> pd.DataFrame:
    if _engine is None:
        logging.exception("no db engine")
    q = """
    SELECT otx.*, tx.accountNumber, tx.totalFees, tx.tradeDate
    FROM transactions tx, optionTx otx
    WHERE tx.activityId = otx.transactionId and otx.assetType="OPTION"
    """
    q = """
    SELECT ft.*, tx.time, tx.accountNumber, tx.tradeDate FROM futureTx ft, transactions tx
    WHERE tx.activityId = ft.transactionId
    """
    df = pd.read_sql_query(q, _engine)
    df['contract'] = df['symbol'].str.split(":").str[0]
    df['underlyingSymbol'] = df['contract'].str[:-3]
    df['tradedt'] = pd.to_datetime(df['tradeDate'], unit='s')
    df['tradedtDate'] = pd.to_datetime(df['tradedt']).dt.date
    df['tradeMonth'] = df['tradedt'].dt.month
    df['tradeMonthDate'] = df['tradedt'].dt.strftime('%y-%m')
    df['tradeYearWeek'] = df['tradedt'].dt.strftime('%y-%U')
    df['expirationDt'] = pd.to_datetime(df['expiration'], unit='s')
    df['expirationYear'] = (df['expirationDt'].dt.isocalendar().year)
    df['expirationWeek'] = df['expirationDt'].dt.isocalendar().week
    df['expirationWeekStr'] = [str(x).zfill(2) for x in df['expirationDt'].dt.isocalendar().week]
    df['expirationYearStr'] = [str(x).zfill(2) for x in df['expirationDt'].dt.isocalendar().year]
    #df['expYearWeek'] = df[['expirationYearStr', 'expirationWeekStr']].agg('-'.join, axis=1)
    df['expYearWeek'] = df['expirationYearStr'] + "-" + df['expirationWeek'].astype(str).str.zfill(2)
    #df['expYearWeek'] = df['expirationWeek'].astype(str).str.zfill(2)
    return df
