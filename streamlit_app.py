import streamlit as st
import pandas as pd
import os, glob
from datetime import datetime

st.set_page_config(page_title="SHG Loan - Ellapuram Block", page_icon="🏦", layout="wide")

# 53 Panchayats of Ellapuram
PANCHAYAT_LIST = [
    "43 Panapakkam", "82 Panapakkam", "Akkarambakkam", "Alapakkam", "Amirthanallur",
    "Athangikavanoor", "Athivakkam", "Athupakkam", "Ayalancheri", "Azhinjivakkam",
    "Enambakkam", "Guruvoyal", "Kakkavakkam", "Kalpattu", "Kannigaipair",
    "Kannigapuram", "Kilambakkam", "Koduveli", "Kommakambedu", "Kumarapettai",
    "Latchivakkam", "Maduravasal", "Magaral", "Malandur", "Mambalam",
    "Manjankarani", "Neiveli", "Pagalmedu", "Palavakkam", "Panayanjeri",
    "Perandur", "Periyapalayam", "Perumudivakkam", "Poochiathipattu", "Poorivakkam",
    "Punnapakkam", "Sembedu", "Sengarai", "Senjiagaram", "Sennankarani",
    "Sethupakkam", "Soolaimeni", "Thamaraikuppam", "Thamaraipakkam", "Thandalam",
    "Tharaadchi", "Thirukandalam", "Thirunilai", "Tholavedu", "Thumbakkam",
    "Vadamadurai", "Vannankuppam", "Vengal"
]

def make_username(name):
    return "".join(c.lower() for c in name if c.isalnum())

PANCHAYAT_USERS = {make_username(p): p for p in PANCHAYAT_LIST}

@st.cache_data
def load_data():
    folder = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(folder, "*.csv"))
    if not files:
        files = glob.glob(os.path.join(folder, "*.xlsx"))
    if files:
        try:
            df = pd.read_csv(files[0]) if files[0].endswith('.csv') else pd.read_excel(files[0])
            df.columns = [c.strip() for c in df.columns]
            return df
        except:
            return None
    return None

def find_col(df, col_type):
    if df is None:
        return None
    for c in df.columns:
        lc = c.lower()
        if col_type == "status" and lc.strip() == "status":
            return c
        if col_type == "ekyc" and "ekyc" in lc:
            return c
        if col_type == "mobile" and ("mobile" in lc or "phone" in lc):
            return c
        if col_type == "bank" and "bank" in lc and "loan" not in lc:
            return c
        if col_type == "livelihood" and "livelihood" in lc:
            return c
        if col_type == "approval" and "approval" in lc:
            return c
        if col_type == "panchayat" and ("panchayat" in lc or "gram" in lc or "village" in lc):
            return c
    if col_type == "status":
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

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'pending_bmmu' not in st.session_state:
    st.session_state['pending_bmmu'] = []
if 'pending_officer' not in st.session_state:
    st.session_state['pending_officer'] = []
if 'app_status' not in st.session_state:
    st.session_state['app_status'] = {}
if 'page' not in st.session_state:
    st.session_state['page'] = 'dashboard'
if 'selected_bmmu_id' not in st.session_state:
    st.session_state['selected_bmmu_id'] = None

def update_status(mid, status, reason, level, panchayat=""):
    st.session_state['app_status'][mid] = {
        'status': status,
        'reason': reason,
        'level': level,
        'panchayat': panchayat,
        'time': datetime.now().strftime("%d-%m-%Y %H:%M")
    }

df = load_data()

