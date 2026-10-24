"""Private, session-only bibexCV interface."""
import hashlib
import os
import streamlit as st
from review import ReviewError, extract_pdf, analyse, demo, report

st.set_page_config(page_title="bibexCV Review Assistant", page_icon="📄")
st.title("bibexCV Review Assistant")
st.write("Evidence-led CV feedback for your next role.")
st.caption("AI suggestions require judgement. No ATS or hiring outcome is guaranteed. Extracted text cannot establish visual layout quality.")

def setting(name, default=""):
    if os.getenv(name):
        return os.getenv(name)
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default

if st.button("Clear session data"):
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()
mode = st.radio("Source", ["My CV", "Synthetic demo — no API calls"])
synthetic = mode.startswith("Synthetic")
source = ""
if synthetic:
    st.info("Fictional CV and prewritten feedback. No API request is made.")
    source = demo()[0]
else:
    upload = st.file_uploader("Text-based PDF: maximum 5 MB and 30 pages", type=["pdf"])
    if upload is not None:
        data = upload.getvalue()
        identity = hashlib.sha256(data).hexdigest()
        if st.session_state.get("pdf_id") != identity:
            st.session_state.pop("cv_text", None)
            st.session_state.pop("consent", None)
            try:
                st.session_state.pdf_text = extract_pdf(data)
                st.session_state.pdf_id = identity
            except ReviewError as exc:
                st.error(str(exc))
                st.stop()
        source = st.session_state.pdf_text
if source:
    if synthetic:
        st.text_area("Synthetic CV", source, disabled=True)
        if st.button("Show synthetic feedback"):
            st.session_state.demo_report = report(demo()[1], "Junior analyst", "Entry level", True)
    else:
        st.text_area("Extracted text — edit or redact before sending", source, key="cv_text", height=300)
        role = st.text_input("Target role", max_chars=150)
        level = st.selectbox("Career level", ["Entry level", "Mid level", "Senior", "Leadership", "Career change"])
        jd = st.text_area("Job description (optional)", max_chars=12000)
        st.caption("Only the edited CV and role context are sent to OpenAI. Remove personal details you do not want to share. No OCR is performed. Provider retention policies apply. The app uses session memory, no shared caches or saved CV/review files.")
        consent = st.checkbox("I consent to sending the edited CV and role context to OpenAI for this analysis.", key="consent")
        if st.button("Analyse", type="primary"):
            try:
                if not consent:
                    raise ReviewError("Consent is required before analysis.")
                with st.spinner("Reviewing…"):
                    result = analyse(st.session_state.cv_text, role, level, jd, setting("OPENAI_API_KEY"), setting("OPENAI_MODEL", "gpt-4o-mini"))
                st.session_state.report = report(result, role, level)
            except ReviewError as exc:
                st.error(str(exc))
previous = st.session_state.get("demo_report" if synthetic else "report")
if previous:
    st.subheader("Synthetic feedback" if synthetic else "Last completed review")
    st.caption("Results reflect the last completed submission; edits do not update them. Analyse submits a new request.")
    st.text(previous)
    st.download_button("Download feedback (.txt)", previous, file_name="bibexCV-feedback.txt", mime="text/plain")
