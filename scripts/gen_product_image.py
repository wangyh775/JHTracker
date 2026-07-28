import urllib.request, json, base64, os, sys

API_KEY = "123456"
CPA_URL = "http://localhost:8317/v1/chat/completions"

PROMPT = """Generate a professional Chinese-style product diagram for "JHTracker — AI-Powered Job Hunt Tracker" (求职全流程管理). The diagram should be a clean, modern infographic / product architecture diagram, NOT a UI screenshot.

Style: Clean flat design, white/light background, blue/teal primary color palette, Chinese text labels.

Label the following major modules in Chinese:
1. 公司库管理 (Company Database) — 500+ companies, multi-dimensional filtering
2. AI 匹配度评分 (AI Scoring) — 0-100 score for each company
3. 投递全流程跟踪 (Application Tracking) — pipeline status
4. 数据看板 (Dashboard) — funnel, charts, stats
5. 简历版本管理 (Resume Management) — upload, preview, versions
6. Offer 对比 (Offer Comparison) — side-by-side comparison
7. 面试复习 (Interview Prep) — built-in study materials
8. 备份恢复 (Backup & Restore) — SQLite export/import

At the bottom show a "100% 本地 / 零云依赖" badge.

Use a clean grid layout with icon-like boxes. Text must be in Chinese. Make it look like a professional product landing page hero image."""

req = urllib.request.Request(CPA_URL)
req.add_header("Content-Type", "application/json")
req.add_header("Authorization", f"Bearer {API_KEY}")
req.data = json.dumps({
    "model": "gemini-3.1-flash-image",
    "stream": False,
    "messages": [{"role": "user", "content": [{"type": "text", "text": PROMPT}]}]
}).encode()

print("Calling Gemini image generation...")
sys.stdout.flush()

try:
    with urllib.request.urlopen(req, timeout=120) as r:
        result = json.loads(r.read().decode())
        img_url = result["choices"][0]["message"]["images"][0]["image_url"]["url"]
        raw = base64.b64decode(img_url.split(",", 1)[1])
        out_path = "D:/DJTU/HermesWorkspace/career-tracker/docs/product-diagram.png"
        with open(out_path, "wb") as f:
            f.write(raw)
        print(f"✅ Image saved to {out_path} ({len(raw)} bytes)")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)