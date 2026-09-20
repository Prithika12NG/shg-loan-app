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
            return pd.read_csv(files[0]) if files[0].endswith('.csv') else pd.read_excel(files[0])
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
        st.sidebar.success(f"Welcome {role}")
    else:
        st.session_state['logged_in']=False
        st.sidebar.error("Use officer/officer123")

df = load_data()

if 'logged_in' in st.session_state and st.session_state['logged_in']:

    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        st.subheader("Ellapuram Block - 17562 Members")
        if df is not None:
            st.dataframe(df.head(30))
            sel = st.selectbox("Select Member", df.iloc[:,0].astype(str))
            c1,c2=st.columns(2)
            with c1:
                if st.button("✅ Approve"): st.success(f"{sel} Approved!")
            with c2:
                if st.button("❌ Reject"): st.error(f"{sel} Rejected!")

    else:
        st.title("SHG Loan Eligibility Checker")
        st.subheader("Ellapuram Block - Mobile Version")

        if df is not None:
            member_id = st.text_input("Enter Member ID")
            loan_amount = st.number_input("Required Loan Amount", min_value=1000, step=1000, value=10000)

            if st.button("Check Eligibility"):
                mask = df.astype(str).apply(lambda x: x.str.contains(member_id, na=False)).any(axis=1)
                found = df[mask]
                if not found.empty:
                    row = found.iloc[0]

                    # Auto find savings column silently
                    savings_col = None
                    for c in df.columns:
                        if any(k in c.lower() for k in ['saving','thrift','balance','sav']):
                            savings_col = c
                            break

                    if savings_col:
                        savings_val = float(str(row[savings_col]).replace(',',''))
                        max_elig = savings_val * 4

                        st.write(f"**Your Savings:** Rs.{savings_val}")
                        st.write(f"**Asking Amount:** Rs.{loan_amount}")
                        st.write(f"**Max Eligible (4x Savings):** Rs.{max_elig}")

                        if loan_amount <= max_elig:
                            st.success(f"✅ ELIGIBLE for Rs.{loan_amount}")
                            st.balloons()
                        else:
                            st.error(f"❌ NOT ELIGIBLE for Rs.{loan_amount}")
                            st.info(f"Reduce amount to below Rs.{max_elig}")
                    else:
                        st.error("Savings data not found")
                else:
                    st.error(f"Member ID {member_id} not found")
        else:
            st.warning("Data file not found")

else:
    st.title("SHG Loan Eligibility - Ellapuram")
    st.info("👈 Login from left sidebar")
    st.code("Officer: officer / officer123\nLeader: leader / leader123\nMember: member / member123")
