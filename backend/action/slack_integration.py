from slack_bolt import App
from backend.action.action_agent import execute_action_agent
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv
load_dotenv()
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("app_mention")
def handle_app_mention(body, say, client):

    query = body["event"]["text"]
    channel_id = body["event"]["channel"]

    try:
        result = execute_action_agent(query)

        say("Analysis completed successfully!")

        client.files_upload_v2(
            channel=channel_id,
            file=result["report"]["pdf"],
            title="Customer Retention Report",
            initial_comment="Here's the generated report."
        )

    except Exception as e:
        say(f" Error: {e}")

if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_SOCKET_TOKEN")).start()
