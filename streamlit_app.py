import streamlit as st
import pandas as pd
import os, glob

st.set_page_config(page_title="SHG Loan Eligibility - Ellapuram", page_icon="🏦", layout="centered")

@st.cache_data
def load_data():
    script_folder = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(script_folder, "*.csv"))
    if not files:
        files = glob.glob(os.path.join(script_folder, "*.xlsx"))
    if files:
        try:
            df = pd.read_csv(files[0]) if files[0].endswith('.csv') else pd.read_excel(files[0])
            df.columns = [c.strip() for c in df.columns]
            return df
        except:
            return None
    return None

st.sidebar.title("🔐 Login")
role = st.sidebar.selectbox("Select Role", ["SHG Member", "SHG Leader", "Bank Officer"])
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    if (role=="Bank Officer" and username=="officer" and password=="officer123") or \
       (role=="SHG Leader" and username=="leader" and password=="leader123") or \
       (role=="SHG Member" and username=="member" and password=="member123"):
        st.session_state['logged_in']=True
        st.session_state['role']=role
    else:
        st.session_state['logged_in']=False
        st.sidebar.error("Use officer/officer123")

df = load_data()

def find_col(df, col_type):
    # FIXED: To avoid Marital Status bug
    cols_lower = {c.lower().strip(): c for c in df.columns}

    if col_type == "status":
        # Priority 1: Exact 'Status' column
        if 'status' in cols_lower:
            return cols_lower['status']
        # Priority 2: Check values contain Active/Inactive
        for c in df.columns:
            if 'marital' in c.lower():
                continue
            try:
                vals = df[c].astype(str).str.lower().tolist()[:50]
                if any(v == 'active' or v == 'inactive' for v in vals):
                    return c
            except:
                pass
        return None

    if col_type == "ekyc":
        for c in df.columns:
            if 'ekyc' in c.lower() or 'e_kyc' in c.lower() or 'kyc' in c.lower():
                return c

    if col_type == "mobile":
        for c in df.columns:
            if 'mobile' in c.lower() or 'phone' in c.lower():
                return c

    if col_type == "bank":
        for c in df.columns:
            if 'bank' in c.lower() or 'account' in c.lower():
                # Avoid loan account
                if 'loan' not in c.lower():
                    return c
    return None

if 'logged_in' in st.session_state and st.session_state['logged_in']:

    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        st.subheader("Ellapuram Block - Approved Applications")
        if df is not None:
            st.dataframe(df.head(30))
            sel = st.selectbox("Select Member ID", df.iloc[:,0].astype(str))
            c1,c2 = st.columns(2)
            with c1:
                if st.button("✅ Approve & Disburse"): st.success(f"{sel} Loan Approved!")
            with c2:
                if st.button("❌ Reject"): st.error(f"{sel} Rejected")

    else:
        st.title("SHG Loan Eligibility Checker")
        st.subheader("Ellapuram Block - Mobile Version")

        member_id = st.text_input("Enter Member ID", value="290047031286")
        loan_amount = st.number_input("Required Loan Amount (Rs.)", min_value=1000, step=5000, value=10000)

        if st.button("Check Eligibility"):
            if df is not None and member_id:
                mask = df.astype(str).apply(lambda x: x.str.contains(member_id, na=False)).any(axis=1)
                found = df[mask]

                if not found.empty:
                    row = found.iloc[0]

                    active_col = find_col(df, "status")
                    ekyc_col = find_col(df, "ekyc")
                    mobile_col = find_col(df, "mobile")
                    bank_col = find_col(df, "bank")

                    st.write("### Verification Details:")
                    checks = []
                    all_ok = True

                    # 1. ACTIVE/INACTIVE - FIXED
                    if active_col:
                        val = str(row[active_col]).strip()
                        is_active = val.lower() == 'active' or 'active' in val.lower()
                        checks.append(("Member Active", is_active, val))
                        if not is_active: all_ok = False
                    else:
                        checks.append(("Member Active", False, "Status column not found"))

                    # 2. eKYC
                    if ekyc_col:
                        val = str(row[ekyc_col]).strip()
                        is_ok = 'verif' in val.lower() or val.lower() in ['yes','verified','1','true','completed']
                        checks.append(("eKYC Verified", is_ok, val))
                        if not is_ok: all_ok = False
                    else:
                        checks.append(("eKYC Verified", False, "eKYC column not found"))

                    # 3. Mobile
                    if mobile_col:
                        val = str(row[mobile_col]).strip()
                        is_ok = val.lower() not in ['','nan','none','0'] and len(val) >= 5
                        checks.append(("Mobile Verified", is_ok, val))
                        if not is_ok: all_ok = False

                    # 4. Bank Account
                    if bank_col:
                        val = str(row[bank_col]).strip()
                        is_ok = val.lower() not in ['','nan','none','0','no'] and len(val) > 3
                        checks.append(("Bank Account Available", is_ok, val))
                        if not is_ok: all_ok = False

                    for name, status, value in checks:
                        if status:
                            st.success(f"✅ {name}: {value}")
                        else:
                            st.error(f"❌ {name}: {value} - FAILED")

                    st.markdown("---")
                    if all_ok:
                        st.success(f"✅ ELIGIBLE - Member {member_id} for Rs.{loan_amount}")
                        st.balloons()
                        st.info(f"Application Submitted to Next Level: SHG Leader -> Bank Officer")
                        st.write("**Status: PENDING WITH BANK OFFICER**")
                    else:
                        st.error(f"❌ NOT ELIGIBLE - {member_id}")
                        st.warning("Complete verification at Ellapuram office")
                else:
                    st.error(f"Member ID {member_id} not found")
            else:
                st.error("Enter Member ID")
else:
    st.title("SHG Loan Eligibility - Ellapuram")
    st.info("👈 Login from left sidebar")
    st.code("Officer: officer / officer123\nLeader: leader / leader123\nMember: member / member123")
