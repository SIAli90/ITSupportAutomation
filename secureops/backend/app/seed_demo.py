"""Optional *fictional* demo data: python -m app.seed_demo (run after first startup)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_engine
from .models import Asset, AuditLog, Incident, User


def main():
    with Session(get_engine()) as db:
        admin = db.scalar(select(User).where(User.role == "admin"))
        if not admin:
            raise SystemExit("Create your administrator account by starting the API first.")
        if db.scalar(select(Asset).where(Asset.tag == "LT-1001")):
            print("Fictional demo records already exist; no changes made.")
            return
        assets = [
            Asset(tag="LT-1001", name="Reception laptop", kind="laptop", status="active", assigned_to="Demo Reception", location="Main office"),
            Asset(tag="SRV-2001", name="File server", kind="server", status="active", location="Data centre"),
            Asset(tag="NET-3001", name="Core network switch", kind="network", status="maintenance", location="Network rack"),
            Asset(tag="DT-4001", name="Analyst workstation", kind="desktop", status="active", assigned_to="Demo Analyst", location="Security office"),
        ]
        db.add_all(assets)
        db.flush()
        incidents = [
            Incident(title="Repeated failed VPN sign-ins", description="Fictional demonstration of repeated authentication failures.", severity="high", status="investigating", asset_id=assets[0].id, created_by_id=admin.id, assigned_to="Demo Analyst"),
            Incident(title="Unexpected outbound traffic", description="Fictional outbound traffic alert under review.", severity="critical", status="open", asset_id=assets[1].id, created_by_id=admin.id),
            Incident(title="Switch firmware update", description="Fictional maintenance follow-up for network switch.", severity="low", status="resolved", asset_id=assets[2].id, created_by_id=admin.id),
        ]
        db.add_all(incidents)
        db.flush()
        for asset in assets:
            db.add(AuditLog(actor_user_id=admin.id, actor_email=admin.email, action="created", resource_type="asset", resource_id=asset.id, details='{"demo_data":true}'))
        for incident in incidents:
            db.add(AuditLog(actor_user_id=admin.id, actor_email=admin.email, action="created", resource_type="incident", resource_id=incident.id, details='{"demo_data":true}'))
        db.commit()
    print("Created 4 fictional assets, 3 fictional incidents, and corresponding audit entries.")


if __name__ == "__main__":
    main()
