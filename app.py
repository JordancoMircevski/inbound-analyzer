import streamlit as st
import pandas as pd
from io import BytesIO
import re

# Избор на јазик
language = st.sidebar.selectbox("Select language / Избери јазик", options=["Македонски", "English"])

# Речник со преводи
texts = {
    "title": {
        "Македонски": "📞 Анализа на пропуштени повици",
        "English": "📞 Missed Calls Analysis"
    },
    "upload_markdown": {
        "Македонски": "⬆️ Прикачи ги Excel фајловите за дојдовни и појдовни повици",
        "English": "⬆️ Upload Excel files for inbound and outbound calls"
    },
    "upload_inbound": {
        "Македонски": "📥 Inbound фајл (дојдовни повици)",
        "English": "📥 Inbound file (incoming calls)"
    },
    "upload_outbound": {
        "Македонски": "📤 Outbound фајл (појдовни повици)",
        "English": "📤 Outbound file (outgoing calls)"
    },
    "missed_calls_subheader": {
        "Македонски": "📉 Вкупно {count} пропуштени повици :",
        "English": "📉 Total {count} missed calls:"
    },
    "download_button": {
        "Македонски": "⬇️ Преземи како Excel",
        "English": "⬇️ Download as Excel"
    },
    "info_upload_files": {
        "Македонски": "📂 Прикачи ги двата фајла за да започне анализата.",
        "English": "📂 Please upload both files to start analysis."
    }
}

st.set_page_config(page_title=texts["title"][language], layout="wide")
st.title(texts["title"][language])
st.markdown(texts["upload_markdown"][language])

# Sidebar – upload на фајлови
inbound_file = st.sidebar.file_uploader(texts["upload_inbound"][language], type=["xlsx"])
outbound_file = st.sidebar.file_uploader(texts["upload_outbound"][language], type=["xlsx"])

if inbound_file and outbound_file:
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)

    df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name']].drop_duplicates(subset='Original Caller Number')
    outbound_numbers = df_out['Callee Number']

    def clean_number(number):
        if pd.isna(number):
            return ""
        number = str(number)
        number = re.sub(r"[^\d]", "", number)
        if number.startswith("00389"):
            number = number[5:]
        elif number.startswith("389"):
            number = number[3:]
        return number.lstrip("0")

    df_in['Original Caller Number'] = df_in['Original Caller Number'].apply(clean_number)
    outbound_numbers_cleaned = outbound_numbers.apply(clean_number)

    missed = df_in[~df_in['Original Caller Number'].isin(outbound_numbers_cleaned)]

    st.subheader(texts["missed_calls_subheader"][language].format(count=len(missed)))
    st.dataframe(missed)

    output = BytesIO()
    missed.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        texts["download_button"][language],
        data=output,
        file_name="missed_calls.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info(texts["info_upload_files"][language])
