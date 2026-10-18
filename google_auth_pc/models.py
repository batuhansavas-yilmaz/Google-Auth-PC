from dataclasses import asdict, dataclass


@dataclass
class Account:
    secret: str
    name: str
    issuer: str
    digits: int = 6
    period: int = 30
    algorithm: str = "SHA1"
    type: str = "totp"
    counter: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        return cls(**data)
