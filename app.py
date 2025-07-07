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

# UI
st.set_page_config(page_title=texts["title"][language], layout="wide")
st.title(texts["title"][language])
st.markdown(texts["upload_markdown"][language])

# Upload на 3 фајла
inbound_file = st.sidebar.file_uploader(texts["upload_inbound"][language], type=["xlsx"])
outbound_file = st.sidebar.file_uploader(texts["upload_outbound"][language], type=["xlsx"])
catpro_file = st.sidebar.file_uploader(texts["upload_catpro"][language], type=["xlsx"])

# Ако сите фајлови се прикачени
if inbound_file and outbound_file and catpro_file:
    # Читање
    df_in = pd.read_excel(inbound_file)
    df_out = pd.read_excel(outbound_file)
    df_cat = pd.read_excel(catpro_file, header=1)  # Втор ред е хедер

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
        return number[-7:]  # земи ги последните 7 цифри за сигурност

    # Подготовка на inbound и outbound
    df_in = df_in[['Original Caller Number', 'Start Time', 'Source Trunk Name']].drop_duplicates(subset='Original Caller Number')
    df_in['Cleaned Number'] = df_in['Original Caller Number'].apply(clean_number)
    df_out['Cleaned Outbound'] = df_out['Callee Number'].apply(clean_number)

    # Catpro
    df_cat['Cleaned GSM'] = df_cat['GSM'].apply(clean_number)

    # Пропуштени: броеви што ги има во inbound, а не во outbound
    missed = df_in[~df_in['Cleaned Number'].isin(df_out['Cleaned Outbound'])]

    # Merge со Catpro по Cleaned Number
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

    final_table.rename(columns={
        'Original Caller Number': 'Phone',
        'Start Time': 'Date',
        'Source Trunk Name': 'Trunk',
        'Agent of insertion': 'Agent',
        'Answer': 'Last contact'
    }, inplace=True)

    # ✅ Debug preview ако има празни полиња
    st.write("⬇️ Првите 10 реда од финалната табела:")
    st.dataframe(final_table.head(10))

    # 📊 Приказ
    st.subheader(texts["missed_calls_subheader"][language].format(count=len(final_table)))
    st.dataframe(final_table)

    # 📥 Преземање како Excel
    output = BytesIO()
    final_table.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label=texts["download_button"][language],
        data=output,
        file_name="missed_calls_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Debug - споредба на броеви ако ништо не се поклопува
    if final_table['Agent'].isna().all():
        st.warning("⚠️ Ниеден број не се совпадна со Catpro податоците. Провери дали бројките се во ист формат.")
        st.write("Пример Cleaned Number од missed:", missed['Cleaned Number'].unique()[:10])
        st.write("Пример Cleaned GSM од Catpro:", df_cat['Cleaned GSM'].unique()[:10])

else:
    st.info(texts["info_upload_files"][language])
