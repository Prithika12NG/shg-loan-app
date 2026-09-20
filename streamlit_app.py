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
            # Clean column names
            df.columns = [c.strip() for c in df.columns]
            return df
        except:
            return None
    return None

# --- LOGIN ---
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
        st.session_state['user']=username
    else:
        st.session_state['logged_in']=False
        st.sidebar.error("Wrong! Use officer/officer123")

df = load_data()

def find_col(df, keywords):
    # Auto find column name like "ekyc", "mobile", "bank", "active"
    for c in df.columns:
        cl = c.lower()
        for k in keywords:
            if k in cl:
                return c
    return None

if 'logged_in' in st.session_state and st.session_state['logged_in']:

    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        st.subheader("Ellapuram Block - Applications for Approval")
        if df is not None:
            # Show members who passed eligibility
            st.dataframe(df.head(30))
            sel = st.selectbox("Select Member ID for Action", df.iloc[:,0].astype(str))
            c1,c2=st.columns(2)
            with c1:
                if st.button("✅ Approve & Disburse"): st.success(f"Loan for {sel} Approved & Sent to Bank!")
            with c2:
                if st.button("❌ Reject"): st.error(f"{sel} Rejected - Inform SHG Leader")

    else: # Member & Leader
        st.title("SHG Loan Eligibility Checker")
        st.subheader("Ellapuram Block - Mobile Version")

        member_id = st.text_input("Enter Member ID", value="290031673652")
        loan_amount = st.number_input("Required Loan Amount (Rs.)", min_value=10000, step=50000, value=100000)

        if st.button("Check Eligibility"):
            if df is not None and member_id:
                mask = df.astype(str).apply(lambda x: x.str.contains(member_id, na=False)).any(axis=1)
                found = df[mask]

                if not found.empty:
                    row = found.iloc[0]

                    # --- AUTO DETECT YOUR COLUMNS ---
                    active_col = find_col(df, ['active','status','Status (Active/Inactive)'])
                    ekyc_col = find_col(df, ['ekyc','e-kyc','kyc'])
                    mobile_col = find_col(df, ['mobile','phone','mobile verified'])
                    bank_col = find_col(df, ['bank','account','bank account'])

                    st.write("### Verification Details:")

                    checks = []
                    all_ok = True

                    # 1. Active Check
                    if active_col:
                        val = str(row[active_col]).lower()
                        is_active = 'active' in val or val in ['yes','1','y','true']
                        checks.append(("Status (Active/Inactive)", is_active, row[active_col]))
                        if not is_active: all_ok = False
                    else:
                        checks.append(("Member Active", True, "Column not found - Assumed Active"))

                    # 2. eKYC Check
                    if ekyc_col:
                        val = str(row[ekyc_col]).lower()
                        is_ekyc = 'verified' in val or 'yes' in val or val in ['1','y','true','completed']
                        checks.append(("eKYC Verified", is_ekyc, row[ekyc_col]))
                        if not is_ekyc: all_ok = False
                    else:
                        checks.append(("eKYC Verified", True, "Column not found"))

                    # 3. Mobile Check
                    if mobile_col:
                        val = str(row[mobile_col]).lower()
                        # Check if column is "mobile verified" or just mobile number exists
                        if 'verif' in mobile_col.lower():
                            is_mob = 'verified' in val or 'yes' in val or val in ['1','y']
                        else:
                            is_mob = val not in ['','nan','none','0'] and len(val) >= 5
                        checks.append(("Mobile Verified", is_mob, row[mobile_col]))
                        if not is_mob: all_ok = False
                    else:
                        checks.append(("Mobile Verified", True, "Column not found"))

                    # 4. Bank Account Check
                    if bank_col:
                        val = str(row[bank_col]).lower()
                        is_bank = val not in ['','nan','none','0','no'] and len(val) > 3
                        checks.append(("Bank Account Available", is_bank, row[bank_col]))
                        if not is_bank: all_ok = False
                    else:
                        checks.append(("Bank Account Available", True, "Column not found"))

                    # Show checks
                    for name, status, value in checks:
                        if status:
                            st.success(f"✅ {name}: {value}")
                        else:
                            st.error(f"❌ {name}: {value} - FAILED")

                    st.markdown("---")
                    # FINAL DECISION
                    if all_ok:
                        st.success(f"✅ ELIGIBLE - Member {member_id} is eligible for Rs.{loan_amount}")
                        st.balloons()
                        st.info(f"Application for Rs.{loan_amount} submitted to next level: SHG Leader -> Bank Officer")
                        st.write("Status: **PENDING WITH BANK OFFICER**")
                        # Save to session for officer to see
                        st.session_state['last_applied'] = member_id
                    else:
                        st.error(f"❌ NOT ELIGIBLE - Member {member_id} failed verification")
                        st.warning("Please complete eKYC / Mobile verification / Bank Account linking in Ellapuram office")
                else:
                    st.error(f"Member ID {member_id} not found in your data")
            else:
                st.error("Enter Member ID")
else:
    st.title("SHG Loan Eligibility - Ellapuram")
    st.info("👈 Login from left sidebar to check")
    st.code("Officer: officer / officer123\nLeader: leader / leader123\nMember: member / member123")
