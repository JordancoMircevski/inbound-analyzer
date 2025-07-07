import streamlit as st
import pandas as pd
import re
from io import BytesIO

# UI јазик
language = st.sidebar.selectbox("Јазик / Language", ["Македонски", "English"])

texts = {
    "title": {
        "Македонски": "📞 Проверка на пропуштени повици",
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
    },
    "filter_checkbox": {
        "Македонски": "🔍 Прикажи само броеви што НЕ се внесени",
        "English": "🔍 Show only numbers that are NOT entered"
    }
}

st.set_page_config(page_title=texts["title"][language], layout="wide")
st.title(texts["title"][language])
st.markdown(texts["upload"][language])

# Функција за чистење броеви без префикс 389 и без водечко 0
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

if st.sidebar.file_uploader(texts["inbound"][language], type=["xlsx"]) and \
   st.sidebar.file_uploader(texts["outbound"][language], type=["xlsx"]) and \
   st.sidebar.file_uploader(texts["catpro"][language], type=["xlsx"]):

    # Ги земаме фајловите од upload (повторно за да ги користиме подоцна)
    inbound_file = st.sidebar.file_uploader(texts["inbound"][language], type=["xlsx"])
    outbound_file = st.sidebar.file_uploader(texts["outbound"][language], type=["xlsx"])
    catpro_file = st.sidebar.file_uploader(texts["catpro"][language], type=["xlsx"])

    if inbound_file and outbound_file and catpro_file:
        df_in = pd.read_excel(inbound_file)
        df_out = pd.read_excel(outbound_file)
        df_cat = pd.read_excel(catpro_file, header=1)

        # Чистење броеви
        df_in['Cleaned Number'] = df_in['Original Caller Number'].apply(clean_number)
        df_in = df_in.sort_values('Start Time').drop_duplicates('Cleaned Number', keep='last')

        df_out['Cleaned Number'] = df_out['Callee Number'].apply(clean_number)

        df_cat = df_cat[df_cat['GSM'].notna()]
        df_cat['Cleaned GSM'] = df_cat['GSM'].apply(clean_number)
        valid_gsm_set = set(df_cat['Cleaned GSM'].dropna())

        if 'Agent of insertion' in df_cat.columns:
            gsm_to_agent = df_cat.set_index('Cleaned GSM')['Agent of insertion'].to_dict()
        else:
            gsm_to_agent = {}

        missed = df_in[~df_in['Cleaned Number'].isin(df_out['Cleaned Number'])].copy()

        missed['Status'] = missed['Cleaned Number'].apply(
            lambda num: "✅ Внесен во систем" if num in valid_gsm_set else "❌ НЕ е внесен"
        )
        missed['Agent'] = missed['Cleaned Number'].apply(
            lambda num: gsm_to_agent.get(num, "") if num in valid_gsm_set else ""
        )

        final_table = missed[[
            'Cleaned Number',
            'Start Time',
            'Source Trunk Name',
            'Status',
            'Agent'
        ]].rename(columns={
            'Cleaned Number': 'Phone',
            'Start Time': 'Date',
            'Source Trunk Name': 'Trunk'
        })

        # Прикажи броеви БЕЗ 0 или 389 - чисти броеви
        # (веќе се чистат во clean_number)

        show_only_missing = st.checkbox(texts["filter_checkbox"][language])
        filtered_table = final_table[final_table['Status'] == "❌ НЕ е внесен"] if show_only_missing else final_table

        st.subheader(texts["count"][language].format(count=len(filtered_table)))
        st.dataframe(filtered_table)

        output = BytesIO()
        filtered_table.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label=texts["download"][language],
            data=output,
            file_name="missed_calls_status.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info(texts["info"][language])
