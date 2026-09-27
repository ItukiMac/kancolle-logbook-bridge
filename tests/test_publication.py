"""Product fixtures and mocked APIs; no network requests or real releases."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publication_checks as checks
import publish_release as publishing

OWNER = "266446300+ItukiMac@users.noreply.github.com"
FAKE = "fixture" + "@" + "example.test"


def zip_bytes(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as archive:
        for name, content in files.items():
            archive.writestr(zipfile.ZipInfo(name), content)
    return output.getvalue()


class ProductFixture:
    version = "1.0.0"
    extname = "klb-chrome-extension-v1.0.0.zip"
    jarname = "klb-logbook-plugin-v1.0.0.jar"
    fullname = "klb-v1.0.0.zip"
    prefix = "klb-v1.0.0/"

    def __init__(self, root):
        self.root = root
        self.dist = root / "dist"
        self.dist.mkdir()
        self.ext = {"LICENSE": b"fixture license\n", "NOTICE.md": b"fixture notice\n", "manifest.json": b'{"version":"1.0.0"}', "background.js": b"// product fixture\n"}
        self.jar = {"META-INF/LICENSE": self.ext["LICENSE"], "META-INF/NOTICE.md": self.ext["NOTICE.md"], "META-INF/MANIFEST.MF": b"Implementation-Version: 1.0.0\r\n", "Product.class": b"compiled fixture"}
        self.source = {"LICENSE": self.ext["LICENSE"], "NOTICE.md": self.ext["NOTICE.md"], "README.md": b"Product fixture\n", "docs/TECHNICAL.md": b"Product documentation\n", "release/RELEASE": b"1.0.0\n", "release/v1.0.0/RELEASE_NOTES.md": b"Product release\n", ".gitignore": b"dist/\n"}
        self.source.update({"extension/" + n: b for n, b in self.ext.items()})
        self.rules = {"source_files": sorted([*self.source, "publication-policy.json"]), "jar_files": sorted(self.jar), "allowed_emails": [OWNER], "owner_names": ["ItukiMac"], "owner_email": OWNER}
        self.rules["required_notices"] = {n: hashlib.sha256(self.source[n]).hexdigest() for n in ("LICENSE", "NOTICE.md", "extension/LICENSE", "extension/NOTICE.md")}
        self.source["publication-policy.json"] = json.dumps(self.rules).encode()
        for name, content in self.source.items():
            file = root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
        self.full = {self.prefix + n: b for n, b in self.source.items() if n in ("LICENSE", "NOTICE.md", "README.md") or n.startswith(("extension/", "docs/"))}
        self.full.update({self.prefix + "RELEASE_NOTES.md": self.source["release/v1.0.0/RELEASE_NOTES.md"], self.prefix + "plugin/" + self.jarname: zip_bytes(self.jar), self.prefix + "plugin/install.sh": b"#!/bin/sh\n", self.prefix + "plugin/disable.sh": b"#!/bin/sh\n"})
        self.write()

    def write(self):
        for name, entries in ((self.extname, self.ext), (self.jarname, self.jar), (self.fullname, self.full)):
            (self.dist / name).write_bytes(zip_bytes(entries))
        self.checksums()

    def checksums(self):
        lines = [hashlib.sha256((self.dist / n).read_bytes()).hexdigest() + "  " + n for n in (self.extname, self.jarname, self.fullname)]
        (self.dist / "SHA256SUMS-v1.0.0.txt").write_text("\n".join(lines) + "\n", encoding="ascii")

    def git(self, *args, author=OWNER, committer=OWNER):
        env = dict(os.environ, GIT_AUTHOR_NAME="ItukiMac", GIT_AUTHOR_EMAIL=author, GIT_COMMITTER_NAME="ItukiMac", GIT_COMMITTER_EMAIL=committer, GIT_CONFIG_NOSYSTEM="1")
        # Avoid external signing hooks and inherited user identity in fixtures.
        return subprocess.check_output(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "-c", "core.hooksPath=/dev/null", "-C", str(self.root), *args], env=env, stderr=subprocess.DEVNULL)

    def init_git(self):
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "Product fixture")
        return self.git("rev-parse", "HEAD").decode().strip()

    def validate(self):
        return checks.validate_release(self.root, self.dist, self.version)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.product = ProductFixture(Path(self.temp.name))


class PackageTests(FixtureTests):
    def test_valid_product(self):
        self.assertEqual(len(self.product.validate()), 4)

    def test_unknown_file_any_extension(self):
        for name in ("personal.py", "personal", "docs/personal.txt"):
            with self.subTest(name=name):
                self.product.full[self.product.prefix + name] = b"fixture"
                self.product.write()
                with self.assertRaises(checks.ValidationError):
                    self.product.validate()
                del self.product.full[self.product.prefix + name]

    def test_missing_license_and_notice(self):
        for entries, name in ((self.product.ext, "LICENSE"), (self.product.jar, "META-INF/NOTICE.md"), (self.product.full, self.product.prefix + "LICENSE")):
            with self.subTest(name=name):
                content = entries.pop(name)
                self.product.write()
                with self.assertRaises(checks.ValidationError):
                    self.product.validate()
                entries[name] = content

    def test_truncated_license(self):
        self.product.ext["LICENSE"] = b"fixture"
        self.product.write()
        with self.assertRaises(checks.ValidationError):
            self.product.validate()

    def test_truncated_canonical_license(self):
        (self.product.root / "LICENSE").write_bytes(b"fixture")
        with self.assertRaises(checks.ValidationError):
            self.product.validate()

    def test_nested_jar_mismatch(self):
        self.product.full[self.product.prefix + "plugin/" + self.product.jarname] = b"different"
        self.product.write()
        with self.assertRaises(checks.ValidationError):
            self.product.validate()

    def test_nested_extension_mismatch(self):
        self.product.full[self.product.prefix + "extension/background.js"] = b"different"
        self.product.write()
        with self.assertRaises(checks.ValidationError):
            self.product.validate()

    def test_distribution_email_is_redacted(self):
        self.product.jar["Product.class"] = FAKE.encode()
        self.product.write()
        with self.assertRaises(checks.ValidationError) as caught:
            self.product.validate()
        self.assertNotIn(FAKE, str(caught.exception))
        self.assertIn("unapproved-email", str(caught.exception))

    def test_nested_email(self):
        self.product.full[self.product.prefix + "plugin/install.sh"] = FAKE.encode()
        self.product.write()
        with self.assertRaises(checks.ValidationError):
            self.product.validate()

    def test_bad_checksum(self):
        (self.product.dist / "SHA256SUMS-v1.0.0.txt").write_text("invalid\n")
        with self.assertRaises(checks.ValidationError):
            self.product.validate()

    def test_unexpected_distribution_file(self):
        (self.product.dist / "extra").write_text("fixture")
        with self.assertRaises(checks.ValidationError):
            self.product.validate()

    def test_invalid_archive_paths(self):
        for name in ("../file", "/file", "a/../file", "a\\file", "C:file", "a//file", "./file"):
            with self.subTest(name=name), self.assertRaises(checks.ValidationError):
                checks.archive(zip_bytes({name: b"data"}), {"file"}, "fixture.zip", self.product.rules)

    def test_nul_in_stored_path(self):
        malformed = zip_bytes({"fileXhidden": b"data"}).replace(b"fileXhidden", b"file\0hidden")
        with self.assertRaises(checks.ValidationError):
            checks.archive(malformed, {"file"}, "fixture.zip", self.product.rules)

    def test_duplicate_entries(self):
        output = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(output, "w") as archive:
                archive.writestr("file", b"one")
                archive.writestr("file", b"two")
        with self.assertRaises(checks.ValidationError):
            checks.archive(output.getvalue(), {"file"}, "fixture.zip", self.product.rules)

    def test_symlink(self):
        output = io.BytesIO()
        entry = zipfile.ZipInfo("file")
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr(entry, b"destination")
        with self.assertRaises(checks.ValidationError):
            checks.archive(output.getvalue(), {"file"}, "fixture.zip", self.product.rules)

    def test_corrupt_archive_and_crc(self):
        good = zip_bytes({"file": b"unique-payload"})
        for content in (b"not an archive", good[:20], good.replace(b"unique-payload", b"unique-payloae")):
            with self.subTest(content_length=len(content)), self.assertRaises(checks.ValidationError):
                checks.archive(content, {"file"}, "fixture.zip", self.product.rules)

    def test_text_encodings_and_allowed_notice(self):
        for content in (FAKE.encode(), FAKE.encode("utf-16")):
            with self.assertRaises(checks.ValidationError):
                checks.check_emails(content, "fixture", self.product.rules)
        rules = copy.deepcopy(self.product.rules)
        rules["allowed_emails"].append(FAKE)
        checks.check_emails(("Copyright fixture <" + FAKE + ">").encode(), "NOTICE", rules)


class HistoryTests(FixtureTests):
    def test_source_inventory(self):
        p = self.product
        p.init_git()
        checks.validate_source(p.root)
        (p.root / "unexpected").write_text("fixture")
        p.git("add", "unexpected")
        with self.assertRaises(checks.ValidationError):
            checks.validate_source(p.root)

    def test_source_email(self):
        p = self.product
        p.init_git()
        (p.root / "README.md").write_text(FAKE)
        with self.assertRaises(checks.ValidationError):
            checks.validate_source(p.root)

    def test_both_commit_identities(self):
        p = self.product
        base = p.init_git()
        checks.validate_history(p.root)
        for role in ("author", "committer"):
            p.git("checkout", "--detach", base)
            p.git("commit", "--allow-empty", "-qm", "Identity fixture", **{role: FAKE})
            with self.assertRaises(checks.ValidationError) as caught:
                checks.validate_history(p.root)
            self.assertNotIn(FAKE, str(caught.exception))

    def test_commit_message(self):
        p = self.product
        p.init_git()
        p.git("commit", "--allow-empty", "-qm", FAKE)
        with self.assertRaises(checks.ValidationError):
            checks.validate_history(p.root)

    def test_annotated_tag_message_and_tagger(self):
        p = self.product
        p.init_git()
        p.git("tag", "-a", "message-fixture", "-m", FAKE)
        with self.assertRaises(checks.ValidationError):
            checks.validate_history(p.root)
        p.git("tag", "-d", "message-fixture")
        p.git("tag", "-a", "identity-fixture", "-m", "Fixture", committer=FAKE)
        with self.assertRaises(checks.ValidationError):
            checks.validate_history(p.root)

    def test_owner_requires_noreply_even_if_other_email_allowed(self):
        rules = copy.deepcopy(self.product.rules)
        rules["allowed_emails"].append(FAKE)
        with self.assertRaises(checks.ValidationError):
            checks.check_identity(f"author ItukiMac <{FAKE}> 1 +0000".encode(), "fixture-sha", rules)


class FakeGitHub:
    def __init__(self, scenario="success"):
        self.scenario = scenario
        self.calls = []
        self.ref = {"object": {"sha": "0" * 40, "type": "commit"}} if scenario == "existing-tag" else None
        self.release = {"id": 7, "tag_name": "v1.0.0", "draft": scenario == "existing-draft"} if scenario in ("existing-release", "existing-draft") else None
        self.assets = []
        self.bytes = {}

    @property
    def mutations(self):
        return [c for c in self.calls if c[0] != "GET"]

    def request(self, method, path, payload=None, binary=False, upload=False):
        self.calls.append((method, path, payload))
        base = "/repos/fixture/product"
        if method == "GET" and path == base:
            if self.scenario == "auth-error":
                raise publishing.ApiError(403)
            if self.scenario == "hidden-repository":
                raise publishing.ApiError(404)
            if self.scenario == "network-error":
                raise publishing.PublishError("api-transport-or-response-failed")
            return {"full_name": "fixture/product", "permissions": {"push": True}}
        if method == "GET" and path.startswith(base + "/git/ref/"):
            if self.scenario == "tag-read-error":
                raise publishing.ApiError(500)
            if self.ref is None:
                raise publishing.ApiError(404)
            return self.ref
        if method == "GET" and path == base + "/releases/tags/v1.0.0":
            if self.scenario == "release-read-error":
                raise publishing.ApiError(403)
            if self.release is None or self.release["draft"]:
                raise publishing.ApiError(404)
            return self.release
        if method == "GET" and path.startswith(base + "/releases?per_page="):
            return [self.release] if self.release else []
        if method == "POST" and path == base + "/git/refs":
            if self.scenario == "tag-race":
                raise publishing.ApiError(422)
            self.ref = {"object": {"sha": payload["sha"], "type": "commit"}}
            return self.ref
        if method == "POST" and path == base + "/releases":
            self.release = dict(payload, id=42)
            if self.scenario == "ambiguous-create":
                raise publishing.PublishError("api-transport-or-response-failed")
            return self.release
        if method == "POST" and "/releases/42/assets?name=" in path:
            if self.scenario == "upload-failure" and self.assets:
                raise publishing.ApiError(503)
            name = path.split("name=")[1]
            asset = {"name": name, "id": len(self.assets) + 100, "state": "uploaded"}
            self.assets.append(asset)
            self.bytes[asset["id"]] = payload
            return asset
        if method == "GET" and path == base + "/releases/42":
            return self.release
        if method == "GET" and path == base + "/releases/42/assets?per_page=100":
            return self.assets
        if method == "GET" and path.startswith(base + "/releases/assets/"):
            return b"tampered" if self.scenario == "bad-download" else self.bytes[int(path.rsplit("/", 1)[1])]
        if method == "PATCH" and path == base + "/releases/42":
            self.release.update(payload)
            return self.release
        raise AssertionError("Unexpected mock API call: " + method + " " + path)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.product = ProductFixture(Path(self.temp.name))
        self.sha = self.product.init_git()
        self.states = []

    def publish(self, api):
        publishing.publish(self.product.root, self.product.dist, "fixture/product", self.sha, "1.0.0", api, self.states.append)

    def test_existing_tag_release_and_draft_never_mutated(self):
        for scenario in ("existing-tag", "existing-release", "existing-draft"):
            api = FakeGitHub(scenario)
            with self.subTest(scenario=scenario), self.assertRaises(publishing.PublishError):
                self.publish(api)
            self.assertEqual(api.mutations, [])

    def test_preflight_errors_never_mutate(self):
        for scenario in ("auth-error", "hidden-repository", "network-error", "tag-read-error", "release-read-error"):
            api = FakeGitHub(scenario)
            with self.subTest(scenario=scenario), self.assertRaises(publishing.PublishError):
                self.publish(api)
            self.assertEqual(api.mutations, [])

    def test_partial_upload_failure_preserves_draft(self):
        api = FakeGitHub("upload-failure")
        with self.assertRaises(publishing.PublishError):
            self.publish(api)
        self.assertTrue(api.release["draft"])
        self.assertEqual(len(api.assets), 1)
        self.assertFalse(any(m[0] in ("DELETE", "PATCH") for m in api.mutations))
        self.assertEqual(self.states[-1]["phase"], "stopped-no-retry")

    def test_download_failure_does_not_publish(self):
        api = FakeGitHub("bad-download")
        with self.assertRaises(publishing.PublishError):
            self.publish(api)
        self.assertTrue(api.release["draft"])
        self.assertFalse(any(m[0] in ("DELETE", "PATCH") for m in api.mutations))

    def test_ambiguous_creation_is_queried_without_retry(self):
        api = FakeGitHub("ambiguous-create")
        with self.assertRaises(publishing.PublishError):
            self.publish(api)
        self.assertTrue(api.release["draft"])
        self.assertEqual(sum(m[1].endswith("/releases") for m in api.mutations), 1)
        self.assertEqual(self.states[-1]["observed_releases"], [{"id": 42, "draft": True}])

    def test_tag_creation_conflict_is_not_overwritten(self):
        api = FakeGitHub("tag-race")
        with self.assertRaises(publishing.PublishError):
            self.publish(api)
        self.assertEqual(len(api.mutations), 1)
        self.assertIsNone(api.release)

    def test_invalid_local_package_causes_no_writes(self):
        (self.product.dist / "extra").write_text("fixture")
        api = FakeGitHub()
        with self.assertRaises(publishing.PublishError):
            self.publish(api)
        self.assertEqual(api.mutations, [])

    def test_success_publishes_only_after_all_download_checks(self):
        api = FakeGitHub()
        self.publish(api)
        self.assertFalse(api.release["draft"])
        self.assertEqual(self.states[-1]["phase"], "published")
        patches = [m for m in api.mutations if m[0] == "PATCH"]
        self.assertEqual(patches, [("PATCH", "/repos/fixture/product/releases/42", {"draft": False, "make_latest": "true"})])
        self.assertEqual(sum(c[0] == "GET" and "/releases/assets/" in c[1] for c in api.calls), 4)
        self.assertFalse(any(m[0] == "DELETE" for m in api.mutations))


if __name__ == "__main__":
    unittest.main()
