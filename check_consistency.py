import requests
import json

CORE_URL = "http://10.243.151.228:8000"

def check_consistency():
    # 1. Fetch Nodes
    print("Fetching Nodes...")
    try:
        r = requests.get(f"{CORE_URL}/api/nodes")
        r.raise_for_status()
        nodes_data = r.json()
        nodes = nodes_data.get("nodes", [])
        node_ids = {n["id"]: n["name"] for n in nodes}
        print(f"Found {len(nodes)} nodes:")
        for nid, name in node_ids.items():
            n = next(n for n in nodes if n["id"] == nid)
            print(f"  - {name} ({nid}) Status: {n['status']} LastSeen: {n['last_seen']}")
    except Exception as e:
        print(f"Error fetching nodes: {e}")
        return

    # 2. Fetch Alerts
    print("\nFetching Alerts...")
    try:
        r = requests.get(f"{CORE_URL}/api/alerts")
        r.raise_for_status()
        alerts_data = r.json()
        alerts = alerts_data.get("alerts", [])
        print(f"Found {len(alerts)} alerts:")
        for a in alerts:
            nid = a["node_id"]
            node_name = node_ids.get(nid, "UNKNOWN_NODE") # Check if ID exists in fetched nodes
            print(f"  - Alert {a['id']} for Node {node_name} ({nid}): {a['message']}")
            
            if nid not in node_ids:
                print(f"    !!! ORPHAN ALERT: Node ID {nid} not found in Node List !!!")
            else:
                 print(f"    (Linked to valid node)")

    except Exception as e:
        print(f"Error fetching alerts: {e}")

if __name__ == "__main__":
    check_consistency()
