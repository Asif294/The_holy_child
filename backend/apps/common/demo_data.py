"""
Sample data for local development and demos.

Everything here is fictional. The command is idempotent — it uses
``get_or_create`` throughout, so running it twice does not duplicate rows.
"""
import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.attendance.models import AttendanceStatus, StudentAttendance
from apps.classes.models import AcademicSession, SchoolClass, Section
from apps.dashboard.models import ActivityLog, SchoolEvent
from apps.exams.models import Exam, ExamSchedule, ExamType, Result
from apps.fees.models import FeeCategory, FeeStructure, Invoice, Payment
from apps.principal.models import ApprovalRequest, Notice, Principal
from apps.students.models import Guardian, Student
from apps.subjects.models import ClassSubject, Subject
from apps.teachers.models import Department, Designation, Teacher

CLASSES = [
    ("Play Group", "প্লে-গ্রুপ", "PG", 1), ("Nursery", "নার্সারি", "NUR", 2),
    ("Class 1", "১ম শ্রেণি", "C1", 3), ("Class 2", "২য় শ্রেণি", "C2", 4),
    ("Class 3", "৩য় শ্রেণি", "C3", 5), ("Class 4", "৪র্থ শ্রেণি", "C4", 6),
    ("Class 5", "৫ম শ্রেণি", "C5", 7), ("Class 6", "৬ষ্ঠ শ্রেণি", "C6", 8),
    ("Class 7", "৭ম শ্রেণি", "C7", 9), ("Class 8", "৮ম শ্রেণি", "C8", 10),
    ("Class 9", "৯ম শ্রেণি", "C9", 11), ("Class 10", "১০ম শ্রেণি", "C10", 12),
]

SUBJECTS = [
    ("Bangla", "বাংলা", "BAN", "compulsory"), ("English", "ইংরেজি", "ENG", "compulsory"),
    ("Mathematics", "গণিত", "MAT", "compulsory"), ("Science", "বিজ্ঞান", "SCI", "compulsory"),
    ("Social Science", "সমাজ বিজ্ঞান", "SOC", "compulsory"), ("Religion", "ধর্ম", "REL", "compulsory"),
    ("ICT", "তথ্য ও যোগাযোগ প্রযুক্তি", "ICT", "compulsory"),
    ("Agriculture", "কৃষিশিক্ষা", "AGR", "optional"), ("Physical Education", "শারীরিক শিক্ষা", "PED", "extra"),
]

DESIGNATIONS = [("Principal", 1), ("Vice Principal", 2), ("Senior Teacher", 3),
                ("Assistant Teacher", 4), ("Junior Teacher", 5)]

DEPARTMENTS = [("Science", "SCI"), ("Languages", "LANG"), ("Mathematics", "MATH"),
               ("Social Studies", "SOCS"), ("Primary Section", "PRIM")]

TEACHER_NAMES = [
    "Md. Abdul Karim", "Nasrin Akter", "Shahidul Islam", "Rehana Parvin", "Mizanur Rahman",
    "Farida Yasmin", "Anwar Hossain", "Salma Khatun", "Jahangir Alam", "Nusrat Jahan",
    "Rafiqul Islam", "Sharmin Sultana",
]

STUDENT_FIRST = ["Tanvir", "Sadia", "Rakib", "Mim", "Sabbir", "Nusrat", "Arif", "Jannatul",
                 "Hasan", "Tasnim", "Sohel", "Afsana", "Imran", "Sumaiya", "Rana", "Fatema"]
STUDENT_LAST = ["Ahmed", "Akter", "Hossain", "Islam", "Rahman", "Khatun", "Uddin", "Begum"]


