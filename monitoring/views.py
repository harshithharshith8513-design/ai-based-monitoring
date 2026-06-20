import logging
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)
MAX_ASSISTANT_PROMPT_LENGTH = 2000


def offline_ai_bot_reply(message):
    text = message.lower()
    if any(word in text for word in ("screen time", "phone time", "device time")):
        return (
            "A practical screen-time plan starts with a clear daily limit, device-free "
            "meals, and a shared charging place outside the bedroom. Adjust the limit "
            "for schoolwork and review the plan with the child each week."
        )
    if any(word in text for word in ("bully", "harass", "threat")):
        return (
            "Save evidence without replying, block and report the account, and involve "
            "a trusted adult or school contact. If there is an immediate threat, contact "
            "local emergency services."
        )
    if any(word in text for word in ("password", "account", "hack", "privacy")):
        return (
            "Use a unique passphrase, enable two-factor authentication, review app "
            "permissions, and avoid sharing personal details such as school, address, "
            "phone number, or live location."
        )
    if any(word in text for word in ("stranger", "contact", "message", "chat")):
        return (
            "Teach the child not to move conversations with strangers to private apps, "
            "share images, or agree to meet. Block suspicious contacts and keep calm so "
            "the child feels safe reporting uncomfortable messages."
        )
    if any(word in text for word in ("location", "lost", "missing", "emergency")):
        return (
            "Check the Guardian Dashboard location with permission, call the child and "
            "trusted contacts, and verify familiar places. For immediate danger or a "
            "missing child, contact local emergency services promptly."
        )
    return (
        "AI Bot is currently in offline safety mode. I can help with screen time, online "
        "privacy, suspicious contacts, cyberbullying, location safety, and family digital "
        "rules. Add a Groq API key to enable live web search and broader AI answers."
    )


def request_groq_reply(user_message, safe_history):
    messages = [
        {
            "role": "system",
            "content": (
                "You are AI Bot, a concise, family-friendly assistant in ChildGuard AI. "
                "Use web search for current, recent, or factual questions that benefit "
                "from up-to-date information. Include clickable source URLs in the answer "
                "when web tools are used. Give practical digital-safety guidance and never "
                "claim to contact emergency services or replace professional advice."
            ),
        },
        *safe_history,
        {"role": "user", "content": user_message},
    ]
    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(
            {
                "model": settings.GROQ_MODEL,
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 512,
                "compound_custom": {
                    "tools": {
                        "enabled_tools": ["web_search", "visit_website"]
                    }
                },
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
            "Groq-Model-Version": "latest",
            "User-Agent": "ChildGuardAI/1.0",
        },
        method="POST",
    )
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    message = payload["choices"][0]["message"]
    executed_tools = message.get("executed_tools") or []
    web_used = any(
        tool.get("type") in {"search", "web_search", "visit_website"}
        for tool in executed_tools
        if isinstance(tool, dict)
    )
    return {
        "reply": message["content"].strip(),
        "web_used": web_used,
    }


def landing(request):
    return render(request, "landing.html")


@login_required
def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@login_required
def profile(request):
    return render(request, "profile.html")


@login_required
def resources(request):
    return render(request, "resources.html")


@login_required
def about(request):
    return render(request, "about.html")


@login_required
def assistant(request):
    if request.method != "POST":
        return render(
            request,
            "assistant.html",
            {"groq_enabled": bool(settings.GROQ_API_KEY)},
        )

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid chat request."}, status=400)

    user_message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])
    if not user_message:
        return JsonResponse({"error": "Please enter a message."}, status=400)
    if len(user_message) > MAX_ASSISTANT_PROMPT_LENGTH:
        return JsonResponse(
            {"error": f"Please keep messages under {MAX_ASSISTANT_PROMPT_LENGTH} characters."},
            status=400,
        )

    safe_history = []
    if isinstance(history, list):
        for item in history[-10:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = str(item.get("content", "")).strip()[:MAX_ASSISTANT_PROMPT_LENGTH]
            if role in {"user", "assistant"} and content:
                safe_history.append({"role": role, "content": content})

    if not settings.GROQ_API_KEY:
        return JsonResponse(
            {
                "reply": offline_ai_bot_reply(user_message),
                "mode": "offline",
                "web_used": False,
            }
        )

    try:
        result = request_groq_reply(user_message, safe_history)
        if not result["reply"]:
            raise ValueError("Groq returned an empty response")
        return JsonResponse(
            {
                "reply": result["reply"],
                "mode": "groq",
                "web_used": result["web_used"],
            }
        )
    except (HTTPError, URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
        logger.exception("Groq assistant request failed")
        return JsonResponse(
            {
                "reply": offline_ai_bot_reply(user_message),
                "mode": "offline-fallback",
                "web_used": False,
                "notice": "Groq was unavailable, so AI Bot answered in offline safety mode.",
            }
        )
