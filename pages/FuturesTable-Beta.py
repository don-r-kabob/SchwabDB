import pandas as pd
import streamlit as st

import dbaccess
import dbutils
import streamlit_utils
from datastructures import read_dashconfig_file
import streamlit_interface as si

dashconfig = read_dashconfig_file("dashboard_config.yaml")
dbconfig = si.read_dbconfig("dbconfig.yaml")

def get_contact_totals(df: pd.DataFrame):
    sum_df = df.groupby(['contract'])['cost'].sum()
    return sum_df
    pass
    sumd = {}
    for i in df.to_dict(orient="records"):
        contract = i['contract']
        cost = i['cost']
        if i['contract'] not in sumd:
            sumd[contract] = 0


def get_underlying_totals(df):
    sum_df = df.groupby(['underlyingSymbol'])[['cost', 'quantity']].sum()
    return sum_df

def get_zeroed_underlying_totals(df):
    sum_df = df.groupby(['underlyingSymbol']).sum()
    sum_df = sum_df.loc[sum_df['quantity']==0,'cost']
    return sum_df

def main(dbconifg, **kwargs):
    streamlit_utils.sidebar_reset_cache_button()
    engine = dbutils.get_engine(dbconfig=dbconfig)
    df = dbaccess.get_futures_tx(engine)
    st.dataframe(df)
    sum_df = get_contact_totals(df)
    st.dataframe(sum_df)
    ul_df = get_underlying_totals(df)
    st.dataframe(
        ul_df.loc[
            ul_df['quantity']==0,
            :
        ]
    )



main(dbconfig)
