import os
import base64
from email.mime.text import MIMEText
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from zoneinfo import ZoneInfo

load_dotenv()

payload_emails = {}

payload_emails["renewal_outreach"] = {
        "to": "{email}",
        "subject": "Let's discuss your upcoming renewal",
        "body": """
        Hi {name},

        I noticed that your renewal is approaching, and I'd like to schedule some time to discuss your goals, answer any questions, and ensure you're getting the most value from our platform.

        Please let me know a convenient time to connect.

        Best regards,
        Customer Success Team
        """
        }

payload_emails["upsell_proposal"] = {
    "to":"{email}",
    "subject" : "Unlock More Value with Your Account",
    "body" : """Hi {name},

We've noticed your team is getting great value from our platform.

Based on your recent growth and usage, we believe an upgraded plan or additional modules could help you achieve your goals more efficiently.

I'd be happy to walk you through the available options and answer any questions.

Best regards,
Customer Success Team"""
}

payload_emails["billing_review"] = {
    "to" : "{email}",
    "subject" : "Let's Resolve Your Billing Concern",
    "body" : """Hi {name},

Thank you for bringing your billing concern to our attention.

We're reviewing your account and will work with you to resolve any invoice or payment discrepancies as quickly as possible.

If you have additional details, please reply to this email.

Best regards,
Customer Success Team"""
}

payload_emails["executive_escalation"] = {
    "to" : "{email}",
    "subject" : "Your Issue Has Been Escalated",
    "body" : """Hi {name},

We understand the impact this issue is having on your business.

Your case has been escalated to our senior leadership and engineering teams for immediate attention.

We'll keep you informed until the issue is fully resolved.

Thank you for your patience.

Best regards,
Customer Success Team"""
}

payload_emails["send_training_material"] = {
    "to" : "{email}",
    "subject" : "Helpful Resources to Get the Most from Our Platform",
    "body" : """Hi {name},

We've put together a few training resources that we believe will help your team make better use of the platform.

These guides cover the features most relevant to your current needs.

Please let us know if you'd also like a live walkthrough.

Best regards,
Customer Success Team"""
}



SCOPES1 = ["https://mail.google.com/"]
SCOPES2 = ["https://www.googleapis.com/auth/calendar"]

def send_email(to: str, subject: str, body: str):
    print(subject)
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES1,
    )

    service = build("gmail", "v1", credentials=creds)
    
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(
    message.as_bytes()
    ).decode()

    result = service.users().messages().send(
    userId="me",
    body={"raw": raw}
    ).execute()
        # count = count + 1

    return {
    "status": "success",
    "message_id": result["id"],
    "thread_id": result["threadId"]
    }

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")


tz = ZoneInfo("Asia/Kolkata")

def schedule_meeting(customer_email, subject, description, as_of_date,start_hr):

    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES2,
    )

    creds.refresh(Request())

    service = build("calendar", "v3", credentials=creds)

    current_date = as_of_date + timedelta(days=1)

    while True:

        # Skip Saturday (5) and Sunday (6)
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        # Check every 1-hour slot from 9 AM to 5 PM
        for hour in range(start_hr, 17):

            start = datetime.combine(current_date, time(hour, 0), tzinfo=tz)
            end = start + timedelta(hours=1)
            print(start)
            print(start.isoformat())

            print(end)
            print(end.isoformat())
            freebusy = service.freebusy().query(
                body={
                    "timeMin": start.isoformat(),
                    "timeMax": end.isoformat(),
                    "timeZone": "Asia/Kolkata",
                    "items": [{"id": "primary"}],
                }
            ).execute()
            print(freebusy["calendars"]["primary"]["busy"]) 

            busy = freebusy["calendars"]["primary"]["busy"]

            if not busy:

                event = {
                    "summary": subject,
                    "description": description,
                    "start": {
                        "dateTime": start.isoformat(),
                        "timeZone": "Asia/Kolkata",
                    },
                    "end": {
                        "dateTime": end.isoformat(),
                        "timeZone": "Asia/Kolkata",
                    },
                    "attendees": [
                        {"email": customer_email}
                    ],
                }

                result = service.events().insert(
                    calendarId="primary",
                    body=event,
                ).execute()

                return {
                    "status": "success",
                    "event_id": result["id"],
                    "meeting_link": result["htmlLink"],
                }

        current_date += timedelta(days=1)
