#!/usr/bin/env python3
"""First publication only. Failed operations are recorded, never retried."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from publication_checks import ValidationError, git, validate_history, validate_release, validate_source


class PublishError(RuntimeError):
    pass


class ApiError(PublishError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"api-failed: status={status}")


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        if request.get_method() != "GET" or target.scheme != "https" or not (target.hostname == "github.com" or (target.hostname or "").endswith(".githubusercontent.com")):
            raise PublishError("unexpected-api-redirect")
        redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
        redirected.remove_header("Authorization")
        return redirected


class GitHub:
    def __init__(self, token):
        if not token:
            raise PublishError("missing-token")
        self.token = token
        self.opener = urllib.request.build_opener(SafeRedirect())

    def request(self, method, path, payload=None, binary=False, upload=False):
        host = "https://uploads.github.com" if upload else "https://api.github.com"
        headers = {"Authorization": "Bearer " + self.token,
                   "Accept": "application/octet-stream" if binary else "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "KLB-publication"}
        if isinstance(payload, bytes):
            data = payload
            headers["Content-Type"] = "application/octet-stream"
        else:
            data = None if payload is None else json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(host + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=120) as response:
                result = response.read(256 * 1024 * 1024 + 1)
            if len(result) > 256 * 1024 * 1024:
                raise PublishError("api-response-too-large")
            return result if binary else json.loads(result)
        except urllib.error.HTTPError as error:
            raise ApiError(error.code) from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise PublishError("api-transport-or-response-failed") from None


def absent(api, path):
    try:
        api.request("GET", path)
    except ApiError as error:
        if error.status == 404:
            return
        raise
    raise PublishError("tag-or-release-already-exists")


def releases(api, base):
    found = []
    for page in range(1, 1001):
        batch = api.request("GET", f"{base}/releases?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise PublishError("invalid-release-list")
        found.extend(batch)
        if len(batch) < 100:
            return found
    raise PublishError("release-list-limit")


def publish(root, dist, repository, sha, version, api, record):
    """No mutation is attempted until local validation and remote preflight pass."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise PublishError("invalid-target")
    base = "/repos/" + repository
    state = {"repository": repository, "commit": sha, "phase": "local-validation"}

    def save(phase):
        state["phase"] = phase
        state["time"] = datetime.now(timezone.utc).isoformat()
        record(dict(state))

    try:
        save("local-validation")
        if git(root, "rev-parse", "HEAD").decode().strip() != sha:
            raise PublishError("checkout-commit-mismatch")
        if git(root, "status", "--porcelain", "--untracked-files=normal").strip():
            raise PublishError("checkout-not-clean")
        if (root / "release/RELEASE").read_text().strip() != version:
            raise PublishError("release-version-mismatch")
        validate_source(root)
        validate_history(root)
        names = validate_release(root, dist, version)
        tag = "v" + version
        state["tag"] = tag
        state["sha256"] = {n: hashlib.sha256((dist / n).read_bytes()).hexdigest() for n in names}
        notes = (root / "release" / tag / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        save("remote-preflight")
        # Confirm repository access before accepting a specific resource's 404.
        repo = api.request("GET", base)
        if repo.get("full_name", "").lower() != repository.lower() or not repo.get("permissions", {}).get("push"):
            raise PublishError("repository-access-not-confirmed")
        absent(api, f"{base}/git/ref/tags/{tag}")
        absent(api, f"{base}/releases/tags/{tag}")
        if any(r.get("tag_name") == tag for r in releases(api, base)):
            raise PublishError("draft-or-release-already-exists")
        # Atomic creation pins the verified commit. Existing refs cannot be updated.
        save("creating-new-tag")
        api.request("POST", base + "/git/refs", {"ref": "refs/tags/" + tag, "sha": sha})
        save("creating-draft")
        draft = api.request("POST", base + "/releases", {"tag_name": tag, "target_commitish": sha, "name": tag, "body": notes, "draft": True})
        release_id = draft.get("id")
        if type(release_id) is not int or draft.get("draft") is not True or draft.get("tag_name") != tag:
            raise PublishError("invalid-created-draft")
        state["release_id"] = release_id
        for name in names:
            save("uploading-" + name)
            api.request("POST", f"{base}/releases/{release_id}/assets?name=" + urllib.parse.quote(name), (dist / name).read_bytes(), upload=True)
        save("verifying-downloads")
        draft = api.request("GET", f"{base}/releases/{release_id}")
        if draft.get("draft") is not True or draft.get("tag_name") != tag or draft.get("body") != notes:
            raise PublishError("draft-changed")
        assets = api.request("GET", f"{base}/releases/{release_id}/assets?per_page=100")
        if len(assets) != len(names) or {a.get("name") for a in assets} != set(names):
            raise PublishError("remote-asset-inventory-mismatch")
        with tempfile.TemporaryDirectory(prefix="klb-download-check-") as directory:
            downloaded = Path(directory)
            for asset in assets:
                name = asset["name"]
                if asset.get("state") != "uploaded" or type(asset.get("id")) is not int:
                    raise PublishError("incomplete-upload")
                content = api.request("GET", f"{base}/releases/assets/{asset['id']}", binary=True)
                if hashlib.sha256(content).hexdigest() != state["sha256"][name]:
                    raise PublishError("download-hash-mismatch")
                (downloaded / name).write_bytes(content)
            validate_release(root, downloaded, version)
        ref = api.request("GET", f"{base}/git/ref/tags/{tag}")
        if ref.get("object", {}).get("sha") != sha or ref.get("object", {}).get("type") != "commit":
            raise PublishError("tag-changed")
        # This PATCH is restricted to the draft ID created by this invocation.
        save("publishing-verified-draft")
        result = api.request("PATCH", f"{base}/releases/{release_id}", {"draft": False, "make_latest": "true"})
        if result.get("id") != release_id or result.get("draft") is not False:
            raise PublishError("publication-result-unconfirmed")
        save("published")
    except Exception as error:
        # An interrupted write may have succeeded remotely. Inspect, never retry.
        state["failed_phase"] = state["phase"]
        state["error"] = str(error) if isinstance(error, (PublishError, ValidationError)) else "unexpected-local-or-response-error"
        if "tag" in state:
            try:
                matches = [r for r in releases(api, base) if r.get("tag_name") == state["tag"]]
                state["observed_releases"] = [{"id": r.get("id"), "draft": r.get("draft")} for r in matches]
                ref = api.request("GET", f"{base}/git/ref/tags/{state['tag']}")
                state["observed_tag_sha"] = ref.get("object", {}).get("sha")
            except (PublishError, TypeError, KeyError):
                state["remote_state"] = "not-fully-confirmed"
        save("stopped-no-retry")
        raise PublishError(state["error"]) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    def record(state):
        args.state.parent.mkdir(parents=True, exist_ok=True)
        with args.state.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True) + "\n")

    try:
        publish(root, root / "dist", args.repository, args.commit, args.version, GitHub(os.environ.get("GH_TOKEN")), record)
    except (PublishError, OSError) as error:
        print(str(error) if isinstance(error, PublishError) else "state-or-source-io-failed", file=sys.stderr)
        return 1
    print("OK: new release published after download verification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
