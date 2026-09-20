# --- REPLACE YOUR OLD eligible=True PART WITH THIS ---

st.markdown("### Check Eligibility with Amount")

member_id = st.text_input("Enter Member ID (from sample_data.csv)")
loan_amount = st.number_input("Required Loan Amount", min_value=1000, step=1000)

if st.button("Check with Sample Data"):
    if df is not None and member_id!= "":
        # Find member in your data
        member_row = df[df.astype(str).apply(lambda x: x.str.contains(member_id, case=False)).any(axis=1)]

        if not member_row.empty:
            row = member_row.iloc[0]
            st.write("Found Member Data:", row)

            # Try to find savings column - auto detect
            savings_col = None
            for col in df.columns:
                if 'saving' in col.lower() or 'thrift' in col.lower() or 'balance' in col.lower():
                    savings_col = col
                    break

            if savings_col:
                savings = float(row[savings_col])
                st.write(f"Your Savings: Rs.{savings}")
                st.write(f"Asking Loan: Rs.{loan_amount}")

                # REAL BANK LOGIC
                max_eligible = savings * 4 # Bank gives 4x of savings
                reasons = []
                eligible = True

                if loan_amount <= max_eligible:
                    reasons.append(f"✅ Amount OK: You can get upto Rs.{max_eligible} (4x savings)")
                else:
                    reasons.append(f"❌ Amount Too High: You saved Rs.{savings}, so max eligible is Rs.{max_eligible}")
                    eligible = False

                # Check repayment if column exists
                for col in df.columns:
                    if 'due' in col.lower() or 'overdue' in col.lower() or 'defaulter' in col.lower():
                        if str(row[col]).lower() in ['yes','1','true','overdue']:
                            reasons.append("❌ Past Due Found")
                            eligible = False

                st.markdown("---")
                if eligible:
                    st.success(f"✅ ELIGIBLE FOR Rs.{loan_amount}")
                    st.balloons()
                else:
                    st.error(f"❌ NOT ELIGIBLE FOR Rs.{loan_amount}")

                for r in reasons:
                    st.write(r)
            else:
                st.warning("Could not find Savings column in your CSV. Tell me column names")
        else:
            st.error(f"Member ID {member_id} not found in sample_data.csv")
    else:
        st.error("Enter Member ID")
