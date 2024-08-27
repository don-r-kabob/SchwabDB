import sys
from datetime import datetime

import pandas as pd
import streamlit as st

import dbaccess
import dbutils
import streamlit_interface as si
import seaborn as sns
import matplotlib.pyplot as plt

import streamlit_utils
from datastructures import read_dashconfig_file
from dbaccess import get_equity_option_transactions

dashconfig = read_dashconfig_file("dashboard_config.yaml")
dbconfig = si.read_dbconfig("dbconfig.yaml")
#st.set_page_config(layout=dashconfig['streamlit']['pagelayout'])

def main(
        dbconfig=None,
        **kwargs
):
    pass
    streamlit_utils.sidebar_reset_cache_button()
    engine = dbutils.get_engine(dbconfig=dbconfig)
    aggType = "expirationDate"
    deliverable_types_list = dbaccess.get_option_types(engine)
    accounts = dbaccess.get_account_numbers(engine)
    #deliverable_types_list.append(None)


    data_controls = st.expander("Data Controls", expanded=True)
    #data_controls = st.expander("Data Controls")
    #plot_container = st.expander("Data", expanded=True)
    plot_container = st.container()
    #plot_controls = st.expander("Plot controls")
    plot_controls = st.container()

    start_dt = None
    end_dt = None
    SHOW_LEGEND = True
    SHOW_XAXIS = True
    SHOW_YAXIS = True
    INVERT_XY = False
    DISPLAY_METHOD = "plot"


    with data_controls:
        deliverable_types = st.multiselect("Contract Types", options=deliverable_types_list, default=deliverable_types_list)
        account_list = st.multiselect("Accounts", options=accounts, default=accounts)


    with plot_controls:
        SHOW_LEGEND = st.checkbox("Show Legend", value=True)
        SHOW_XAXIS = st.checkbox("Show X-axis", value=True)
        SHOW_YAXIS = st.checkbox("Show Y-axis", value=True)
        INVERT_XY = st.checkbox("Invert X/Y", value=False)

    with data_controls:
        min_date = datetime.fromtimestamp(dbaccess.get_min_option_expiration_timestamp(engine)).date()
        max_date = datetime.fromtimestamp(dbaccess.get_max_option_expiration_timestamp(engine)).date()
        default_start = datetime.now().replace(month=1, day=1).date()
        default_end = datetime.now().replace(month=12, day=31).date()
        start_date, end_date = st.slider(
            "Expiration Date Range",
            value=[
                default_start,
                default_end
                #,datetime.now().replace(year=2024, month=1, day=1).date(),
                #,datetime.now().date()
            ],
            #min_value=datetime.now().replace(year=2023, month=1, day=1).date(),
            min_value=min_date,
            #max_value=datetime.now().date())
            max_value = max_date
        )
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.min.time())


    st.write(start_dt, end_dt)
    with st.spinner("Getting db transactions"):
        df = dbaccess.get_option_transactions(
            engine=engine,
            exp_start_dt=start_dt,
            exp_end_dt=end_dt,
            accounts=None
        )
        tickers = df['underlyingSymbol'].unique()


    with data_controls:
        DISPLAY_METHOD = st.selectbox("display", options=["plot", "table"])
        remove_tickers_list = st.multiselect("Remove Tickers", options=tickers)

    fig: plt.Figure
    ax: plt.Axes
    with st.spinner("Processing filters and making figure"):
        df = df.loc[df['deliverableType'].isin(deliverable_types), :]
        df = df.loc[~df['underlyingSymbol'].isin(remove_tickers_list), :]
        df = df.loc[df['accountNumber'].isin(account_list), :]
        df = df.sort_values("tradeDate")
        tx_gb = df.groupby([aggType, "accountNumber"])['cost'].sum().reset_index()

        if DISPLAY_METHOD == "plot":
            xaxis = aggType
            yaxis = "cost"
            if INVERT_XY:
                yaxis = aggType
                xaxis = "cost"
            fig, ax = plt.subplots()
            sns.barplot(
                tx_gb,
                x=xaxis,
                y=yaxis,
                ax=ax,
                hue="accountNumber"
            )
            ax.tick_params(axis='x', rotation=90)
            ax.set_title("Option Premium - By Expiration")
            ax.set_ylabel("Net Premium")
    with plot_container:
        if DISPLAY_METHOD == "plot":
            st.pyplot(fig)
        elif DISPLAY_METHOD == "table":
            st.dataframe(df)
    return 0

main(dbconfig=dbconfig)
sys.exit(0)

# DEAD CODE

engine = schwab_db.get_engine(dbconfig=dbconfig)
#print(engine)
xaxis = "expirationDate"
use_equity = True
use_futures = True
use_index = True
use_null = True

start_date, end_date = st.slider(
    "Expiration Date Range",
    value=[
        datetime.now().replace(year=2024, month=1, day=1).date(),
        datetime.now().date()
    ],
    min_value=datetime.now().replace(year=2023, month=1, day=1).date(),
    max_value=datetime.now().date())
start_dt =  datetime.combine(start_date, datetime.min.time())
end_dt =  datetime.combine(end_date, datetime.min.time())
st.write(start_dt)
print(type(start_dt))
if use_equity:
    with st.spinner("Getting Equity Options Transactions data"):
        equity_df = get_equity_option_transactions(
            engine=engine,
            exp_start_dt=start_dt,
            exp_end_dt=end_dt,
            accounts=None
        )
        st.dataframe(equity_df)
        if tx_df is None:
            tx_df = equity_df
        else:
            tx_df = pd.concat(tx_df, equity_df)
tx_df = tx_df.sort_values("tradeDate")
st.write("Size", tx_df.shape)
#st.dataframe(tx_df.loc[tx_df['activityId'==62763080761,:]])
st.dataframe(tx_df)
#nlv_df['dt'] = pd.to_datetime(nlv_df['timestamp'])
tx_gb = tx_df.groupby([xaxis, "accountNumber"])['cost'].sum().reset_index()
#tx_gb['cumsum'] = tx_gb['cost'].cumsum()

    #nlv_gb = nlv_df.groupby(['date', 'initialNLV', "accountNumber"]).size().reset_index().rename(columns={0:'count'})
    #nlv_gb = nlv_df.groupby(['date', 'currentNLV', "accountNumber"]).size().reset_index().rename(columns={0:'count'})
    #st.dataframe(tx_gb)
display_control_con = st.expander("Display Controls")
with display_control_con:
    SHOW_LEGEND = st.checkbox("Show Legend", value=True)
    SHOW_XAXIS = st.checkbox("Show X-axis", value=True)
    SHOW_YAXIS = st.checkbox("Show Y-axis", value=True)
st.dataframe(tx_gb)
fig: plt.Figure
ax: plt.Axes
fig, ax = plt.subplots()
sns.barplot(
    tx_gb,
    x=xaxis,
    y="cost",
    ax=ax,
    hue="accountNumber"
)
ax.tick_params(axis='x', rotation=90)
ax.set_title("Option Premium - By Expiration")
ax.set_ylabel("Net Premium")
if SHOW_LEGEND is False:
    ax.legend().remove()
if SHOW_XAXIS is False:
    ax.tick_params(axis='x', labelleft=False)
if SHOW_YAXIS is False:
    ax.tick_params(axis='y', labelleft=False)
#ax.get_legend().remove()

st.pyplot(fig)