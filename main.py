#!/usr/bin/env python3
"""
Rank your GitHub repositories by clones (last 14 days) or by stars.

Usage:
  - Export a token: export GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXX
  - Run (clones, requires token with repo access to those repos):
      python main.py --owner myridia --by clones --csv clones.csv
  - Run (stars, public info only):
      python main.py --owner myridia --by stars --csv stars.csv
"""

import os
import sys
import time
import argparse
import requests
import csv

API_BASE = "https://api.github.com"
PER_PAGE = 100


def github_session(token):
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github+json"})
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s


def list_repos_public(session, owner):
    repos = []
    page = 1
    while True:
        url = f"{API_BASE}/users/{owner}/repos"
        resp = session.get(url, params={"per_page": PER_PAGE, "page": page})
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def list_repos_authenticated(session, owner):
    # List repos accessible to the token, then filter by owner
    repos = []
    page = 1
    while True:
        resp = session.get(
            f"{API_BASE}/user/repos", params={"per_page": PER_PAGE, "page": page}
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend([r for r in data if r.get("owner", {}).get("login") == owner])
        page += 1
    return repos


def get_clones(session, owner, repo):
    url = f"{API_BASE}/repos/{owner}/{repo}/traffic/clones"
    resp = session.get(url)
    if resp.status_code == 204:
        return {"count": 0, "uniques": 0, "clones": []}
    if resp.status_code == 403:
        raise PermissionError(
            "403 Forbidden: token lacks permission to read traffic for this repo."
        )
    if resp.status_code == 404:
        raise FileNotFoundError(
            "404 Not Found: traffic endpoint not available or repo not accessible."
        )
    resp.raise_for_status()
    return resp.json()


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--owner", required=True, help="GitHub username or org (e.g. myridia)"
    )
    p.add_argument(
        "--by",
        choices=["clones", "stars"],
        default="clones",
        help="Rank by clones (requires owner token) or by stars (public)",
    )
    p.add_argument("--csv", help="Write CSV output")
    p.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Sleep between API calls to avoid rate bursts",
    )
    args = p.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    session = github_session(token)

    # Decide listing method
    repos = []
    try:
        if token:
            repos = list_repos_authenticated(session, args.owner)
            if not repos:
                # fallback to public list if token had no matching owner-accessible repos
                repos = list_repos_public(session, args.owner)
        else:
            repos = list_repos_public(session, args.owner)
    except requests.HTTPError as e:
        print("Failed to list repositories:", e, file=sys.stderr)
        sys.exit(1)

    if not repos:
        print("No repositories found for owner", args.owner)
        sys.exit(0)

    results = []
    if args.by == "stars":
        for r in repos:
            results.append(
                {
                    "name": r["name"],
                    "value": r.get("stargazers_count", 0),
                    "extra": {"stars": r.get("stargazers_count", 0)},
                }
            )
    else:  # clones
        for r in repos:
            name = r["name"]
            try:
                clones = get_clones(session, args.owner, name)
                count = clones.get("count", 0)
                uniques = clones.get("uniques", 0)
                results.append(
                    {
                        "name": name,
                        "value": count,
                        "extra": {"clones_count": count, "clones_uniques": uniques},
                    }
                )
            except PermissionError as pe:
                print(f"Skipping {name}: {pe}", file=sys.stderr)
            except FileNotFoundError as fe:
                print(f"Skipping {name}: {fe}", file=sys.stderr)
            except requests.HTTPError as he:
                print(f"Skipping {name}: HTTP error {he}", file=sys.stderr)
            time.sleep(args.sleep)

    results.sort(key=lambda x: x["value"], reverse=True)

    # Print to stdout
    print(f"Ranking {len(results)} repos for {args.owner} by {args.by}:")
    for r in results:
        if args.by == "stars":
            print(f"{r['value']:6d} stars  {r['name']}")
        else:
            print(
                f"{r['extra']['clones_count']:6d} clones  {r['extra']['clones_uniques']:6d} uniques  {r['name']}"
            )

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            fieldnames = ["name", "value", "extra"]
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(
                    {"name": r["name"], "value": r["value"], "extra": str(r["extra"])}
                )
        print("Wrote CSV to", args.csv)


if __name__ == "__main__":
    main()
