import requests
import streamlit as st
import time

def stream_text(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.02)

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Customer Retention Copilot",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Customer Retention Copilot")

# ------------------------------------------------------------------
# Session State
# ------------------------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_payload" not in st.session_state:
    st.session_state.pending_payload = None

if "report" not in st.session_state:
    st.session_state.report = None

# ------------------------------------------------------------------
# Display Chat History
# ------------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ------------------------------------------------------------------
# User Input
# ------------------------------------------------------------------

prompt = st.chat_input("Ask something...")

if prompt:

    # -----------------------------
    # Display user message
    # -----------------------------
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # -----------------------------
    # Call FastAPI
    # -----------------------------
    request_body = {
        "thread_id": st.session_state.thread_id,
        "message": prompt,
    }

    with st.spinner("Thinking..."):

        try:

            response = requests.post(
                f"{API_URL}/chat",
                json=request_body,
            )

            response.raise_for_status()

            data = response.json()

        except Exception as e:

            st.error(str(e))
            st.stop()

    # -----------------------------
    # Save thread id
    # -----------------------------
    st.session_state.thread_id = data["thread_id"]

    # -----------------------------
    # Handle normal chat
    # -----------------------------
    if data["type"] == "chat":

        assistant_message = data["response"]

        with st.chat_message("assistant"):
            st.write_stream(stream_text(assistant_message))

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": assistant_message,
            }
        )

    # -----------------------------
    # Handle approval
    # -----------------------------
    elif data["type"] == "approval":

        st.session_state.pending_payload = data["payload"]

        assistant_message = (
            "Human approval is required before I can execute this action."
        )

        with st.chat_message("assistant"):
            st.markdown(assistant_message)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": assistant_message,
            }
        )

    # -----------------------------
    # Handle report
    # -----------------------------
    elif data["type"] == "report":

        st.session_state.report = data["graph_state"]

        assistant_message = "Analysis completed successfully."

        with st.chat_message("assistant"):
            st.markdown(assistant_message)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": assistant_message,
            }
        )

# ------------------------------------------------------------------
# Placeholder for Approval UI
# (We'll implement this in Part 2)
# ------------------------------------------------------------------

if st.session_state.pending_payload is not None:

    st.divider()

    st.info("Approval UI will be added in Part 2.")

# ------------------------------------------------------------------
# Approval UI
# ------------------------------------------------------------------

if st.session_state.pending_payload is not None:

    st.divider()
    st.subheader("Human Approval Required")

    payload = st.session_state.pending_payload.copy()

    st.write("Review the action below before executing it.")

    with st.expander("Action Details", expanded=True):

        account_id = st.text_input(
            "Account ID",
            value=str(payload.get("account_id", "")),
            disabled=True,
        )

        action = st.text_input(
            "Action",
            value=payload.get("action", ""),
            disabled=True,
        )

        reason = st.text_area(
            "Reason",
            value=payload.get("reason", ""),
            height=100,
        )

        payload["reason"] = reason

        if "email" in payload:

            st.markdown("### Email")

            email_to = st.text_input(
                "To",
                value=payload["email"].get("to", ""),
            )

            email_subject = st.text_input(
                "Subject",
                value=payload["email"].get("subject", ""),
            )

            email_body = st.text_area(
                "Body",
                value=payload["email"].get("body", ""),
                height=250,
            )

            payload["email"]["to"] = email_to
            payload["email"]["subject"] = email_subject
            payload["email"]["body"] = email_body

        if "meeting" in payload:

            st.markdown("### Meeting")

            meeting_subject = st.text_input(
                "Meeting Subject",
                value=payload["meeting"].get("subject", ""),
            )

            meeting_email = st.text_input(
                "Customer Email",
                value=payload["meeting"].get("customer_email", ""),
            )

            meeting_description = st.text_area(
                "Meeting Description",
                value=payload["meeting"].get("description", ""),
                height=150,
            )

            payload["meeting"]["subject"] = meeting_subject
            payload["meeting"]["customer_email"] = meeting_email
            payload["meeting"]["description"] = meeting_description

    approve_col, reject_col = st.columns(2)

    # ----------------------------------------------------------
    # APPROVE
    # ----------------------------------------------------------

    with approve_col:

        if st.button(
            "Approve",
            use_container_width=True,
            type="primary",
        ):

            approval_request = {
                "thread_id": st.session_state.thread_id,
                "approval": {
                    "decision": "approve",
                    "payload": payload,
                },
            }

            with st.spinner("Executing action..."):

                try:

                    response = requests.post(
                        f"{API_URL}/approval",
                        json=approval_request,
                    )

                    response.raise_for_status()

                    data = response.json()

                except Exception as e:

                    st.error(str(e))
                    st.stop()

            # Another approval required
            if data["type"] == "approval":

                st.session_state.pending_payload = data["payload"]

                st.rerun()

            # Final report
            else:

                st.session_state.pending_payload = None
                st.session_state.report = data["graph_state"]

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "Analysis completed successfully.",
                    }
                )

                st.rerun()

    # ----------------------------------------------------------
    # REJECT
    # ----------------------------------------------------------

    with reject_col:

        if st.button(
            "Reject",
            use_container_width=True,
        ):

            approval_request = {
                "thread_id": st.session_state.thread_id,
                "approval": {
                    "decision": "reject",
                    "payload": payload,
                },
            }

            with st.spinner("Updating..."):

                try:

                    response = requests.post(
                        f"{API_URL}/approval",
                        json=approval_request,
                    )

                    response.raise_for_status()

                    data = response.json()

                except Exception as e:

                    st.error(str(e))
                    st.stop()

            if data["type"] == "approval":

                st.session_state.pending_payload = data["payload"]

                st.rerun()

            else:

                st.session_state.pending_payload = None
                st.session_state.report = data["graph_state"]

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "Analysis completed successfully.",
                    }
                )

                st.rerun()

