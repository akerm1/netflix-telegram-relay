import html
import re
from email import policy
from email.message import EmailMessage
from typing import Any

NETFLIX_SENDERS = (
    "info@account.netflix.com",
    "info@mailer.netflix.com",
)


class ParsedEmail:
    def __init__(self, category: str | None = None, data: dict[str, Any] | None = None):
        self.category = category  # 'code', 'household_link', 'password_reset' or None
        self.data = data or {}

    @property
    def is_code(self) -> bool:
        return self.category == "code"

    @property
    def is_household_link(self) -> bool:
        return self.category == "household_link"

    @property
    def is_password_reset(self) -> bool:
        return self.category == "password_reset"


def _get_body_text(msg: EmailMessage) -> tuple[str, str, str]:
    subject = msg.get("Subject", "") or ""
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.iter_parts():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition", ""))
            if "attachment" in cdisp:
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except Exception:
                decoded = payload.decode("utf-8", errors="replace")
            if ctype == "text/html":
                body_html += decoded
            elif ctype == "text/plain":
                body_text += decoded
    else:
        ctype = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload is not None:
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except Exception:
                decoded = payload.decode("utf-8", errors="replace")
            if ctype == "text/html":
                body_html = decoded
            else:
                body_text = decoded

    return subject, body_text, body_html


def _extract_urls_from_html(html_content: str):
    urls = []
    hp = re.compile(r"href=[\"']([^\"']+)[\"']", re.IGNORECASE)
    for m in hp.findall(html_content):
        try:
            urls.append(html.unescape(m))
        except Exception:
            urls.append(m)
    return urls


def _extract_all_urls(text: str):
    return re.findall(r"(https?://[^\s<>\"']+)", text, re.IGNORECASE)


def parse_email_message(raw_bytes: bytes) -> ParsedEmail:
    try:
        msg = EmailMessage(policy=policy.default)
        msg.set_content(raw_bytes)
    except Exception:
        try:
            from email import message_from_bytes

            msg = message_from_bytes(raw_bytes, policy=policy.default)
        except Exception:
            return ParsedEmail()

    subject, body_text, body_html = _get_body_text(msg)
    combined_text = " ".join([subject or "", body_text or ""])
    combined_html = body_html or ""
    subj_l = (subject or "").lower()
    text_l = combined_text.lower()

    pr_kw = ["reset your password", "password reset"]
    hh_kw = ["household", "update", "traveling", "confirm"]
    cd_kw = ["temporary code", "verification code", "access code"]

    has_pr = any(k in subj_l or k in text_l for k in pr_kw)
    has_hh = any(k in subj_l or k in text_l for k in hh_kw)
    has_cd = any(k in subj_l or k in text_l for k in cd_kw)

    urls_from_html = _extract_urls_from_html(combined_html)
    urls_from_text = _extract_all_urls(combined_text)
    all_urls = urls_from_html + urls_from_text

    # Category C: Password Reset (SENSITIVE) - checked first
    if has_pr or any(
        "netflix.com/password" in u or "netflix.com/account/loginhelp" in u for u in all_urls
    ):
        for u in all_urls:
            if "netflix.com/password" in u or "netflix.com/account/loginhelp" in u:
                return ParsedEmail("password_reset", {"url": u})
        if has_pr and all_urls:
            return ParsedEmail("password_reset", {"url": all_urls[0]})

    # Category B: Household Update Link
    if has_hh or any(
        "netflix.com/account/travel" in u or "netflix.com/verify" in u for u in all_urls
    ):
        for u in all_urls:
            if "netflix.com/account/travel" in u or "netflix.com/verify" in u:
                return ParsedEmail("household_link", {"url": u})
        if has_hh and all_urls:
            return ParsedEmail("household_link", {"url": all_urls[0]})

    # Category A: OTP / Access Code
    if has_cd:
        m = re.search(r"\b\d{4}\b", combined_text)
        if not m and combined_html:
            try:
                m = re.search(r"\b\d{4}\b", html.unescape(combined_html))
            except Exception:
                pass
        if m:
            return ParsedEmail("code", {"value": m.group(0)})

    # Fallback: any standalone 4-digit code
    m = re.search(r"\b\d{4}\b", combined_text)
    if not m and combined_html:
        try:
            m = re.search(r"\b\d{4}\b", html.unescape(combined_html))
        except Exception:
            pass
    if m:
        return ParsedEmail("code", {"value": m.group(0)})

    return ParsedEmail()
