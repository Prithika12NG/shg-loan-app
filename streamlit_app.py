import streamlit as st
import pandas as pd
import os, glob

st.set_page_config(page_title="SHG Loan - Ellapuram 3 Level", page_icon="🏦", layout="centered")

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
        except: return None
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
        st.sidebar.error("Wrong Login")

df = load_data()

def find_col(df, col_type):
    cols_lower = {c.lower().strip(): c for c in df.columns}
    if col_type == "status":
        if 'status' in cols_lower: return cols_lower['status']
        for c in df.columns:
            if 'marital' in c.lower(): continue
            try:
                vals = [str(v).lower().strip() for v in df[c].tolist()[:50]]
                if 'active' in vals or 'inactive' in vals: return c
            except: pass
    if col_type == "ekyc":
        for c in df.columns:
            if 'ekyc' in c.lower() or 'kyc' in c.lower(): return c
    if col_type == "mobile":
        for c in df.columns:
            if 'mobile' in c.lower() or 'phone' in c.lower(): return c
    if col_type == "bank":
        for c in df.columns:
            if 'bank' in c.lower() and 'loan' not in c.lower(): return c
    if col_type == "livelihood":
        for c in df.columns:
            if 'livelihood' in c.lower() or 'primary' in c.lower(): return c
    if col_type == "approval":
        for c in df.columns:
            if 'approval' in c.lower(): return c
    return None

if 'pending_leader' not in st.session_state: st.session_state['pending_leader'] = []
if 'pending_officer' not in st.session_state: st.session_state['pending_officer'] = []
if 'selected_leader_id' not in st.session_state: st.session_state['selected_leader_id'] = None

