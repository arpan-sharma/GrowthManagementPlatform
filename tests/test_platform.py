from tests.conftest import BASE

ROOT = BASE.removesuffix("/auth")


def bearer(login):
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_academic_routes_require_a_token(client):
    assert client.get(f"{ROOT}/batches").status_code == 401
    assert client.get(f"{ROOT}/students").status_code == 401
    assert client.post(f"{ROOT}/notices", json={"title": "Hi", "content": "Hello"}).status_code == 401


def test_teacher_can_run_the_class_and_students_only_see_themselves(client, admin_login):
    teacher = bearer(admin_login)

    batches = client.get(f"{ROOT}/batches", headers=teacher)
    assert batches.status_code == 200
    assert any(row["id"] == "bat_demo" for row in batches.json())

    created = client.post(
        f"{ROOT}/students",
        headers=teacher,
        json={
            "first_name": "Priya",
            "last_name": "Nair",
            "email": "priya@example.com",
            "contact_number": "+919800000002",
            "roll_number": "24-019",
            "batch_id": "bat_demo",
            "password": "student123",
        },
    )
    assert created.status_code == 201, created.text
    priya = created.json()["id"]
    assert client.post(
        f"{ROOT}/students",
        headers=teacher,
        json={
            "first_name": "Priya",
            "last_name": "Again",
            "email": "priya2@example.com",
            "contact_number": "+919800000003",
            "roll_number": "24-019",
            "batch_id": "bat_demo",
            "password": "student123",
        },
    ).status_code == 409

    session = client.get(
        f"{ROOT}/attendance/session",
        headers=teacher,
        params={"batch_id": "bat_demo", "subject_id": "sub_maths"},
    )
    assert session.status_code == 200
    assert session.json()["batch_name"] == "Batch A"
    assert any(row["student_id"] == "stu_aarav" for row in session.json()["students"])

    marked = client.post(
        f"{ROOT}/attendance/session",
        headers=teacher,
        json={
            "batch_id": "bat_demo",
            "subject_id": "sub_maths",
            "marks": [
                {"student_id": "stu_aarav", "status": "Absent"},
                {"student_id": priya, "status": "Present"},
            ],
        },
    )
    assert marked.status_code == 201
    body = marked.json()
    assert body["subject_name"] == "Maths"
    assert len(body["students"]) >= 2
    aarav_row = next(row for row in body["students"] if row["student_id"] == "stu_aarav")
    assert aarav_row["status"] == "Absent"

    exam = client.post(
        f"{ROOT}/tests",
        headers=teacher,
        json={
            "name": "Algebra quiz",
            "subject_id": "sub_maths",
            "chapter_id": "ch_algebra",
            "batch_id": "bat_demo",
            "on_date": "2026-10-06",
            "max_marks": 20,
        },
    )
    assert exam.status_code == 201, exam.text
    test_id = exam.json()["id"]
    question = client.post(
        f"{ROOT}/tests/{test_id}/questions",
        headers=teacher,
        json={
            "text": "Solve 2x = 4",
            "question_type": "Numerical",
            "marks": 5,
            "chapter_id": "ch_algebra",
            "topic_id": "top_linear",
            "answer": "2",
        },
    )
    assert question.status_code == 201

    scored = client.put(
        f"{ROOT}/tests/{test_id}/marks",
        headers=teacher,
        json={"entries": [{"student_id": "stu_aarav", "marks": 8}, {"student_id": priya, "marks": 18}]},
    )
    assert scored.status_code == 200
    assert scored.json()["status"] == "Done"
    assert {row["student_id"] for row in scored.json()["marks"]} == {"stu_aarav", priya}
    assert client.put(
        f"{ROOT}/tests/{test_id}/marks",
        headers=teacher,
        json={"entries": [{"student_id": "stu_aarav", "marks": 99}]},
    ).status_code == 422

    fee = client.put(
        f"{ROOT}/fees/{priya}",
        headers=teacher,
        json={"total": 8000, "due_date": "2026-10-20"},
    )
    assert fee.status_code == 200 and fee.json()["status"] == "Partial"
    paid = client.post(f"{ROOT}/fees/{priya}/payments", headers=teacher, json={"amount": 8000})
    assert paid.status_code == 201 and paid.json()["status"] == "Paid"

    notice = client.post(
        f"{ROOT}/notices",
        headers=teacher,
        json={"title": "Holiday", "content": "Holiday on Friday"},
    )
    assert notice.status_code == 201
    assert client.get(f"{ROOT}/dashboard", headers=teacher).status_code == 200

    aarav = client.post(
        f"{BASE}/student/login",
        json={"institution_code": "DEMO01", "roll_number": "24-018", "password": "student123"},
    )
    assert aarav.status_code == 200, aarav.text
    student = bearer(aarav)

    assert client.post(f"{ROOT}/batches", headers=student, json={"name": "Nope"}).status_code == 403
    own = client.get(f"{ROOT}/students", headers=student)
    assert own.status_code == 200 and [row["id"] for row in own.json()] == ["stu_aarav"]
    assert client.get(f"{ROOT}/students/{priya}", headers=student).status_code == 404

    profile = client.get(f"{ROOT}/students/stu_aarav", headers=teacher)
    assert profile.status_code == 200
    body = profile.json()
    assert body["student"]["id"] == "stu_aarav"
    assert "subjects" in body and "chapters" in body
    assert body["fee"] is not None

    paper = client.get(f"{ROOT}/tests/{test_id}", headers=student)
    assert paper.status_code == 200
    assert [row["student_id"] for row in paper.json()["marks"]] == ["stu_aarav"]
    assert paper.json()["questions"][0]["answer"] == ""
    assert paper.json()["batch_average"] == 65.0

    fees = client.get(f"{ROOT}/fees", headers=student)
    assert fees.status_code == 200 and [row["student_id"] for row in fees.json()] == ["stu_aarav"]
    notices = client.get(f"{ROOT}/notices", headers=student)
    assert any(row["content"] == "Holiday on Friday" for row in notices.json())


def test_teacher_can_delete_student(client, admin_login):
    teacher = bearer(admin_login)
    created = client.post(
        f"{ROOT}/students",
        headers=teacher,
        json={
            "first_name": "To",
            "last_name": "Remove",
            "email": "remove.me@example.com",
            "contact_number": "+919800000099",
            "roll_number": "24-099",
            "batch_id": "bat_demo",
            "password": "student123",
        },
    )
    assert created.status_code == 201
    student_id = created.json()["id"]
    assert client.delete(f"{ROOT}/students/{student_id}", headers=teacher).status_code == 204
    assert client.get(f"{ROOT}/students/{student_id}", headers=teacher).status_code == 404
    assert student_id not in {row["id"] for row in client.get(f"{ROOT}/students", headers=teacher).json()}
