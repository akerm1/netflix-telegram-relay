"""Debug: show raw FETCH INTERNALDATE response structure."""

import imaplib
import os

from dotenv import load_dotenv

load_dotenv()

conn = imaplib.IMAP4_SSL("imap.gmail.com", timeout=30)
conn.login(os.getenv("EMAIL_ACCOUNT"), os.getenv("EMAIL_APP_PASSWORD"))
conn.select("INBOX")

typ, data = conn.search(None, "UNSEEN", '(FROM "netflix.com")')
ids = data[0].split()
print("ids:", len(ids))

mid = ids[-1]
typ, d = conn.fetch(mid, "(INTERNALDATE)")
print("type:", typ)
print("repr:", repr(d))

# also check element types
if d and d[0] is not None:
    print("elem0 type:", type(d[0]), "->", type(d[0][0]) if isinstance(d[0], tuple) else "n/a")

conn.logout()
