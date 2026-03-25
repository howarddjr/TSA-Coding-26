"""
STEM Career Path Explorer
Flask application for middle/high school students exploring STEM careers.

Recommendation Logic:
  - Each career has interest tags and skill tags.
  - User provides selected interests (checkboxes) and strengths (checkboxes).
  - Score = (1.0 × interest_tag_matches) + (1.5 × strength_tag_matches) + 0.5 bonus if career is HS-appropriate.
  - Normalized to 0–100. Ties broken by total matching technical skill count.
  - Logic is transparent, deterministic, and simple.
"""

import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stem-explorer-dev-secret-2024")

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "careers.json")

# ── Strength → interest-tag mapping (used in scoring)
STRENGTH_TAG_MAP = {
    "analytical thinking": ["math", "data", "research", "problem-solving"],
    "creativity":          ["design", "building", "robotics"],
    "teamwork":            ["communication", "leadership"],
    "communication":       ["communication", "leadership"],
    "perseverance":        ["research", "security", "biology"],
    "attention to detail": ["security", "data", "research", "biology"],
    "curiosity":           ["research", "biology", "data", "environment"],
    "ethics":              ["security", "biology", "environment"],
}

INTEREST_OPTIONS = [
    ("coding",         "Coding",          "fa-solid fa-code"),
    ("math",           "Math",            "fa-solid fa-square-root-variable"),
    ("biology",        "Biology",         "fa-solid fa-microscope"),
    ("building",       "Building Things", "fa-solid fa-hammer"),
    ("environment",    "Environment",     "fa-solid fa-leaf"),
    ("security",       "Security",        "fa-solid fa-shield-halved"),
    ("robotics",       "Robotics",        "fa-solid fa-robot"),
    ("data",           "Data",            "fa-solid fa-chart-bar"),
    ("design",         "Design",          "fa-solid fa-pen-ruler"),
    ("communication",  "Communication",   "fa-solid fa-comments"),
    ("leadership",     "Leadership",      "fa-solid fa-users"),
    ("research",       "Research",        "fa-solid fa-flask"),
    ("problem-solving","Problem Solving",  "fa-solid fa-lightbulb"),
]

STRENGTH_OPTIONS = [
    ("analytical thinking", "Analytical Thinking", "fa-solid fa-brain"),
    ("creativity",          "Creativity",          "fa-solid fa-palette"),
    ("teamwork",            "Teamwork",            "fa-solid fa-handshake"),
    ("communication",       "Communication",       "fa-solid fa-comment-dots"),
    ("perseverance",        "Perseverance",        "fa-solid fa-fire"),
    ("attention to detail", "Attention to Detail", "fa-solid fa-magnifying-glass"),
    ("curiosity",           "Curiosity",           "fa-solid fa-star"),
    ("ethics",              "Ethics",              "fa-solid fa-scale-balanced"),
]

WORK_STYLE_TAG_MAP = {
    "hands-on": ["building", "robotics", "design"],
    "research": ["research", "data", "biology", "environment"],
    "creative": ["design", "coding", "problem-solving"],
    "team": ["communication", "leadership", "project-management"],
    "independent": ["coding", "data", "research"],
}

CHALLENGE_TYPE_TAG_MAP = {
    "design": ["design", "engineering", "building"],
    "data": ["data", "math", "analytics"],
    "sustainability": ["environment", "biology", "materials"],
    "health": ["biology", "biomedical", "data"],
    "systems": ["communications", "network", "security", "engineering"],
}


def load_careers():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def compute_scores(careers, interests, strengths, work_style=None, challenge_types=None):
    """
    Returns list of (career, score_0_to_100) sorted descending.
    Weighted scoring from multiple quiz dimensions:
      - 1.0×interest tag matches
      - 1.5×strength-inferred tag matches
      - 1.2×work-style tag matches
      - 1.3×challenge-type tag matches
    Normalized to 0-100.
    """
    if work_style is None:
        work_style = []
    if challenge_types is None:
        challenge_types = []
    strength_interests = set()
    for s in strengths:
        for tag in STRENGTH_TAG_MAP.get(s, []):
            strength_interests.add(tag)

    work_interests = set()
    for w in work_style:
        for tag in WORK_STYLE_TAG_MAP.get(w, []):
            work_interests.add(tag)

    challenge_interests = set()
    for ch in challenge_types:
        for tag in CHALLENGE_TYPE_TAG_MAP.get(ch, []):
            challenge_interests.add(tag)

    user_interests = set(interests)

    scored = []
    for c in careers:
        tags = set(c.get("tags", []))
        interest_matches = len(tags & user_interests)
        strength_matches = len(tags & strength_interests)
        work_matches = len(tags & work_interests)
        challenge_matches = len(tags & challenge_interests)

        raw = (
            1.0 * interest_matches
            + 1.5 * strength_matches
            + 1.2 * work_matches
            + 1.3 * challenge_matches
        )
        tech_skills = len(c.get("skills", {}).get("technical", []))
        scored.append((c, raw, tech_skills))
    max_raw = max((s[1] for s in scored), default=1) or 1
    result = []
    for c, raw, tech in scored:
        normalized = round((raw / max_raw) * 100)
        result.append({"career": c, "score": normalized, "tech_count": tech})

    result.sort(key=lambda x: (-x["score"], -x["tech_count"]))
    return result


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template(
        "home.html",
        interest_options=INTEREST_OPTIONS,
        strength_options=STRENGTH_OPTIONS,
        selected_interests=session.get("interests", []),
        selected_strengths=session.get("strengths", []),
        selected_work_style=session.get("work_style", []),
        selected_challenge_types=session.get("challenge_types", []),
    )


