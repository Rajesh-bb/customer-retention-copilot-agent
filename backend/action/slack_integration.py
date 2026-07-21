from slack_bolt import App

app = App(token=)

@app.event("app_mention")
def handle_app_mention(body,say):
    query = body["event"]["text"]
    