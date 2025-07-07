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
    },
    "test_number": {
        "Македонски": "Тестиран број за внесен статус:",
        "English": "Test number for insertion status:"
    }
}

st.set_page_config(page_title=texts["title"][language], layout="wide")
st.title(texts["title"][language])
st.markdown(texts["upload"][language])

# Upload фајлови
inbound_file = st.sidebar.file_uploader(texts["inbound"][language], type=["xlsx"])
outbound_file = st.sidebar.file_uploader(texts["outbound"][language], type=["xlsx"])
catpro_file = st.sidebar.file_uploader(texts["catpro"][language], type=["xlsx"])

# Функција за чистење броеви
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
    # Вчитување на фајлови
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)
    df_cat = pd.read_excel(catpro_file, header=1)

    # 1. Чистење inbound броеви и групирање по последен повик
    df_in['Cleaned Number'] = df_in['Original Caller Number'].apply(clean_number)
    df_in = df_in.sort_values('Start Time').drop_duplicates('Cleaned Number', keep='last')

    # 2. Чистење outbound броеви
    df_out['Cleaned Number'] = df_out['Callee Number'].apply(clean_number)

    # 3. Чистење Catpro (GSM и агент)
    df_cat = df_cat[df_cat['GSM'].notna()]  # Отстрани редови без GSM
    df_cat['Cleaned GSM'] = df_cat['GSM'].apply(clean_number)
    valid_gsm_set = set(df_cat['Cleaned GSM'].dropna())

    gsm_to_agent = df_cat.set_index('Cleaned GSM')['Agent of insertion'].to_dict()

    # 4. Пропуштени повици = inbound броеви што ги нема во outbound
    missed = df_in[~df_in['Cleaned Number'].isin(df_out['Cleaned Number'])].copy()

    # 5. Проверка дали бројот е внесен во систем (дали постои во Catpro)
    missed['Status'] = missed['Cleaned Number'].apply(
        lambda num: "✅ Внесен во систем" if num in valid_gsm_set else "❌ НЕ е внесен"
    )
    missed['Agent'] = missed['Cleaned Number'].apply(
        lambda num: gsm_to_agent.get(num, "") if num in valid_gsm_set else ""
    )

    # 6. Финална табела
    final_table = missed[[
        'Original Caller Number',
        'Start Time',
        'Source Trunk Name',
        'Status',
        'Agent'
    ]].rename(columns={
        'Original Caller Number': 'Phone',
        'Start Time': 'Date',
        'Source Trunk Name': 'Trunk'
    })

    # Приказ во Streamlit
    st.subheader(texts["count"][language].format(count=len(final_table)))
    st.dataframe(final_table)

    # Export во Excel
    output = BytesIO()
    final_table.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label=texts["download"][language],
        data=output,
        file_name="missed_calls_status.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Тестирање на фиксен број за внесен статус ---
    test_number_raw = st.text_input(texts["test_number"][language], value="070123456")
    test_number = clean_number(test_number_raw)

    if st.button("Провери статус"):
        if test_number in valid_gsm_set:
            agent_name = gsm_to_agent.get(test_number, "Агентот не е пронајден")
            st.success(f"Бројот {test_number_raw} Е ВНЕСЕН во систем.\nАгент: {agent_name}")
        else:
            st.error(f"Бројот {test_number_raw} НЕ Е внесен во систем.")

else:
    st.info(texts["info"][language])
