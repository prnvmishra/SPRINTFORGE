"""End-to-end check of the settings, avatar, leaderboard and community endpoints.

Creates throwaway accounts against a running API and deletes them at the end.
"""

import io
import json
import random
import struct
import sys
import urllib.error
import urllib.request
import uuid
import zlib

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
MODULE_ID = None


def request(method, path, token=None, body=None, files=None):
    url = f"{BASE}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if files is not None:
        boundary = uuid.uuid4().hex
        name, content, content_type = files
        buffer = io.BytesIO()
        buffer.write(f"--{boundary}\r\n".encode())
        buffer.write(
            f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'.encode()
        )
        buffer.write(f"Content-Type: {content_type}\r\n\r\n".encode())
        buffer.write(content)
        buffer.write(f"\r\n--{boundary}--\r\n".encode())
        data = buffer.getvalue()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
            if not raw or not response.headers.get_content_type().endswith("json"):
                return response.status, None
            return response.status, json.loads(raw)
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, (json.loads(raw) if raw else None)


def png_bytes(size=8):
    def chunk(kind, payload):
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x7f\xd7\x00" * size for _ in range(size))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def check(label, condition, detail=""):
    print(f"{'PASS' if condition else 'FAIL'}  {label} {detail}")
    if not condition:
        check.failed = True


check.failed = False


def register(prefix):
    email = f"{prefix}{random.randint(10000, 99999)}@sprintforge.dev"
    status, payload = request(
        "POST", "/auth/register", body={"name": f"{prefix.title()} Tester", "email": email, "password": "Testpass123!"}
    )
    assert status == 201, (status, payload)
    return email, payload["access_token"]


def main():
    global MODULE_ID
    status, modules = request("GET", "/practice/modules")
    MODULE_ID = modules["modules"][0]["id"]

    email, token = register("primary")
    other_email, other_token = register("secondary")

    # ---------------------------------------------------------- profile
    new_email = f"renamed{random.randint(10000, 99999)}@sprintforge.dev"
    status, payload = request(
        "PATCH", "/account/profile", token, {"name": "Renamed Tester", "email": new_email, "bio": "Learning in public."}
    )
    check("profile update", status == 200 and payload["bio"] == "Learning in public.", str(status))

    status, payload = request(
        "PATCH", "/account/profile", token, {"name": "Renamed Tester", "email": other_email, "bio": ""}
    )
    check("email conflict rejected", status == 409, str(status))

    # --------------------------------------------------------- password
    status, _ = request("POST", "/account/password", token, {"current_password": "wrong", "new_password": "Newpass123!"})
    check("wrong current password rejected", status == 400, str(status))
    status, _ = request(
        "POST", "/account/password", token, {"current_password": "Testpass123!", "new_password": "Newpass123!"}
    )
    check("password changed", status == 204, str(status))
    status, _ = request("POST", "/auth/login", body={"email": new_email, "password": "Newpass123!"})
    check("login with new password", status == 200, str(status))

    # ----------------------------------------------------------- avatar
    status, payload = request("POST", "/account/avatar", token, files=("a.png", png_bytes(), "image/png"))
    check("avatar upload", status == 200 and (payload or {}).get("avatar_url", "").startswith("/uploads/"), str(status))
    avatar_url = payload["avatar_url"]
    status, _ = request("GET", avatar_url, token)
    check("avatar served statically", status == 200, str(status))
    status, _ = request("POST", "/account/avatar", token, files=("a.gif", b"GIF89a", "image/gif"))
    check("bad content type rejected", status == 415, str(status))
    status, _ = request("POST", "/account/avatar", token, files=("big.png", b"\x00" * (2 * 1024 * 1024 + 10), "image/png"))
    check("oversize rejected", status == 413, str(status))
    status, payload = request("DELETE", "/account/avatar", token)
    check("avatar removed", status == 200 and payload["avatar_url"] is None, str(status))

    # ------------------------------------------------------ leaderboard
    status, board = request("GET", "/leaderboard?limit=5", token)
    check("leaderboard fetch", status == 200 and "formula" in board, str(status))
    check("current user resolved", board["current_user"] is not None)
    ranks = [entry["rank"] for entry in board["entries"]]
    check("ranks sequential", ranks == sorted(ranks))
    scores = [entry["score"] for entry in board["entries"]]
    check("scores descending", scores == sorted(scores, reverse=True))

    # -------------------------------------------------------- community
    status, post = request("POST", f"/community/modules/{MODULE_ID}/posts", token, {"body": "  How do I start?  "})
    check("post created", status == 201 and post["body"] == "How do I start?", str(status))
    status, reply = request(
        "POST", f"/community/modules/{MODULE_ID}/posts", other_token, {"body": "Read the brief first.", "parent_id": post["id"]}
    )
    check("reply created", status == 201 and reply["parent_id"] == post["id"], str(status))

    status, thread = request("GET", f"/community/modules/{MODULE_ID}/posts", token)
    root = next((item for item in thread["posts"] if item["id"] == post["id"]), None)
    check("thread nests reply", root is not None and len(root["replies"]) == 1, str(status))
    check("ownership flags", root["can_delete"] is True and root["replies"][0]["can_delete"] is False)

    status, counts = request("GET", "/community/counts", token)
    check("counts include module", counts["counts"].get(MODULE_ID, 0) >= 2, str(status))

    status, _ = request("DELETE", f"/community/posts/{reply['id']}", token)
    check("cannot delete others' post", status == 403, str(status))
    status, _ = request("DELETE", f"/community/posts/{post['id']}", token)
    check("author deletes own post", status == 204, str(status))
    status, thread = request("GET", f"/community/modules/{MODULE_ID}/posts", token)
    check("reply removed with parent", all(item["id"] != post["id"] for item in thread["posts"]), str(status))

    # ------------------------------------------------- account deletion
    status, _ = request("DELETE", "/account", token, {"confirmation": "nope"})
    check("bad confirmation rejected", status == 400, str(status))
    status, _ = request("DELETE", "/account", token, {"confirmation": "DELETE"})
    check("account deleted", status == 204, str(status))
    status, _ = request("GET", "/auth/me", token)
    check("token no longer resolves", status == 401, str(status))

    status, _ = request("DELETE", "/account", other_token, {"confirmation": other_email})
    check("second account deleted by email confirmation", status == 204, str(status))

    print("\nRESULT:", "FAILURES PRESENT" if check.failed else "ALL PASS")
    return 1 if check.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
