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
dbconfig = streamlit_utils.read_dbconfig("dbconfig.yaml")
#st.set_page_config(layout=dashconfig['streamlit']['pagelayout'])

def main(
        dbconfig=None,
        **kwargs
):
    pass
    streamlit_utils.sidebar_reset_cache_button()
    engine = dbutils.get_engine(dbconfig=dbconfig)
    #aggType = "expirationDate"
    #aggType = "expYearWeek"

    deliverable_types_list = dbaccess.get_option_types(engine)
    accounts = dbaccess.get_account_numbers(engine)
    #deliverable_types_list.append(None)

    agg_values_list = ["tradedtDate", "expirationDate", "tradeMonthDate", "tradeYearWeek"]

    aggType = st.selectbox("Aggregation", options=agg_values_list, index=0)


    data_controls = st.expander("Data Controls", expanded=True)
    #data_controls = st.expander("Data Controls")
    #plot_container = st.expander("Data", expanded=True)
    plot_container = st.container()
    table_container = st.container()
    #plot_controls = st.expander("Plot controls")
    plot_controls = st.container()
    with plot_controls:
        plot_controls1, plot_controls2, plot_controls3 = st.columns(3)

    start_dt = None
    end_dt = None
    SHOW_LEGEND = True
    SHOW_XAXIS = True
    SHOW_YAXIS = True
    SHOW_CURRENT_EXP = False
    PLOT_AGGREAGTE = "Discrete"
    INVERT_XY = False
    DISPLAY_METHOD = "plot"

    plot_options_list = ["Discrete", "Cumulative"]


    with data_controls:
        deliverable_types = st.multiselect("Contract Types", options=deliverable_types_list, default=deliverable_types_list)
        account_list = st.multiselect("Accounts", options=accounts, default=accounts)


    with plot_controls1:
        SHOW_LEGEND = st.checkbox("Show Legend", value=True)
        SHOW_XAXIS = st.checkbox("Show X-axis", value=True)
        SHOW_YAXIS = st.checkbox("Show Y-axis", value=True)
        if aggType == "expYearWeek":
            SHOW_CURRENT_EXP = st.checkbox("Show current expYear", value=True)

        INVERT_XY = st.checkbox("Invert X/Y", value=False)

    with plot_controls2:
        figure_width = st.number_input("Figure Width", value=6.4, step=0.25)
        figure_height = st.number_input("Figure Height", value=4.8, step=0.25)

    with (data_controls):
        if aggType == "expYearWeek" or aggType == "expirationDate" or aggType == "expiration":
            min_date = datetime.fromtimestamp(dbaccess.get_min_option_expiration_timestamp(engine)).date()
            max_date = datetime.fromtimestamp(dbaccess.get_max_option_expiration_timestamp(engine)).date()
            slider_label = "Expiration Date Range"
            title = "{} Option Premium - By Expiration ({})"
        elif aggType == "tradeDate" or \
                aggType == "tradedtDate" or \
                aggType == "tradeMonthDate" or \
                aggType == "tradeYearWeek":
            min_date = datetime.fromtimestamp(dbaccess.get_min_option_transaction_timestamp(engine)).date()
            max_date = datetime.fromtimestamp(dbaccess.get_max_option_transaction_timestamp(engine)).date()
            #min_date = datetime.fromtimestamp(dbaccess.#)
            slider_label = "Trade Date Range"
            title = "{} Option Premium - By Transaction ({})"
            pass
        default_start = datetime.now().replace(month=1, day=1).date()
        default_end = datetime.now().replace(month=12, day=31).date()
        start_date, end_date = st.slider(
            slider_label,
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
    with st.spinner("Getting db transactions"):
        df = dbaccess.get_futures_tx(
            _engine=engine
            #,exp_start_dt=start_dt,
            #exp_end_dt=end_dt,
            #accounts=None
        )
        tickers = df['symbol'].unique()
    with data_controls:
        DISPLAY_METHOD = st.selectbox("display", options=["plot", "table"], index=0)
        remove_tickers_list = st.multiselect("Remove Tickers", options=tickers)
        PLOT_AGGREAGTE = st.selectbox("Plot Aggregate", options=plot_options_list, index=0)

    fig: plt.Figure
    ax: plt.Axes
    with st.spinner("Processing filters and making figure"):
        #df = df.loc[df['deliverableType'].isin(deliverable_types), :]
        #df = df.loc[~df['underlyingSymbol'].isin(remove_tickers_list), :]
        #df = df.loc[df['accountNumber'].isin(account_list), :]
        df = df.sort_values("tradeDate")
        if PLOT_AGGREAGTE == "Discrete":
           tx_gb = df.groupby([aggType, "accountNumber"])['cost'].sum().reset_index()
        elif PLOT_AGGREAGTE == "Cumulative":
            tx_gb = df.groupby([aggType])['cost'].sum().groupby(level=0).cumsum().reset_index()
            tx_gb['cumsum'] = tx_gb['cost'].cumsum()

        if DISPLAY_METHOD == "plot":
            xaxis = aggType
            if INVERT_XY:
                yaxis = aggType
                xaxis = "cost"
            fig, ax = plt.subplots(figsize=(figure_width, figure_height))
            if PLOT_AGGREAGTE == "Discrete":
                if INVERT_XY:
                    xaxis = "cost"
                else:
                    yaxis = "cost"
                sns.barplot(
                    tx_gb,
                    x=xaxis,
                    y=yaxis,
                    ax=ax,
                    hue="accountNumber",
                    zorder=5
                )
                #ax.set_title(f"Option Premium - By Expiration")
                ax.set_title(title.format(PLOT_AGGREAGTE, aggType))
            elif PLOT_AGGREAGTE == "Cumulative":
                if INVERT_XY:
                    xaxis = "cumsum"
                else:
                    yaxis = "cumsum"
                sns.barplot(
                    tx_gb,
                    x=xaxis,
                    y=yaxis,
                    ax=ax,
                    zorder=5
                )
                ax.set_title(f"Cumulative Option Premium - By Expiration")
            ax.tick_params(axis='x', rotation=90)
            data_value_label = "Net Value"
            if INVERT_XY:
                ax.set_xlabel(data_value_label)
            else:
                ax.set_ylabel(data_value_label)

            dtn = datetime.now()
            if SHOW_CURRENT_EXP and (dtn >= start_dt and dtn <= end_dt):
                if INVERT_XY:
                    ticklabels = ax.get_yticklabels()
                    ticklabels = [tick.get_text() for tick in ax.get_yticklabels()]
                else:
                    ticklabels = ax.get_xticklabels()
                    ticklabels = [tick.get_text() for tick in ax.get_xticklabels()]
                if aggType == "expYearWeek":
                    #dtniso = dtn.isocalendar()[0:2]

                    now_year_week = "-".join(str(x).zfill(2) for x in dtn.isocalendar()[0:2])
                    print(now_year_week)
                    tl: plt.Text
                    for tl in ticklabels:
                        pass
                        #if tl.get_text() == now_year_week:
                            #ax.axvline(tl.get_position(), col="red", linestyle="dashed", label="Current Week")

                    if INVERT_XY:
                        print(ticklabels)
                        ax.axhline(ticklabels.index(now_year_week), color='red', linestyle='dotted', zorder=1)
                    else:
                        ax.axvline(ticklabels.index(now_year_week), color='red', linestyle='dotted', zorder=1)
            if SHOW_XAXIS is False:
                ax.tick_params(axis='x', labelbottom=False)
            if SHOW_YAXIS is False:
                ax.tick_params(axis='y', labelleft=False)
            if SHOW_LEGEND is False:
                ax.legend().remove()

    if DISPLAY_METHOD == "plot":
        #plot_container.empty()
        with plot_container:
            #st.empty()
            st.pyplot(fig)
            plt.close(fig)
    elif DISPLAY_METHOD == "table":
        #plot_container.empty()
        with plot_container:
            #st.empty()
            st.dataframe(tx_gb)
            st.dataframe(df)

    print("Finishing")
    return 0

main(dbconfig=dbconfig)