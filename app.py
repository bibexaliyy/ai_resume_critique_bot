import streamlit as st
import pymupdf as fitz
import openai
import os

st.set_page_config(page_title="AI Resume Critique Bot")

# Load API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("AI Resume Critique Bot")
st.write("Upload your resume (PDF), and get smart feedback powered by AI!")

uploaded_file = st.file_uploader("Choose your resume (PDF format)", type="pdf")

def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def get_resume_feedback(resume_text):
    prompt = f"""
You are a professional HR and resume expert.
Critique the following resume content. Provide clear feedback on:
1. Formatting
2. Clarity and tone
3. Use of keywords (especially for tech roles)
4. Suggestions for improvement

Here is the resume text:
\"\"\"{resume_text}\"\"\"
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )

    return response["choices"][0]["message"]["content"]

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    st.subheader("Resume Feedback from AI:")
    with st.spinner("Analyzing..."):
        feedback = get_resume_feedback(resume_text)
    st.success("Analysis complete!")
    st.markdown(feedback)
