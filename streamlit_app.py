import streamlit as st
import pandas as pd
import os, glob
from datetime import datetime

st.set_page_config(page_title="SHG Loan - Ellapuram", page_icon="🏦", layout="centered")

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
            if 'livelihood' in c.lower(): return c
    if col_type == "approval":
        for c in df.columns:
            if 'approval' in c.lower(): return c
    return None

if 'pending_leader' not in st.session_state: st.session_state['pending_leader'] = []
if 'pending_officer' not in st.session_state: st.session_state['pending_officer'] = []
if 'selected_leader_id' not in st.session_state: st.session_state['selected_leader_id'] = None
if 'app_status' not in st.session_state: st.session_state['app_status'] = {} # MemberID -> Status tracking

def update_status(member_id, status, reason="", level=""):
    st.session_state['app_status'][member_id] = {
        'status': status,
        'reason': reason,
        'level': level,
        'time': datetime.now().strftime("%d-%m-%Y %H:%M")
    }

if 'logged_in' in st.session_state and st.session_state['logged_in']:

    # --- 3. BANK OFFICER ---
    if st.session_state['role'] == "Bank Officer":
        st.title("🏦 Bank Officer Dashboard")
        if len(st.session_state['pending_officer'])==0:
            st.info("No applications from Leader.")
        else:
            df_list = pd.DataFrame(st.session_state['pending_officer'])
            st.dataframe(df_list, use_container_width=True)
            member_ids = [x['id'] for x in st.session_state['pending_officer']]
            sel = st.selectbox("Select Member ID", member_ids)
            app = next((x for x in st.session_state['pending_officer'] if x['id']==sel), None)
            if app:
                c1,c2 = st.columns(2)
                with c1:
                    if st.button(f"✅ Disburse {sel}"):
                        update_status(sel, "✅ APPROVED & DISBURSED", "Loan disbursed successfully", "Bank Officer")
                        st.balloons()
                        st.success(f"{sel} Disbursed!")
                        st.session_state['pending_officer'] = [x for x in st.session_state['pending_officer'] if x['id']!=sel]
                        st.rerun()
                with c2:
                    st.write("Reject with Reason:")
                    rej_reason = st.text_input("Reason for rejection", key=f"off_rej_{sel}", placeholder="e.g. Documents incomplete, CIBIL low")
                    if st.button(f"❌ Reject {sel}"):
                        if not rej_reason: rej_reason = "Rejected by Bank Officer - No reason given"
                        update_status(sel, "❌ REJECTED BY BANK OFFICER", rej_reason, "Bank Officer")
                        st.session_state['pending_officer'] = [x for x in st.session_state['pending_officer'] if x['id']!=sel]
                        st.error(f"{sel} Rejected")
                        st.rerun()

    # --- 2. SHG LEADER WITH REASON ---
    elif st.session_state['role'] == "SHG Leader":
        st.title("👩‍💼 SHG Leader Dashboard")
        st.subheader(f"Pending: {len(st.session_state['pending_leader'])} Applications")

        if len(st.session_state['pending_leader'])==0:
            st.info("No pending applications.")
        else:
            list_data = [{"S.No": i+1, "Member ID": app['id'], "Loan": f"Rs.{app['amount']}"} for i, app in enumerate(st.session_state['pending_leader'])]
            st.table(pd.DataFrame(list_data))

            member_ids = [app['id'] for app in st.session_state['pending_leader']]
            selected = st.selectbox("Select Member ID", member_ids)
            if st.button("🔍 View & Check Eligibility", type="primary"):
                st.session_state['selected_leader_id'] = selected

            if st.session_state['selected_leader_id']:
                sel_id = st.session_state['selected_leader_id']
                app = next((x for x in st.session_state['pending_leader'] if x['id']==sel_id), None)
                if app:
                    st.divider()
                    st.write(f"## Member: {sel_id}")
                    if df is not None:
                        mask = df.astype(str).apply(lambda x: x.str.contains(sel_id, na=False)).any(axis=1)
                        found = df[mask]
                        if not found.empty:
                            row = found.iloc[0]
                            liv_col = find_col(df, "livelihood")
                            appr_col = find_col(df, "approval")
                            liv_val = str(row[liv_col]).strip() if liv_col else "NA"
                            appr_val = str(row[appr_col]).strip() if appr_col else "NA"

                            is_liv_ok = liv_val.lower() not in ['','--','nan','none','0','na']
                            is_bm_ok = 'approved' in appr_val.lower()

                            if is_liv_ok: st.success(f"✅ Primary Livelihoods: {liv_val}")
                            else: st.error(f"❌ Primary Livelihoods: {liv_val} - FAILED")

                            if is_bm_ok: st.success(f"✅ Approval Status: {appr_val}")
                            else: st.error(f"❌ Approval Status: {appr_val} - NOT Approved by BM")

                            st.markdown("---")
                            if is_liv_ok and is_bm_ok:
                                if st.button(f"📤 Forward {sel_id} to Bank Officer", type="primary"):
                                    new_o = {'id': sel_id, 'amount': app['amount'], 'livelihood': liv_val, 'bm_status': appr_val}
                                    if not any(x['id']==sel_id for x in st.session_state['pending_officer']):
                                        st.session_state['pending_officer'].append(new_o)
                                    update_status(sel_id, "⏳ PENDING WITH BANK OFFICER", "Approved by SHG Leader, forwarded to Bank", "SHG Leader")
                                    st.session_state['pending_leader'] = [x for x in st.session_state['pending_leader'] if x['id']!=sel_id]
                                    st.session_state['selected_leader_id'] = None
                                    st.rerun()
                            else:
                                st.error("Cannot forward - As per your screenshot")
                                # REJECTION WITH REASON
                                reason = st.text_area("Enter Rejection Reason (Member will see this)",
                                    value=f"Primary Livelihoods: {liv_val} | Approval Status: {appr_val} - Not Approved by BM. Please contact BM.",
                                    key=f"reason_{sel_id}")
                                if st.button(f"❌ Reject & Send Back {sel_id}"):
                                    update_status(sel_id, "❌ REJECTED BY SHG LEADER", reason, "SHG Leader")
                                    st.session_state['pending_leader'] = [x for x in st.session_state['pending_leader'] if x['id']!=sel_id]
                                    st.session_state['selected_leader_id'] = None
                                    st.rerun()

    # --- 1. MEMBER WITH STATUS TRACKER ---
    else:
        st.title("SHG Loan Eligibility Checker")

        # NEW: STATUS TRACKER ON TOP
        st.subheader("📊 Track Your Application Status")
        track_id = st.text_input("Enter Member ID to Track Status", value="290047031286", key="track")
        if st.button("🔎 Track Status"):
            if track_id in st.session_state['app_status']:
                info = st.session_state['app_status'][track_id]
                st.write(f"**Member ID: {track_id}**")
                if "REJECTED" in info['status']:
                    st.error(f"{info['status']}")
                elif "APPROVED" in info['status']:
                    st.success(f"{info['status']}")
                else:
                    st.warning(f"{info['status']}")

                st.write(f"**Level:** {info['level']}")
                st.write(f"**Reason / Remarks:** {info['reason']}")
                st.write(f"**Last Updated:** {info['time']}")
            else:
                st.info("No application history found for this ID. Check eligibility below to apply.")

        st.divider()
        st.subheader("Apply for New Loan")

        member_id = st.text_input("Enter Member ID", value="290047031286", key="apply")
        loan_amount = st.number_input("Loan Amount", min_value=1000, step=5000, value=10000)

        # Show existing status for this ID before applying
        if member_id in st.session_state['app_status']:
            info = st.session_state['app_status'][member_id]
            if "REJECTED" in info['status']:
                st.warning(f"Previous Status: {info['status']} - Reason: {info['reason']}")

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
                    for col_type, name in [(active_col,"Member Active"), (ekyc_col,"eKYC"), (mobile_col,"Mobile"), (bank_col,"Bank Account")]:
                        if col_type:
                            val=str(row[col_type]).strip()
                            if name=="Member Active":
                                is_ok=val.lower().strip()=='active'
                            elif name=="eKYC":
                                is_ok='verif' in val.lower() or val.lower() in ['yes','verified','1']
                            else:
                                is_ok=val not in ['','--','nan'] and len(val)>=3
                            if is_ok: st.success(f"✅ {name}: {val}")
                            else: st.error(f"❌ {name}: {val} - FAILED"); all_ok=False
                    if all_ok:
                        st.success("✅ ELIGIBLE")
                        st.session_state['eligible_member']=member_id
                        st.session_state['eligible_amount']=loan_amount
                        st.session_state['show_submit']=True
                    else:
                        st.error("❌ NOT ELIGIBLE")
                        update_status(member_id, "❌ AUTO-REJECTED - Eligibility Failed", "Failed Active/eKYC/Mobile/Bank check", "System")
                        st.session_state['show_submit']=False

        if st.session_state.get('show_submit', False):
            if st.button("📤 Submit to SHG Leader"):
                new_app={'id':st.session_state['eligible_member'],'amount':st.session_state['eligible_amount']}
                if not any(x['id']==new_app['id'] for x in st.session_state['pending_leader']):
                    st.session_state['pending_leader'].append(new_app)
                update_status(new_app['id'], "⏳ PENDING WITH SHG LEADER", "Eligible and submitted to Leader for livelihood & BM approval verification", "SHG Member")
                st.success("Submitted to Leader! Now track status above.")
                st.session_state['show_submit']=False

else:
    st.title("SHG Loan - Ellapuram")
    st.info("👈 Login")
    st.code("member/member123\nleader/leader123\nofficer/officer123")
