import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

import schwab_db
import streamlit_interface as si

import streamlit_utils
from dbaccess import get_nlv

dbconfig = streamlit_utils.read_dbconfig("dbconfig.yaml")
engine = schwab_db.get_engine(dbconfig=dbconfig)

def main(dbconfig: dict, **kwargs):

    display_controls = st.container()
    plot_con = st.container()

    data_columns = ['currentNLV', 'initialNLV', 'currentBP', 'initialBP']

    DISPLAY_TYPE = "plot"
    with st.spinner("Getting NLV data"):
        nlv_df = get_nlv(engine=engine)
        #nlv_df['dt'] = pd.to_datetime(nlv_df['timestamp'])
        #data_columns = list(nlv_df.columns)



    with display_controls:

        field = st.selectbox("Data Column", options=data_columns, index=data_columns.index("currentNLV"))


        #nlv_gb = nlv_df.groupby(['date', 'initialNLV', "accountNumber"]).size().reset_index().rename(columns={0:'count'})
        nlv_gb = nlv_df.groupby(['date', field, "accountNumber"]).size().reset_index().rename(columns={0:'count'})
    #st.dataframe(nlv_gb)
#st.dataframe(nlv_df))
    with plot_con:
        if DISPLAY_TYPE=="plot":

            fig, ax = plt.subplots()
            sns.lineplot(
                nlv_gb,
                x="date",
                y=field,
                hue="accountNumber",
                ax=ax
            )
            ax.get_legend().remove()
            ax.tick_params(axis='x', rotation=90)


            st.pyplot(fig)
        elif DISPLAY_TYPE == "table":
            st.dataframe(nlv_gb)
    return 0


main(dbconfig)