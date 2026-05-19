import base64
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

OTP_TTL_SECONDS = 300
_pending_registrations: dict[str, dict] = {}


def create_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def save_pending_registration(mobile: str, registration_data: dict, otp: str) -> None:
    _pending_registrations[mobile] = {
        "data": registration_data,
        "otp": otp,
        "expires_at": time.time() + OTP_TTL_SECONDS,
    }


def verify_pending_registration(mobile: str, otp: str) -> dict | None:
    pending = _pending_registrations.get(mobile)
    if not pending:
        return None

    if pending["expires_at"] < time.time():
        _pending_registrations.pop(mobile, None)
        return None

    if pending["otp"] != otp:
        return None

    _pending_registrations.pop(mobile, None)
    return pending["data"]


def send_mobile_otp(mobile: str, otp: str) -> tuple[bool, str]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not account_sid or not auth_token or not from_number:
        return False, "Twilio is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER."

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload = urllib.parse.urlencode(
        {
            "From": from_number,
            "To": mobile,
            "Body": f"Your registration OTP is {otp}. It expires in 5 minutes.",
        }
    ).encode("utf-8")

    auth_header = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if 200 <= response.status < 300:
                return True, "OTP sent successfully."
            return False, f"Twilio returned status code {response.status}."
    except urllib.error.HTTPError as exc:
        return False, f"Twilio error: {exc.code} {exc.reason}"
    except urllib.error.URLError as exc:
        return False, f"Could not reach Twilio: {exc.reason}"
