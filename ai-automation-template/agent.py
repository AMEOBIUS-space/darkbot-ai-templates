#!/usr/bin/env python3
"""AI Automation Agent Template — OpenAI + n8n integration."""
import json, os, logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an AI automation agent. You help businesses automate:
- Email processing and responses
- CRM data entry
- Report generation
- Customer support
- Data analysis
Always be concise, professional, and action-oriented."""

def process_task(task_type, data):
    """Process automation task via AI."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {task_type}\nData: {json.dumps(data)}\nProvide actionable result."}
        ],
        temperature=0.3,
        max_tokens=500
    )
    return response.choices[0].message.content

def email_auto_reply(subject, body):
    """Auto-generate email reply."""
    return process_task("email_reply", {"subject": subject, "body": body})

def generate_report(data, report_type="weekly"):
    """Generate business report from data."""
    return process_task("report", {"data": data, "type": report_type})

def crm_entry(raw_text):
    """Extract CRM fields from raw text."""
    return process_task("crm_entry", {"text": raw_text})

if __name__ == "__main__":
    # Demo
    print(email_auto_reply("Meeting request", "Can we schedule a call next week?"))
