import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date

st.set_page_config(page_title="MMX AI Claims Processing Assistant", page_icon="🧾", layout="wide")
st.markdown("""
<style>
.stApp {background:#F4F7FB;} [data-testid="stSidebar"] {background:#10233F;}
[data-testid="stSidebar"] * {color:#F4F7FB !important;}
.hero {background:linear-gradient(120deg,#10233F,#1B4268);padding:24px 28px;border-radius:16px;color:#fff;margin-bottom:18px;}
.hero h1 {color:#fff;margin:0;font-size:30px;} .hero p {color:#DCE8F4;margin:8px 0 0 0;}
.notice {background:#FFF7E6;border:1px solid #F3D18A;padding:10px 14px;border-radius:10px;color:#704D00;margin-bottom:14px;}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv(Path(__file__).parent / "demo_claims.csv", keep_default_na=False)

if "claims_records" not in st.session_state:
    st.session_state.claims_records = load_data().to_dict("records")
if "claim_audit" not in st.session_state:
    st.session_state.claim_audit = []
if "claim_summaries" not in st.session_state:
    st.session_state.claim_summaries = {}

def records_df():
    return pd.DataFrame(st.session_state.claims_records)

def refresh():
    st.rerun()

st.sidebar.title("MMX Claims Assistant")
st.sidebar.caption("Proposed concept • Interactive demo console")
pages = ["Claims Overview", "Claims Work Queue", "Claim Details & Status", "New Claim Intake", "Document Checklist", "Case Summary", "AI Assistant", "Activity Log", "About & Pilot"]
page = st.sidebar.radio("Workspace", pages)
st.sidebar.markdown("---")
st.sidebar.caption("Prototype v0.2 • Fictional data")
st.markdown("""<div class="hero"><h1>AI Claims Processing Assistant</h1><p>Organise claim information, identify missing items and help claims teams prepare clearer case summaries.</p></div>""", unsafe_allow_html=True)
st.markdown('<div class="notice">DEMONSTRATION ONLY — all records are fictional. Changes are saved in this browser session only. This independent prototype is not an official MMX product, has no live MMX connection, and does not approve, reject, value, investigate or settle claims.</div>', unsafe_allow_html=True)

df = records_df()
STATUSES = ["Needs documents", "Ready for review", "Under review", "Escalated", "Closed - demo"]
CHECKLISTS = {
    "Motor": ["Claim form or first notification of loss", "Driver and vehicle details", "Incident description", "Photos or damage assessment, if applicable", "Police or accident reference, where applicable", "Repair estimate or assessor report, if required"],
    "Property": ["Claim form or first notification of loss", "Policy and risk address details", "Incident description and date", "Photos or inventory, where applicable", "Supplier estimate or assessor report, if required"],
    "Liability": ["Claim notification", "Description of alleged event", "Relevant correspondence and supporting records", "Available witness or incident details", "Legal or liability documents, if applicable"],
    "Other": ["Claim notification", "Policy reference and incident details", "Supporting evidence relevant to the claim", "Additional items confirmed by the authorised handler"]
}

def pick_claim(label="Choose a claim", key="claim_pick"):
    opts = df["claim_id"].astype(str).tolist()
    return st.selectbox(label, opts, key=key)

def selected_record(claim_id):
    return next((r for r in st.session_state.claims_records if str(r["claim_id"]) == str(claim_id)), None)

def audit(claim_id, action, detail):
    st.session_state.claim_audit.insert(0, {"time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), "claim_id": claim_id, "action": action, "detail": detail})

if page == "Claims Overview":
    st.subheader("Claims operations overview")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Demo claim records", f"{len(df):,}")
    c2.metric("Needs documents", f"{(df['status']=='Needs documents').sum():,}")
    c3.metric("Ready for review", f"{(df['status']=='Ready for review').sum():,}")
    c4.metric("Escalated for human review", f"{(df['status']=='Escalated').sum():,}")
    left,right = st.columns(2)
    with left:
        by_status=df.groupby("status",as_index=False).size()
        st.plotly_chart(px.bar(by_status,x="status",y="size",color="status",title="Work queue by status",labels={"status":"Workflow status","size":"Claims"}).update_layout(showlegend=False,plot_bgcolor="white",paper_bgcolor="white"),use_container_width=True)
    with right:
        by_type=df.groupby("claim_type",as_index=False).size()
        st.plotly_chart(px.pie(by_type,names="claim_type",values="size",hole=.48,title="Claims by type").update_layout(paper_bgcolor="white"),use_container_width=True)
    st.subheader("Priority worklist")
    priority=df[df["status"].isin(["Needs documents","Escalated"])][["claim_id","claim_type","received_date","status","missing_items","assigned_to"]]
    st.dataframe(priority,use_container_width=True,hide_index=True)
    st.caption("Priority is workflow follow-up only; it is not a decision about claim validity or entitlement.")
    if not priority.empty:
        chosen=st.selectbox("Open a priority claim",priority["claim_id"].tolist(),key="overview_open")
        if st.button("Open selected claim details",type="primary"):
            st.session_state.open_claim=chosen
            st.session_state.claim_nav_hint=True
            st.info("Use **Claim Details & Status** in the sidebar; your selected claim is available there.")

elif page == "Claims Work Queue":
    st.subheader("Interactive claims work queue")
    c1,c2=st.columns(2)
    with c1: status_filter=st.multiselect("Workflow status",sorted(df["status"].unique()),default=sorted(df["status"].unique()))
    with c2: type_filter=st.multiselect("Claim type",sorted(df["claim_type"].unique()),default=sorted(df["claim_type"].unique()))
    q=st.text_input("Search claim ID, assigned team or missing item",placeholder="e.g. CLM-1004")
    view=df[df["status"].isin(status_filter)&df["claim_type"].isin(type_filter)].copy()
    if q:
        mask=view.astype(str).apply(lambda col: col.str.contains(q,case=False,na=False)).any(axis=1)
        view=view[mask]
    st.dataframe(view[["claim_id","claim_type","received_date","status","missing_items","assigned_to","estimated_amount_demo"]],use_container_width=True,hide_index=True)
    st.download_button("Download filtered queue (CSV)",view.to_csv(index=False).encode("utf-8"),"claims_work_queue_demo.csv","text/csv")
    if not view.empty:
        chosen=st.selectbox("Select a record to open",view["claim_id"].tolist(),key="queue_open")
        if st.button("Set as active claim",key="queue_active"):
            st.session_state.open_claim=chosen
            st.success(f"{chosen} selected. Open Claim Details & Status in the sidebar.")
    st.caption("Amounts are fictional demo values and are not reserves, offers or approved payments.")

elif page == "Claim Details & Status":
    st.subheader("Claim details and workflow status")
    default_claim=st.session_state.get("open_claim",df.iloc[0]["claim_id"])
    options=df["claim_id"].tolist()
    chosen=st.selectbox("Claim record",options,index=options.index(default_claim) if default_claim in options else 0,key="detail_claim")
    r=selected_record(chosen)
    a,b,c=st.columns(3)
    a.metric("Workflow status",r["status"])
    b.metric("Days open (demo)",int(float(r.get("days_open",0) or 0)))
    c.metric("Illustrative amount",f"R {float(r.get('estimated_amount_demo',0) or 0):,.0f}")
    st.markdown("#### Record information")
    st.write(f"**Claim type:** {r['claim_type']}  ·  **Received:** {r['received_date']}  ·  **Assigned team:** {r['assigned_to']}")
    st.write(f"**Missing items:** {r['missing_items'] or 'None listed in demo record'}")
    with st.form("status_update_form"):
        new_status=st.selectbox("Update workflow status",STATUSES,index=STATUSES.index(r["status"]) if r["status"] in STATUSES else 0)
        new_team=st.text_input("Assigned team",value=str(r["assigned_to"]))
        new_missing=st.text_area("Missing items (separate multiple items with semicolons)",value=str(r["missing_items"]))
        update_note=st.text_input("Reason / note for activity log",placeholder="e.g. requested outstanding estimate")
        submitted=st.form_submit_button("Save record updates",type="primary")
    if submitted:
        old_status=r["status"]
        r["status"]=new_status; r["assigned_to"]=new_team.strip() or r["assigned_to"]; r["missing_items"]=new_missing.strip()
        audit(chosen,"Record updated",f"Status: {old_status} → {new_status}. {update_note.strip()}".strip())
        st.success("Updates saved for this session.")
        refresh()
    st.markdown("#### Quick actions")
    q1,q2,q3=st.columns(3)
    with q1:
        if st.button("Mark ready for review"):
            r["status"]="Ready for review"; audit(chosen,"Status changed","Marked ready for review by demo user."); refresh()
    with q2:
        if st.button("Flag for human escalation"):
            r["status"]="Escalated"; audit(chosen,"Status changed","Flagged for authorised human review."); refresh()
    with q3:
        if st.button("Clear missing-items field"):
            r["missing_items"]=""; audit(chosen,"Checklist field updated","Missing-items field cleared in demo record."); refresh()
    st.warning("These are demo workflow labels only. They do not represent coverage, liability, fraud or settlement decisions.")

elif page == "New Claim Intake":
    st.subheader("New claim intake")
    st.write("Create a fictional record and keep it in the current app session.")
    with st.form("claim_intake"):
        col1,col2=st.columns(2)
        with col1:
            claim_ref=st.text_input("Claim reference",placeholder="e.g. CLM-DEMO-2001")
            claim_type=st.selectbox("Claim type",["Motor","Property","Liability","Other"])
            received=st.date_input("Date received",value=date.today())
            policy_ref=st.text_input("Policy reference (demo)",placeholder="POL-DEMO-001")
        with col2:
            channel=st.selectbox("Received via",["Broker","Email","Portal","Call centre","Other"])
            incident_date=st.date_input("Incident date",value=date.today())
            description=st.text_area("Incident description",placeholder="Fictional factual summary; avoid personal or sensitive data.")
            missing=st.text_input("Outstanding documents",placeholder="Separate items with semicolons")
            consent=st.checkbox("I confirm this is fictional/demo information.")
        submitted=st.form_submit_button("Create and save demo claim",type="primary")
    if submitted:
        if not claim_ref.strip() or not policy_ref.strip() or not description.strip(): st.error("Complete claim reference, policy reference and incident description.")
        elif not consent: st.error("Confirm that the information is fictional.")
        elif claim_ref.strip() in df["claim_id"].astype(str).tolist(): st.error("That claim reference already exists. Choose a unique demo reference.")
        else:
            rec={"claim_id":claim_ref.strip(),"claim_type":claim_type,"received_date":str(received),"status":"Needs documents" if missing.strip() else "Ready for review","missing_items":missing.strip(),"assigned_to":"Unassigned demo queue","estimated_amount_demo":0,"days_open":0,"policy_reference_demo":policy_ref.strip(),"received_via_demo":channel,"incident_date_demo":str(incident_date),"incident_description_demo":description.strip()}
            st.session_state.claims_records.append(rec); audit(claim_ref.strip(),"Claim created",f"New fictional {claim_type} intake received via {channel}.")
            st.success("Claim created and saved for this session.")
            st.json({"claim_reference":claim_ref.strip(),"policy_reference_demo":policy_ref.strip(),"received_via":channel,"incident_date":str(incident_date),"next_step":"Authorised handler to verify policy details, facts and applicable documents.","decision_status":"No decision made — human review required"})
            st.info("Session records are not written to a permanent database and may disappear when the session resets.")

elif page == "Document Checklist":
    st.subheader("Document completeness assistant")
    chosen=pick_claim("Choose a claim",key="check_claim")
    r=selected_record(chosen)
    st.markdown(f"### {chosen} · {r['claim_type']}")
    st.write(f"Current workflow status: **{r['status']}**")
    st.caption("Illustrative checklist only. Confirm requirements against policy wording and the applicable approved procedure.")
    for item in CHECKLISTS.get(r["claim_type"],CHECKLISTS["Other"]): st.checkbox(item,key=f"check_{chosen}_{item}")
    if r["missing_items"]: st.warning(f"Demo record lists missing items: {r['missing_items']}")
    else: st.success("No missing items are listed in this fictional record. This does not mean the claim is covered or ready for payment.")
    if st.button("Log checklist reviewed"):
        audit(chosen,"Checklist reviewed","Illustrative checklist reviewed in demo."); st.success("Review noted in session activity log.")

elif page == "Case Summary":
    st.subheader("Claims case summary")
    chosen=pick_claim("Select a claim for summary",key="summary_claim")
    r=selected_record(chosen)
    st.markdown(f"### {chosen} — {r['claim_type']}")
    a,b,c=st.columns(3); a.metric("Workflow status",r["status"]); b.metric("Days since received",int(float(r.get("days_open",0) or 0))); c.metric("Demo amount",f"R {float(r.get('estimated_amount_demo',0) or 0):,.0f}")
    st.write(f"**Received:** {r['received_date']}  ·  **Assigned team:** {r['assigned_to']}  ·  **Missing items:** {r['missing_items'] or 'None listed'}")
    default_summary=st.session_state.claim_summaries.get(chosen, f"Claim {chosen} is a fictional {r['claim_type'].lower()} case received on {r['received_date']}. Current workflow status: {r['status']}. Assigned team: {r['assigned_to']}. Missing items recorded: {r['missing_items'] or 'None listed'}. Next step: verify policy details, confirm applicable documentation and review the facts against the relevant policy wording and operating procedure. No coverage, liability, fraud or settlement decision has been made.")
    summary=st.text_area("Editable summary",default_summary,height=190,key=f"summary_text_{chosen}")
    s1,s2=st.columns(2)
    with s1:
        if st.button("Save summary in this session"):
            st.session_state.claim_summaries[chosen]=summary; audit(chosen,"Summary saved","Editable case summary saved to session."); st.success("Summary saved for this session.")
    with s2: st.download_button("Download summary (TXT)",summary,f"{chosen}_summary.txt")
    st.warning("A summary must be checked by an authorised claims handler before use in a real workflow.")

elif page == "AI Assistant":
    st.subheader("Claims workflow assistant")
    st.caption("Rule-based demo helper. It does not connect to a live AI model or MMX system.")
    chosen=pick_claim("Choose a claim context",key="assistant_claim")
    r=selected_record(chosen)
    question=st.text_area("Ask about next administrative steps",placeholder="e.g. What should the handler check next?",height=90)
    if st.button("Generate guidance",type="primary"):
        gaps=[x.strip() for x in str(r["missing_items"]).split(";") if x.strip()]
        st.markdown("#### Suggested administrative guidance")
        st.write(f"For **{chosen}** ({r['claim_type']}), the recorded workflow status is **{r['status']}**.")
        if gaps: st.write("- Follow up on listed items: " + ", ".join(gaps) + ".")
        else: st.write("- No missing items are recorded in this demo row; verify completeness against the applicable checklist.")
        st.write("- Confirm policy and incident details against approved source records.")
        st.write("- Record the handler's next action and escalate ambiguity to an authorised reviewer.")
        if question.strip(): st.write(f"**Your question:** {question.strip()}")
        st.info("This response is a fixed rule-based template, not generative AI. It makes no coverage, liability, fraud or settlement determination.")
        audit(chosen,"Assistant guidance generated","Rule-based administrative guidance displayed.")

elif page == "Activity Log":
    st.subheader("Session activity log")
    st.write("Shows actions taken in this running demo session; it is not a production audit trail.")
    if st.session_state.claim_audit:
        log=pd.DataFrame(st.session_state.claim_audit)
        st.dataframe(log,use_container_width=True,hide_index=True)
        st.download_button("Download activity log (CSV)",log.to_csv(index=False).encode("utf-8"),"mmx_demo_activity_log.csv","text/csv")
    else: st.info("No actions logged yet. Updating a claim or creating an intake will add an entry.")
    if st.button("Clear session activity log"):
        st.session_state.claim_audit=[]; refresh()

else:
    st.subheader("About the concept")
    st.markdown("""**Goal:** propose a workflow assistant that complements existing insurance administration capabilities.

**Interactive demo features:** searchable work queue, claim detail view, editable workflow statuses, quick status actions, session-only intake records, illustrative document checklists, editable summaries, rule-based assistant panel and session activity log.

**Production requirements:** MMX approval, secure identity and permissions, durable database, auditable changes, approved policy/checklist rules, privacy controls, testing and any authorised integration. The current prototype is not an official MMX product.""")
    st.subheader("Pilot plan")
    st.markdown("1. Confirm the current claims workflow with MMX stakeholders.\n2. Select one administrative use case.\n3. Test using synthetic or approved de-identified records.\n4. Validate outputs with claims professionals.\n5. Review privacy, access controls and audit requirements before integration.")
    st.subheader("Human review boundaries")
    st.markdown("- No automated approval, rejection, valuation, settlement or fraud decisions.\n- Policy wording and authorised staff remain the source of decisions.\n- Demo records are session-only and fictional.")

st.markdown("---")
st.caption("MMX AI Claims Processing Assistant • Proposed independent concept • Not an official MMX Systems product")
