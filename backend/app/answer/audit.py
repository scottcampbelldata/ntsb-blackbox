from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditEvent:
    step: str
    detail: str


@dataclass
class AuditTrail:
    events: list[AuditEvent] = field(default_factory=list)

    def add(self, step, detail):
        self.events.append(AuditEvent(step=step, detail=detail))

    def to_list(self):
        return [event.__dict__ for event in self.events]

