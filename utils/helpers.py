import uuid


def generate_anon_id() -> str:
    # Keep IDs short and anonymous.
    return f"anon-{str(uuid.uuid4())[:8]}"
