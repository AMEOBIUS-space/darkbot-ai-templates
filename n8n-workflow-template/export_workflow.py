#!/usr/bin/env python3
"""N8N Workflow Template — AI-powered lead qualification and auto-response pipeline.
Export as n8n workflow JSON, import via n8n editor."""
import json, os

WORKFLOW = {
    "name": "DarkBot AI Lead Qualification Pipeline",
    "nodes": [
        {
            "parameters": {},
            "id": "webhook-trigger",
            "name": "Lead Webhook",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [250, 300],
            "webhookId": "lead-intake",
            "properties": {
                "httpMethod": "POST",
                "path": "lead",
                "responseMode": "responseNode"
            }
        },
        {
            "parameters": {
                "functionCode": """
// Extract lead data
const lead = items[0].json.body;
return [{
    json: {
        name: lead.name || 'Unknown',
        email: lead.email || '',
        phone: lead.phone || '',
        budget: lead.budget || 0,
        project_type: lead.project_type || 'unknown',
        description: lead.description || '',
        source: lead.source || 'website',
        timestamp: new Date().toISOString(),
        score: 0
    }
}];
"""
            },
            "id": "extract-lead",
            "name": "Extract Lead",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": [450, 300]
        },
        {
            "parameters": {
                "model": "gpt-4o-mini",
                "messages": {
                    "values": {
                        "system": "You are a lead qualification AI. Score the lead 1-10 based on budget, project clarity, and urgency. Return JSON: {score, priority, suggested_response, estimated_value}.",
                        "user": "={{JSON.stringify($json)}}"
                    }
                }
            },
            "id": "ai-qualify",
            "name": "AI Qualify",
            "type": "n8n-nodes-base.openAi",
            "typeVersion": 1,
            "position": [650, 300]
        },
        {
            "parameters": {
                "functionCode": """
// Parse AI score and route
const aiResult = JSON.parse(items[0].json.message?.content || '{}');
const lead = items[0].json;
lead.score = aiResult.score || 5;
lead.priority = aiResult.priority || 'medium';
lead.estimated_value = aiResult.estimated_value || 0;

// Route: score >= 8 = hot, >= 5 = warm, < 5 = cold
let route = 'cold';
if (lead.score >= 8) route = 'hot';
else if (lead.score >= 5) route = 'warm';

return [{json: {...lead, route, suggested_response: aiResult.suggested_response || ''}}];
"""
            },
            "id": "route-lead",
            "name": "Route Lead",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": [850, 300]
        },
        {
            "parameters": {
                "conditions": {
                    "string": [{"value1": "={{$json.route}}", "operation": "equal", "value2": "hot"}]
                }
            },
            "id": "if-hot",
            "name": "Hot Lead?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 1,
            "position": [1050, 300]
        },
        {
            "parameters": {
                "chatId": "599082521",
                "text": "=🔥 HOT LEAD (score: {{$json.score}})\nName: {{$json.name}}\nProject: {{$json.project_type}}\nBudget: ${{$json.budget}}\nValue: ${{$json.estimated_value}}\n{{$json.description}}",
                "additionalFields": {"parse_mode": "HTML"}
            },
            "id": "tg-notify",
            "name": "Telegram Notify",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1,
            "position": [1250, 200]
        },
        {
            "parameters": {
                "to": "={{$json.email}}",
                "subject": "Thanks for your inquiry!",
                "text": "={{$json.suggested_response}}",
                "from": "bot@darkbot.ai"
            },
            "id": "auto-reply",
            "name": "Auto Reply Email",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 1,
            "position": [1250, 400]
        },
        {
            "parameters": {
                "operation": "insert",
                "table": "leads",
                "columns": "name,email,phone,budget,project_type,description,score,priority,estimated_value,created_at",
                "values": "={{$json.name}},={{$json.email}},{{$json.phone}},{{$json.budget}},{{$json.project_type}},{{$json.description}},{{$json.score}},{{$json.priority}},{{$json.estimated_value}},{{$json.timestamp}}"
            },
            "id": "save-db",
            "name": "Save to DB",
            "type": "n8n-nodes-base.mySql",
            "typeVersion": 1,
            "position": [1450, 300]
        }
    ],
    "connections": {
        "Lead Webhook": {"main": [[{"node": "Extract Lead", "type": "main", "index": 0}]]},
        "Extract Lead": {"main": [[{"node": "AI Qualify", "type": "main", "index": 0}]]},
        "AI Qualify": {"main": [[{"node": "Route Lead", "type": "main", "index": 0}]]},
        "Route Lead": {"main": [[{"node": "Hot Lead?", "type": "main", "index": 0}]]},
        "Hot Lead?": {
            "main": [
                [{"node": "Telegram Notify", "type": "main", "index": 0}],
                [{"node": "Auto Reply Email", "type": "main", "index": 0}]
            ]
        },
        "Telegram Notify": {"main": [[{"node": "Save to DB", "type": "main", "index": 0}]]},
        "Auto Reply Email": {"main": [[{"node": "Save to DB", "type": "main", "index": 0}]]}
    }
}

def export_workflow(path: str = "workflow.json"):
    """Export workflow JSON for n8n import."""
    with open(path, "w") as f:
        json.dump(WORKFLOW, f, indent=2)
    print(f"Exported: {path}")
    return path

if __name__ == "__main__":
    export_workflow()
