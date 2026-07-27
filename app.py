import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Google API Key not found. Add GOOGLE_API_KEY to your .env file.")
    st.stop()

genai.configure(api_key=API_KEY)


@st.cache_resource
def get_working_model():
    """Automatically find a model that works with this API key."""

    # 1) Try common models first
    preferred = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
    ]
    for name in preferred:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("Say OK")
            return m
        except Exception:
            continue

    # 2) Auto-detect from your account
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                try:
                    model = genai.GenerativeModel(m.name)
                    model.generate_content("Say OK")
                    return model
                except Exception:
                    continue
    except Exception:
        pass

    return None


def generate_sql(model, prompt):
    full_prompt = f"""
You are an expert SQL developer.

Based on the user's request, provide:
1. SQL Query
2. Expected Output Table (markdown format)
3. Simple Explanation

User Request:
{prompt}

Return ONLY in this format:

---SQL---
SQL QUERY HERE

---OUTPUT---
Markdown Table Here

---EXPLANATION---
Explanation Here
"""
    response = model.generate_content(full_prompt)
    return response.text


def parse_response(text):
    sql, output, explanation = "", "", ""
    try:
        if "---SQL---" in text:
            text = text.split("---SQL---")[1]
        if "---OUTPUT---" in text:
            sql, text = text.split("---OUTPUT---", 1)
        if "---EXPLANATION---" in text:
            output, explanation = text.split("---EXPLANATION---", 1)
    except Exception:
        sql = text
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql, output.strip(), explanation.strip()


def main():
    st.set_page_config(
        page_title="AI SQL Query Generator",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 AI SQL Query Generator")
    st.write("Generate SQL queries from plain English using Google Gemini.")

    model = get_working_model()

    if model is None:
        st.error("❌ No working Gemini model found for this API key. Please create a new API key in Google AI Studio.")
        return

    user_input = st.text_area(
        "Enter your requirement:",
        height=150,
        placeholder="Example: Show top 5 employees with highest salary."
    )

    if st.button("Generate SQL"):
        if not user_input.strip():
            st.warning("Please enter a prompt.")
            return

        with st.spinner("Finding model & generating SQL... (first run may take a few seconds)"):
            try:
                raw = generate_sql(model, user_input)
                sql, output, explanation = parse_response(raw)

                st.success("✅ SQL Generated Successfully!")

                st.subheader("📌 SQL Query")
                st.code(sql, language="sql")

                if output:
                    st.subheader("📊 Expected Output")
                    st.markdown(output)

                if explanation:
                    st.subheader("📖 Explanation")
                    st.write(explanation)

            except Exception as e:
                st.error(f"Error: {e}")


if __name__ == "__main__":
    main()