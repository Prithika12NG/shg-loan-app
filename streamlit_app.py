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
    cols_lower = {c.lower().strip(): c for c in df.columns}
    if col_type == "status":
        if 'status' in cols_lower:
            return cols_lower['status']
        for c in df.columns:
            if 'marital' in c.lower():
                continue
            try:
                vals = [str(v).lower().strip() for v in df[c].tolist()[:50]]
                if 'active' in vals or 'inactive' in vals:
                    return c
            except:
                pass
        return None
    if col_type == "ekyc":
        for c in df.columns:
            if 'ekyc' in c.lower() or 'kyc' in c.lower():
                return c
    if col_type == "mobile":
        for c in df.columns:
            if 'mobile' in c.lower() or 'phone' in c.lower():
                return c
    if col_type == "bank":
        for c in df.columns:
            if 'bank' in c.lower() and 'loan' not in c.lower():
                return c
            if c.lower().strip() in ['account','bank account','bank_account']:
                return c
    return None

if 'logged_in' in st.session_state and st.session_state['logged_in']:

    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        st.subheader("Ellapuram Block - Applications")
        if df is not None:
            st.dataframe(df.head(30))
            sel = st.selectbox("Select Member ID", df.iloc[:,0].astype(str))
            c1,c2 = st.columns(2)
            with c1:
                if st.button("✅ Approve"): st.success(f"{sel} Approved!")
            with c2:
                if st.button("❌ Reject"): st.error(f"{sel} Rejected")

    else:
        st.title("SHG Loan Eligibility Checker")
        st.subheader("Ellapuram Block - Mobile Version")

        member_id = st.text_input("Enter Member ID", value="290031673652")
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

                    # 1. ACTIVE CHECK - FIXED: INACTIVE should be RED
                    if active_col:
                        val = str(row[active_col]).strip()
                        # FIXED LOGIC - Only exact ACTIVE is eligible
                        is_active = val.lower().strip() == 'active'
                        checks.append(("Member Active", is_active, val))
                        if not is_active: all_ok = False
                    else:
                        checks.append(("Member Active", False, "Status column not found"))

                    # 2. eKYC
                    if ekyc_col:
                        val = str(row[ekyc_col]).strip()
                        v = val.lower()
                        is_ok = v in ['yes','verified','available','completed','1'] or 'verif' in v
                        checks.append(("eKYC Verified", is_ok, val))
                        if not is_ok: all_ok = False
                    else:
                        checks.append(("eKYC Verified", False, "eKYC column not found"))

                    # 3. Mobile
                    if mobile_col:
                        val = str(row[mobile_col]).strip()
                        is_ok = val not in ['','--','nan','none','0','not available'] and len(val) >= 5
                        checks.append(("Mobile Verified", is_ok, val if val!='--' else "Not Available"))
                        if not is_ok: all_ok = False
                    else:
                        checks.append(("Mobile Verified", False, "Mobile column not found"))

                    # 4. Bank Account
                    if bank_col:
                        val = str(row[bank_col]).strip()
                        is_ok = val not in ['','--','nan','none','0','not available'] and len(val) > 3
                        checks.append(("Bank Account Available", is_ok, val if val!='--' else "Not Available"))
                        if not is_ok: all_ok = False
                    else:
                        checks.append(("Bank Account Available", False, "Bank column not found"))

                    for name, status, value in checks:
                        if status:
                            st.success(f"✅ {name}: {value}")
                        else:
                            st.error(f"❌ {name}: {value} - FAILED")

                    st.markdown("---")
                    if all_ok:
                        st.success(f"✅ ELIGIBLE - Member {member_id} for Rs.{loan_amount}")
                        st.balloons()
                        st.info("Application Submitted to Next Level: SHG Leader -> Bank Officer")
                        st.write("**Status: PENDING WITH BANK OFFICER**")
                    else:
                        st.error(f"❌ NOT ELIGIBLE - Member {member_id}")
                        st.warning("Complete verification at Ellapuram Block office")
                else:
                    st.error(f"Member ID {member_id} not found")
            else:
                st.error("Enter Member ID")
else:
    st.title("SHG Loan Eligibility - Ellapuram")
    st.info("👈 Login from left sidebar")
    st.code("Officer: officer / officer123\nLeader: leader / leader123\nMember: member / member123")
