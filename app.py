import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests 
st.set_page_config(page_title="C-PRO Multi Page App", layout="wide")

# Sidebar untuk navigasi halaman
page = st.sidebar.radio(
    "📌 Pilih Halaman",
    ["📂 File Repository" , "📊 Monitoring Setup User", "🎯 Random Sampling dari Excel", "📈 Komparasi Progress", "🗂 Monitoring WP Progress"]
)

# ====== PAGE 0: FILE REPOSITORY ======
if page == "📂 File Repository":
    st.title("📂 File Repository (Download Template File)")

    st.subheader("⬇️ Download Template File")

    files_to_download = {
        "📌 Branch File": "https://raw.githubusercontent.com/andi-arch1/randomsampling/main/BRANCH.xlsx",
        "📌 Workingpaper File": "https://raw.githubusercontent.com/andi-arch1/randomsampling/main/WORKINGPAPERBATCH2.xlsx",
        "📌 Cover Central File": "https://raw.githubusercontent.com/andi-arch1/randomsampling/main/COVERCENTRAL.xlsx"
    }
    for label, url in files_to_download.items():
        response = requests.get(url)
        if response.status_code == 200:
            st.download_button(
                label=f"⬇️ Download {label}",
                data=response.content,
                file_name=url.split("/")[-1],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning(f"⚠️ {label} gagal dimuat dari GitHub.")

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
    fungsi = st.radio("🔧 Pilih Mode:", ["Network", "Central"])

    # Upload file utama
    uploaded_file = st.file_uploader("📝 Upload file utama:", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.success("✅ File utama berhasil dimuat!")
        st.dataframe(df.head())

        # =======================
        # MODE NETWORK
        # =======================
        if fungsi == "Network":
            st.info("📡 Mode: Network")
            branch_col = st.selectbox("🏢 Pilih kolom Cabang:", df.columns)

            # Opsional: pakai periode
            use_period = st.checkbox("📅 Gunakan periode?")
            if use_period:
                period_col = st.selectbox("Pilih kolom Periode:", df.columns)
                min_period, max_period = st.select_slider(
                    "Range Periode:",
                    options=sorted(df[period_col].unique()),
                    value=(df[period_col].min(), df[period_col].max())
                )
                df = df[df[period_col].between(min_period, max_period)]

            if st.button("🚀 Jalankan Sampling Network"):
                sampled_list = []
                for cabang, group in df.groupby(branch_col):
                    # ambil max 30 sample per cabang
                    n = min(30, len(group))
                    sampled_list.append(group.sample(n=n, random_state=42))

                sampled_df = pd.concat(sampled_list).reset_index(drop=True)
                
                st.subheader("📄 Hasil Random Sampling (Network)")
                st.dataframe(sampled_df)

        # =======================
        # MODE CENTRAL
        # =======================
        elif fungsi == "Central":
            mapping_file = st.file_uploader("🗂️ Upload file mapping central:", type=["xlsx"])
            if mapping_file:
                df_map = pd.read_excel(mapping_file)
                st.success("✅ Mapping central berhasil dimuat!")
                st.dataframe(df_map.head())

                central_function = st.selectbox(
                    "🏢 Pilih Function Central:",
                    ["COVER CENTRAL CREDIT", "COVER CENTRAL REMEDIAL", "COVER CENTRAL IWM"]
                )
                left_col = st.selectbox("🔑 Pilih kolom penghubung (File Utama):", df.columns)
                right_col = st.selectbox("🔑 Pilih kolom penghubung (File Mapping):", df_map.columns)

                total_sample = st.number_input("🎯 Total sample per Central", min_value=1, value=30)
                extra_group_col = st.multiselect("🧩 Tambah kolom untuk group by (opsional):", df.columns)

                if st.button("🚀 Jalankan Sampling Central"):
                    merged_df = df.merge(df_map, left_on=left_col, right_on=right_col, how="left")

                    final_list = []

                    # Loop per central
                    for central_name, group in merged_df.groupby(central_function):
                        cabang_count = group["ID CABANG"].nunique()
                        if cabang_count == 0:
                            continue

                        # target maksimal sample per central
                        remaining = total_sample
                        sample_per_cabang = max(1, total_sample // cabang_count)

                        for cabang_id, cabang_group in group.groupby("ID CABANG"):
                            if extra_group_col:
                                for _, sub_group in cabang_group.groupby(extra_group_col):
                                    n = min(sample_per_cabang, len(sub_group))
                                    remaining -= n
                                    final_list.append(sub_group.sample(n=n, random_state=42))
                            else:
                                n = min(sample_per_cabang, len(cabang_group))
                                remaining -= n
                                final_list.append(cabang_group.sample(n=n, random_state=42))

                        # Kalau masih ada sisa slot, tambahin ke cabang yg punya data lebih
                        if remaining > 0:
                            for cabang_id, cabang_group in group.groupby("ID CABANG"):
                                if remaining <= 0:
                                    break
                                extra_n = min(remaining, len(cabang_group) - sample_per_cabang)
                                if extra_n > 0:
                                    final_list.append(cabang_group.sample(n=extra_n, random_state=42))
                                    remaining -= extra_n

                    if final_list:
                        sampled_df = pd.concat(final_list).reset_index(drop=True)

                        # Drop kolom mapping (COVER CENTRAL)
                        cols_to_drop = [col for col in sampled_df.columns if col.startswith("COVER CENTRAL")]
                        sampled_df = sampled_df.drop(columns=cols_to_drop, errors="ignore")

                        st.subheader(f"📄 Hasil Random Sampling (Central - {central_function})")
                        st.dataframe(sampled_df)
                    else:
                        st.warning("⚠️ Tidak ada data yang bisa di-sampling.")
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

            # ---------- TABEL PROGRESS PER BRANCH ----------
        if not filtered_df.empty:
            branch_progress = (
                filtered_df.groupby("BRANCH_NAME")
                .apply(lambda x: pd.Series({
                    "Jumlah Data": len(x),
                    "Jumlah SUBMIT": x["STATUS"].eq("SUBMIT").sum(),
                    "Persentase (%)": (x["STATUS"].eq("SUBMIT").sum() / len(x)) * 100
                }))
                .reset_index()
            )
            
            st.subheader("📊 Progress Pengerjaan per Branch")

            # Styling function
            def highlight_progress(val):
                if val == 100:
                    color = 'background-color: green; color: black; font-weight: bold;'
                elif val >= 50:
                    color = 'background-color: orange; color: white;'
                else:
                    color = 'background-color: red; color: white;'
                return color

            styled_table = branch_progress.style.applymap(
                highlight_progress, subset=["Persentase (%)"]
            ).format({"Persentase (%)": "{:.2f}%"})

            st.dataframe(styled_table, use_container_width=True)
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
