import streamlit as st
import pandas as pd

st.title("📊 Random Sampling dari Excel")

# Upload file Excel
uploaded_file = st.file_uploader("📥 Upload file Excel kamu", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, dtype=str)
        st.success("✅ File berhasil dimuat!")
        st.subheader("🔍 Pratinjau Data")
        st.dataframe(df.head())

        # Pilih kolom untuk grouping (hanya kolom object dan kategori)
        group_col = st.selectbox(
            "🧩 Pilih kolom pengelompokan (group by):",
            options=df.columns
        )

        # Pilih jumlah sample per grup
        n_sample = st.slider("🎯 Jumlah sample per grup", min_value=1, max_value=100, value=6)

        # Tombol untuk melakukan sampling
        if st.button("🚀 Jalankan Random Sampling"):
            sampled_df = (
                df.groupby(group_col, group_keys=False)
                  .apply(lambda x: x.sample(n=min(n_sample, len(x)), random_state=42))
                  .reset_index(drop=True)
            )

            st.subheader("📄 Hasil Random Sampling")
            st.dataframe(sampled_df)

            # Opsi untuk mengunduh hasil sampling
            @st.cache_data
            def convert_df_to_excel(df):
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name='Sampled')
                return output.getvalue()

            excel_data = convert_df_to_excel(sampled_df)
            st.download_button(
                label="📥 Download Hasil Sampling (.xlsx)",
                data=excel_data,
                file_name="hasil_sampling.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Gagal membaca file: {e}")

else:
    st.info("📝 Silakan upload file Excel terlebih dahulu.")
