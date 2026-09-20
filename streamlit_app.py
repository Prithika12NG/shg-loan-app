import streamlit as st
import pandas as pd

st.set_page_config(page_title="SHG Loan App", layout="wide")

# --- DAY 2: LOGIN SYSTEM ---
st.sidebar.title("🔐 Login")

role = st.sidebar.selectbox("Select Role", ["SHG Member", "SHG Leader", "Bank Officer"])

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_btn = st.sidebar.button("Login")

# Simple login logic (for college project - no database needed)
def check_login(role, username, password):
    if role == "Bank Officer" and username == "officer" and password == "officer123":
        return True
    if role == "SHG Leader" and username == "leader" and password == "leader123":
        return True
    if role == "SHG Member" and username == "member" and password == "member123":
        return True
    return False

if login_btn:
    if check_login(role, username, password):
        st.session_state['logged_in'] = True
        st.session_state['role'] = role
        st.success(f"Welcome {role} : {username}")
    else:
        st.error("Wrong Username/Password")
        st.session_state['logged_in'] = False

# --- MAIN APP AFTER LOGIN ---
if 'logged_in' in st.session_state and st.session_state['logged_in']:

    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        st.write("All Loan Applications")
        # Show all data
        df = pd.read_csv("sample_data.csv")
        st.dataframe(df)
        
        # Approve/Reject Button
        selected_id = st.selectbox("Select Loan ID to Action", df['member_id'] if 'member_id' in df.columns else df.iloc[:,0])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve Loan"):
                st.success(f"Loan {selected_id} Approved!")
        with col2:
            if st.button("❌ Reject Loan"):
                st.error(f"Loan {selected_id} Rejected!")

    elif st.session_state['role'] == "SHG Member":
        st.title("👩 SHG Member - Eligibility Check")
        # Your old eligibility code comes here
        loan_amt = st.number_input("Loan Amount", min_value=1000)
        if st.button("Check Eligibility"):
            st.success("Eligible! Contact your Leader")

    elif st.session_state['role'] == "SHG Leader":
        st.title("👩‍💼 SHG Leader - Apply Loan")
        shg_name = st.text_input("SHG Name")
        members = st.number_input("No of Members", min_value=1)
        if st.button("Apply for Loan"):
            st.success(f"Application Sent for {shg_name}")

else:
    st.title("SHG Loan Eligibility App")
    st.info("👈 Please Login from left sidebar to continue")
    st.write("**Demo Logins for Viva:**")
    st.code("Bank Officer -> username: officer / password: officer123\nSHG Leader -> username: leader / password: leader123\nSHG Member -> username: member / password: member123")
