import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="📞 Пропуштени повици", layout="wide")
st.title("📞 Анализа на пропуштени (неповратени) повици")

st.markdown("⬆️ Прикачи ги Excel фајловите за дојдовни и појдовни повици")

# Sidebar – upload на фајлови
inbound_file = st.sidebar.file_uploader("📥 Inbound фајл (дојдовни повици)", type=["xlsx"])
outbound_file = st.sidebar.file_uploader("📤 Outbound фајл (појдовни повици)", type=["xlsx"])

if inbound_file and outbound_file:
    # Читање на Excel фајловите
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)

    # Проверка дали постојат потребните колони
    required_inbound_cols = {'Original Caller Number', 'Start Time', 'Source Trunk Name'}
    required_outbound_cols = {'Callee Number'}

    if not required_inbound_cols.issubset(df_in.columns):
        st.error("❌ Inbound фајлот ги нема потребните колони.")
    elif not required_outbound_cols.issubset(df_out.columns):
        st.error("❌ Outbound фајлот ги нема потребните колони.")
    else:
        # Земање на релевантни колони и чистење
        df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name']].drop_duplicates(subset='Original Caller Number')
        outbound_numbers = df_out['Callee Number']

        # Напредна функција за чистење на броеви
        def clean_number(number):
            if pd.isna(number):
                return ""
            number = str(number)
            number = re.sub(r"[^\d]", "", number)  # Тргни сè што не е бројка
            if number.startswith("00389"):
                number = number[5:]
            elif number.startswith("389"):
                number = number[3:]
            elif number.startswith("07") and len(number) == 9:
                return number  # Веќе е чист број
            return number.lstrip("0")  # Тргни водечки нули ако има

        # Чистење на броевите
        df_in['Cleaned Number'] = df_in['Original Caller Number'].apply(clean_number)
        outbound_numbers_cleaned = outbound_numbers.apply(clean_number)

        # Филтрирање: пропуштени (неповратени) броеви
        missed = df_in[~df_in['Cleaned Number'].isin(outbound_numbers_cleaned)]

        # Приказ
        st.subheader(f"📉 Вкупно {len(missed)} пропуштени повици (неповратени):")
        st.dataframe(missed[['Original Caller Number', 'Start Time', 'Source Trunk Name']])

        # Преземање како Excel
        output = BytesIO()
        missed[['Original Caller Number', 'Start Time', 'Source Trunk Name']].to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="⬇️ Преземи како Excel",
            data=output,
            file_name="missed_calls.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("📂 Прикачи ги двата фајла за да започне анализата.")
