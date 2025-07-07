import streamlit as st
import pandas as pd
from io import BytesIO
import re

# Јазик
language = st.sidebar.selectbox("Select language / Избери јазик", ["Македонски", "English"])
texts = {
    "title": {
        "Македонски": "📞 Анализа на пропуштени повици",
        "English": "📞 Missed Calls Analysis"
    },
    "upload_markdown": {
        "Македонски": "⬆️ Прикачи ги трите Excel фајлови (дојдовни, појдовни, Catpro)",
        "English": "⬆️ Upload all three Excel files (inbound, outbound, Catpro)"
    },
    "upload_inbound": {
        "Македонски": "📥 Inbound фајл (дојдовни повици)",
        "English": "📥 Inbound file (incoming calls)"
    },
    "upload_outbound": {
        "Македонски": "📤 Outbound фајл (појдовни повици)",
        "English": "📤 Outbound file (outgoing calls)"
    },
    "upload_catpro": {
        "Македонски": "📊 Catpro извештај",
        "English": "📊 Catpro report"
    },
    "missed_calls_subheader": {
        "Македонски": "📉 Вкупно {count} пропуштени повици :",
        "English": "📉 Total {count} missed calls:"
    },
    "download_button": {
        "Македонски": "⬇️ Преземи финална табела",
        "English": "⬇️ Download final table"
    },
    "info_upload_files": {
        "Македонски": "📂 Прикачи ги сите три фајла за да започне анализата.",
        "English": "📂 Please upload all three files to start analysis."
    }
}

st.set_page_config(page_title=texts["title"][language], layout="wide")
st.title(texts["title"][language])
st.markdown(texts["upload_markdown"][language])

# Upload
inbound_file = st.sidebar.file_uploader(texts["upload_inbound"][language], type=["xlsx"])
outbound_file = st.sidebar.file_uploader(texts["upload_outbound"][language], type=["xlsx"])
catpro_file = st.sidebar.file_uploader(texts["upload_catpro"][language], type=["xlsx"])

if inbound_file and outbound_file and catpro_file:

    # Читање на Excel-ите
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)
    df_cat = pd.read_excel(catpro_file, header=1)

    # Чистење броеви
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

    # Inbound
    df_in['Cleaned Number'] = df_in['Original Caller Number'].apply(clean_number)
    df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name', 'Cleaned Number']].drop_duplicates(subset='Cleaned Number')

    # Outbound
    df_out['Cleaned Number'] = df_out['Callee Number'].apply(clean_number)

    # Catpro
    df_cat['Cleaned GSM'] = df_cat['GSM'].apply(clean_number)

    # Филтрирање: повици што немаат повратен појдовен
    missed = df_in[~df_in['Cleaned Number'].isin(df_out['Cleaned Number'])]

    # Спојување со Catpro
    final = pd.merge(
        missed,
        df_cat[['Cleaned GSM', 'Agent of insertion', 'Answer', 'GSM']],
        left_on='Cleaned Number',
        right_on='Cleaned GSM',
        how='left'
    )

    # Финална табела
    final_table = final[[
        'Original Caller Number',
        'Start Time',
        'Source Trunk Name',
        'GSM',
        'Agent of insertion',
        'Answer'
    ]]

    final_table = final_table.rename(columns={
        'Original Caller Number': 'Phone',
        'Start Time': 'Date',
        'Source Trunk Name': 'Trunk',
        'Agent of insertion': 'Agent',
        'Answer': 'Last contact'
    })

    # Приказ
    st.subheader(texts["missed_calls_subheader"][language].format(count=len(final_table)))
    st.dataframe(final_table)

    # Export
    output = BytesIO()
    final_table.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label=texts["download_button"][language],
        data=output,
        file_name="missed_calls_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info(texts["info_upload_files"][language])
