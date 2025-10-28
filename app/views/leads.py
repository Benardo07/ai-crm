from collections import Counter

from flask import (
    Blueprint,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..extensions import db
from ..forms import LeadFormData, parse_lead_form, validate_lead_form
from ..models import Lead
from ..services import enqueue_sentiment_refresh

bp = Blueprint("leads", __name__)


@bp.before_request
def ensure_authenticated():
    if session.get("user"):
        return None

    target = request.full_path if request.query_string else request.path
    return redirect(url_for("auth.login", next=target))


@bp.route("/")
@bp.route("/leads")
def list_leads():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    leads_payload: list[dict[str, str | int | float | bool | None]] = []
    status_counts: Counter[str] = Counter()
    sentiment_counts: Counter[str] = Counter()
    last_updated = None

    for lead in leads:
        status_counts[lead.status] += 1
        sentiment_label = lead.sentiment or "Not Analyzed"
        sentiment_counts[sentiment_label] += 1
        if last_updated is None or lead.updated_at > last_updated:
            last_updated = lead.updated_at

        leads_payload.append(
            {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone or "",
                "status": lead.status,
                "notes": lead.notes or "",
                "sentiment": sentiment_label,
                "isAnalyzing": sentiment_label == "Analyzing",
                "sentimentScore": round(lead.sentiment_score, 4)
                if lead.sentiment_score is not None
                else None,
                "createdAt": lead.created_at.isoformat(),
                "updatedAt": lead.updated_at.isoformat(),
                "editUrl": url_for("leads.edit_lead", lead_id=lead.id),
                "deleteUrl": url_for("leads.delete_lead", lead_id=lead.id),
            }
        )

    sentiment_summary = {
        "Positive": sentiment_counts.get("Positive", 0),
        "Neutral": sentiment_counts.get("Neutral", 0),
        "Negative": sentiment_counts.get("Negative", 0),
        "Not Analyzed": sentiment_counts.get("Not Analyzed", 0),
        "Analyzing": sentiment_counts.get("Analyzing", 0),
    }

    last_updated_display = (
        last_updated.strftime("%b %d, %Y %I:%M %p") if last_updated else None
    )

    return render_template(
        "leads/list.html",
        statuses=Lead.STATUS_CHOICES,
        leads_payload=leads_payload,
        status_order=Lead.STATUS_CHOICES,
        sentiment_options=[
            "Positive",
            "Neutral",
            "Negative",
            "Analyzing",
            "Not Analyzed",
        ],
        status_counts=dict(status_counts),
        sentiment_summary=sentiment_summary,
        total_leads=len(leads),
        last_updated=last_updated_display,
        title="Lead Dashboard",
    )


@bp.get("/leads/status")
def leads_status():
    ids_param = request.args.get("ids", "")
    lead_ids: list[int] = []
    for chunk in ids_param.split(","):
        value = chunk.strip()
        if not value:
            continue
        if value.isdigit():
            lead_ids.append(int(value))

    if not lead_ids:
        return jsonify([])

    leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
    payload = [
        {
            "id": lead.id,
            "sentiment": lead.sentiment,
            "sentiment_score": lead.sentiment_score,
            "is_analyzing": lead.sentiment == "Analyzing",
            "updated_at": lead.updated_at.isoformat(),
        }
        for lead in leads
    ]
    return jsonify(payload)


@bp.route("/leads/add", methods=["GET", "POST"])
def add_lead():
    if request.method == "POST":
        form_data = parse_lead_form(request.form)
        errors = validate_lead_form(form_data)

        if errors:
            return render_template(
                "leads/form.html",
                form=form_data.as_dict(),
                errors=errors,
                statuses=Lead.STATUS_CHOICES,
                mode="add",
                title="Add Lead",
            )

        has_notes = bool(form_data.notes)
        lead = Lead(
            name=form_data.name,
            email=form_data.email,
            phone=form_data.phone or None,
            status=form_data.status,
            notes=form_data.notes or None,
            sentiment="Analyzing" if has_notes else None,
            sentiment_score=None,
        )

        try:
            db.session.add(lead)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            errors.append("A lead with this email already exists.")
            return render_template(
                "leads/form.html",
                form=form_data.as_dict(),
                errors=errors,
                statuses=Lead.STATUS_CHOICES,
                mode="add",
                title="Add Lead",
            )
        except SQLAlchemyError as exc:  # pragma: no cover - defensive
            db.session.rollback()
            abort(500, description=str(exc))

        if has_notes:
            enqueue_sentiment_refresh(lead.id)

        return redirect(url_for("leads.list_leads"))

    return render_template(
        "leads/form.html",
        form=LeadFormData().as_dict(),
        errors=[],
        statuses=Lead.STATUS_CHOICES,
        mode="add",
        title="Add Lead",
    )


@bp.route("/leads/edit/<int:lead_id>", methods=["GET", "POST"])
def edit_lead(lead_id: int):
    lead = Lead.query.get_or_404(lead_id)

    if request.method == "POST":
        form_data = parse_lead_form(request.form)
        errors = validate_lead_form(form_data)

        if errors:
            return render_template(
                "leads/form.html",
                form=form_data.as_dict(),
                errors=errors,
                statuses=Lead.STATUS_CHOICES,
                mode="edit",
                lead_id=lead_id,
                title="Edit Lead",
            )

        has_notes = bool(form_data.notes)
        lead.name = form_data.name
        lead.email = form_data.email
        lead.phone = form_data.phone or None
        lead.status = form_data.status
        lead.notes = form_data.notes or None
        lead.sentiment = "Analyzing" if has_notes else None
        lead.sentiment_score = None

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            errors.append("A lead with this email already exists.")
            return render_template(
                "leads/form.html",
                form=form_data.as_dict(),
                errors=errors,
                statuses=Lead.STATUS_CHOICES,
                mode="edit",
                lead_id=lead_id,
                title="Edit Lead",
            )
        except SQLAlchemyError as exc:  # pragma: no cover
            db.session.rollback()
            abort(500, description=str(exc))

        if has_notes:
            enqueue_sentiment_refresh(lead.id)

        return redirect(url_for("leads.list_leads"))

    form = LeadFormData(
        name=lead.name,
        email=lead.email,
        phone=lead.phone or "",
        status=lead.status,
        notes=lead.notes or "",
    )

    return render_template(
        "leads/form.html",
        form=form.as_dict(),
        errors=[],
        statuses=Lead.STATUS_CHOICES,
        mode="edit",
        lead_id=lead_id,
        title="Edit Lead",
    )


@bp.post("/leads/delete/<int:lead_id>")
def delete_lead(lead_id: int):
    lead = Lead.query.get_or_404(lead_id)
    try:
        db.session.delete(lead)
        db.session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        abort(500, description=str(exc))

    return redirect(url_for("leads.list_leads"))
