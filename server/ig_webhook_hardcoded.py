# ig_webhook_hardcoded_debug.py
import os
import csv
import json
from datetime import datetime
from flask import Flask, request, jsonify, abort

# --- HARD-CODED (for testing only) ---
PAGE_ACCESS_TOKEN = "EAATYVMYRxpABP6oYEN1S9MZAML4mYY5nOUvVNALoz7CLwZCFbtRBkFLJzx2M0jGOaTfVbZCbpqVNndu9ZAInwzCNXy5FZCI9zKX3o1ZBJKpa8vlV8IgcWv2fb6cqMB2zIrW1GgqDJK9vJoRMjZBRZAnKorauTavgyypRlcejE9lPBEZAByJFqpnXQ1u4PqgY0N9D3jzQ1AUzOZB6eFjQcU1JWTTJLO75r4GA59CZBDS"
VERIFY_TOKEN = "my_verify_token_for_testing"
APP_SECRET = None  # skip signature verification in this test
CSV_FILE = "instagram_messages_hardcoded.csv"
# ---------------------------------------

app = Flask(__name__)

def ensure_csv_header():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "received_at", "page_id", "sender_id", "sender_username",
                "message_id", "message_text", "timestamp", "raw_json"
            ])
            print("[DEBUG] CSV header created.")

def verify_signature(req):
    # Signature verification skipped in this test script
    return True

# -----------------------------
# GET handler for webhook verification
# -----------------------------
@app.route("/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    print("[DEBUG][GET] Webhook verify called with args:", request.args)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print(f"[DEBUG][GET] Verification SUCCESS. Responding with challenge: {challenge}")
        return str(challenge), 200, {"Content-Type": "text/plain"}
    else:
        print(f"[DEBUG][GET] Verification FAILED. Token mismatch: received {token}")
        return "Verification token mismatch", 403

# -----------------------------
# POST handler for incoming messages
# -----------------------------
@app.route("/webhook", methods=["POST"])
def webhook_receive():
    print("[DEBUG][POST] Incoming POST request headers:", dict(request.headers))
    print("[DEBUG][POST] Raw request body:", request.data.decode("utf-8"))

    if APP_SECRET and not verify_signature(request):
        print("[DEBUG][POST] Signature verification failed.")
        abort(403)

    payload = request.get_json(force=True, silent=True)
    if not payload:
        print("[DEBUG][POST] No JSON payload received.")
        return "No JSON", 400

    print("[DEBUG][POST] JSON payload parsed:", json.dumps(payload, indent=2, ensure_ascii=False))
    ensure_csv_header()

    object_type = payload.get("object")
    entries = payload.get("entry", [])
    print(f"[DEBUG][POST] Object type: {object_type}, entries count: {len(entries)}")

    records = []

    for entry_idx, entry in enumerate(entries):
        print(f"[DEBUG][POST] Processing entry {entry_idx}: {json.dumps(entry, indent=2, ensure_ascii=False)}")
        page_id = entry.get("id")
        changes = entry.get("changes", [])

        for change in changes:
            val = change.get("value", {})
            messages = val.get("messages") or val.get("message")
            if messages:
                if isinstance(messages, list):
                    for m in messages:
                        records.append((page_id, m, val))
                        print(f"[DEBUG][POST] Added message from changes list: {m}")
                elif isinstance(messages, dict):
                    records.append((page_id, messages, val))
                    print(f"[DEBUG][POST] Added message from changes dict: {messages}")

            if "messaging" in val:
                for m in val.get("messaging", []):
                    records.append((page_id, m, val))
                    print(f"[DEBUG][POST] Added messaging event: {m}")

        mess_list = entry.get("messaging") or entry.get("messaging_events")
        if mess_list:
            for m in mess_list:
                records.append((page_id, m, {}))
                print(f"[DEBUG][POST] Added messaging/messaging_events: {m}")

    appended = 0
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for page_id, m, context in records:
            sender_id = ""
            sender_username = ""
            message_text = ""
            message_id = ""
            ts = None

            if isinstance(m, dict):
                # extract sender info
                sender_id = m.get("sender", {}).get("id", "") or m.get("from", {}).get("id", "")
                sender_username = m.get("sender", {}).get("username", "") or m.get("from", {}).get("username", "")
                message_text = m.get("text", "") or m.get("message", {}).get("text", "")
                message_id = m.get("id") or m.get("mid") or m.get("message", {}).get("mid") or ""
                ts = m.get("timestamp") or m.get("created_time") or context.get("timestamp")

            # fallback: deep search for text
            if not message_text:
                def deep_search_text(d):
                    if isinstance(d, dict):
                        for k, v in d.items():
                            if k in ("text", "message_text", "body"):
                                return v
                            found = deep_search_text(v)
                            if found:
                                return found
                    elif isinstance(d, list):
                        for it in d:
                            found = deep_search_text(it)
                            if found:
                                return found
                    return None
                try:
                    message_text = deep_search_text(m) or message_text
                except Exception as e:
                    print("[DEBUG][POST] Exception during deep search:", e)

            received_at = datetime.utcnow().isoformat() + "Z"
            ts_iso = ""
            try:
                if isinstance(ts, (int, float)):
                    ts_iso = datetime.utcfromtimestamp(int(ts)/1000 if ts > 1e10 else int(ts)).isoformat() + "Z"
                elif isinstance(ts, str) and ts.isdigit():
                    val = int(ts)
                    ts_iso = datetime.utcfromtimestamp(val/1000 if val > 1e10 else val).isoformat() + "Z"
            except Exception as e:
                print("[DEBUG][POST] Exception converting timestamp:", e)

            raw = json.dumps({"message": m, "context": context}, ensure_ascii=False)
            writer.writerow([
                received_at, page_id or "", sender_id or "", sender_username or "",
                message_id or "", message_text or "", ts_iso or "", raw
            ])
            appended += 1
            print(f"[DEBUG][POST] Message appended to CSV: sender={sender_username}, text={message_text}")

    print(f"[DEBUG][POST] Total messages appended in this request: {appended}")
    return jsonify({"status": "received", "saved": appended}), 200

if __name__ == "__main__":
    ensure_csv_header()
    print("Starting IG webhook test server (hard-coded token).")
    print("Webhook endpoint: http://0.0.0.0:5000/webhook")
    app.run(host="0.0.0.0", port=5000, debug=True)
