#!/usr/bin/env python3
"""
AI Agent Adoption Scanner — Restaurants
Scans London vs California for food businesses and estimates AI agent adoption.
Uses OpenStreetMap Overpass API (free, no key needed).
"""

import requests
import json
import time
import sys
import re
from urllib.parse import urlparse
from collections import defaultdict

OVERBOSS = "https://overpass-api.de/api/interpreter"
USER_AGENT = "HeySalad-Scanner/1.0"

# ─── London: bounding box covers Greater London ───
LONDON_BBOX = {
    "name": "London & Greater London",
    "bbox": [51.28, -0.52, 51.69, 0.35],
}

# ─── California: split into regions to avoid timeout ───
CA_REGIONS = [
    {"name": "Bay Area",           "bbox": [37.2, -122.6, 37.9, -121.8]},
    {"name": "Los Angeles",        "bbox": [33.7, -118.7, 34.3, -117.9]},
    {"name": "San Diego",          "bbox": [32.5, -117.3, 33.1, -116.8]},
    {"name": "Sacramento + Valley","bbox": [38.0, -121.6, 38.7, -120.5]},
    {"name": "Orange County",      "bbox": [33.5, -118.1, 33.9, -117.5]},
    {"name": "Inland Empire",      "bbox": [33.8, -117.7, 34.3, -116.8]},
]

# Delivery/ordering platforms that most restaurants use — NOT AI-specific
COMMON_PLATFORMS = {
    "deliveroo.co.uk", "just-eat.co.uk", "ubereats.com", "doordash.com",
    "grubhub.com", "opentable.com", "resy.com", "sevenrooms.com",
    "square.site", "squareup.com", "toasttab.com", "chownow.com",
}

# True AI-first platforms — these are actual AI agent products
AI_PLATFORMS = {
    "kea.ai", "conversenow.ai", "valyant.ai", "presto.com",
    "soundhound.com", "olo.com", "checkmate.com", "slerp.com",
    "flipdish.com", "orders.co", "sundayapp.com", "tockhq.com",
    "hangry.ai", "orderai.com", "bitesauce.com",
}

def query_overpass(bbox, limit=200):
    """Query Overpass for restaurants in a bounding box."""
    s, w, n, e = bbox["bbox"]
    query = f"""[out:json][timeout:25];
(
  node["amenity"~"restaurant|cafe|fast_food"]({s},{w},{n},{e});
);
out center {limit};"""
    try:
        r = requests.post(OVERBOSS,
            data={"data": query},
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=30)
        r.raise_for_status()
        return r.json().get("elements", [])
    except Exception as e:
        print(f"     ⚠️  Query failed: {e}")
        return []

def extract_website(elem):
    tags = elem.get("tags", {})
    for key in ["website", "contact:website", "url"]:
        val = tags.get(key, "").strip()
        if val and val.startswith("http"):
            return val
    return None

def check_website_ai(website_url):
    """Fetch a website and check for AI/automation signals."""
    try:
        r = requests.get(website_url, timeout=5, headers={
            "User-Agent": USER_AGENT, "Accept": "text/html"
        })
        text = r.text.lower()
        found_platforms = []
        found_ai = []
        
        for plat in COMMON_PLATFORMS:
            if plat in text:
                found_platforms.append(plat)
        
        for ai in AI_PLATFORMS:
            if ai in text:
                found_ai.append(ai)
        
        # Also check for AI-related text signals
        ai_text_signals = []
        for phrase in ["chatbot", "ai ordering", "virtual assistant", "automated order",
                        "voice ordering", "ai agent", "ai chat", "ai-powered"]:
            if phrase in text:
                ai_text_signals.append(phrase)
        
        return {
            "platforms": found_platforms,
            "ai_platforms": found_ai,
            "ai_text": ai_text_signals,
        }
    except:
        return None

def classify(signals):
    """Classify AI likelihood from signals."""
    if signals is None:
        return {"level": "no website", "score": 0}
    
    ai_count = len(signals.get("ai_platforms", [])) + len(signals.get("ai_text", []))
    plat_count = len(signals.get("platforms", []))
    
    if ai_count >= 1:
        return {"level": "AI LIKELY", "score": 3}
    elif plat_count >= 2:
        return {"level": "automated", "score": 2}
    elif plat_count == 1:
        return {"level": "basic online", "score": 1}
    else:
        return {"level": "no automation", "score": 0}

