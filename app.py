import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="📞 Пропуштени повици", layout="wide")
st.title("📞 Анализа на пропуштени повици")

st.markdown("⬆️ Прикачи ги Excel фајловите за дојдовни и појдовни повици")

# Sidebar – upload на фајлови
inbound_file = st.sidebar.file_uploader("📥 Inbound фајл (дојдовни повици)", type=["xlsx"])
outbound_file = st.sidebar.file_uploader("📤 Outbound фајл (појдовни повици)", type=["xlsx"])

if inbound_file and outbound_file:
    # Читање на Excel фајловите
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)

    # Земање на релевантни колони
    df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name']].drop_duplicates(subset='Original Caller Number')
    outbound_numbers = df_out['Callee Number']

    # Подобрена функција за чистење на броеви
    def clean_number(number):
        if pd.isna(number):
            return ""
        number = str(number)
        number = re.sub(r"[^\d]", "", number)  # Тргни сè што не е број
        if number.startswith("00389"):
            number = number[5:]
        elif number.startswith("389"):
            number = number[3:]
        return number.lstrip("0")  # Опционално: тргни водечка нула

    # Чистење на броевите
    df_in['Original Caller Number'] = df_in['Original Caller Number'].apply(clean_number)
    outbound_numbers_cleaned = outbound_numbers.apply(clean_number)

    # Филтрирање: броеви кои ве имаат повикано, а вие не сте ги повикале
    missed = df_in[~df_in['Original Caller Number'].isin(outbound_numbers_cleaned)]

    st.subheader(f"📉 Вкупно {len(missed)} пропуштени повици :")
    st.dataframe(missed)

    # Export to Excel (правилно со BytesIO)
    output = BytesIO()
    missed.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button("⬇️ Преземи како Excel", data=output, file_name="missed_calls.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("📂 Прикачи ги двата фајла за да започне анализата.")
