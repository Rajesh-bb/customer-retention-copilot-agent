import requests
import streamlit as st
import time

def stream_text(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.02)

def should_stream(text: str) -> bool:

    markdown_score = 0

    markdown_score += text.count("|---")
    markdown_score += text.count("```")
    markdown_score += text.count("##")
    markdown_score += text.count("\n- ")
    markdown_score += text.count("\n* ")

    return markdown_score == 0


def render_report(report: dict, show_download=True):

    st.divider()

    st.title("📊 Customer Retention Report")


    st.header("Executive Summary")
    st.write_stream(
    stream_text(report["summary"]["executive_summary"])
    )

    st.header("Overall Assessment")
    assessment = st.empty()

    assessment.info(
    st.write_stream(
        stream_text(report["summary"]["overall_assessment"])
    )
    )


    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Key Findings")

        for finding in report["summary"]["key_findings"]:

            st.write_stream(
                stream_text(f"• {finding}")
            )

    with col2:

        st.subheader("Recommended Actions")

        for action in report["summary"]["recommended_actions"]:

            st.write_stream(
                stream_text(f"• {action}")
            )

    st.divider()


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


    st.header("Download Report")
    if show_download:

        with open(report["pdf"], "rb") as pdf_file:

            st.download_button(
                label="📄 Download Customer Retention Report",
                data=pdf_file,
                file_name="customer_retention_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )



API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Customer Retention Copilot",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Customer Retention Copilot")


if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_payload" not in st.session_state:
    st.session_state.pending_payload = None

reports = [
    message
    for message in st.session_state.messages
    if message["type"] == "report"
]

last_report = reports[-1] if reports else None

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["type"] == "text":
            st.markdown(message["content"])

        elif message["type"] == "report":
            render_report(
            message["content"],
            show_download=(message is last_report),
        )


prompt = st.chat_input("Ask something...")

if prompt:


    st.session_state.messages.append(
    {
        "role": "user",
        "type": "text",
        "content": prompt,
    }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

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

    st.session_state.thread_id = data["thread_id"]

    if data["type"] == "chat":

        assistant_message = data["response"]


        with st.chat_message("assistant"):

            if should_stream(assistant_message):
                st.write_stream(stream_text(assistant_message))
            else:
                st.markdown(assistant_message)


        st.session_state.messages.append(
        {
            "role": "assistant",
            "type": "text",
            "content": assistant_message,
        }
    )


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
        "type": "text",
        "content": assistant_message,
    }
)
  
    elif data["type"] == "report":


        assistant_message = "Analysis completed successfully."

        with st.chat_message("assistant"):
            st.markdown(assistant_message)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "type": "text",
                "content": "Analysis completed successfully.",
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "type": "report",
                "content": data["graph_state"],
            }
        )

    

if st.session_state.pending_payload is not None:

    st.divider()


if st.session_state.pending_payload is not None:

    with st.sidebar:

        st.header("Human Approval")

        payload = st.session_state.pending_payload.copy()


        # payload = st.session_state.pending_payload.copy()

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


                if data["type"] == "approval":

                    st.session_state.pending_payload = data["payload"]

                    st.rerun()

                else:

                    st.session_state.pending_payload = None

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "type": "text",
                            "content": "Analysis completed successfully.",
                        }
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "type": "report",
                            "content": data["graph_state"],
                        }
                    )

                    st.rerun()


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

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "type": "text",
                            "content": "Analysis completed successfully.",
                        }
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "type": "report",
                            "content": data["graph_state"],
                        }
                    )
