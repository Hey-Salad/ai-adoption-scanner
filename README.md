# AI Agent Adoption Scanner

## What It Does
Scans restaurants in London vs California using OpenStreetMap data and checks
each business's website for AI agent signals (chatbots, AI ordering platforms, virtual assistants).

## How to Run
```bash
python3 /home/hs-chilu/.openclaw/workspace/ai-adoption-scan/scanner.py
```

## Results (Jun 25, 2026)

| Metric | London | California |
|--------|--------|------------|
| Total businesses scanned | 500 | 2,000 |
| With websites | 182 (36.4%) | 996 (49.8%) |
| Websites analyzed | 30 | 120 |
| **AI LIKELY** | **0 (0%)** | **1 (0.8%)** |
| Automated (ordering platforms) | 7 (23.3%) | 8 (6.7%) |
| Basic online only | 2 (6.7%) | 9 (7.5%) |
| No automation detected | 21 (70%) | 98 (81.7%) |
| No website at all | — | 4 (3.3%) |

## Key Finding
**AI agent adoption in restaurants is effectively 0%.** The market is wide open.
Most businesses use delivery platforms (Deliveroo/Uber Eats/DoorDash) but none
have actual AI agents handling ordering, customer service, or operations.

The only AI-positive hit was **Nation's Giant Hamburgers** (CA) using olo.com.

## Limitations
- No Google Places API key configured (uses free OpenStreetMap)
- OSM data is less complete than Google for business info
- Memory constrained on 15GB host (can't scan all regions at once)
- Website scanning limited to 30 per region to avoid rate limiting

## Next Steps
- Get Google Places API key for richer data
- Deploy to cloud for full-scale scanning
- Add more AI detection signals (OpenAI embeddings, Claude API integration)
