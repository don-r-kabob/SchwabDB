import argparse

import streamlit as st

import dbutils
#import queries

import streamlit_utils
from datastructures import read_dashconfig_file
from streamlit_utils import read_dbconfig

dashconfig = read_dashconfig_file("dashboard_config.yaml")
st.set_page_config(layout=dashconfig['streamlit']['pagelayout'])


def main(appconfig_file=None, dbconfig_file=None, **kwargs):
    dbconfig = read_dbconfig("dbconfig.yaml")
    #conf = Config()
    #conf.read_config(appconfig_file)
    st.header("Schwab Database Streamlit Interface")
    streamlit_utils.sidebar_reset_cache_button()
    return
    engine = dbutils.get_engine(dbconfig=dbconfig)
    #df = queries.get_account_option_premium_by_expiration(engine)
    #df['total_price'] = df['price']*df['quantity']
    #df['expirationDate'] = pd.to_datetime(df['expirationDate'])
    #df['expirationDow'] = df['expirationDate'].dt.day_name()
    #st.dataframe(df)
    df = df.loc[df['expirationDow']=="Friday",:]
    st.dataframe(df)
    df2 = df.groupby(['expirationDate'])['total_price'].sum()
    st.dataframe(df2)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Schwab Database Dashboard")
    parser.add_argument(
        '--appconfig',
        dest="appconfig_file",
        default="schwab.app_config.json",
        type=str,
        help='Path to the configuration file'
    )
    parser.add_argument(
        '--dbconfig',
        dest="dbconfig_file",
        type=str,
        default="dbconfig.yaml",
        help='Path to the configuration file'
    )
    args = parser.parse_args()
    main(**vars(args))

