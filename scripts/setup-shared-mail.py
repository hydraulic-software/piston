#!/usr/bin/env python3
"""Administrator provisioning for authenticated shared email introductions."""
import argparse
import ast
import grp
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import subprocess


def grant_delivery_access(user, state_dir, contacts):
    # Postfix local(8) command delivery does not enable supplementary groups.
    # A normal login or sg test therefore cannot verify this access path.
    subprocess.run(["setfacl", "-m", f"u:{user.pw_uid}:rx", str(state_dir)], check=True)
    subprocess.run(["setfacl", "-m", f"u:{user.pw_uid}:rw", str(contacts)], check=True)
    subprocess.run(["setpriv", f"--reuid={user.pw_uid}", f"--regid={user.pw_gid}", "--clear-groups",
                    "--", "/usr/bin/python3", "-c",
                    "import sys; f=open(sys.argv[1], 'r+'); f.close()", str(contacts)], check=True)


def forward_content(text, contacts, introducers):
    # Only edit a single, recognized Piston delivery pipe. Keep all existing
    # authentication variables; do not replace arbitrary forwarding rules.
    pipe = ast.literal_eval(text.strip())
    if not isinstance(pipe, str) or not pipe.startswith("|env "):
        raise ValueError("not a managed env delivery pipe")
    words = shlex.split(pipe[1:])
    if not words[-1].endswith(("/piston-mail-filter", "/axiom-mail-filter")):
        raise ValueError("not a Piston filter")
    values = {}
    for item in words[1:-1]:
        name, sep, value = item.partition("=")
        if not sep or not re.fullmatch(r"[A-Z_][A-Z_0-9]*", name):
            raise ValueError("unsupported forwarding command")
        values[name] = value
    if values.get("BOT_REQUIRE_ALIGNED_DKIM") != "1" or not values.get("BOT_AUTH_RESULTS_ID"):
        raise ValueError("aligned DKIM configuration required")
    values.update(BOT_MAIL_SHARED_CONTACTS=str(contacts), BOT_MAIL_INTRODUCERS=",".join(introducers))
    return json.dumps("|" + shlex.join(["env", *[f"{k}={v}" for k, v in values.items()], words[-1]])) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", action="append", required=True)
    parser.add_argument("--introducer", action="append", required=True)
    parser.add_argument("--state-dir", type=Path, default=Path("/var/lib/piston-mail"))
    parser.add_argument("--group", default="piston-mail-contacts")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*", args.group):
        parser.error("invalid group name")
    if not args.state_dir.is_absolute() or args.state_dir == Path("/"):
        parser.error("state directory must be an absolute dedicated path")
    for address in args.introducer:
        if not re.fullmatch(r"[^\s,@]+@[^\s,@]+\.[^\s,@]+", address):
            parser.error("invalid introducer address")
    contacts = args.state_dir / "contacts"
    for path in [*args.state_dir.parents, args.state_dir, contacts]:
        if path.is_symlink():
            parser.error("shared state path must not use symlinks")
    plans = []
    for name in dict.fromkeys(args.user):
        user = pwd.getpwnam(name)
        forward = Path(user.pw_dir) / ".forward"
        if forward.is_symlink() or not forward.is_file():
            parser.error(f"{name}: expected regular managed .forward")
        content = forward_content(forward.read_text(), contacts, args.introducer)
        plans.append((user, forward, content))
    if args.dry_run:
        print(f"Would provision {contacts} and configure: " + ", ".join(args.user))
        return
    if os.geteuid() != 0:
        parser.error("run as root, or use --dry-run")
    for command in ("setfacl", "setpriv"):
        if shutil.which(command) is None:
            parser.error(f"{command} required (install acl and util-linux before provisioning)")
    try:
        group = grp.getgrnam(args.group)
    except KeyError:
        subprocess.run(["groupadd", "--system", args.group], check=True)
        group = grp.getgrnam(args.group)
    args.state_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
    os.chown(args.state_dir, 0, group.gr_gid)
    os.chmod(args.state_dir, 0o750)
    fd = os.open(contacts, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o660)
    try:
        os.fchown(fd, 0, group.gr_gid)
        os.fchmod(fd, 0o660)
    finally:
        os.close(fd)
    for user, forward, content in plans:
        subprocess.run(["usermod", "-aG", args.group, user.pw_name], check=True)
        # Verify ACL/filesystem support and actual delivery identity before
        # enabling a filter configuration that could otherwise bounce mail.
        grant_delivery_access(user, args.state_dir, contacts)
        backup = forward.with_name(".forward.before-shared-contacts")
        if not backup.exists():
            fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w") as handle:
                handle.write(forward.read_text())
        fd = os.open(forward, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.chown(forward, user.pw_uid, user.pw_gid)
        os.chmod(forward, 0o600)
    print("Shared contacts configured. Verify fresh delivery-process groups and authenticated cross-account delivery.")


if __name__ == "__main__":
    main()
