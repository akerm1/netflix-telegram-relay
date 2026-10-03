from logger import setup_logger
from parser import parse_email_message

# HTML email with household link (typical Netflix HTML)
html_mail = (
    b'From: info@account.netflix.com\r\n'
    b'Subject: Let us know if this was you\r\n'
    b'Content-Type: text/html\r\n\r\n'
    b'<html><body><p>Your temporary access code: <b>7314</b></p>'
    b'<a href="https://www.netflix.com/verify?ci=abc">Confirm</a></body></html>'
)
r = parse_email_message(html_mail)
print("html household:", r.category, r.data)
assert r.category == "household_link", r.category

# HTML code email
html_code = (
    b'From: info@account.netflix.com\r\n'
    b'Subject: Your verification code\r\n'
    b'Content-Type: text/html\r\n\r\n'
    b'<html><body>Your verification code is 5566.</body></html>'
)
r = parse_email_message(html_code)
print("html code:", r.category, r.data)
assert r.category == "code" and r.data["value"] == "5566", r.data

# unknown email
r = parse_email_message(b"From: x@y.com\r\nSubject: hello\r\n\r\njust saying hi")
print("unknown:", r.category)
assert r.category is None

# logging masks passwords
lg = setup_logger("smoketest")
lg.info("EMAIL_APP_PASSWORD=rawsecret123 token=abc")

print("ALL PARSER/LOGGING TESTS PASSED")
