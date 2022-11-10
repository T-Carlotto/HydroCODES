import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from io import StringIO
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
from openpyxl.workbook import Workbook
import matplotlib.pylab as plt
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import AdaBoostRegressor
import csv
import streamlit.components.v1 as components

st.title("Hydrograph Separation Tool")

components.html("""<form action="https://www.paypal.com/donate" method="post" target="_top">
                    <!-- Identify your business so that you can collect the payments. -->
                    <input type="hidden" name="business" value="donations@kcparkfriends.org">
                    <!-- Specify details about the contribution -->
                    <input type="hidden" name="no_recurring" value="0">
                    <input type="hidden" name="item_name" value="Friends of the Park">
                    <input type="hidden" name="item_number" value="Fall Cleanup Campaign">
                    <input type="hidden" name="currency_code" value="USD">
                    <!-- Display the payment button. -->
                    <input type="image" name="submit" src="https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif" alt="Donate">
                    <img alt="" width="1" height="1" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" >
                    </form> 
                    """)

tab1, tab2 = st.tabs(["🗃 Input data", "📈 Output"])

with tab1:
    file = st.file_uploader("Please choose a file")

with tab2:
    fig, ax = plt.subplots()
    plt.xticks(rotation=45)

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output)
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    #format1 = workbook.add_format({'num_format': '0.00'})
    #worksheet.set_column('A:A', None, format1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def Lyne_Hollick_filter(df,alpha):
    Q = df['StreamFlow']
    Q_LH[0] = Q[0]
    for i in range(len(Q)-1):
        i=i+1
        Q_LH[i] = alpha*Q_LH[i-1]+ 0.5*(1 - alpha) * (Q[i] + Q[i-1])
        if (Q_LH[i]>Q[i]):
            Q_LH[i] = Q[i]
    return Q_LH

def Chapman_filter(df,alpha):
    Q = df['StreamFlow']
    Q_CH[0] = Q[0]
    for i in range(len(Q)-1):
        i=i+1
        Q_CH[i] = (alpha/(2-alpha))*Q_CH[i-1] + ((1 - alpha)/(2-alpha)) * Q[i]
        if (Q_CH[i]>Q[i]):
            Q_CH[i] = Q[i]
    return Q_CH

def Eckhardt_filter(df,alpha,BFI_max):
    Q = df['StreamFlow']
    Q_EK[0] = Q[0]
    for i in range(len(Q)-1):
        i=i+1
        Q_EK[i] = ((1-BFI_max)*alpha*Q_EK[i-1]+(1-alpha)*BFI_max*Q[i])/(1-alpha*BFI_max)
        if (Q_EK[i]>Q[i]):
            Q_EK[i] = Q[i]
    return Q_EK

if file is not None:

    option = st.sidebar.multiselect(
            'Select the numeric filter',
            ['Lyne-Hollick', 'Chapman', 'Eckhardt'])

    df= pd.read_csv(file)

    results = df
    results1 = pd.DataFrame()
    results2 = pd.DataFrame()
    results3 = pd.DataFrame()

    with tab2:
        ax.plot(df['Time'], df['StreamFlow'])
        plt.axis([min(df['Time']), max(df['Time']), min(df['StreamFlow']), max(df['StreamFlow'])])


    for ifn in range(len(option)):
        if (option[ifn]=='Lyne-Hollick'):
            Q_LH = []
            Q_LH = [0 for i in df['StreamFlow']]
            st.sidebar.header("Lyne-Hollick filter parameter")
            alpha_lh = st.sidebar.number_input(label='alpha1', value=0.995, format="%lf", min_value=0.0000,
                                            max_value=1.0000, step=0.0001, disabled=False, label_visibility="visible")

        if (option[ifn]=='Chapman'):
            Q_CH = []
            Q_CH = [0 for i in df['StreamFlow']]
            st.sidebar.header("Chapman filter parameter")
            alpha_ch = st.sidebar.number_input(label='alpha2', value=0.995, format="%lf", min_value=0.0000,
                                            max_value=1.0000, step=0.0001, disabled=False, label_visibility="visible")

        if (option[ifn]=='Eckhardt'):
            Q_EK = []
            Q_EK = [0 for i in df['StreamFlow']]
            st.sidebar.header("Eckhardt filter parameters")
            alpha_ek = st.sidebar.number_input(label='alpha3', value=0.995, format="%lf", min_value=0.000,
                                            max_value=1.000, step=0.001, disabled=False, label_visibility="visible")
            BFI_max = st.sidebar.number_input(label='BFI_max', value=0.600, format="%lf", min_value=0.000,
                                           max_value=1.000, step=0.001, disabled=False, label_visibility="visible")

    if (option):
        #if (st.sidebar.button(label='Run')):
            for ifn in range(len(option)):
                if (option[ifn] == 'Chapman'):
                    Q_CH = Chapman_filter(df, alpha_ch)
                    results1 = pd.DataFrame({'Chapman': Q_CH})
                    results = pd.concat([results, results1], axis=1, join="inner")

                    with tab2:
                        ax.plot(df['Time'], Q_CH)
                        plt.axis([min(df['Time']), max(df['Time']), min(Q_CH), max(df['StreamFlow'])])

                if (option[ifn] == 'Lyne-Hollick'):
                    Q_LH = Lyne_Hollick_filter(df, alpha_lh)
                    results2 = pd.DataFrame({'Lyne-Hollick': Q_LH})
                    results = pd.concat([results, results2], axis=1, join="inner")

                    with tab2:
                        ax.plot(df['Time'], Q_LH)
                        plt.axis([min(df['Time']), max(df['Time']), min(Q_LH), max(df['StreamFlow'])])

                if (option[ifn] == 'Eckhardt'):
                    Q_EK = Eckhardt_filter(df, alpha_ek, BFI_max)
                    results3 = pd.DataFrame({'Eckhardt': Q_EK})
                    results = pd.concat([results, results3], axis=1, join="inner")

                    with tab2:
                        ax.plot(df['Time'], Q_EK)
                        plt.axis([min(df['Time']), max(df['Time']), min(Q_EK), max(df['StreamFlow'])])
            with tab2:
                RES_xlsx = to_excel(results)
                st.download_button(label='📥 Download Current Result',data=RES_xlsx,file_name='FilterResults.xlsx')
    with tab2:
        plt.xlabel('Time')
        plt.ylabel('Streamflow')
        #st.pyplot(fig)
        st.plotly_chart(fig,use_container_width=True)