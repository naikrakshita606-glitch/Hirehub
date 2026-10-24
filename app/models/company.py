from dataclasses import dataclass, field


@dataclass
class Company:
    id: str = ''
    name: str = ''
    location: str = ''
    industry: str = ''
    description: str = ''
    recruiters: list[str] = field(default_factory=list)
