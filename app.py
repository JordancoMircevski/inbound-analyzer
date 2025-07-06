import streamlit as st
import pandas as pd

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

    # Земање на релевантни колони
    df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name']].drop_duplicates(subset='Original Caller Number')
    outbound_numbers = df_out['Callee Number']

    # Функција за чистење на броеви (само трга 389 или +389)
    def clean_number(number):
        if pd.isna(number):
            return ""
        number = str(number).replace(" ", "").replace("-", "").strip()
        if number.startswith("+389"):
            number = number[4:]
        elif number.startswith("389"):
            number = number[3:]
        return number

    # Чистење на броевите
    df_in['Original Caller Number'] = df_in['Original Caller Number'].apply(clean_number)
    outbound_numbers_cleaned = outbound_numbers.apply(clean_number)

    # Филтрирање: броеви кои ве имаат повикано, а вие не сте ги повикале
    missed = df_in[~df_in['Original Caller Number'].isin(outbound_numbers_cleaned)]

    st.subheader(f"📉 Вкупно {len(missed)} пропуштени повици (неповратени):")
    st.dataframe(missed)

    # Export to Excel
    download = missed.to_excel(index=False, engine='openpyxl')
    st.download_button("⬇️ Преземи како Excel", download, file_name="missed_calls.xlsx")

else:
    st.info("📂 Прикачи ги двата фајла за да започне анализата.") ovaa analiza misalm deka e tocna  