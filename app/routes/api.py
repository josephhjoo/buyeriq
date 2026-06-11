from flask import Blueprint, request, jsonify, render_template, Response
from app.models.models import SessionLocal, Search, Buyer
from app.services.buyer_agent import research_buyers
from app.services.csv_export import buyers_to_csv
from app.services.pdf_export import generate_buyer_report
from datetime import datetime
import json

api = Blueprint("api", __name__)


# ── Pages ────────────────────────────────────────────────────────────────────

@api.route("/")
def index():
    return render_template("index.html")


# ── Research ─────────────────────────────────────────────────────────────────

@api.route("/api/research", methods=["POST"])
def run_research():
    """Run the buyer research agent and save results."""
    data = request.json
    required = ["industry", "revenue_m", "geography", "description"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        result = research_buyers(data)
    except Exception as e:
        return jsonify({"error": f"Research failed: {str(e)}"}), 500

    # Persist the search and its buyers
    db = SessionLocal()
    try:
        search = Search(
            target_name=data.get("name") or "Confidential",
            industry=data.get("industry"),
            revenue_m=data.get("revenue_m"),
            geography=data.get("geography"),
            description=data.get("description"),
            research_notes=result.get("research_notes"),
        )
        db.add(search)
        db.flush()  # get search.id

        for b in result.get("buyers", []):
            db.add(Buyer(
                search_id=search.id,
                firm_name=b.get("firm_name"),
                buyer_type=b.get("buyer_type"),
                rationale=b.get("rationale"),
                contact_name=b.get("contact_name"),
                contact_title=b.get("contact_title"),
                confidence=b.get("confidence", 0),
                confidence_reasoning=b.get("confidence_reasoning"),
                source_urls=json.dumps(b.get("source_urls", [])),
            ))
        db.commit()
        db.refresh(search)
        out = search.to_dict()
    finally:
        db.close()

    return jsonify(out), 201


# ── Past Searches ─────────────────────────────────────────────────────────────

@api.route("/api/searches", methods=["GET"])
def list_searches():
    db = SessionLocal()
    searches = db.query(Search).order_by(Search.created_at.desc()).all()
    result = [s.to_dict(include_buyers=False) for s in searches]
    db.close()
    return jsonify(result)


@api.route("/api/searches/<int:search_id>", methods=["GET"])
def get_search(search_id):
    db = SessionLocal()
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        db.close()
        return jsonify({"error": "Search not found"}), 404
    result = search.to_dict()
    db.close()
    return jsonify(result)


# ── Exports ───────────────────────────────────────────────────────────────────

@api.route("/api/searches/<int:search_id>/export/csv", methods=["GET"])
def export_csv(search_id):
    db = SessionLocal()
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        db.close()
        return jsonify({"error": "Search not found"}), 404
    csv_bytes = buyers_to_csv(search.to_dict())
    name = search.target_name.replace(" ", "_")
    db.close()
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition":
                 f"attachment; filename=BuyerList_{name}_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@api.route("/api/searches/<int:search_id>/export/pdf", methods=["GET"])
def export_pdf(search_id):
    db = SessionLocal()
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        db.close()
        return jsonify({"error": "Search not found"}), 404
    pdf_bytes = generate_buyer_report(search.to_dict())
    name = search.target_name.replace(" ", "_")
    db.close()
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition":
                 f"attachment; filename=BuyerReport_{name}_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )
