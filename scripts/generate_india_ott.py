#!/usr/bin/env python3
"""India OTT subscribed calendar: confirmed dates and minimal factual metadata only."""
import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import json
import logging
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

SOURCE = "https://cinebuds.com/ott-release-dates/"
TZ = "America/Phoenix"
AGENT = "IndiaOTTCalendar/1.0 (personal release-date calendar)"
MONTHS = {v.lower(): i for i, v in enumerate(
    ("January","February","March","April","May","June","July","August","September","October","November","December"),1)}
MONTHS.update({k[:3]:v for k,v in list(MONTHS.items())})
DATE = re.compile(r"\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)(?:\s+(20\d{2}))?\b", re.I)

@dataclass(frozen=True)
class Release:
    title: str
    day: date
    language: str
    platform: str
    url: str = SOURCE

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = 0
        self.rows = []
        self.row = None
        self.cell = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.tables += 1
        elif tag == "tr" and self.tables:
            self.row = []
        elif tag in ("td","th") and self.row is not None:
            self.cell = {"parts":[], "links":[], "attrs":a}
        elif tag == "a" and self.cell is not None and a.get("href"):
            self.cell["links"].append(urljoin(SOURCE,a["href"]))
        elif tag == "time" and self.cell is not None and a.get("datetime"):
            self.cell["datetime"] = a["datetime"]
    def handle_data(self, data):
        if self.cell is not None:
            self.cell["parts"].append(data)
    def handle_endtag(self, tag):
        if tag in ("td","th") and self.cell is not None and self.row is not None:
            self.cell["text"] = " ".join(" ".join(self.cell["parts"]).split())
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None
        elif tag == "table":
            self.tables = max(0,self.tables-1)

def get_day(value, today, datetime_attr=None):
    if datetime_attr:
        try: return date.fromisoformat(datetime_attr[:10])
        except ValueError: pass
    m = DATE.search(value)
    if not m: return None
    day, month = int(m[1]), MONTHS[m[2].lower()]
    years = [int(m[3])] if m[3] else range(today.year-1,today.year+3)
    options = []
    for y in years:
        try: d = date(y,month,day)
        except ValueError: continue
        days = (d-today).days
        if -45 <= days <= 430: options.append((abs(days),d))
    return min(options)[1] if options else None

def safe_link(value):
    u = urlsplit(value)
    return value if u.scheme in ("http","https") and u.hostname in ("cinebuds.com","www.cinebuds.com") else SOURCE

def uid(r):
    token = (r.title.casefold().strip()+"|"+r.platform.casefold().strip()).encode("utf-8")
    return "ott-"+hashlib.sha256(token).hexdigest()[:24]+"@vihari23.github.io"

def parse(document, today):
    p = Rows()
    p.feed(document)
    found = {}
    for cells in p.rows:
        if len(cells) < 4: continue
        d,t,l,platform = cells[:4]
        label = d["text"].lower()
        if "expected" in label or "unconfirmed" in label or "tentative" in label: continue
        if not re.search(r"\b(confirmed|released|out today)\b",label): continue
        when = get_day(d["text"],today,d.get("datetime") or d["attrs"].get("data-date"))
        if not when: continue
        title, language, service = t["text"].strip(),l["text"].strip(),platform["text"].strip()
        if not title or not language or not service or len(title)>160 or len(service)>120: continue
        link = next((safe_link(x) for x in t["links"] if safe_link(x)!=SOURCE),SOURCE)
        r = Release(title,when,language,service,link)
        if uid(r) not in found or (found[uid(r)].url == SOURCE and link != SOURCE):
            found[uid(r)] = r
    return sorted(found.values(),key=lambda x:(x.day,x.platform.casefold(),x.title.casefold()))

def escape(value):
    return value.replace("\\","\\\\").replace("\r\n","\n").replace("\r","\n").replace("\n","\\n").replace(",","\\,").replace(";","\\;")

def fold(line):
    out, part, octets = [],"",0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if n+octets>75:
            out.append(part)
            part, octets = " "+ch,n+1
        else:
            part, octets = part+ch,octets+n
    out.append(part)
    return "\r\n".join(out)

def render(items):
    if not items: raise ValueError("Never publish an empty calendar")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Personal India OTT Releases//EN",
        "CALSCALE:GREGORIAN","METHOD:PUBLISH","X-WR-CALNAME:India OTT Releases",
        "X-WR-TIMEZONE:"+TZ,"REFRESH-INTERVAL;VALUE=DURATION:P1D","X-PUBLISHED-TTL:PT24H",
        "BEGIN:VTIMEZONE","TZID:"+TZ,"BEGIN:STANDARD","DTSTART:19700101T000000",
        "TZOFFSETFROM:-0700","TZOFFSETTO:-0700","TZNAME:MST","END:STANDARD","END:VTIMEZONE"]
    for r in items:
        ymd = r.day.strftime("%Y%m%d")
        primary = r.language.split(" Also in ",1)[0]
        detail = (f"India OTT release date: {r.day.isoformat()}\nPlatform: {r.platform}\n"
                  f"Languages: {r.language}\nSource: {r.url}\n"
                  "Time 8:00–9:00 AM Phoenix is a display slot, NOT a streaming launch time. "
                  "Dates and availability can change; check the platform.")
        lines += ["BEGIN:VEVENT","UID:"+uid(r),"DTSTAMP:"+stamp,
            f"DTSTART;TZID={TZ}:{ymd}T080000",f"DTEND;TZID={TZ}:{ymd}T090000",
            "SUMMARY:"+escape(f"OTT: {r.title} — {r.platform} ({primary})"),
            "DESCRIPTION:"+escape(detail),"URL:"+r.url,
            "STATUS:CONFIRMED","TRANSP:TRANSPARENT","CATEGORIES:OTT,ENTERTAINMENT","END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(map(fold,lines))+"\r\n"

def snapshot(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Release(x["title"],date.fromisoformat(x["date"]),x["language"],x["platform"],
                    safe_link(x.get("url",SOURCE))) for x in data]

def fetch():
    robots = RobotFileParser()
    robots.set_url("https://cinebuds.com/robots.txt")
    robots.read()
    if robots.disallow_all or not robots.can_fetch(AGENT,SOURCE):
        raise RuntimeError("Robots rules disallow fetching Cinebuds")
    req = Request(SOURCE,headers={"User-Agent":AGENT,"Accept":"text/html"})
    with urlopen(req,timeout=25) as response:
        raw = response.read(3000001)
        if len(raw)>3000000: raise ValueError("Page exceeds safe fetch limit")
        return raw.decode("utf-8",errors="replace")

def build(now,source_path,destination):
    status = "Live"
    try:
        page = fetch()
        if "ott" not in page.lower(): raise ValueError("Unexpected source content")
        releases = parse(page,now)
        if len(releases)<3: raise ValueError(f"Extracted only {len(releases)} confirmed rows")
    except Exception as exc:
        status = "Seed snapshot; live updates unavailable"
        logging.warning("Live source unavailable (%s); using 2026-11-13 reviewed facts",exc)
        releases = snapshot(source_path)
    # If the source is down for a prolonged period, preserve the calendar URL,
    # but never invent future events.
    active = [x for x in releases if now-timedelta(days=30) <= x.day <= now+timedelta(days=430)]
    if not active:
        active = releases if status != "Live" else []
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(render(active).encode("utf-8"))
    print(f"India OTT: {len(active)} events; source status: {status}; output: {destination}")
    return status

if __name__ == "__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--seed",type=Path,default=Path("data/india-ott-seed.json"))
    cli.add_argument("--output",type=Path,default=Path("_site/india-ott.ics"))
    cli.add_argument("--date",type=date.fromisoformat,default=datetime.now(timezone.utc).date())
    args=cli.parse_args()
    try: build(args.date,args.seed,args.output)
    except Exception as exc:
        logging.error("Could not publish OTT: %s",exc)
        sys.exit(1)