@transaction.atomic
def load_demo_data() -> dict:
    """Populate the database with a small but coherent school. Returns row counts."""
    random.seed(2026)
    today = timezone.localdate()

    session, _ = AcademicSession.objects.get_or_create(
        name=str(today.year),
        defaults={"start_date": date(today.year, 1, 1), "end_date": date(today.year, 12, 31), "is_current": True},
    )

    classes = {}
    for name, name_bn, code, order in CLASSES:
        school_class, _ = SchoolClass.objects.get_or_create(
            code=code, defaults={"name": name, "name_bn": name_bn, "order": order}
        )
        classes[code] = school_class

    subjects = {}
    for name, name_bn, code, category in SUBJECTS:
        subject, _ = Subject.objects.get_or_create(
            code=code, defaults={"name": name, "name_bn": name_bn, "category": category}
        )
        subjects[code] = subject

    designations = {
        name: Designation.objects.get_or_create(name=name, defaults={"rank": rank})[0]
        for name, rank in DESIGNATIONS
    }
    departments = {
        code: Department.objects.get_or_create(code=code, defaults={"name": name})[0]
        for name, code in DEPARTMENTS
    }

    # --- Teaching staff ------------------------------------------------ #
    teachers = []
    department_codes = list(departments)
    for index, full_name in enumerate(TEACHER_NAMES, start=1):
        designation = designations["Principal"] if index == 1 else (
            designations["Senior Teacher"] if index <= 4 else designations["Assistant Teacher"]
        )
        teacher, _ = Teacher.objects.get_or_create(
            employee_id=f"THC-T-{index:04d}",
            defaults={
                "full_name": full_name,
                "email": f"teacher{index}@holychildschool.edu.bd",
                "phone": f"017{index:08d}",
                "designation": designation,
                "department": departments[department_codes[index % len(department_codes)]],
                "joining_date": date(2006 + (index % 15), 1, 15),
                "qualification": random.choice(["M.A., B.Ed.", "M.Sc., B.Ed.", "B.A. (Hons), M.A.", "M.Ed."]),
                "experience_years": random.randint(2, 20),
                "gender": "male" if index % 2 else "female",
                "blood_group": random.choice(["A+", "B+", "O+", "AB+"]),
                "address": "Longorpara, Sribordi, Sherpur",
            },
        )
        teachers.append(teacher)

    # --- Sections and class-subject mapping ---------------------------- #
    sections = []
    for school_class in classes.values():
        for section_name in (["A", "B"] if school_class.order >= 8 else ["A"]):
            section, _ = Section.objects.get_or_create(
                school_class=school_class,
                name=section_name,
                defaults={
                    "capacity": 40,
                    "room_number": f"{school_class.order}{section_name}",
                    "class_teacher": random.choice(teachers[1:]),
                },
            )
            sections.append(section)

        for subject in list(subjects.values())[: 5 if school_class.order <= 7 else 8]:
            ClassSubject.objects.get_or_create(
                school_class=school_class,
                subject=subject,
                defaults={"teacher": random.choice(teachers[1:]), "weekly_periods": random.randint(3, 6)},
            )

    # --- Principal ----------------------------------------------------- #
    principal_teacher = teachers[0]
    Principal.objects.get_or_create(
        full_name=principal_teacher.full_name,
        defaults={
            "teacher": principal_teacher,
            "designation": "Principal",
            "email": "principal@holychildschool.edu.bd",
            "phone": "01700000001",
            "qualification": "M.A. in English, B.Ed.",
            "experience_years": 22,
            "tenure_start": date(2006, 1, 1),
            "is_current": True,
            "message": (
                "Welcome to The Holy Child Pre-Cadet & High School. Since 2006 we have "
                "worked to give the children of Longorpara a disciplined, caring and "
                "modern education from Play Group through Class 10. Our teachers treat "
                "every pupil as an individual, and our results speak for the effort our "
                "students put in. We are glad you are here."
            ),
        },
    )

    # --- Students and guardians ---------------------------------------- #
    students = []
    counter = 0
    for section in sections:
        for roll in range(1, random.randint(18, 30)):
            counter += 1
            full_name = f"{random.choice(STUDENT_FIRST)} {random.choice(STUDENT_LAST)}"
            guardian, _ = Guardian.objects.get_or_create(
                phone=f"018{counter:08d}",
                defaults={
                    "full_name": f"Md. {random.choice(STUDENT_LAST)}",
                    "relation": "father",
                    "occupation": random.choice(["Farmer", "Teacher", "Business", "Service", "Doctor"]),
                    "address": "Longorpara, Sribordi, Sherpur",
                },
            )
            student, _ = Student.objects.get_or_create(
                student_id=f"THC-{today.year}-{counter:04d}",
                defaults={
                    "admission_number": f"ADM-{today.year}-{counter:04d}",
                    "roll_number": roll,
                    "full_name": full_name,
                    "school_class": section.school_class,
                    "section": section,
                    "session": session,
                    "guardian": guardian,
                    "father_name": guardian.full_name,
                    "mother_name": f"Mrs. {random.choice(STUDENT_LAST)}",
                    "gender": random.choice(["male", "female"]),
                    "blood_group": random.choice(["A+", "B+", "O+", "AB+", "O-"]),
                    "date_of_birth": date(today.year - 6 - section.school_class.order, random.randint(1, 12),
                                          random.randint(1, 28)),
                    "admission_date": date(today.year, 1, random.randint(1, 28)),
                    "emergency_contact": guardian.phone,
                    "present_address": "Longorpara, Sribordi, Sherpur",
                    "permanent_address": "Longorpara, Sribordi, Sherpur",
                },
            )
            students.append(student)

    # --- Attendance for the last 10 school days ------------------------ #
    attendance_rows = 0
    if not StudentAttendance.objects.exists():
        records = []
        for offset in range(10):
            day = today - timedelta(days=offset)
            if day.weekday() == 4:  # Friday — weekly holiday in Bangladesh.
                continue
            for student in students:
                status = random.choices(
                    [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LATE,
                     AttendanceStatus.LEAVE],
                    weights=[88, 6, 4, 2],
                )[0]
                records.append(
                    StudentAttendance(student=student, section=student.section, date=day, status=status)
                )
        StudentAttendance.objects.bulk_create(records, ignore_conflicts=True)
        attendance_rows = len(records)

    # --- Fees ----------------------------------------------------------- #
    fee_categories = {}
    for name, code, frequency in [
        ("Tuition Fee", "TUI", "monthly"), ("Admission Fee", "ADM", "one_time"),
        ("Exam Fee", "EXM", "yearly"), ("Session Charge", "SES", "yearly"),
    ]:
        fee_categories[code] = FeeCategory.objects.get_or_create(
            code=code, defaults={"name": name, "frequency": frequency}
        )[0]

    for school_class in classes.values():
        FeeStructure.objects.get_or_create(
            session=session,
            school_class=school_class,
            category=fee_categories["TUI"],
            defaults={"amount": Decimal(300 + school_class.order * 50), "due_day": 10},
        )

    invoices = 0
    if not Invoice.objects.exists():
        for index, student in enumerate(students[:120], start=1):
            amount = Decimal(300 + (student.school_class.order if student.school_class else 1) * 50)
            invoice = Invoice.objects.create(
                invoice_number=f"INV-{today.year}-{index:05d}",
                student=student,
                session=session,
                category=fee_categories["TUI"],
                title=f"Tuition — {today.strftime('%B %Y')}",
                period_month=today.month,
                period_year=today.year,
                amount=amount,
                issue_date=today.replace(day=1),
                due_date=today.replace(day=10),
            )
            invoices += 1
            if index % 3:  # roughly two thirds are settled
                Payment.objects.create(
                    receipt_number=f"RCP-{today.year}-{index:05d}",
                    invoice=invoice,
                    amount=amount,
                    method=random.choice(["cash", "bkash", "nagad", "bank"]),
                    paid_at=timezone.now() - timedelta(days=random.randint(0, 20)),
                )

    # --- Exams ---------------------------------------------------------- #
    exam_type, _ = ExamType.objects.get_or_create(
        code="HY", defaults={"name": "Half Yearly Examination", "weight": 50}
    )
    exam, _ = Exam.objects.get_or_create(
        name=f"Half Yearly Examination {today.year}",
        defaults={
            "exam_type": exam_type,
            "session": session,
            "start_date": today + timedelta(days=14),
            "end_date": today + timedelta(days=24),
            "instructions": "Answer scripts must be submitted on time. Mobile phones are not allowed.",
        },
    )
    for offset, subject in enumerate(list(subjects.values())[:5]):
        ExamSchedule.objects.get_or_create(
            exam=exam,
            school_class=classes["C9"],
            subject=subject,
            defaults={
                "exam_date": exam.start_date + timedelta(days=offset * 2),
                "start_time": time(10, 0),
                "end_time": time(13, 0),
                "room": "Hall 1",
            },
        )

    results = 0
    if not Result.objects.exists():
        for student in [s for s in students if s.school_class and s.school_class.code == "C9"][:25]:
            for subject in list(subjects.values())[:5]:
                Result.objects.create(
                    exam=exam, student=student, subject=subject,
                    marks_obtained=Decimal(random.randint(35, 98)), full_marks=100,
                )
                results += 1

    # --- Notices, events and activity ----------------------------------- #
    for title, body, priority in [
        ("Half Yearly Examination Routine Published",
         "The routine for the Half Yearly Examination is now available at the school office.", "important"),
        ("Parents' Meeting", "A parents' meeting will be held in the school hall. All guardians are requested "
                             "to attend.", "normal"),
        ("Annual Sports Day", "The annual sports day will be held on the school ground. Registration is open "
                              "at the office.", "normal"),
    ]:
        Notice.objects.get_or_create(
            title=title,
            defaults={"body": body, "priority": priority, "is_published": True, "published_at": timezone.now()},
        )

    for title, category, offset in [
        ("Half Yearly Examination Begins", "exam", 14),
        ("Annual Sports Day", "sports", 30),
        ("Parents' Meeting", "meeting", 7),
        ("Victory Day", "holiday", 45),
    ]:
        SchoolEvent.objects.get_or_create(
            title=title,
            defaults={
                "category": category,
                "start_date": today + timedelta(days=offset),
                "venue": "School premises",
                "is_holiday": category == "holiday",
            },
        )

    ApprovalRequest.objects.get_or_create(
        title="Casual leave for three days",
        defaults={"category": "leave", "details": "Family emergency. Requesting leave from the 3rd to the 5th."},
    )

    for action, module, description in [
        ("created", "student", "New student admitted to Class 6"),
        ("payment", "fee", "Tuition payment received"),
        ("attendance", "attendance", "Attendance recorded for Class 9 — Section A"),
        ("published", "notice", "Notice published: Half Yearly Examination Routine"),
    ]:
        ActivityLog.objects.get_or_create(
            description=description, defaults={"action": action, "module": module, "actor_name": "System"}
        )

    return {
        "classes": len(classes),
        "sections": len(sections),
        "subjects": len(subjects),
        "teachers": len(teachers),
        "students": len(students),
        "attendance": attendance_rows,
        "invoices": invoices,
        "results": results,
    }
