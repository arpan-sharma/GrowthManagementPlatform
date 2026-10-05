from dataclasses import dataclass


@dataclass
class Fee:
    id: str
    student_id: str
    paid: int
    balance: int
    due_date: str
