from nexus.core.db.database import SessionLocal
from nexus.core.db.models import AlertModel, NodeModel

db = SessionLocal()
alerts = db.query(AlertModel).filter(AlertModel.status == "active").all()
print(f"Active Alerts: {len(alerts)}")
for a in alerts:
    node = db.query(NodeModel).get(a.node_id)
    node_name = node.name if node else "Unknown"
    print(f"[{a.type}] Node: {node_name} ({a.node_id}) - {a.message} (Created: {a.created_at})")