# SIDEBAR LOGIN / LOGOUT
with st.sidebar:
    if not st.session_state['logged_in']:
        st.title("Login")
        role = st.selectbox("Select Role", ["Panchayat", "BMMU", "Bank Officer"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            ok = False
            panchayat_name = ""
            if role == "Panchayat":
                if username.lower() in PANCHAYAT_USERS and password == "test123":
                    ok = True
                    panchayat_name = PANCHAYAT_USERS[username.lower()]
            elif role == "BMMU":
                if username.lower() == "bmmu" and password == "bmmu123":
                    ok = True
            elif role == "Bank Officer":
                if username.lower() == "officer" and password == "officer123":
                    ok = True
            if ok:
                st.session_state['logged_in'] = True
                st.session_state['role'] = role
                st.session_state['username'] = username
                st.session_state['panchayat_name'] = panchayat_name if role == "Panchayat" else ""
                st.session_state['page'] = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid login. Panchayat: vengal/test123, BMMU: bmmu/bmmu123, Officer: officer/officer123")
    else:
        st.success(f"Logged in as: {st.session_state['role']}")
        if st.session_state['role'] == "Panchayat":
            st.info(f"{st.session_state['panchayat_name']}")
        st.write(f"User: {st.session_state['username']}")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['page'] = 'dashboard'
            st.rerun()

if not st.session_state['logged_in']:
    st.title("SHG Loan - Ellapuram Block")
    st.info("Login from sidebar. Flow: Panchayat -> BMMU -> Bank Officer")
else:
    role = st.session_state['role']
    panchayat_name = st.session_state.get('panchayat_name', '')

    def get_counts(filter_panchayat=None):
        statuses = st.session_state['app_status']
        if filter_panchayat:
            statuses = {k: v for k, v in statuses.items() if v.get('panchayat') == filter_panchayat}

        if filter_panchayat:
            p_bmmu = len([x for x in st.session_state['pending_bmmu'] if x.get('panchayat') == filter_panchayat])
            p_bank = len([x for x in st.session_state['pending_officer'] if x.get('panchayat') == filter_panchayat])
        else:
            p_bmmu = len(st.session_state['pending_bmmu'])
            p_bank = len(st.session_state['pending_officer'])

        # --- FIXED LOGIC FOR BANK OFFICER ---
        if role == "Bank Officer":
            rejected = len([v for v in statuses.values() if "REJECTED BY BANK" in v['status']])
            accepted = len([v for v in statuses.values() if "DISBURSED" in v['status']])
            total = p_bank + rejected + accepted
            p_bmmu = 0 # Bank officer should not see BMMU pending
        elif role == "BMMU":
            rejected = len([v for v in statuses.values() if "REJECTED BY BMMU" in v['status']])
            accepted = len([v for v in statuses.values() if "DISBURSED" in v['status']])
            forwarded = len([v for v in statuses.values() if "PENDING WITH BANK" in v['status']])
            total = p_bmmu + p_bank + rejected + accepted + forwarded
        else: # Panchayat
            rejected = len([v for v in statuses.values() if "REJECTED" in v['status']])
            accepted = len([v for v in statuses.values() if "APPROVED" in v['status'] or "DISBURSED" in v['status']])
            total = len(statuses)

        return total, p_bmmu, p_bank, rejected, accepted

    if st.session_state['page'] == 'dashboard':
        filter_p = panchayat_name if role == "Panchayat" else None
        total, p_bmmu, p_bank, rej, acc = get_counts(filter_p)
        st.title(f"Dashboard - {role} - {panchayat_name if filter_p else ''}")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total", total)
        c2.metric("Pending at BMMU", p_bmmu)
        c3.metric("Pending at Bank", p_bank)
        c4.metric("Rejected", rej)
        c5.metric("Accepted", acc)
        st.divider()
        if role == "Panchayat":
            colA, colB = st.columns(2)
            with colA:
                if st.button("New Loan Application", type="primary", use_container_width=True):
                    st.session_state['page'] = 'new_application'
                    st.rerun()
            with colB:
                if st.button("Track Application Status", use_container_width=True):
                    st.session_state['page'] = 'track'
                    st.rerun()
            if total > 0:
                st.write("My Submissions")
                my_apps = {k: v for k, v in st.session_state['app_status'].items() if v.get('panchayat') == panchayat_name}
                st.dataframe(pd.DataFrame.from_dict(my_apps, orient='index'), use_container_width=True)
        elif role == "BMMU":
            if st.button("View Pending Applications", type="primary"):
                st.session_state['page'] = 'bmmu_list'
                st.rerun()
        elif role == "Bank Officer":
            if st.button("View Bank Pending List", type="primary"):
                st.session_state['page'] = 'officer_list'
                st.rerun()

    elif st.session_state['page'] == 'new_application':
        st.title("New Loan Application")
        if st.button("Back to Dashboard"):
            st.session_state['page'] = 'dashboard'
            st.rerun()
        st.subheader(f"Panchayat: {panchayat_name}")
        member_id = st.text_input("Enter Member ID", value="290047031286")
        loan_amount = st.number_input("Loan Amount Rs.", min_value=1000, step=5000, value=10000)

        if st.button("Check Eligibility"):
            if df is not None and member_id:
                mask = df.astype(str).apply(lambda x: x.str.contains(member_id, na=False)).any(axis=1)
                found = df[mask]
                if not found.empty:
                    row = found.iloc[0]
                    panchayat_col = find_col(df, "panchayat")
                    if panchayat_col:
                        member_panchayat = str(row[panchayat_col]).strip()
                        if member_panchayat.lower()!= panchayat_name.lower():
                            st.error("ACCESS DENIED - This member is not from your Panchayat")
                            st.warning(f"This Member ID {member_id} belongs to {member_panchayat} Panchayat, not your {panchayat_name} Panchayat. You can only submit members of your own panchayat.")
                            st.stop()
                    ac = find_col(df, "status")
                    ek = find_col(df, "ekyc")
                    mo = find_col(df, "mobile")
                    ba = find_col(df, "bank")
                    all_ok = True
                    checks = []
                    if ac:
                        v = str(row[ac]).strip()
                        is_ok = v.lower().strip() == 'active'
                        checks.append(("Member Active", is_ok, v))
                        all_ok = all_ok and is_ok
                    if ek:
                        v = str(row[ek]).strip()
                        is_ok = 'verif' in v.lower() or v.lower() in ['yes', 'verified', '1']
                        checks.append(("eKYC", is_ok, v))
                        all_ok = all_ok and is_ok
                    if mo:
                        v = str(row[mo]).strip()
                        is_ok = v not in ['', '--', 'nan'] and len(v) >= 5
                        checks.append(("Mobile", is_ok, v))
                        all_ok = all_ok and is_ok
                    if ba:
                        v = str(row[ba]).strip()
                        is_ok = v not in ['', '--', 'nan'] and len(v) > 3
                        checks.append(("Bank Account", is_ok, v))
                        all_ok = all_ok and is_ok
                    for n, s, v in checks:
                        if s:
                            st.success(f"✅ {n}: {v}")
                        else:
                            st.error(f"❌ {n}: {v}")
                    if panchayat_col:
                        st.info(f"Panchayat Verified: {member_panchayat}")
                    if all_ok:
                        st.success("ELIGIBLE - Ready to submit to BMMU")
                        st.session_state['eligible_member'] = member_id
                        st.session_state['eligible_amount'] = loan_amount
                        st.session_state['show_submit'] = True
                    else:
                        st.error("NOT ELIGIBLE")
                        update_status(member_id, "REJECTED - Eligibility Failed", "Failed check", "Panchayat", panchayat_name)
                        st.session_state['show_submit'] = False
                else:
                    st.error("Member ID not found")
        if st.session_state.get('show_submit', False):
            if st.button("Submit to BMMU", type="primary"):
                new_app = {'id': st.session_state['eligible_member'], 'amount': st.session_state['eligible_amount'], 'panchayat': panchayat_name}
                if not any(x['id'] == new_app['id'] for x in st.session_state['pending_bmmu']):
                    st.session_state['pending_bmmu'].append(new_app)
                update_status(new_app['id'], "PENDING AT BMMU", "Submitted by Panchayat", "Panchayat", panchayat_name)
                st.success("Submitted to BMMU")
                st.session_state['show_submit'] = False
                st.session_state['page'] = 'dashboard'
                st.rerun()

    elif st.session_state['page'] == 'track':
        st.title("Track Application Status")
        if st.button("Back to Dashboard"):
            st.session_state['page'] = 'dashboard'
            st.rerun()
        track_id = st.text_input("Enter Member ID")
        if st.button("Track"):
            if track_id in st.session_state['app_status']:
                info = st.session_state['app_status'][track_id]
                if "REJECTED" in info['status']:
                    st.error(info['status'])
                elif "APPROVED" in info['status']:
                    st.success(info['status'])
                else:
                    st.warning(info['status'])
                st.write(f"Panchayat: {info.get('panchayat','')}")
                st.write(f"Level: {info['level']}")
                st.write(f"Reason: {info['reason']}")
                st.write(f"Time: {info['time']}")
            else:
                st.info("No history")

    elif st.session_state['page'] == 'bmmu_list':
        st.title("BMMU Dashboard")
        if st.button("Back to Dashboard"):
            st.session_state['page'] = 'dashboard'
            st.session_state['selected_bmmu_id'] = None
            st.rerun()
        if len(st.session_state['pending_bmmu']) == 0:
            st.info("No pending applications")
        else:
            list_data = [{"S.No": i+1, "Member ID": x['id'], "Amount": x['amount'], "Panchayat": x.get('panchayat','')} for i, x in enumerate(st.session_state['pending_bmmu'])]
            st.table(pd.DataFrame(list_data))
            sel = st.selectbox("Select Member ID", [x['id'] for x in st.session_state['pending_bmmu']])
            if st.button("View & Check Eligibility", type="primary"):
                st.session_state['selected_bmmu_id'] = sel
            if st.session_state['selected_bmmu_id']:
                sel_id = st.session_state['selected_bmmu_id']
                app = next((x for x in st.session_state['pending_bmmu'] if x['id'] == sel_id), None)
                if app and df is not None:
                    st.divider()
                    st.write(f"Checking: {sel_id} | Panchayat: {app.get('panchayat')}")
                    mask = df.astype(str).apply(lambda x: x.str.contains(sel_id, na=False)).any(axis=1)
                    found = df[mask]
                    if not found.empty:
                        row = found.iloc[0]
                        liv_col = find_col(df, "livelihood")
                        appr_col = find_col(df, "approval")
                        liv_val = str(row[liv_col]).strip() if liv_col else "NA"
                        appr_val = str(row[appr_col]).strip() if appr_col else "NA"
                        is_liv = liv_val.lower() not in ['', '--', 'nan', 'none', '0', 'na']
                        is_bm = 'approved' in appr_val.lower()
                        if is_liv:
                            st.success(f"Primary Livelihoods: {liv_val}")
                        else:
                            st.error(f"Primary Livelihoods: {liv_val}")
                        if is_bm:
                            st.success(f"Approval Status: {appr_val}")
                        else:
                            st.error(f"Approval Status: {appr_val} - NOT Approved by BM")
                        if is_liv and is_bm:
                            if st.button(f"Forward {sel_id} to Bank Officer", type="primary"):
                                new_o = {'id': sel_id, 'amount': app['amount'], 'panchayat': app.get('panchayat',''), 'livelihood': liv_val, 'bm_status': appr_val}
                                if not any(x['id'] == sel_id for x in st.session_state['pending_officer']):
                                    st.session_state['pending_officer'].append(new_o)
                                update_status(sel_id, "PENDING WITH BANK OFFICER", "Approved by BMMU", "BMMU", app.get('panchayat',''))
                                st.session_state['pending_bmmu'] = [x for x in st.session_state['pending_bmmu'] if x['id']!= sel_id]
                                st.session_state['selected_bmmu_id'] = None
                                st.rerun()
                        else:
                            reason = st.text_area("Rejection Reason", value=f"Primary Livelihoods: {liv_val} | Approval Status: {appr_val} - Not Approved by BM", key=f"rej_{sel_id}")
                            if st.button(f"Reject {sel_id}"):
                                update_status(sel_id, "REJECTED BY BMMU", reason, "BMMU", app.get('panchayat',''))
                                st.session_state['pending_bmmu'] = [x for x in st.session_state['pending_bmmu'] if x['id']!= sel_id]
                                st.session_state['selected_bmmu_id'] = None
                                st.rerun()

    elif st.session_state['page'] == 'officer_list':
        st.title("Bank Officer - Final Approval")
        if st.button("Back to Dashboard"):
            st.session_state['page'] = 'dashboard'
            st.rerun()
        if len(st.session_state['pending_officer']) == 0:
            st.info("No applications from BMMU")
        else:
            st.dataframe(pd.DataFrame(st.session_state['pending_officer']), use_container_width=True)
            sel = st.selectbox("Select Member ID", [x['id'] for x in st.session_state['pending_officer']])
            app = next((x for x in st.session_state['pending_officer'] if x['id'] == sel), None)
            if app:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"Disburse {sel}", type="primary"):
                        update_status(sel, "APPROVED & DISBURSED", "Loan disbursed", "Bank Officer", app.get('panchayat',''))
                        st.balloons()
                        st.session_state['pending_officer'] = [x for x in st.session_state['pending_officer'] if x['id']!= sel]
                        st.rerun()
                with c2:
                    rej_reason = st.text_input("Rejection Reason", key=f"off_{sel}")
                    if st.button(f"Reject {sel}"):
                        if not rej_reason:
                            rej_reason = "Rejected by Bank"
                        update_status(sel, "REJECTED BY BANK OFFICER", rej_reason, "Bank Officer", app.get('panchayat',''))
                        st.session_state['pending_officer'] = [x for x in st.session_state['pending_officer'] if x['id']!= sel]
                        st.rerun()
