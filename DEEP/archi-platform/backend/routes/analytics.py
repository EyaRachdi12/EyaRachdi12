"""
GET /api/analytics — Real-time analytics dashboard data
Aggregates statistics from clients, projects, messages, and AI usage
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list:
    """Load JSON file or return empty list if not found."""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def _get_month_key(timestamp_or_date: str) -> str:
    """Convert timestamp or date string to 'YYYY-MM' format."""
    try:
        # Try parsing as timestamp
        if timestamp_or_date.isdigit():
            dt = datetime.fromtimestamp(int(timestamp_or_date))
            return dt.strftime("%Y-%m")
        # Try parsing as "Mai 2026" format
        months_fr = {
            "jan": 1, "fév": 2, "mar": 3, "avr": 4, "mai": 5, "jun": 6,
            "jul": 7, "aoû": 8, "sep": 9, "oct": 10, "nov": 11, "déc": 12
        }
        parts = timestamp_or_date.lower().split()
        if len(parts) == 2:
            month_name = parts[0][:3]
            year = parts[1]
            if month_name in months_fr:
                return f"{year}-{months_fr[month_name]:02d}"
    except:
        pass
    # Default to current month
    return datetime.now().strftime("%Y-%m")


@router.get("/analytics")
def get_analytics():
    """
    Returns comprehensive analytics data:
    - AI usage stats (plans analyzed, captions, VQA questions, sketches)
    - Monthly activity (plans, videos, new clients)
    - Model usage percentages
    - Top active projects
    """
    
    # Load all data sources
    clients = _load_json("clients_db.json")
    projects = _load_json("projects_db.json")
    
    # Count conversations and messages
    conversations = _load_json("conversations.json")
    total_messages = 0
    total_images_shared = 0
    
    for conv in conversations:
        conv_id = conv.get("id", "")
        messages_file = f"messages_{conv_id}.json"
        messages = _load_json(messages_file)
        total_messages += len(messages)
        # Count images in messages
        total_images_shared += sum(1 for m in messages if m.get("image_url"))
    
    # ── AI Stats ──────────────────────────────────────────────────────────────
    # These would ideally be tracked in a separate analytics DB
    # For now, we estimate based on available data
    
    plans_analyzed = len(projects) + total_images_shared  # Projects + shared images
    captions_generated = plans_analyzed  # Assume 1 caption per plan
    vqa_questions = total_messages // 3  # Estimate: ~1/3 of messages are questions
    sketches_generated = len([p for p in projects if p.get("plan_style")])  # Projects with style
    briefs_structured = len(projects)  # One brief per project
    videos_3d = len([p for p in projects if p.get("progress", 0) > 50])  # Advanced projects
    
    ai_stats = [
        {"label": "Plans analysés", "value": plans_analyzed, "icon": "🧠", "color": "#c9a96e"},
        {"label": "Captions générées", "value": captions_generated, "icon": "📝", "color": "#56b4d3"},
        {"label": "Vidéos 3D", "value": videos_3d, "icon": "🎬", "color": "#bb6bd9"},
        {"label": "Briefs structurés", "value": briefs_structured, "icon": "📋", "color": "#6fcf97"},
        {"label": "Questions VQA", "value": vqa_questions, "icon": "❓", "color": "#f2994a"},
        {"label": "Esquisses générées", "value": sketches_generated, "icon": "🎨", "color": "#eb5757"},
    ]
    
    # ── Monthly Activity ──────────────────────────────────────────────────────
    # Group by month
    monthly_stats = defaultdict(lambda: {"plans": 0, "videos": 0, "clients": 0})
    
    # Count projects by month
    for project in projects:
        month_key = _get_month_key(project.get("created_at", project.get("date", "")))
        monthly_stats[month_key]["plans"] += 1
        if project.get("progress", 0) > 50:
            monthly_stats[month_key]["videos"] += 1
    
    # Count clients by month
    for client in clients:
        month_key = _get_month_key(client.get("since", ""))
        monthly_stats[month_key]["clients"] += 1
    
    # Convert to sorted list (last 6 months)
    months_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    sorted_months = sorted(monthly_stats.keys(), reverse=True)[:6]
    sorted_months.reverse()  # Oldest to newest
    
    monthly_data = []
    for month_key in sorted_months:
        year, month_num = month_key.split("-")
        month_name = months_fr[int(month_num) - 1]
        stats = monthly_stats[month_key]
        monthly_data.append({
            "month": month_name,
            "plans": stats["plans"],
            "videos": stats["videos"],
            "clients": stats["clients"],
        })
    
    # If no data, provide sample data for current month
    if not monthly_data:
        current_month = months_fr[datetime.now().month - 1]
        monthly_data = [
            {"month": current_month, "plans": len(projects), "videos": videos_3d, "clients": len(clients)}
        ]
    
    # ── Model Usage ───────────────────────────────────────────────────────────
    # Calculate based on actual usage
    total_ai_calls = plans_analyzed + vqa_questions + sketches_generated + briefs_structured
    
    if total_ai_calls > 0:
        cnn_lstm_pct = min(100, int((captions_generated / total_ai_calls) * 100))
        vqa_pct = min(100, int((vqa_questions / total_ai_calls) * 100))
        stable_diff_pct = min(100, int((sketches_generated / total_ai_calls) * 100))
        llm_pct = min(100, int((briefs_structured / total_ai_calls) * 100))
        nerf_pct = min(100, int((videos_3d / total_ai_calls) * 100))
    else:
        cnn_lstm_pct = vqa_pct = stable_diff_pct = llm_pct = nerf_pct = 0
    
    model_usage = [
        {"label": "CNN + LSTM (Plans)", "pct": cnn_lstm_pct, "color": "var(--accent)"},
        {"label": "NeRF (3D)", "pct": nerf_pct, "color": "#bb6bd9"},
        {"label": "Stable Diffusion", "pct": stable_diff_pct, "color": "#56b4d3"},
        {"label": "VQA", "pct": vqa_pct, "color": "#6fcf97"},
        {"label": "LLM (Briefs)", "pct": llm_pct, "color": "#f2994a"},
    ]
    
    # ── Top Projects ──────────────────────────────────────────────────────────
    # Sort by progress (most active = highest progress)
    top_projects = sorted(
        [p for p in projects if p.get("name")],
        key=lambda p: p.get("progress", 0),
        reverse=True
    )[:3]
    
    colors = ["var(--accent)", "#56b4d3", "#6fcf97"]
    top_projects_data = []
    for i, project in enumerate(top_projects):
        # Activity score = progress + (has caption) + (has style)
        activity = project.get("progress", 0) // 5  # Scale down
        if project.get("plan_caption"):
            activity += 5
        if project.get("plan_style"):
            activity += 3
        
        top_projects_data.append({
            "name": project["name"],
            "activity": activity,
            "color": colors[i % len(colors)],
        })
    
    # If no projects, provide placeholder
    if not top_projects_data:
        top_projects_data = [
            {"name": "Aucun projet", "activity": 0, "color": "var(--accent)"}
        ]
    
    # ── Response ──────────────────────────────────────────────────────────────
    return JSONResponse(content={
        "ai_stats": ai_stats,
        "monthly_data": monthly_data,
        "model_usage": model_usage,
        "top_projects": top_projects_data,
        "summary": {
            "total_clients": len(clients),
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.get("status") == "En cours"]),
            "total_messages": total_messages,
        }
    })
