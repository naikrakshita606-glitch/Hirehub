from dataclasses import dataclass


@dataclass
class Resume:
    id: str = ''
    candidate_id: str = ''
    file_name: str = ''
    file_path: str = ''
    uploaded_at: str = ''
