#!/usr/bin/env python3

import argparse
import getpass
import hashlib
import json
import os
import sys
import time

import requests

API = "https://jjjm03299-wq.github.io/solid-potato/api/get-ram/"

APP_DIR = os.path.join(os.path.expanduser("~"), ".ram-tool")
AUTH_FILE = os.path.join(APP_DIR, "auth.json")
SESSION_FILE = os.path.join(APP_DIR, "session.json")

SESSION_TIMEOUT = 180  # 3 minutes


def ensure_dir():
    os.makedirs(APP_DIR, exist_ok=True)


def sha256(pin):
    return hashlib.sha256(pin.encode()).hexdigest()


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def load(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def register():
    if os.path.exists(AUTH_FILE):
        print("PIN already registered.")
        return

    pin1 = getpass.getpass("Enter new PIN: ")
    pin2 = getpass.getpass("Confirm new PIN: ")

    if pin1 != pin2:
        print("PINs do not match.")
        sys.exit(1)

    save(AUTH_FILE, {"hash": sha256(pin1)})
    print("PIN registered successfully.")


def login():
    auth = load(AUTH_FILE)

    if auth is None:
        print("No PIN registered.")
        return

    pin = getpass.getpass("Enter PIN: ")

    if sha256(pin) != auth["hash"]:
        print("Invalid PIN.")
        sys.exit(1)

    save(SESSION_FILE, {
        "expires": time.time() + SESSION_TIMEOUT
    })

    print("Login successful.")


def logout():
    auth = load(AUTH_FILE)

    if auth is None:
        print("No PIN registered.")
        return

    pin = getpass.getpass("Enter PIN: ")

    if sha256(pin) != auth["hash"]:
        print("Invalid PIN.")
        sys.exit(1)

    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

    print("Logged out successfully.")


def authenticated():
    session = load(SESSION_FILE)

    if session is None:
        print("❌ Access Denied: PIN session expired or locked.")
        print("Please authenticate using 'ram-tool auth login' first.")
        return False

    if time.time() > session["expires"]:
        os.remove(SESSION_FILE)

        print("❌ Access Denied: PIN session expired or locked.")
        print("Please authenticate using 'ram-tool auth login' first.")
        return False

    return True


def status():
    if authenticated():
        remaining = int(load(SESSION_FILE)["expires"] - time.time())
        print("Authenticated")
        print(f"Session expires in {remaining} seconds.")


def get_ram():
    if not authenticated():
        return

    try:
        r = requests.get(API, timeout=10)
        r.raise_for_status()

        data = r.json()

        print(f"RAM: {data['ram_mb']} MB")

    except Exception as e:
        print("API error:", e)
        sys.exit(1)


def version():
    print("ram-tool 1.0.0")


def main():

    ensure_dir()

    parser = argparse.ArgumentParser(
        prog="ram-tool",
        description="Fetch RAM value from API"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("get", help="Fetch RAM from API")
    sub.add_parser("version", help="Show version")

    auth = sub.add_parser("auth", help="Authentication")

    auth_sub = auth.add_subparsers(dest="action")

    auth_sub.add_parser("register")
    auth_sub.add_parser("login")
    auth_sub.add_parser("logout")
    auth_sub.add_parser("status")

    args = parser.parse_args()

    if args.command == "get":
        get_ram()

    elif args.command == "version":
        version()

    elif args.command == "auth":

        if args.action == "register":
            register()

        elif args.action == "login":
            login()

        elif args.action == "logout":
            logout()

        elif args.action == "status":
            status()

        else:
            auth.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
