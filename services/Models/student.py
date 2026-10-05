from dataclasses import dataclass

from services.Models.user import User


@dataclass
class Student(User):
    batch: str = ""
    roll_number: str = ""

# Example usage:
# student = Student(
#     id="S001",
#     first_name="Aarav",
#     last_name="Sharma",
#     email="aarav@example.com",
#     password="secret123",
#     contact_number="+91-9876543210",
#     role="student",
#     batch="Maths-2026",
#     roll_number="24-018",
# )
