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
            return df
        except:
            return None
    return None

st.sidebar.title("🔐 Login")
role = st.sidebar.selectbox("Select Role", ["SHG Member", "SHG Leader", "Bank Officer"])
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_ok = False

if st.sidebar.button("Login"):
    if (role=="Bank Officer" and username=="officer" and password=="officer123") or \
       (role=="SHG Leader" and username=="leader" and password=="leader123") or \
       (role=="SHG Member" and username=="member" and password=="member123"):
        st.session_state['logged_in']=True
        st.session_state['role']=role
        login_ok=True
        st.sidebar.success(f"Welcome {role}")
    else:
        st.sidebar.error("Use officer/officer123")
        st.session_state['logged_in']=False

# Load data
df = load_data()

if 'logged_in' in st.session_state and st.session_state['logged_in']:

    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        st.subheader("Ellapuram Block - All Applications")
        if df is not None:
            st.dataframe(df.head(30))
            sel = st.selectbox("Select Member ID", df.iloc[:,0].astype(str))
            c1,c2=st.columns(2)
            with c1:
                if st.button("✅ Approve Loan"):
                    st.success(f"{sel} Approved!")
            with c2:
                if st.button("❌ Reject Loan"):
                    st.error(f"{sel} Rejected!")

    else:
        st.title("SHG Loan Eligibility Checker")
        st.subheader("Amount Check with Sample Data")

        if df is not None:
            st.write("Columns in your data:", list(df.columns))
            member_id = st.text_input("Enter Member ID")
            loan_amount = st.number_input("Required Loan Amount", min_value=1000, step=1000, value=10000)

            if st.button("Check Eligibility with Sample Data"):
                # Search member
                mask = df.astype(str).apply(lambda x: x.str.contains(member_id, na=False)).any(axis=1)
                found = df[mask]
                if not found.empty:
                    row = found.iloc[0]
                    st.write("Member Found:", row.to_dict())

                    # Auto find savings column
                    savings_col = None
                    for c in df.columns:
                        if any(k in c.lower() for k in ['saving','thrift','balance','sav']):
                            savings_col = c
                            break

                    if savings_col:
                        try:
                            savings_val = float(str(row[savings_col]).replace(',',''))
                            max_elig = savings_val * 4
                            st.info(f"Your Savings ({savings_col}): Rs.{savings_val} | Max Eligible: Rs.{max_elig} | Asking: Rs.{loan_amount}")

                            if loan_amount <= max_elig:
                                st.success(f"✅ ELIGIBLE for Rs.{loan_amount}")
                                st.balloons()
                                st.write(f"Reason: Amount {loan_amount} <= 4x Savings ({max_elig})")
                            else:
                                st.error(f"❌ NOT ELIGIBLE for Rs.{loan_amount}")
                                st.write(f"Reason: Asking {loan_amount} is more than max {max_elig}. Reduce amount or increase savings.")
                        except:
                            st.error("Savings value not number, check CSV")
                    else:
                        st.warning("No Savings column found. Tell me your column names")
                else:
                    st.error(f"Member ID {member_id} not found in CSV")
        else:
            st.warning("sample_data.csv not found in GitHub")
else:
    st.title("SHG Loan Eligibility - Ellapuram")
    st.info("👈 Login from sidebar to check amount-based eligibility")
    st.code("Bank Officer: officer / officer123\nLeader: leader / leader123\nMember: member / member123")
