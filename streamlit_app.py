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
                    reasons.append(f"✅ Aadhaar KYC: {aadhaar_val}")
                else:
                    eligible = False
                    reasons.append(f"❌ Aadhaar KYC Not Verified: {aadhaar_val}")

                if acc_val and acc_val.upper() not in ['NAN', 'NONE', '-', '0'] and len(acc_val) >= 4:
                    reasons.append(f"✅ Bank Account Linked: {acc_val}")
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
                st.dataframe(pd.DataFrame([row]))

                # Auto-clear for next search - helps mobile
                st.info("👉 Enter next Member Code above and click CHECK again - will work in 1 click now!")

st.caption("TNRTP | Ellapuram | 1-Click Fixed")
