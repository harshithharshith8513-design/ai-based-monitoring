import logging
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse

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


def register(request):
    if request.user.is_authenticated:
        return redirect("monitoring:home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        fullname = request.POST.get("fullname")
        
        # Aadhaar parameters returned from UI verified state
        aadhaar_verified = request.POST.get("aadhaar_verified") == "true"
        aadhaar_name = request.POST.get("aadhaar_name")

        if not username or not password or not fullname:
            messages.error(request, "Please fill in all basic registration fields.")
            return render(request, "register.html")

        if len(username) < 5:
            messages.error(request, "Username must be at least 5 characters long.")
            return render(request, "register.html")

        # Password complexity validation: >= 8 chars, upper, lower, digit, special char
        import re
        password_regex = re.compile(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"
        )
        if not password_regex.match(password):
            messages.error(
                request,
                "Password must be at least 8 characters long and contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character (@$!%*?&#)."
            )
            return render(request, "register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        if not aadhaar_verified:
            messages.error(request, "Aadhaar e-KYC / DigiLocker verification is mandatory.")
            return render(request, "register.html")

        # Extract extra Aadhaar fields
        aadhaar_number = request.POST.get("aadhaar_number")
        aadhaar_mobile = request.POST.get("aadhaar_mobile")
        aadhaar_address = request.POST.get("aadhaar_address")
        aadhaar_dob = request.POST.get("aadhaar_dob")

        if not aadhaar_number or len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            messages.error(request, "A valid 12-digit Aadhaar number is required.")
            return render(request, "register.html")

        if not aadhaar_mobile or len(aadhaar_mobile) != 10 or not aadhaar_mobile.isdigit():
            messages.error(request, "A valid 10-digit Aadhaar linked mobile number is required.")
            return render(request, "register.html")

        if not aadhaar_dob:
            messages.error(request, "Aadhaar Date of Birth is required.")
            return render(request, "register.html")

        if not aadhaar_address or not aadhaar_address.strip():
            messages.error(request, "Aadhaar Resident Address is required.")
            return render(request, "register.html")

        # Enforce Age Restricting Validation (Guardian must be >= 18)
        aadhaar_age_str = request.POST.get("aadhaar_age")
        try:
            aadhaar_age = int(aadhaar_age_str)
            if aadhaar_age < 18:
                messages.error(
                    request,
                    f"Guardian account creation denied. You must be at least 18 years old (Age extracted: {aadhaar_age})."
                )
                return render(request, "register.html")
        except (ValueError, TypeError):
            messages.error(request, "Aadhaar Age information could not be verified.")
            return render(request, "register.html")

        # Validation: Verify Name Matches Aadhaar
        if fullname.strip().lower() != aadhaar_name.strip().lower():
            messages.error(
                request,
                f"Registration name '{fullname}' does not match Aadhaar profile name '{aadhaar_name}'."
            )
            return render(request, "register.html")

        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "register.html")

        try:
            # Create user and log in
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=fullname
            )
            login(request, user)
            messages.success(request, f"Welcome to ChildGuard AI, {fullname}!")
            return redirect("monitoring:home")
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, "register.html")

    return render(request, "register.html")


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
