from slack_bolt import App
from backend.action.action_agent import execute_action_agent
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv
from backend.CSM.csm_agent import csm_agent
import traceback
load_dotenv()
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("app_mention")
def handle_app_mention(body, say, client):

    query = body["event"]["text"]
    channel_id = body["event"]["channel"]

    try:
        result = csm_agent(query,execute_action=False)
        print("\n========== SLACK ==========")
        print("Query:", query)
        print("Result:", result)
        print("===========================\n")

        say(result["response"].content[0]["text"])

# Upload the report ONLY if a new analysis was performed
        if result["analysis_ran"]:

            say("Analysis completed successfully!")

            client.files_upload_v2(
                channel=channel_id,
                file="reports/customer_retention_report.pdf",
                title="Customer Retention Report",
                initial_comment="Here's the generated report."
            )


    # except Exception as e:

    #     say(f" Error: {e}")

    except Exception as e:
        # Print complete traceback with file names, line numbers, and error details directly to terminal
        print("\n❌ Error processing Slack app mention:")
        traceback.print_exc()

        # Send a clean generic error notification to Slack
        say("⚠️ An error occurred while processing your request. Please check the terminal logs for details.")

if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_SOCKET_TOKEN")).start()