# ------------------------------------------------------------------
# Report Viewer
# ------------------------------------------------------------------

if st.session_state.report is not None:

    report = st.session_state.report

    st.divider()

    st.title("📊 Customer Retention Report")

    # ----------------------------------------------------------
    # Executive Summary
    # ----------------------------------------------------------

    st.header("Executive Summary")

    st.write(report["summary"]["executive_summary"])

    st.header("Overall Assessment")

    st.info(report["summary"]["overall_assessment"])

    # ----------------------------------------------------------
    # Key Findings & Recommended Actions
    # ----------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Key Findings")

        for finding in report["summary"]["key_findings"]:
            st.markdown(f"• {finding}")

    with col2:

        st.subheader("Recommended Actions")

        for action in report["summary"]["recommended_actions"]:
            st.markdown(f"• {action}")

    st.divider()

    # ----------------------------------------------------------
    # Charts
    # ----------------------------------------------------------

    st.header("Visual Insights")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.subheader("Sentiment Distribution")

        st.image(
            report["charts"]["sentiment_chart"],
            use_container_width=True,
        )

        st.subheader("Pain Points")

        st.image(
            report["charts"]["pain_point_chart"],
            use_container_width=True,
        )

    with chart_col2:

        st.subheader("Appreciations")

        st.image(
            report["charts"]["appreciation_chart"],
            use_container_width=True,
        )

    st.divider()

    # ----------------------------------------------------------
    # Feedback Themes
    # ----------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Top Pain Points")

        for pain in report["feedback_themes"]["pain_points"]:

            st.markdown(
                f"**{pain['title']}** — {pain['count']} accounts"
            )

    with col2:

        st.subheader("Top Appreciations")

        for item in report["feedback_themes"]["appreciations"]:

            st.markdown(
                f"**{item['title']}** — {item['count']} accounts"
            )

    st.divider()

    # ----------------------------------------------------------
    # Chart Insights
    # ----------------------------------------------------------

    st.header("Chart Insights")

    st.markdown(
        f"**Sentiment:** {report['summary']['chart_insights']['sentiment']}"
    )

    st.markdown(
        f"**Pain Points:** {report['summary']['chart_insights']['pain_points']}"
    )

    st.markdown(
        f"**Appreciations:** {report['summary']['chart_insights']['appreciations']}"
    )

    st.divider()

    # ----------------------------------------------------------
    # Download PDF
    # ----------------------------------------------------------

    st.header("Download Report")

    with open(report["pdf"], "rb") as pdf_file:

        st.download_button(
            label="📄 Download Customer Retention Report",
            data=pdf_file,
            file_name="customer_retention_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# if st.session_state.report is not None:

#     st.divider()

#     st.subheader("Report")

#     st.write(st.session_state.report)