@app.route("/recommend", methods=["POST"])
def recommend():
    interests       = request.form.getlist("interests")
    strengths       = request.form.getlist("strengths")
    work_style      = request.form.getlist("work_style")
    challenge_types = request.form.getlist("challenge_types")
    grade           = request.form.get("grade", "")

    session["interests"]         = interests
    session["strengths"]         = strengths
    session["work_style"]        = work_style
    session["challenge_types"]   = challenge_types
    session["grade"]             = grade
    session.modified = True

    careers = load_careers()
    scored  = compute_scores(careers, interests, strengths, work_style, challenge_types)

    # All available tags for filter chips
    all_tags = sorted({tag for c in careers for tag in c.get("tags", [])})

    return render_template(
        "recommend.html",
        scored=scored,
        interests=interests,
        strengths=strengths,
        all_tags=all_tags,
        bookmarks=session.get("bookmarks", []),
        interest_options=INTEREST_OPTIONS,
    )


@app.route("/careers")
def careers():
    all_careers = load_careers()
    all_tags    = sorted({tag for c in all_careers for tag in c.get("tags", [])})
    return render_template(
        "careers.html",
        careers=all_careers,
        all_tags=all_tags,
        bookmarks=session.get("bookmarks", []),
    )


@app.route("/career/<career_id>")
def career_detail(career_id):
    careers  = load_careers()
    career   = next((c for c in careers if c["id"] == career_id), None)
    if not career:
        flash("Career not found.", "warning")
        return redirect(url_for("careers"))

    # Similar careers: share at least 2 tags
    career_tags = set(career.get("tags", []))
    similar = [
        c for c in careers
        if c["id"] != career_id and len(set(c.get("tags", [])) & career_tags) >= 2
    ][:4]

    return render_template(
        "career_detail.html",
        career=career,
        similar=similar,
        bookmarks=session.get("bookmarks", []),
        compare_list=session.get("compare_list", []),
    )


@app.route("/bookmark/<career_id>", methods=["POST"])
def bookmark(career_id):
    bookmarks = session.get("bookmarks", [])
    if career_id in bookmarks:
        bookmarks.remove(career_id)
    else:
        bookmarks.append(career_id)
    session["bookmarks"] = bookmarks
    session.modified = True

    next_url = request.form.get("next") or url_for("careers")
    return redirect(next_url)


@app.route("/compare/toggle/<career_id>", methods=["POST"])
def compare_toggle(career_id):
    compare_list = session.get("compare_list", [])
    if career_id in compare_list:
        compare_list.remove(career_id)
    else:
        if len(compare_list) < 3:
            compare_list.append(career_id)
        else:
            flash("You can compare up to 3 careers at a time.", "info")
    session["compare_list"] = compare_list
    session.modified = True

    next_url = request.form.get("next") or url_for("careers")
    return redirect(next_url)


@app.route("/compare")
def compare():
    compare_list = session.get("compare_list", [])
    careers      = load_careers()
    selected     = [c for c in careers if c["id"] in compare_list]
    return render_template("compare.html", careers=selected, compare_list=compare_list)


@app.route("/roadmap")
def roadmap():
    interests       = session.get("interests", [])
    strengths       = session.get("strengths", [])
    work_style      = session.get("work_style", [])
    challenge_types = session.get("challenge_types", [])
    bookmarks       = session.get("bookmarks", [])

    careers = load_careers()
    scored  = compute_scores(careers, interests, strengths, work_style, challenge_types)

    # Primary career: first bookmark that is also top-scored; else just top scored
    bookmark_scored = [s for s in scored if s["career"]["id"] in bookmarks]
    primary = (bookmark_scored[0] if bookmark_scored else (scored[0] if scored else None))

    return render_template(
        "roadmap.html",
        primary=primary,
        scored=scored[:6],
        interests=interests,
        strengths=strengths,
        interest_options=INTEREST_OPTIONS,
        strength_options=STRENGTH_OPTIONS,
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.context_processor
def inject_globals():
    bookmarks    = session.get("bookmarks", [])
    compare_list = session.get("compare_list", [])
    return {
        "bookmark_count": len(bookmarks),
        "compare_count":  len(compare_list),
        "bookmarks":      bookmarks,
        "compare_list":   compare_list,
    }


if __name__ == "__main__":
    app.run(debug=True)
