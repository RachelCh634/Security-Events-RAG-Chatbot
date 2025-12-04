import pandas as pd

def build_document(row: pd.Series) -> str:
    try:
        parts = []
        if pd.notna(row.get("Timestamp")):
            parts.append(f"Timestamp: {row['Timestamp']}")
        if row.get("Location"):
            parts.append(f"Location: {row['Location']}")
        name = row.get("EventName") or row.get("Name") or ""
        category = row.get("Category") or ""
        if name or category:
            parts.append(" - ".join([p for p in [name, category] if p]))
        if row.get("Severity"):
            parts.append(f"Severity: {row['Severity']}")
        for field in ["Description", "OperatorNote"]:
            if row.get(field):
                parts.append(f"{field.replace('Note', ' Note')}:")
                parts.append(str(row[field]))
        return "\n".join(parts)
    except Exception as e:
        print(f"Error building document for EventID {row.get('EventID')}: {e}")
        return ""

def build_metadata(row: pd.Series) -> dict:
    meta = {}
    try:
        meta["EventID"] = int(row["EventID"])
    except Exception:
        meta["EventID"] = str(row.get("EventID", "")) if hasattr(row, 'get') else row.get("EventID", "")
    try:
        event_type_id = row.get("EventTypeID", "")
        meta["EventTypeID"] = int(event_type_id) if isinstance(event_type_id, str) and event_type_id.isdigit() else event_type_id
    except Exception:
        meta["EventTypeID"] = str(row.get("EventTypeID", "")) if hasattr(row, 'get') else row.get("EventTypeID", "")
    
    timestamp_val = ""
    try:
        if "Timestamp" in row.index:
            ts = row["Timestamp"]
            if pd.notna(ts):
                timestamp_val = str(ts).split(' ')[0] + ' ' + str(ts).split(' ')[1] if ' ' in str(ts) else str(ts)
    except Exception as e:
        pass
    
    def get_safe(key, default=""):
        try:
            if key in row.index:
                val = row[key]
                return str(val) if pd.notna(val) else default
            return default
        except:
            return default
    
    meta.update({
        "EventName": get_safe("EventName") or get_safe("Name") or "",
        "Category": get_safe("Category") or "",
        "SystemCode": get_safe("SystemCode") or "",
        "Location": get_safe("Location") or "",
        "Severity": get_safe("Severity") or "",
        "Timestamp": timestamp_val,
        "SourceDeviceID": get_safe("SourceDeviceID"),
    })
    return meta