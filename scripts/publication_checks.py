"""Fail-closed source, Git identity and product archive validation."""
import hashlib
import io
import json
import re
import stat
import subprocess
import zipfile
import zlib
from pathlib import PurePosixPath

EMAIL = re.compile(rb"[A-Za-z0-9_.+%\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")


class ValidationError(ValueError):
    """Only categories and redacted object locations may enter this exception."""


def fail(category, location):
    safe = EMAIL.sub(b"[redacted]", str(location).encode("utf-8", "replace"))
    raise ValidationError(category + ": " + json.dumps(safe.decode("utf-8"), ensure_ascii=True))


def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if p.returncode:
        fail("git-read-failed", "repository")
    return p.stdout


def policy(root):
    try:
        rules = json.loads((root / "publication-policy.json").read_text(encoding="utf-8"))
        for key in ("source_files", "jar_files", "allowed_emails", "owner_names"):
            values = rules[key]
            if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values) or len(set(values)) != len(values):
                raise ValueError()
        if rules["owner_email"] not in rules["allowed_emails"]:
            raise ValueError()
        if set(rules["required_notices"]) != {"LICENSE", "NOTICE.md", "extension/LICENSE", "extension/NOTICE.md"} or any(not re.fullmatch("[0-9a-f]{64}", v) for v in rules["required_notices"].values()):
            raise ValueError()
        return rules
    except (OSError, ValueError, KeyError, TypeError):
        fail("invalid-policy", "publication-policy.json")


def check_notices(root, rules):
    for name, digest in rules["required_notices"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            fail("reviewed-notice-mismatch", name)


def check_emails(data, location, rules):
    # Compressed image pixels are not text. Inspect PNG textual metadata instead.
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        texts = []
        offset = 8
        while offset + 12 <= len(data):
            size = int.from_bytes(data[offset:offset + 4], "big")
            kind = data[offset + 4:offset + 8]
            payload = data[offset + 8:offset + 8 + size]
            if kind in (b"tEXt", b"eXIf"):
                texts.append(payload)
            elif kind in (b"zTXt", b"iTXt"):
                try:
                    keyword, rest = payload.split(b"\0", 1)
                    texts.append(keyword)
                    if kind == b"zTXt":
                        compressed, content = True, rest[1:]
                    else:
                        compressed = bool(rest[0])
                        language, translated, content = rest[2:].split(b"\0", 2)
                        texts.extend((language, translated))
                    if compressed:
                        decoder = zlib.decompressobj()
                        content = decoder.decompress(content, 1024 * 1024)
                        if not decoder.eof or decoder.unconsumed_tail:
                            fail("image-metadata-limit", location)
                    texts.append(content)
                except (ValueError, IndexError, zlib.error):
                    fail("invalid-image-metadata", location)
            offset += size + 12
        data = b"\n".join(texts)
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            data = data.decode("utf-16").encode("utf-8")
        except UnicodeError:
            fail("invalid-text-encoding", location)
    allowed = {v.lower().encode("ascii") for v in rules["allowed_emails"]}
    if any(m.group().lower() not in allowed for m in EMAIL.finditer(data)):
        fail("unapproved-email", location)


def check_identity(line, location, rules):
    match = re.fullmatch(rb"(?:author|committer|tagger) (.*) <([^<>]*)> [0-9]+ [+-][0-9]{4}", line)
    if not match:
        fail("invalid-git-identity", location)
    name, address = match.groups()
    if address.lower() not in {v.lower().encode("ascii") for v in rules["allowed_emails"]}:
        fail("unapproved-git-identity", location)
    if name.decode("utf-8", "replace").casefold() in {v.casefold() for v in rules["owner_names"]} and address != rules["owner_email"].encode("ascii"):
        fail("owner-noreply-required", location)


def validate_source(root, rules=None):
    rules = rules or policy(root)
    check_notices(root, rules)
    entries = git(root, "ls-files", "--stage", "-z").split(b"\0")
    found = set()
    for entry in filter(None, entries):
        header, name = entry.split(b"\t", 1)
        mode, _, stage = header.split()
        path = name.decode("utf-8")
        if mode not in (b"100644", b"100755") or stage != b"0":
            fail("invalid-source-entry", path)
        if path not in rules["source_files"]:
            fail("unapproved-source-file", path)
        found.add(path)
        file = root / path
        if file.is_symlink() or not file.is_file():
            fail("invalid-source-file", path)
        check_emails(file.read_bytes(), path, rules)
    if found != set(rules["source_files"]):
        fail("missing-source-file", sorted(set(rules["source_files"]) - found)[0])


def validate_history(root, rules=None):
    rules = rules or policy(root)
    if git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
        fail("incomplete-history", "repository")
    objects = {}
    for line in git(root, "rev-list", "--objects", "--all", "HEAD").splitlines():
        sha, _, path = line.partition(b" ")
        objects[sha] = path.decode("utf-8", "replace")
    for sha in git(root, "for-each-ref", "--format=%(objectname)", "refs/tags").splitlines():
        objects.setdefault(sha, "tag")
    process = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"], input=b"\n".join(objects) + b"\n", capture_output=True)
    if process.returncode:
        fail("git-read-failed", "repository")
    stream = io.BytesIO(process.stdout)
    for sha, path in objects.items():
        header = stream.readline().split()
        if len(header) != 3 or header[0] != sha:
            fail("git-object-read-failed", sha.decode())
        kind, size = header[1], int(header[2])
        data = stream.read(size)
        if len(data) != size or stream.read(1) != b"\n":
            fail("git-object-read-failed", sha.decode())
        if kind not in (b"commit", b"tag", b"blob"):
            continue
        location = sha.decode() + (" " + path if path else "")
        if kind in (b"commit", b"tag"):
            for line in data.split(b"\n\n", 1)[0].splitlines():
                if line.startswith((b"author ", b"committer ", b"tagger ")):
                    check_identity(line, location, rules)
        check_emails(data, location, rules)


def archive(data, expected, location, rules):
    result = {}
    seen = set()
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for entry in z.infolist():
                name = entry.orig_filename
                path = PurePosixPath(name)
                canonical = str(path) + ("/" if name.endswith("/") else "")
                if not name or name in seen or name != canonical or path.is_absolute() or ".." in path.parts or any(c in name for c in ("\\", ":", "\0")):
                    fail("invalid-archive-path", location)
                seen.add(name)
                mode = entry.external_attr >> 16
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                    fail("invalid-archive-file-type", location + "/" + name)
                if entry.is_dir():
                    if entry.file_size or not any(n.startswith(name) for n in expected):
                        fail("unexpected-archive-directory", location + "/" + name)
                    z.read(entry)
                    continue
                if stat.S_ISDIR(mode) or name not in expected:
                    fail("unapproved-archive-file", location + "/" + name)
                total += entry.file_size
                if entry.file_size > 64 * 1024 * 1024 or total > 256 * 1024 * 1024:
                    fail("archive-size-limit", location)
                result[name] = z.read(entry)
                if not name.endswith(".jar"):
                    check_emails(result[name], location + "/" + name, rules)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error, OSError):
        fail("corrupt-archive", location)
    if set(result) != set(expected):
        fail("missing-archive-file", location)
    return result