def scan_region(bbox_config, sample_limit=30):
    """Scan a region."""
    print(f"\n  📍 {bbox_config['name']}...", flush=True)
    elements = query_overpass(bbox_config, limit=200)
    total = len(elements)
    if total == 0:
        return {"total": 0, "classified": [], "stats": {}}
    
    # Get businesses with websites
    with_www = []
    all_biz = []
    for elem in elements:
        tags = elem.get("tags", {})
        name = tags.get("name", "Unnamed")
        ttype = tags.get("amenity", "unknown")
        website = extract_website(elem)
        all_biz.append({"name": name, "type": ttype, "website": website})
        if website:
            with_www.append((name, ttype, website))
    
    www_count = len(with_www)
    sample = with_www[:sample_limit]
    
    print(f"     {total} businesses | {www_count} with websites | analyzing {len(sample)}...")
    
    results = []
    for i, (name, ttype, url) in enumerate(sample):
        signals = check_website_ai(url)
        cls = classify(signals)
        results.append({
            "name": name, "type": ttype, "website": url,
            "signals": signals, "level": cls["level"], "score": cls["score"]
        })
        time.sleep(0.25)
    
    stats = defaultdict(int)
    for r in results:
        stats[r["level"]] += 1
    
    return {
        "total": total,
        "www_count": www_count,
        "sampled": len(results),
        "classified": results,
        "stats": dict(stats),
    }

def main():
    print("╔══════════════════════════════════════════╗")
    print("║   HeySalad AI Agent Adoption Scanner     ║")
    print("║   Food & Restaurants — London vs CA      ║")
    print("╚══════════════════════════════════════════╝")
    
    # London
    print("\n🔍 LONDON")
    london = scan_region(LONDON_BBOX)
    
    # California (multi-region)
    print("\n🔍 CALIFORNIA")
    ca_combined = {"total": 0, "www_count": 0, "sampled": 0, "classified": [], "stats": defaultdict(int)}
    for region in CA_REGIONS:
        result = scan_region(region)
        ca_combined["total"] += result["total"]
        ca_combined["www_count"] += result.get("www_count", 0)
        ca_combined["sampled"] += result.get("sampled", 0)
        ca_combined["classified"].extend(result.get("classified", []))
        for k, v in result.get("stats", {}).items():
            ca_combined["stats"][k] += v
    
    # Print comparison
    print("\n\n" + "=" * 60)
    print("📊  AI AGENT ADOPTION COMPARISON")
    print("=" * 60)
    
    for label, data in [("London & Greater London", london), ("California (6 regions)", ca_combined)]:
        print(f"\n📍 {label}")
        print(f"   Total food businesses:  {data['total']:,}")
        if data["total"]:
            www_pct = round(data.get("www_count", 0) / data["total"] * 100, 1)
        else:
            www_pct = 0
        print(f"   With websites:          {data.get('www_count', 0):,} ({www_pct}%)")
        print(f"   Websites analyzed:      {data['sampled']}")
        if data["sampled"]:
            print(f"   AI adoption breakdown:")
            for level in ["AI LIKELY", "automated", "basic online", "no automation", "no website"]:
                count = data["stats"].get(level, 0)
                pct = round(count / data["sampled"] * 100, 1)
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"      {level:15s} {bar} {count:3d} ({pct}%)")
            ai_pct = round(data["stats"].get("AI LIKELY", 0) / data["sampled"] * 100, 1)
            auto_pct = round(
                (data["stats"].get("AI LIKELY", 0) + data["stats"].get("automated", 0)) 
                / data["sampled"] * 100, 1
            )
            print(f"   Est. AI-active:         {ai_pct}%")
            print(f"   Est. AI+automated:      {auto_pct}%")
    
    # Top AI businesses
    print("\n\n" + "=" * 60)
    print("🔝  TOP AI-LIKELY BUSINESSES")
    print("=" * 60)
    
    for label, data in [("London", london), ("California", ca_combined)]:
        ai_biz = [b for b in data.get("classified", []) if b["level"] == "AI LIKELY"]
        ai_biz.sort(key=lambda x: x["score"], reverse=True)
        print(f"\n📍 {label}:")
        for b in ai_biz[:8]:
            ai_names = b.get("signals", {}).get("ai_platforms", []) if b.get("signals") else []
            ai_text = b.get("signals", {}).get("ai_text", []) if b.get("signals") else []
            sig_desc = ", ".join(ai_names + ai_text)
            print(f"   ✅ {b['name']} ({b['type']})")
            print(f"      {sig_desc}")
            print(f"      {b['website']}")
    
    # Save report
    report = {
        "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "london": {
            "total": london["total"],
            "www_count": london.get("www_count", 0),
            "stats": dict(london.get("stats", {})),
        },
        "california": {
            "total": ca_combined["total"],
            "www_count": ca_combined.get("www_count", 0),
            "stats": dict(ca_combined.get("stats", {})),
        },
        "top_ai_london": [
            {"name": b["name"], "type": b["type"], 
             "signals": b.get("signals", {}), "website": b["website"]}
            for b in london.get("classified", []) if b["level"] == "AI LIKELY"
        ][:20],
        "top_ai_california": [
            {"name": b["name"], "type": b["type"],
             "signals": b.get("signals", {}), "website": b["website"]}
            for b in ca_combined.get("classified", []) if b["level"] == "AI LIKELY"
        ][:20],
    }
    
    import os
    os.makedirs("/home/hs-chilu/.openclaw/workspace/ai-adoption-scan", exist_ok=True)
    with open("/home/hs-chilu/.openclaw/workspace/ai-adoption-scan/report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n\n💾 Full report: /home/hs-chilu/.openclaw/workspace/ai-adoption-scan/report.json")

if __name__ == "__main__":
    main()