if 'logged_in' in st.session_state and st.session_state['logged_in']:

    # --- 3. BANK OFFICER ---
    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        if len(st.session_state['pending_officer'])==0:
            st.info("No applications from Leader yet.")
        else:
            # LIST VIEW FOR OFFICER TOO
            st.write(f"**{len(st.session_state['pending_officer'])} Applications Forwarded by Leader**")
            df_list = pd.DataFrame(st.session_state['pending_officer'])
            st.dataframe(df_list, use_container_width=True)

            sel = st.selectbox("Select Member ID to Action", [x['id'] for x in st.session_state['pending_officer']])
            app = next((x for x in st.session_state['pending_officer'] if x['id']==sel), None)
            if app:
                st.write(f"Details: {app}")
                c1,c2 = st.columns(2)
                with c1:
                    if st.button(f"✅ Disburse {sel}"):
                        st.balloons()
                        st.success("Disbursed!")
                        st.session_state['pending_officer'] = [x for x in st.session_state['pending_officer'] if x['id']!=sel]
                        st.rerun()
                with c2:
                    if st.button(f"❌ Reject {sel}"):
                        st.session_state['pending_officer'] = [x for x in st.session_state['pending_officer'] if x['id']!=sel]
                        st.rerun()

    # --- 2. SHG LEADER - NEW LIST VIEW ---
    elif st.session_state['role'] == "SHG Leader":
        st.title("👩‍💼 SHG Leader Dashboard")
        st.subheader(f"Pending Applications: {len(st.session_state['pending_leader'])}")

        if len(st.session_state['pending_leader'])==0:
            st.info("No applications pending.")
        else:
            # STEP 1: LIST VIEW
            st.write("### 📋 Applications List (Click View to check eligibility)")
            list_data = []
            for i, app in enumerate(st.session_state['pending_leader']):
                list_data.append({"S.No": i+1, "Member ID": app['id'], "Loan Amount": f"Rs.{app['amount']}"})

            df_list = pd.DataFrame(list_data)
            st.table(df_list)

            # Select box for list
            member_ids = [app['id'] for app in st.session_state['pending_leader']]
            selected = st.selectbox("Select Member ID to Verify", member_ids, key="leader_select")

            if st.button("🔍 View & Check Eligibility", type="primary"):
                st.session_state['selected_leader_id'] = selected

            # STEP 2: DETAIL CHECK AFTER CLICK
            if st.session_state['selected_leader_id']:
                sel_id = st.session_state['selected_leader_id']
                app = next((x for x in st.session_state['pending_leader'] if x['id']==sel_id), None)

                if app:
                    st.divider()
                    st.write(f"## Checking: Member ID {sel_id} | Loan: Rs.{app['amount']}")

                    if df is not None:
                        mask = df.astype(str).apply(lambda x: x.str.contains(sel_id, na=False)).any(axis=1)
                        found = df[mask]
                        if not found.empty:
                            row = found.iloc[0]
                            liv_col = find_col(df, "livelihood")
                            appr_col = find_col(df, "approval")

                            liv_val = str(row[liv_col]).strip() if liv_col else "Not Found"
                            appr_val = str(row[appr_col]).strip() if appr_col else "Not Found"

                            is_liv_ok = liv_val.lower() not in ['','--','nan','none','0','not available','na']
                            is_bm_ok = 'approved' in appr_val.lower()

                            if is_liv_ok:
                                st.success(f"✅ Primary Livelihoods: {liv_val}")
                            else:
                                st.error(f"❌ Primary Livelihoods: {liv_val} - FAILED")

                            if is_bm_ok:
                                st.success(f"✅ Approval Status: {appr_val} (Approved by BM)")
                            else:
                                st.error(f"❌ Approval Status: {appr_val} - NOT Approved by BM - Pending with Bookkeeper etc")

                            st.markdown("---")
                            if is_liv_ok and is_bm_ok:
                                st.success("✅ Leader Verification PASSED")
                                if st.button(f"📤 Forward {sel_id} to Bank Officer", type="primary"):
                                    new_o = {'id': sel_id, 'amount': app['amount'], 'livelihood': liv_val, 'bm_status': appr_val}
                                    if not any(x['id']==sel_id for x in st.session_state['pending_officer']):
                                        st.session_state['pending_officer'].append(new_o)
                                    st.session_state['pending_leader'] = [x for x in st.session_state['pending_leader'] if x['id']!=sel_id]
                                    st.session_state['selected_leader_id'] = None
                                    st.success("Forwarded!")
                                    st.rerun()
                            else:
                                st.error("Cannot forward - Check failed as in your screenshot")
                                if st.button(f"❌ Reject & Send Back {sel_id}"):
                                    st.session_state['pending_leader'] = [x for x in st.session_state['pending_leader'] if x['id']!=sel_id]
                                    st.session_state['selected_leader_id'] = None
                                    st.rerun()

    # --- 1. MEMBER ---
    else:
        st.title("SHG Loan Eligibility Checker")
        member_id = st.text_input("Enter Member ID", value="290047031286")
        loan_amount = st.number_input("Loan Amount", min_value=1000, step=5000, value=10000)

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
                    all_ok = True
                    checks=[]
                    if active_col:
                        val=str(row[active_col]).strip()
                        is_ok=val.lower().strip()=='active'
                        checks.append(("Member Active",is_ok,val))
                        if not is_ok: all_ok=False
                    if ekyc_col:
                        val=str(row[ekyc_col]).strip()
                        is_ok='verif' in val.lower() or val.lower() in ['yes','verified','1']
                        checks.append(("eKYC Verified",is_ok,val))
                        if not is_ok: all_ok=False
                    if mobile_col:
                        val=str(row[mobile_col]).strip()
                        is_ok=val not in ['','--','nan'] and len(val)>=5
                        checks.append(("Mobile Verified",is_ok,val))
                        if not is_ok: all_ok=False
                    if bank_col:
                        val=str(row[bank_col]).strip()
                        is_ok=val not in ['','--','nan'] and len(val)>3
                        checks.append(("Bank Account Available",is_ok,val))
                        if not is_ok: all_ok=False
                    for n,s,v in checks:
                        if s: st.success(f"✅ {n}: {v}")
                        else: st.error(f"❌ {n}: {v} - FAILED")
                    if all_ok:
                        st.success(f"✅ ELIGIBLE")
                        st.session_state['eligible_member']=member_id
                        st.session_state['eligible_amount']=loan_amount
                        st.session_state['show_submit']=True
                    else:
                        st.error("❌ NOT ELIGIBLE")
                        st.session_state['show_submit']=False

        if st.session_state.get('show_submit', False):
            if st.button("📤 Submit to SHG Leader"):
                new_app={'id':st.session_state['eligible_member'],'amount':st.session_state['eligible_amount']}
                if not any(x['id']==new_app['id'] for x in st.session_state['pending_leader']):
                    st.session_state['pending_leader'].append(new_app)
                st.success("Submitted to Leader! PENDING WITH LEADER")
                st.session_state['show_submit']=False

else:
    st.title("SHG Loan - Ellapuram")
    st.info("👈 Login")
    st.code("member/member123\nleader/leader123\nofficer/officer123")