def validate_release(root, dist, version):
    if not VERSION.fullmatch(version):
        fail("invalid-version", "release/RELEASE")
    rules = policy(root)
    check_notices(root, rules)
    extname = f"klb-chrome-extension-v{version}.zip"
    jarname = f"klb-logbook-plugin-v{version}.jar"
    fullname = f"klb-v{version}.zip"
    sumsname = f"SHA256SUMS-v{version}.txt"
    names = (extname, jarname, fullname, sumsname)
    if {p.name for p in dist.iterdir()} != set(names) or any(not (dist / n).is_file() or (dist / n).is_symlink() for n in names):
        fail("unexpected-distribution-files", "dist")
    blobs = {n: (dist / n).read_bytes() for n in names}
    extpaths = {p.removeprefix("extension/") for p in rules["source_files"] if p.startswith("extension/")}
    docs = {p for p in rules["source_files"] if p.startswith("docs/")}
    prefix = f"klb-v{version}/"
    rootpaths = {"README.md", "LICENSE", "NOTICE.md", "RELEASE_NOTES.md"}
    fullpaths = rootpaths | docs | {"extension/" + n for n in extpaths} | {"plugin/" + jarname, "plugin/install.sh", "plugin/disable.sh"}
    ext = archive(blobs[extname], extpaths, extname, rules)
    jar = archive(blobs[jarname], set(rules["jar_files"]), jarname, rules)
    full = archive(blobs[fullname], {prefix + n for n in fullpaths}, fullname, rules)
    for name in ("LICENSE", "NOTICE.md"):
        canonical = (root / name).read_bytes()
        if not canonical.strip() or any(b != canonical for b in (ext[name], jar["META-INF/" + name], full[prefix + name])):
            fail("license-or-notice-mismatch", name)
    for name, data in ext.items():
        if full[prefix + "extension/" + name] != data or (root / "extension" / name).read_bytes() != data:
            fail("extension-content-mismatch", name)
    for name in docs | rootpaths:
        source = root / (f"release/v{version}/RELEASE_NOTES.md" if name == "RELEASE_NOTES.md" else name)
        if full[prefix + name] != source.read_bytes():
            fail("source-content-mismatch", name)
    if full[prefix + "plugin/" + jarname] != blobs[jarname]:
        fail("nested-jar-mismatch", jarname)
    try:
        if json.loads(ext["manifest.json"])["version"] != version:
            fail("extension-version-mismatch", "manifest.json")
        if f"Implementation-Version: {version}".encode() not in jar["META-INF/MANIFEST.MF"].splitlines():
            fail("plugin-version-mismatch", "META-INF/MANIFEST.MF")
        sums = {}
        for line in blobs[sumsname].decode("ascii").splitlines():
            digest, name = line.split("  ")
            if name in sums or name not in names[:3] or digest != hashlib.sha256(blobs[name]).hexdigest():
                fail("invalid-checksum", sumsname)
            sums[name] = digest
        if set(sums) != set(names[:3]):
            fail("incomplete-checksums", sumsname)
    except (UnicodeError, ValueError, KeyError):
        fail("invalid-package-metadata", "dist")
    check_emails(blobs[sumsname], sumsname, rules)
    return names
