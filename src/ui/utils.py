def quality_label(desc: str | None) -> str:
    if desc is None or (isinstance(desc, str) and desc.strip() == ""):
        return "Vide"
    if not isinstance(desc, str):
        desc = str(desc)
    length = len(desc)
    if length < 50: return "<50c"
    elif length < 200: return "50-200c"
    elif length < 500: return "200-500c"
    else: return ">500c"

def truncate_desc(desc, max_len=80):
    if desc is None: return ""
    s = str(desc)
    if len(s) > max_len: return s[:max_len] + "..."
    return s
