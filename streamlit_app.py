import streamlit as st
import pandas as pd
import os, glob

st.set_page_config(page_title="SHG Loan Eligibility - Ellapuram", page_icon="🏦", layout="centered")
st.title("🏦 SHG Loan Eligibility Checker")
st.subheader("Ellapuram Block - 17562 Members | Mobile Version")
st.markdown("---")

@st.cache_data
def load_data():
    script_folder = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(script_folder, "*.csv"))
    if not files:
        files = glob.glob(os.path.join(script_folder, "*.xlsx"))
    if not files:
        return None, None
    fp = files[0]
    df = pd.read_csv(fp, low_memory=False) if fp.endswith('.csv') else pd.read_excel(fp)
    df.columns = df.columns.str.strip()
    return df, fp

def find_column(df, keyword):
    for col in df.columns:
        if keyword.lower() in col.lower():
            return col
    return None

df, filename = load_data()

if df is None:
    st.error("CSV not found")
else:
    st.success(f"Loaded: {os.path.basename(filename)} | Total Members: {len(df)}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Members", len(df))
    col2.metric("Panchayats", df[find_column(df, "Panchayat")].nunique() if find_column(df, "Panchayat") else "N/A")
    col3.metric("File", os.path.basename(filename)[:15])

    st.markdown("---")

    # FIXED: Use form - 1 click works always
    with st.form("check_form", clear_on_submit=False):
        member_code = st.text_input("Enter Member Code", placeholder="e.g., 290031673718")
        submitted = st.form_submit_button("CHECK ELIGIBILITY", use_container_width=True)

    if submitted:
        if not member_code:
            st.warning("Enter Member Code")
        else:
            mask = False
            for col in df.columns:
                try:
                    mask |= df[col].astype(str).str.contains(str(member_code), na=False, case=False)
                except: pass
            matched = df[mask]

            if matched.empty:
                st.error(f"Member Code {member_code} Not Found")
            else:
                row = matched.iloc[0]
                col_aadhaar = find_column(df, "Aadhaar KYC")
                col_acc = find_column(df, "Account Number")

                aadhaar_val = str(row.get(col_aadhaar, '')).strip().upper() if col_aadhaar else ''
                acc_val = str(row.get(col_acc, '')).strip() if col_acc else ''

                eligible = True
                reasons = []

                if 'VERIFIED' in aadhaar_val or 'YES' in aadhaar_val:
                    reasons.append(f"✅ Aadhaar KYC : Verified")
                else:
                    eligible = False
                    reasons.append(f"❌ Aadhaar KYC Not Verified : Not Verified")

                if acc_val and acc_val.upper() not in ['NAN', 'NONE', '-', '0'] and len(acc_val) >= 4:
                    reasons.append(f"✅ Bank Account: Linked (Secure)")
                else:
                    eligible = False
                    reasons.append("❌ Bank Account Not Linked")

                st.markdown("---")
                if eligible:
                    st.success("✅ ELIGIBLE FOR LOAN")
                    st.balloons()
                else:
                    st.error("❌ NOT ELIGIBLE")

                for r in reasons:
                    st.write(r)

                st.markdown("### Member Details")
                # SAFE - Show only non-sensitive columns
                safe_cols = [find_column(df, "Member"), find_column(df, "SHG"), find_column(df, "Panchayat"), find_column(df, "Block")]
                safe_cols = [c for c in safe_cols if c is not None]
                safe_data = row[safe_cols].to_frame().T if safe_cols else pd.DataFrame([row])
                st.dataframe(safe_data)

                # Don't show Aadhaar or Account number full - mask it
                st.write(f"🔒 Aadhaar KYC Status: {'Verified' if 'VERIFIED' in aadhaar_val or 'YES' in aadhaar_val else 'Not Verified'}")
                st.write(f"🔒 Bank Account: {'Linked' if len(acc_val)>=4 else 'Not Linked'} (Number hidden for privacy)")

                # Auto-clear for next search - helps mobile
                st.info("👉 Enter next Member Code above and click CHECK again - will work in 1 click now!")
st.caption("TNRTP | Ellapuram | 1-Click Fixed")
