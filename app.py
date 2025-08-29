import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="C-PRO Multi Page App", layout="wide")

# Sidebar untuk navigasi halaman
page = st.sidebar.radio(
    "📌 Pilih Halaman",
    ["📊 Monitoring Setup User", "🎯 Random Sampling dari Excel", "📈 Komparasi Progress", "🗂 Monitoring WP Progress"]
)

# ====== PAGE 1: MONITORING SETUP USER ======
if page == "📊 Monitoring Setup User":
    st.title("📊 Monitoring Setup User per Branch & LOB")

    # Upload file pertama (data branch)
    file1 = st.file_uploader("Upload File BRANCHLIST (BRANCH_ID, BRANCH_NAME, AREA)", type=["xlsx"])
    # Upload file kedua (data realisasi)
    file2 = st.file_uploader("Upload File Realisasi Setup (BRANCH_ID, LOB, PIC)", type=["xlsx"])

    # Hardcode daftar LOB
    lob_list = [
        "COLLATERAL", "CR 1", "CR 2", "FINANCE, ACCOUNTING & TAX",
        "CREDIT", "CRM", "GS, EHS & IT", "HC", "IWM", "MFI",
        "MMU", "MPF", "NMC", "UFI"
    ]

    if file1 and file2:
        df_branch = pd.read_excel(file1)
        df_real = pd.read_excel(file2)

        # Pastikan kolom sesuai format
        df_branch.columns = df_branch.columns.str.strip()
        df_real.columns = df_real.columns.str.strip()

        # Expand branch × LOB
        df_expected = pd.DataFrame([
            {"BRANCH_ID": row["BRANCH_ID"], "BRANCH_NAME": row["BRANCH_NAME"], "AREA": row["AREA"], "LINE_OF_BUSINESS": lob}
            for _, row in df_branch.iterrows()
            for lob in lob_list
        ])

        # Join dengan data realisasi
        df_merge = pd.merge(
            df_expected,
            df_real[["BRANCH_ID", "LINE_OF_BUSINESS", "EMPLOYEE_NUMBER"]],
            on=["BRANCH_ID", "LINE_OF_BUSINESS"],
            how="left"
        )

        # Tentukan status
        df_merge["Status"] = df_merge["EMPLOYEE_NUMBER"].apply(lambda x: "Sudah Setup" if pd.notna(x) else "Belum Setup")

        # Filter UI - dibuat lebih rapi dengan columns
        with st.expander("🔍 Filter Data", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                branch_filter = st.multiselect(
                    "🏢 Filter Branch",
                    options=sorted(df_merge["BRANCH_NAME"].unique()),
                    placeholder="Pilih Branch..."
                )
            with col2:
                AREA_filter = st.multiselect(
                    "🌍 Filter AREA",
                    options=sorted(df_merge["AREA"].unique()),
                    placeholder="Pilih AREA..."
                )
            with col3:
                lob_filter = st.multiselect(
                    "📂 Filter LOB",
                    options=lob_list,
                    placeholder="Pilih LOB..."
                )
            with col4:
                setup_filter = st.multiselect(
                    "Filter Status",
                    options=sorted(df_merge["Status"].unique()),
                    placeholder="Pilih Status..."
                )

        # Apply filters
        filtered_df = df_merge.copy()
        if branch_filter:
            filtered_df = filtered_df[filtered_df["BRANCH_NAME"].isin(branch_filter)]
        if AREA_filter:
            filtered_df = filtered_df[filtered_df["AREA"].isin(AREA_filter)]
        if lob_filter:
            filtered_df = filtered_df[filtered_df["LINE_OF_BUSINESS"].isin(lob_filter)]
        if setup_filter:
            filtered_df = filtered_df[filtered_df["Status"].isin(setup_filter)]

        # Summary untuk plot
        AREA_summary = filtered_df.groupby(["AREA", "Status"]).size().reset_index(name="Count")

        # Grafik bar stacked
        fig_bar = px.bar(
            AREA_summary,
            x="AREA",
            y="Count",
            color="Status",
            orientation="v",
            barmode="stack",
            title="📍 Grafik Status per AREA (Stacked)",
            labels={"Count": "Jumlah", "AREA": "Area"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("📋 Tabel Data Hasil Setup")
        st.dataframe(filtered_df, use_container_width=True)

        # Grafik Pie total status
        status_summary = filtered_df["Status"].value_counts().reset_index()
        status_summary.columns = ["Status", "Count"]

        fig_pie = px.pie(
            status_summary,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map={"Sudah Setup": "#00CC22", "Belum Setup": "#EF3B3B"},
            hole=0.4,
            title="Distribusi Status Setup Keseluruhan"
        )
        fig_pie.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

        # Export ke Excel
        import io
        def to_excel(filtered_df, AREA_summary, status_summary):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                filtered_df.to_excel(writer, index=False, sheet_name="Filtered Data")
                AREA_summary.to_excel(writer, index=False, sheet_name="Summary Area")
                status_summary.to_excel(writer, index=False, sheet_name="Summary Status")
            return output.getvalue()

        excel_export = to_excel(filtered_df, AREA_summary, status_summary)
        today_str = datetime.now().strftime("%d%b%Y")
        st.download_button(
            label="📥 Download Hasil Monitoring (.xlsx)",
            data=excel_export,
            file_name=f"hasil_monitoring{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ====== PAGE 2: RANDOM SAMPLING ======
elif page == "🎯 Random Sampling dari Excel":
    st.subheader("📥 Random Sampling dari Excel")
    st.markdown("""Upload file Excel yang ingin Anda gunakan untuk **Random Sampling** berdasarkan kolom yang dipilih.""")

    uploaded_file = st.file_uploader("📝 Silakan upload file Excel kamu:", type=["xlsx"])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.success("✅ File berhasil dimuat!")
            st.subheader("🔍 Pratinjau Data")
            st.dataframe(df.head())

            # Pilih kolom untuk grouping (boleh lebih dari 1)
            group_cols = st.multiselect("🧩 Pilih kolom pengelompokan (group by):", options=df.columns)

            # Pilih jumlah sample per grup
            n_sample = st.slider("🎯 Jumlah sample per grup", min_value=1, max_value=100, value=6)

            if group_cols and st.button("🚀 Jalankan Random Sampling"):
                sampled_df = (
                    df.groupby(group_cols, group_keys=False)
                      .apply(lambda x: x.sample(n=min(n_sample, len(x)), random_state=42))
                      .reset_index(drop=True)
                )

                st.subheader("📄 Hasil Random Sampling")
                st.dataframe(sampled_df)

                @st.cache_data
                def convert_df_to_excel(df):
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False, sheet_name='Sampled')
                    return output.getvalue()
                
                today_str = datetime.now().strftime("%d%b%Y")
                excel_data = convert_df_to_excel(sampled_df)
                st.download_button(
                    label="📥 Download Hasil Sampling (.xlsx)",
                    data=excel_data,
                    file_name=f"hasil_sampling{today_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"❌ Gagal membaca file: {e}")
    else:
        st.info("📝 Silakan upload file Excel terlebih dahulu.")


# ====== PAGE 3: KOMPARASI PROGRESS ======
elif page == "📈 Komparasi Progress":
    st.title("📈 Komparasi Progress")

    col1, col2 = st.columns(2)
    with col1:
        file_before = st.file_uploader("Upload Excel Hari ke-1 (Before)", type=["xlsx"])
    with col2:
        file_after = st.file_uploader("Upload Excel Hari ke-2 (After)", type=["xlsx"])

    if file_before and file_after:
        # Baca semua data
        df_before_all = pd.read_excel(file_before)
        df_after_all = pd.read_excel(file_after)

        # Filter hanya yang Sudah Setup
        df_before = df_before_all[df_before_all["Status"] == "Sudah Setup"]
        df_after = df_after_all[df_after_all["Status"] == "Sudah Setup"]

        # Hitung persentase
        persen_before = len(df_before) / len(df_before_all) * 100 if len(df_before_all) > 0 else 0
        persen_after = len(df_after) / len(df_after_all) * 100 if len(df_after_all) > 0 else 0

        # Buat dataframe perbandingan
        df_compare = pd.DataFrame({
            "Waktu": ["Sebelum", "Sesudah"],
            "Persentase": [persen_before, persen_after]
        })
        df_compare["Perubahan"] = df_compare["Persentase"].diff()

        # Plot horizontal bar (grouped)
        fig = px.bar(
            df_compare,
            y=["Sudah Setup"] * len(df_compare),  # hanya 1 kategori
            x="Persentase",
            color="Waktu",
            orientation="h",
            barmode="group",
            text="Persentase",
            title="📊 Komparasi Progress Sudah Setup"
        )

        # Tambah anotasi perubahan
        perubahan = persen_after - persen_before
        fig.add_annotation(
            x=persen_after + 1,
            y="Sudah Setup",
            text=f"{perubahan:+.2f}%",
            showarrow=False,
            font=dict(color="yellow", size=12)
        )

        fig.update_traces(texttemplate='%{text:.2f}%', textposition="inside")
        fig.update_layout(xaxis_title="Persentase (%)", yaxis_title="Status")

        # Tampilkan chart
        st.plotly_chart(fig, use_container_width=True)

        # Tampilkan tabel ringkas
        st.dataframe(df_compare)

# ====== PAGE 4: MONITORING WP PROGRESS ======
elif page == "🗂 Monitoring WP Progress":
    st.title("🗂 WPProgress Reporting")

    # Upload files
    branch_file = st.file_uploader("Upload Branch Excel", type=["xlsx"])
    wp_file = st.file_uploader("Upload WP Excel", type=["xlsx"])
    progress_file = st.file_uploader("Upload WPProgress Excel", type=["xlsx"])

    if branch_file and wp_file and progress_file:
        # Load data
        df_branch = pd.read_excel(branch_file)
        df_wp = pd.read_excel(wp_file)
        df_progress = pd.read_excel(progress_file)

        st.subheader("Preview Data")
        st.write("Branch", df_branch.head())
        st.write("WP", df_wp.head())
        st.write("WPProgress", df_progress.head())

        # --- Cross Join Branch × WP ---
        df_branch["key"] = 1
        df_wp["key"] = 1
        df_cross = pd.merge(df_branch, df_wp, on="key").drop("key", axis=1)

        # --- Normalisasi COMPLIANCE_INDICATOR biar konsisten ---
        def normalize_text(s):
            if pd.isna(s):
                return None
            return " ".join(str(s).split()).strip().lower()

        df_cross["CI_NORM"] = df_cross["COMPLIANCE_INDICATOR"].apply(normalize_text)
        df_progress["CI_NORM"] = df_progress["COMPLIANCE_INDICATOR"].apply(normalize_text)

        # --- Bikin hash pendek buat ID (lebih enak buat chart) ---
        import hashlib
        def make_hash(text):
            if pd.isna(text):
                return None
            return "CI_" + hashlib.md5(text.encode()).hexdigest()[:6]

        df_cross["CI_CODE"] = df_cross["CI_NORM"].apply(make_hash)
        df_progress["CI_CODE"] = df_progress["CI_NORM"].apply(make_hash)

        # --- Merge dengan WPProgress (lookup 4 keys, pakai CI_CODE) ---
        merged = pd.merge(
            df_cross,
            df_progress,
            on=["BRANCH_ID", "LINE_OF_BUSINESS", "SUB_WP", "PROCESS", "CI_CODE"],
            how="left"
        )

        # Simpan teks asli compliance indicator (biar tetap bisa dibaca panjangnya)
        merged["COMPLIANCE_TEXT"] = merged["COMPLIANCE_INDICATOR_x"].combine_first(merged["COMPLIANCE_INDICATOR_y"])
        merged.drop(columns=["COMPLIANCE_INDICATOR_x", "COMPLIANCE_INDICATOR_y"], inplace=True)
        merged.rename(columns={"COMPLIANCE_TEXT": "COMPLIANCE_INDICATOR"}, inplace=True)

        # ---------- BERSIHKAN DUPLIKAT KOLUMN (hilangkan _x/_y) ----------
        def coalesce_cols(df, bases):
            for base in bases:
                cx, cy = f"{base}_x", f"{base}_y"
                if cx in df.columns and cy in df.columns:
                    df[base] = df[cx].combine_first(df[cy])
                    df.drop(columns=[cx, cy], inplace=True)
                elif cx in df.columns:
                    df.rename(columns={cx: base}, inplace=True)
                elif cy in df.columns:
                    df.rename(columns={cy: base}, inplace=True)

        # satukan kolom yang berpotensi dobel
        coalesce_cols(merged, ["AREA", "COMPANY_ID", "BRANCH_NAME", "EVIDENCE_FILE_NAME"])

        # ---------- BENTUK DATA TAMPILAN SESUAI PERMINTAAN ----------
        desired_cols = [
            "BRANCH_ID", "BRANCH_NAME", "AREA",
            "COMPANY_ID",
            "LINE_OF_BUSINESS", "SUB_WP", "PROCESS",
            "COMPLIANCE_INDICATOR", "INSPECTION_CATEGORY",
            "PIC", "SCORE_COMPLIANCE_INDICATOR", "TOTAL_SAMPLE",
            "SCORE", "STATUS", "EVIDENCE_FILE_NAME"
        ]

        for c in desired_cols:
            if c not in merged.columns:
                merged[c] = pd.NA

        cleaned = merged[desired_cols].copy()

        cleaned = merged[desired_cols].copy()

        # ---------- BUSINESS RULE: Kalau TOTAL_SAMPLE = 0, maka SCORE = 100 ----------
        cleaned.loc[
            (cleaned["TOTAL_SAMPLE"].fillna(0).astype(float).astype(int) == 0),
            "SCORE"
        ] = 100

        # ---------- INIT SESSION STATE ----------
        if "selected_area" not in st.session_state:
            st.session_state.selected_area = sorted(cleaned["AREA"].dropna().unique())

        if "selected_lob" not in st.session_state:
            st.session_state.selected_lob = sorted(cleaned["LINE_OF_BUSINESS"].dropna().unique())

        # ---------- FILTER UI ----------
        st.subheader("Filter Data")

        with st.form("filter_form"):
            col1, col2 = st.columns(2)

            # --- Area ---
            area_options = sorted(cleaned["AREA"].dropna().unique())
            valid_area = [x for x in st.session_state.selected_area if x in area_options]

            selected_area = st.multiselect(
                "Pilih Area",
                options=area_options,
                default=valid_area,
            )

            # --- LOB (dependent on Area) ---
            lob_options = sorted(
                cleaned[cleaned["AREA"].isin(selected_area)]["LINE_OF_BUSINESS"].dropna().unique()
            )
            valid_lob = [x for x in st.session_state.selected_lob if x in lob_options]

            selected_lob = st.multiselect(
                "Pilih Line of Business",
                options=lob_options,
                default=valid_lob,
            )

            apply_filter = st.form_submit_button("✅ Apply Filter")

        # Tombol reset di luar form
        reset_filter = st.button("🔄 Reset Filter")

        # --- Logic tombol ---
        if apply_filter:
            st.session_state.selected_area = selected_area
            st.session_state.selected_lob = selected_lob

        if reset_filter:
            st.session_state.selected_area = area_options
            st.session_state.selected_lob = sorted(cleaned["LINE_OF_BUSINESS"].dropna().unique())
            apply_filter = True  # langsung tampilkan semua data

        # ---------- FILTERING ----------
        if apply_filter:
            filtered_df = cleaned[
                (cleaned["AREA"].isin(st.session_state.selected_area)) &
                (cleaned["LINE_OF_BUSINESS"].isin(st.session_state.selected_lob))
            ]

            st.subheader("Hasil Gabungan (Kolom Terpilih)")
            st.caption(f"Menampilkan {len(filtered_df):,} baris setelah filter.")
            st.dataframe(filtered_df.head(200), use_container_width=True)

        else:
            st.info("Pilih filter lalu klik **Apply Filter** untuk menampilkan data.")
            filtered_df = pd.DataFrame()

            # ---------- GRAFIK ----------
            # 1) Jumlah Status Submit
        if "STATUS" in filtered_df.columns and not filtered_df.empty:
            status_counts = (
                filtered_df["STATUS"]
                .dropna()
                .astype(str)
                .str.strip()
                .value_counts()
                .reset_index()
            )
            status_counts.columns = ["STATUS", "JUMLAH"]
            fig_pie = px.pie(
                status_counts,
                names="STATUS", values="JUMLAH",
                title="Distribusi Status Submit",
                hole=0.3
            )

            # 2) Rata-rata SCORE per LOB
            score_avg = filtered_df.groupby("LINE_OF_BUSINESS", dropna=False)["SCORE"].mean().reset_index()
            fig_bar = px.bar(
                score_avg,
                x="LINE_OF_BUSINESS", y="SCORE", color="LINE_OF_BUSINESS",
                title="Rata-rata Nilai (SCORE) per Line of Business",
                text_auto=True
            )
            fig_bar.update_layout(xaxis_tickangle=-45)

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                st.plotly_chart(fig_bar, use_container_width=True)

            # 3) Stacked bar per AREA
            area_progress = (
                filtered_df.groupby("AREA")
                .apply(lambda x: (x["STATUS"].eq("SUBMIT").sum() / len(x)) * 100)
                .reset_index(name="Persentase")
            )
            fig_area = px.bar(
                area_progress,
                x="AREA", y="Persentase",
                title="Persentase Pengerjaan per Area (Filtered)",
                text="Persentase",
                color="Persentase",
                color_continuous_scale="Blues"
            )
            fig_area.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

            st.plotly_chart(fig_area, use_container_width=True, key="area_progress_chart")

        # ---------- DOWNLOAD ----------
        output_file = "hasil_gabungan_filtered.csv"
        filtered_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        with open(output_file, "rb") as f:
            st.download_button(
                label="Download Hasil Gabungan (CSV)",
                data=f,
                file_name="hasil_gabungan.csv",
                mime="text/csv"
            )
