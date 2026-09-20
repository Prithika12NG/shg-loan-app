# --- NEW APPLICATION PAGE (Panchayat) WITH VALIDATION ---
    elif st.session_state['page']=='new_application':
        st.title("➕ New Loan Application")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state['page']='dashboard'; st.rerun()

        st.subheader(f"Panchayat: {panchayat_name} - Search Member Eligibility")
        member_id = st.text_input("Enter Member ID", value="290047031286")
        loan_amount = st.number_input("Loan Amount Rs.", min_value=1000, step=5000, value=10000)

        if st.button("Check Eligibility"):
            if df is not None and member_id:
                mask = df.astype(str).apply(lambda x: x.str.contains(member_id, na=False)).any(axis=1)
                found = df[mask]
                if not found.empty:
                    row = found.iloc[0]

                    # --- NEW: FIND PANCHAYAT COLUMN FROM YOUR EXCEL ---
                    panchayat_col = None
                    for c in df.columns:
                        lc = c.lower()
                        if 'panchayat' in lc or 'gp name' in lc or 'village panchayat' in lc or 'gram' in lc:
                            panchayat_col = c
                            break

                    # --- VALIDATION: IS THIS MEMBER FROM THIS PANCHAYAT? ---
                    if panchayat_col:
                        member_panchayat = str(row[panchayat_col]).strip()
                        logged_panchayat = panchayat_name.strip()

                        # Case-insensitive compare
                        if member_panchayat.lower()!= logged_panchayat.lower():
                            st.error(f"⛔ ACCESS DENIED!")
                            st.warning(f"This Member ID {member_id} belongs to **{member_panchayat} Panchayat**, not your **{logged_panchayat} Panchayat**.")
                            st.info("You can only apply for members of your own panchayat. This member is not in your block.")
                            st.stop() # STOP HERE - Don't show eligibility

                    # If validation passed, continue eligibility check
                    ac = find_col(df,"status"); ek = find_col(df,"ekyc"); mo = find_col(df,"mobile"); ba = find_col(df,"bank")
                    all_ok=True
                    checks=[]
                    if ac:
                        v=str(row[ac]).strip(); is_ok=v.lower().strip()=='active'; checks.append(("Member Active",is_ok,v)); all_ok=all_ok and is_ok
                    if ek:
                        v=str(row[ek]).strip(); is_ok='verif' in v.lower() or v.lower() in ['yes','verified','1']; checks.append(("eKYC",is_ok,v)); all_ok=all_ok and is_ok
                    if mo:
                        v=str(row[mo]).strip(); is_ok=v not in ['','--','nan'] and len(v)>=5; checks.append(("Mobile",is_ok,v)); all_ok=all_ok and is_ok
                    if ba:
                        v=str(row[ba]).strip(); is_ok=v not in ['','--','nan'] and len(v)>3; checks.append(("Bank Account",is_ok,v)); all_ok=all_ok and is_ok

                    for n,s,v in checks:
                        if s: st.success(f"✅ {n}: {v}")
                        else: st.error(f"❌ {n}: {v} - FAILED")

                    if all_ok:
                        # Extra display
                        if panchayat_col:
                            st.info(f"✅ Panchayat Verified: {member_panchayat} (Matches your login)")
                        st.success("✅ ELIGIBLE - Ready to submit to BMMU")
                        st.session_state['eligible_member']=member_id
                        st.session_state['eligible_amount']=loan_amount
                        st.session_state['show_submit']=True
                    else:
                        st.error("❌ NOT ELIGIBLE")
                        update_status(member_id,"❌ AUTO-REJECTED","Failed eligibility check", "Panchayat", panchayat_name)
                        st.session_state['show_submit']=False
                else:
                    st.error("Member ID not found in data")
            else:
                st.error("No data file found")

        if st.session_state.get('show_submit', False):
            if st.button("📤 Submit to BMMU", type="primary"):
                new_app={'id':st.session_state['eligible_member'],'amount':st.session_state['eligible_amount'],'panchayat':panchayat_name}
                if not any(x['id']==new_app['id'] for x in st.session_state['pending_bmmu']):
                    st.session_state['pending_bmmu'].append(new_app)
                update_status(new_app['id'],"⏳ PENDING AT BMMU","Eligible, submitted by Panchayat, pending livelihood & BM approval check at BMMU","Panchayat",panchayat_name)
                st.success(f"Submitted to BMMU! Status: PENDING AT BMMU")
                st.session_state['show_submit']=False
                st.session_state['page']='dashboard'
                st.rerun()
