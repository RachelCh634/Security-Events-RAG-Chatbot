from datetime import datetime, timedelta

def parse_filters(q):
    filters = {}
    q = q.lower()

    # Severity
    if "critical" in q: filters["severity"] = "critical"
    elif "high" in q: filters["severity"] = "high"
    elif "medium" in q: filters["severity"] = "medium"
    elif "low" in q: filters["severity"] = "low"

    # Category
    if "fire" in q or "smoke" in q: filters["category"] = "fire safety"
    elif "camera" in q or "video" in q: filters["category"] = "video"
    elif "access" in q or "badge" in q or "door" in q: filters["category"] = "access control"
    elif "motion" in q or "unauthorized" in q: filters["category"] = "security"

    # Location
    for loc in ["building a","building b","building c","parking","server room","lobby"]:
        if loc in q:
            filters["location"] = loc
            break

    # Time
    if "today" in q: filters["time"] = 1
    elif "yesterday" in q: filters["time"] = 2
    elif "week" in q: filters["time"] = 7
    elif "month" in q: filters["time"] = 30

    return filters

def build_where(filters):
    clause = []
    if "severity" in filters:
        clause.append({"Severity": {"$eq": filters["severity"]}})
    if "category" in filters:
        clause.append({"Category": {"$eq": filters["category"]}})
    if not clause:
        return None
    if len(clause) == 1:
        return clause[0]
    return {"$and": clause}

def filter_loc(docs, metas, loc):
    out_docs, out_metas = [], []
    for d, m in zip(docs, metas):
        if loc in m.get("Location", "").lower():
            out_docs.append(d)
            out_metas.append(m)
    return out_docs, out_metas

def filter_loc_with_embeds(docs, metas, embeds, loc):
    out_docs, out_metas, out_embeds = [], [], []
    for d, m, e in zip(docs, metas, embeds):
        if loc in m.get("Location", "").lower():
            out_docs.append(d)
            out_metas.append(m)
            out_embeds.append(e)
    return out_docs, out_metas, out_embeds

def filter_time(docs, metas, days):
    cutoff = datetime.now() - timedelta(days=days)
    out_docs, out_metas = [], []
    for d, m in zip(docs, metas):
        try:
            t = datetime.strptime(m.get("Timestamp", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
            if t >= cutoff:
                out_docs.append(d)
                out_metas.append(m)
        except Exception:
            out_docs.append(d)
            out_metas.append(m)
    return out_docs, out_metas

def filter_time_with_embeds(docs, metas, embeds, days):
    cutoff = datetime.now() - timedelta(days=days)
    out_docs, out_metas, out_embeds = [], [], []
    for d, m, e in zip(docs, metas, embeds):
        try:
            t = datetime.strptime(m.get("Timestamp", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S")
            if t >= cutoff:
                out_docs.append(d)
                out_metas.append(m)
                out_embeds.append(e)
        except Exception:
            out_docs.append(d)
            out_metas.append(m)
            out_embeds.append(e)
    return out_docs, out_metas, out_embeds