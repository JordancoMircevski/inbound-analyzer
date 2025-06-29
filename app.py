import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="📞 Call Analysis", layout="wide")

st.markdown("""
<style>
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f7f9fc;
}
h1 {
    color: #0B3D91;
    font-weight: 800;
    margin-bottom: 0;
}
h2 {
    color: #0B3D91;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
    font-weight: 700;
}
.upload-container {
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgb(11 61 145 / 0.15);
    margin-bottom: 40px;
    border: 1px solid #d1d9e6;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}
.stDownloadButton>button {
    background-color: #0B3D91;
    color: white;
    font-weight: 600;
    border-radius: 8px;
    padding: 0.6rem 1.4rem;
    border: none;
    transition: background-color 0.3s ease;
}
.stDownloadButton>button:hover {
    background-color: #08306b;
}
.dataframe table {
    width: 100% !important;
    border-collapse: separate !important;
    border-spacing: 0 10px !important;
    font-size: 14px !important;
}
.dataframe th {
    background-color: #0B3D91 !important;
    color: white !important;
    font-weight: 700 !important;
    padding: 10px !important;
    border: none !important;
    border-radius: 8px 8px 0 0 !important;
    text-align: center !important;
}
.dataframe td {
    background-color: white !important;
    padding: 10px !important;
    border: none !important;
    text-align: center !important;
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.1);
}
.dataframe tr {
    border-radius: 8px !important;
}
.sidebar .sidebar-content {
    background-color: #f0f4f8;
    border-radius: 12px;
    padding: 20px;
    margin-top: 20px;
    box-shadow: 0 4px 14px rgb(11 61 145 / 0.1);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>📞 Inbound Call Analysis</h1>", unsafe_allow_html=True)
st.markdown("---")

with st.container():
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("⬆️ Attach your Excel report (.xlsx)", type=["xlsx"])
    st.markdown('</div>', unsafe_allow_html=True)

if not uploaded_file:
    st.info("Please upload an Excel (.xlsx) file to start analysis.")
else:
    try:
        df = pd.read_excel(uploaded_file)
        first_col = df.columns[0]
        df = df[df[first_col].astype(str).str.lower() == 'sub_cdr']

        required_columns = [
            'Caller Number',
            'Callee Number',
            'Start Time',
            'Answer Time',
            'End Time',
            'Call Time',
            'Talk Time',
            'Source Trunk Name'
        ]

        found_cols = [col for col in required_columns if col in df.columns]
        missing_cols = [col for col in required_columns if col not in df.columns]

        if not found_cols:
            st.error("❌ Requested columns not found in the uploaded file.")
        else:
            df_filtered = df[found_cols]

            if missing_cols:
                st.warning(f"⚠️ Missing columns: {', '.join(missing_cols)}")

            df_filtered['Start Time'] = pd.to_datetime(df_filtered['Start Time'], errors='coerce')
            min_date = df_filtered['Start Time'].min().date()
            max_date = df_filtered['Start Time'].max().date()

            with st.sidebar:
                st.header("🔎 Filter Options")
                start_date, end_date = st.date_input(
                    "📅 Select period:",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )

                trunk_options = df_filtered['Source Trunk Name'].dropna().unique()
                selected_trunks = st.multiselect(
                    "🔀 Select Source Trunk(s):",
                    options=trunk_options,
                    default=trunk_options[:1]
                )

            df_filtered = df_filtered[
                (df_filtered['Start Time'] >= pd.to_datetime(start_date)) &
                (df_filtered['Start Time'] <= pd.to_datetime(end_date))
            ]

            df_filtered['Call Time'] = pd.to_numeric(df_filtered['Call Time'], errors='coerce').fillna(0)
            df_filtered = df_filtered[df_filtered['Call Time'] >= 5]

            df_filtered['Talk Time'] = pd.to_numeric(df_filtered['Talk Time'], errors='coerce').fillna(0)

            # --- Overview metrics ---
            st.markdown("## Overview")
            col1, col2, col3 = st.columns(3)

            total_calls_all = len(df_filtered)
            total_talk_all = round(df_filtered['Talk Time'].sum() / 60, 2)
            total_call_all = round(df_filtered['Call Time'].sum() / 60, 2)

            col1.metric("☎️ Total Calls", total_calls_all)
            col2.metric("🗣️ Total Talk Time (min)", total_talk_all)
            col3.metric("⏳ Total Wait Time (min)", total_call_all)

            # --- Филтрирана табела со сите повици ---
            st.markdown("## 📋 Filtered Call Data")
            st.dataframe(df_filtered, use_container_width=True)

            # --- Анализа по избрани trunk-ови ---
            df_trunk = df_filtered[df_filtered['Source Trunk Name'].isin(selected_trunks)]

            if df_trunk.empty:
                st.warning("⚠️ No data for the selected trunk(s) and period.")
            else:
                df_trunk['Talk Time'] = pd.to_numeric(df_trunk['Talk Time'], errors='coerce').fillna(0)
                df_trunk['Call Time'] = pd.to_numeric(df_trunk['Call Time'], errors='coerce').fillna(0)
                df_trunk = df_trunk[df_trunk['Call Time'] >= 5]

                agent_stats = df_trunk.groupby('Callee Number').agg({
                    'Talk Time': 'sum',
                    'Call Time': 'sum',
                    'Start Time': 'count'
                }).reset_index().rename(columns={
                    'Callee Number': 'Agent',
                    'Start Time': 'Number of Calls'
                })

                agent_stats['Talk Time (min)'] = round(agent_stats['Talk Time'] / 60, 2)
                agent_stats['Call Time (min)'] = round(agent_stats['Call Time'] / 60, 2)

                total_calls = agent_stats['Number of Calls'].sum()
                total_talk = agent_stats['Talk Time (min)'].sum()

                agent_stats['% Talk Time'] = agent_stats['Talk Time (min)'].apply(lambda x: round((x / total_talk) * 100, 2) if total_talk > 0 else 0)

                st.markdown("## Agent Analysis")
                st.dataframe(agent_stats[['Agent', 'Talk Time (min)', 'Call Time (min)', 'Number of Calls', '% Talk Time']], use_container_width=True)

                st.markdown("## Selected Trunks Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("☎️ Total Calls", total_calls)
                col2.metric("🗣️ Total Talk Time (min)", round(total_talk, 2))
                col3.metric("⏳ Total Wait Time (min)", round(agent_stats['Call Time (min)'].sum(), 2))

                def to_excel(data):
                    output = BytesIO()
                    data.to_excel(output, index=False)
                    output.seek(0)
                    return output

                st.download_button(
                    label="⬇️ Download Filtered Data as Excel",
                    data=to_excel(df_trunk),
                    file_name="filtered_call_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"❌ Error processing the file: {e}")
