import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="📞 Анализа на пропуштени повици", layout="wide")
st.title("📞 Анализа на пропуштениповици")

st.markdown("⬆️ Прикачи два Excel фајла: inbound (дојдовни) и outbound (појдовни)")

# Sidebar за фајлови
inbound_file = st.sidebar.file_uploader("📥 Inbound фајл (дојдовни повици)", type=["xlsx"])
outbound_file = st.sidebar.file_uploader("📤 Outbound фајл (појдовни повици)", type=["xlsx"])

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

if inbound_file and outbound_file:
    # Читање на податоците
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)

    # Извлекување на колони од интерес
    df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name']].drop_duplicates(subset='Original Caller Number')
    outbound_numbers = df_out['Callee Number']

    # Чистење на броевите
    df_in['Original Caller Number'] = df_in['Original Caller Number'].apply(clean_number)
    outbound_numbers_cleaned = outbound_numbers.apply(clean_number)

    # Филтрирање: кои броеви не сте ги повикале назад
    missed = df_in[~df_in['Original Caller Number'].isin(outbound_numbers_cleaned)]

    st.subheader(f"📉 Вкупно {len(missed)} пропуштени повици (неповикани назад):")
    st.dataframe(missed)

    # Подготви Excel за преземање
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        missed.to_excel(writer, index=False)
    buffer.seek(0)

    st.download_button(
        label="⬇️ Преземи Excel со пропуштени повици",
        data=buffer,
        file_name="missed_calls.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("📂 Прикачи ги двата фајла за да започне анализата.")
