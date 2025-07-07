import streamlit as st
import pandas as pd
import re
from io import BytesIO

# UI јазик
language = st.sidebar.selectbox("Јазик / Language", ["Македонски", "English"])

texts = {
    "title": {
        "Македонски": "📞 Проверка на внесени пропуштени повици",
        "English": "📞 Missed Calls System Check"
    },
    "upload": {
        "Македонски": "⬆️ Прикачи ги Excel фајловите: Inbound, Outbound, Catpro",
        "English": "⬆️ Upload Inbound, Outbound, and Catpro Excel files"
    },
    "inbound": {"Македонски": "📥 Inbound", "English": "📥 Inbound"},
    "outbound": {"Македонски": "📤 Outbound", "English": "📤 Outbound"},
    "catpro": {"Македонски": "📊 Catpro", "English": "📊 Catpro"},
    "count": {
        "Македонски": "📉 Вкупно {count} пропуштени броеви:",
        "English": "📉 Total {count} missed numbers:"
    },
    "download": {"Македонски": "⬇️ Преземи Excel", "English": "⬇️ Download Excel"},
    "info": {
        "Македонски": "📂 Прикачи ги сите три фајла за да започне анализата.",
        "English": "📂 Please upload all three files to start the analysis."
    }
}

st.set_page_config(page_title=texts["title"][language], layout="wide")
st.title(texts["title"][language])
st.markdown(texts["upload"][language])

inbound_file = st.sidebar.file_uploader(texts["inbound"][language], type=["xlsx"])
outbound_file = st.sidebar.file_uploader(texts["outbound"][language], type=["xlsx"])
catpro_file = st.sidebar.file_uploader(texts["catpro"][language], type=["xlsx"])

# Чистење број
def clean_number(number):
    if pd.isna(number):
        return ""
    number = str(number)
    number = re.sub(r"[^\d]", "", number)
    if number.startswith("00389"):
        number = number[5:]
    elif number.startswith("389"):
        number = number[3:]
    elif number.startswith("0"):
        number = number[1:]
    return number

if inbound_file and outbound_file and catpro_file:
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)
    df_cat = pd.read_excel(catpro_file, header=1)

    # Чистење броеви
    df_in['Cleaned Number'] = df_in['Original Caller Number'].apply(clean_number)
    df_out['Cleaned Number'] = df_out['Callee Number'].apply(clean_number)
    df_cat['Cleaned GSM'] = df_cat['GSM'].apply(clean_number)

    # Пропуштени броеви
    missed = df_in[~df_in['Cleaned Number'].isin(df_out['Cleaned Number'])].copy()

    # Проверка дали е внесен
    missed['Status'] = missed['Cleaned Number'].apply(
        lambda num: "✅ Внесен во систем" if num in df_cat['Cleaned GSM'].values else "❌ НЕ е внесен"
    )

    # Финална табела
    final_table = missed[['Original Caller Number', 'Start Time', 'Source Trunk Name', 'Status']].rename(columns={
        'Original Caller Number': 'Phone',
        'Start Time': 'Date',
        'Source Trunk Name': 'Trunk'
    })

    # Приказ
    st.subheader(texts["count"][language].format(count=len(final_table)))
    st.dataframe(final_table)

    # Преземање
    output = BytesIO()
    final_table.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label=texts["download"][language],
        data=output,
        file_name="missed_calls_status.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info(texts["info"][language])
