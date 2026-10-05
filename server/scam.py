"""Optional scam-intent layer: transcript text -> Ollama Gemma -> JSON.
Set OLLAMA_MODEL to a Gemma tag you have pulled (check `ollama list`)."""
import json, os, urllib.request

URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
TACTICS = "urgency, payment_request, otp_request, impersonation, secrecy, threat"

PROMPT = """You screen phone-call transcripts for scams. Tactics list: {tactics}.
Return JSON only: {{"risk":"low|medium|high","tactics":[...],"reason":"max 20 words"}}.
Ordinary calls (delivery, family, appointment reminders) are LOW risk with empty tactics.
Examples:
"Hi, your parcel arrives at 5 pm, please keep your phone nearby." -> {{"risk":"low","tactics":[],"reason":"routine delivery notice"}}
"This is the bank. Your account is frozen, read me the OTP right now." -> {{"risk":"high","tactics":["urgency","otp_request","impersonation"],"reason":"asks for OTP urgently while posing as the bank"}}
Transcript: "{text}"
JSON:"""

def classify(text):
    body = json.dumps({"model": MODEL, "prompt": PROMPT.format(tactics=TACTICS, text=text[-800:]),
                       "stream": False, "format": "json"}).encode()
    try:
        req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            out = json.loads(json.loads(r.read())["response"])
        if out.get("risk") in ("low", "medium", "high"):
            return out
    except Exception as e:
        print("[scam] failed:", e)
    return None
