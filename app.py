import streamlit as st
import pandas as pd
from io import BytesIO

# Sidebar - избор на јазик
language = st.sidebar.selectbox("Select language / Избери јазик", ["Македонски", "English"])

# Текстови за Македонски
texts_mk = {
    "title": "📞 Анализа на пропуштени повици",
    "upload_instruction": "⬆️ Прикачи два Excel фајла: inbound (дојдовни) и outbound (појдовни)",
    "inbound_upload": "📥 Inbound фајл (дојдовни повици)",
    "outbound_upload": "📤 Outbound фајл (појдовни повици)",
    "missed_calls": "📉 Вкупно {count} пропуштени повици (неповикани назад):",
    "download_button": "⬇️ Преземи Excel со пропуштени повици",
    "upload_info": "📂 Прикачи ги двата фајла за да започне анализата."
}

# Текстови за Англиски
texts_en = {
    "title": "📞 Missed Calls Analysis",
    "upload_instruction": "⬆️ Upload two Excel files: inbound and outbound calls",
    "inbound_upload": "📥 Inbound file (received calls)",
    "outbound_upload": "📤 Outbound file (made calls)",
    "missed_calls": "📉 Total {count} missed calls (not called back):",
    "download_button": "⬇️ Download Excel with missed calls",
    "upload_info": "📂 Please upload both files to start the analysis."
}

texts = texts_mk if language == "Македонски" else texts_en

def clean_number(number):
    if pd.isna(number):
        return ""
    number = str(number).replace(" ", "").replace("-", "").strip()
    if number.startswith("+389"):
        number = number[4:]
    elif number.startswith("389"):
        number = number[3:]
    if number.startswith("0"):
        number = number[1:]
    return number

st.set_page_config(page_title=texts["title"], layout="wide")
st.title(texts["title"])
st.markdown(texts["upload_instruction"])

# Sidebar file uploaders
inbound_file = st.sidebar.file_uploader(texts["inbound_upload"], type=["xlsx"])
outbound_file = st.sidebar.file_uploader(texts["outbound_upload"], type=["xlsx"])

if inbound_file and outbound_file:
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)

    df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name']].drop_duplicates(subset='Original Caller Number')
    outbound_numbers = df_out['Callee Number']

    df_in['Original Caller Number'] = df_in['Original Caller Number'].apply(clean_number)
    outbound_numbers_cleaned = outbound_numbers.apply(clean_number)

    missed = df_in[~df_in['Original Caller Number'].isin(outbound_numbers_cleaned)]

    st.subheader(texts["missed_calls"].format(count=len(missed)))
    st.dataframe(missed)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        missed.to_excel(writer, index=False)
    buffer.seek(0)

    st.download_button(
        label=texts["download_button"],
        data=buffer,
        file_name="missed_calls.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info(texts["upload_info"])
