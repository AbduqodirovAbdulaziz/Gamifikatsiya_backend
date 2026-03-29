from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.classroom.models import Classroom, ClassroomInvitation, Enrollment
from apps.courses.models import Course, Lesson
from apps.gamification.models import Badge, LevelTitle
from apps.quizzes.models import AnswerChoice, Question, Quiz
from apps.users.models import StudentProfile, TeacherProfile, UserRole

User = get_user_model()


TOPIC_PACKS = [
    {
        "subject": "Matematika",
        "classroom": "Matematika Ustalari",
        "course": "Ball va badge tizimi",
        "quiz": "Badge va ball bo'yicha test",
        "school": "Toshkent ixtisoslashtirilgan maktabi",
        "teacher_name": ("Aziza", "Karimova"),
        "teacher_bio": "Gamifikatsiya yordamida masala yechish motivatsiyasini oshiradi.",
    },
    {
        "subject": "Informatika",
        "classroom": "Kod va Reyting",
        "course": "Leaderboard bilan faollikni oshirish",
        "quiz": "Leaderboard strategiyalari testi",
        "school": "Raqamli texnologiyalar litseyi",
        "teacher_name": ("Jahongir", "Rasulov"),
        "teacher_bio": "O'quvchilarni mini challenge va sprintlar bilan rag'batlantiradi.",
    },
    {
        "subject": "Fizika",
        "classroom": "Fizika Challenge",
        "course": "Challenge orqali kuch va harakat",
        "quiz": "Fizika challenge testi",
        "school": "Innovatsion fanlar maktabi",
        "teacher_name": ("Dilshod", "Ergashev"),
        "teacher_bio": "Qisqa topshiriqlar va sovrinli musobaqalarni darsga qo'shadi.",
    },
    {
        "subject": "Ingliz tili",
        "classroom": "English Quest",
        "course": "Quest asosida vocabulary o'rganish",
        "quiz": "English quest testi",
        "school": "Xalqaro tillar markazi",
        "teacher_name": ("Madina", "Yusupova"),
        "teacher_bio": "Vocabulary quest va badge'lar bilan doimiy mashq hosil qiladi.",
    },
    {
        "subject": "Biologiya",
        "classroom": "Bio Explorer",
        "course": "Missiyalar orqali biologiya",
        "quiz": "Biologik missiyalar testi",
        "school": "Tabiiy fanlar gimnaziyasi",
        "teacher_name": ("Umida", "Hakimova"),
        "teacher_bio": "Darsni missiya va bosqichlarga bo'lib, qiziqishni ushlab turadi.",
    },
]

LESSON_TYPES = ["text", "video", "interactive"]

BADGE_DEFINITIONS = [
    ("Birinchi qadam", "Dastlabki darsni yakunlaganlar uchun", "lesson", "count", 1, 5, 2, "common"),
    ("Bilim ovchisi", "5 ta testni muvaffaqiyatli topshirganlar uchun", "quiz", "count", 5, 15, 5, "rare"),
    ("Streak qahramoni", "7 kun ketma-ket faollik uchun", "streak", "streak", 7, 20, 8, "epic"),
    ("Sinf yetakchisi", "Guruh ichida faol ishtirok etganlar uchun", "social", "custom", 1, 25, 10, "rare"),
    ("Gamifikator", "Bir nechta challenge va badge to'plaganlar uchun", "special", "custom", 1, 50, 20, "legendary"),
]

LEVEL_TITLES = [
    (1, "Yangi ishtirokchi", 0, 99),
    (2, "Faol o'quvchi", 100, 249),
    (3, "Topshiriq ustasi", 250, 499),
    (4, "Challenge chempioni", 500, 999),
    (5, "Gamifikatsiya qahramoni", 1000, 999999),
]


class Command(BaseCommand):
    help = (
        "Asosiy demo ma'lumotlarni yaratadi: foydalanuvchilar, sinfxonalar, "
        "kurslar, darslar, testlar, badge va level title lar."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Yaratiladigan asosiy to'plamlar soni. Default: 5",
        )
        parser.add_argument(
            "--password",
            default="DemoPass123!",
            help="Demo foydalanuvchilar uchun boshlang'ich parol.",
        )
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Mavjud demo user lar parolini ham qayta o'rnatadi.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = max(1, min(options["count"], len(TOPIC_PACKS)))
        password = options["password"]
        reset_passwords = options["reset_passwords"]
        now = timezone.now()

        created_counts = {
            "teachers": 0,
            "parents": 0,
            "students": 0,
            "classrooms": 0,
            "enrollments": 0,
            "courses": 0,
            "lessons": 0,
            "quizzes": 0,
            "questions": 0,
            "choices": 0,
            "invitations": 0,
            "badges": 0,
            "level_titles": 0,
        }

        parents = []
        students = []
        teachers = []

        for index in range(1, count + 1):
            parent, created = self._upsert_user(
                username=f"demoparent{index}",
                email=f"demoparent{index}@example.com",
                password=password,
                role=UserRole.PARENT,
                first_name=f"Otaona {index}",
                last_name="Demo",
                phone=f"+998901000{index:02d}",
                bio="Farzandining ta'lim jarayonini kuzatib boruvchi demo foydalanuvchi.",
                reset_passwords=reset_passwords,
            )
            parents.append(parent)
            if created:
                created_counts["parents"] += 1

        for index in range(1, count + 1):
            topic = TOPIC_PACKS[index - 1]
            teacher, created = self._upsert_user(
                username=f"demoteacher{index}",
                email=f"demoteacher{index}@example.com",
                password=password,
                role=UserRole.TEACHER,
                first_name=topic["teacher_name"][0],
                last_name=topic["teacher_name"][1],
                phone=f"+998971000{index:02d}",
                bio=topic["teacher_bio"],
                reset_passwords=reset_passwords,
            )
            TeacherProfile.objects.update_or_create(
                user=teacher,
                defaults={
                    "subject_expertise": topic["subject"],
                    "school": topic["school"],
                    "is_verified": True,
                },
            )
            teachers.append(teacher)
            if created:
                created_counts["teachers"] += 1

        for index in range(1, count + 1):
            student, created = self._upsert_user(
                username=f"demostudent{index}",
                email=f"demostudent{index}@example.com",
                password=password,
                role=UserRole.STUDENT,
                first_name=f"O'quvchi {index}",
                last_name="Demo",
                phone=f"+998931000{index:02d}",
                bio="Gamifikatsiya ilovasi uchun demo o'quvchi.",
                parent=parents[(index - 1) % len(parents)],
                reset_passwords=reset_passwords,
            )
            StudentProfile.objects.get_or_create(user=student)
            students.append(student)
            if created:
                created_counts["students"] += 1

        classrooms = []
        for index in range(1, count + 1):
            topic = TOPIC_PACKS[index - 1]
            teacher = teachers[index - 1]
            classroom, created = Classroom.objects.get_or_create(
                name=topic["classroom"],
                teacher=teacher,
                defaults={
                    "subject": topic["subject"],
                    "description": (
                        f"{topic['subject']} fanida gamifikatsiya elementlari asosida "
                        "raqobat va rag'batlantirish muhitini yaratish uchun demo sinf."
                    ),
                    "academic_year": "2025-2026",
                    "is_active": True,
                    "max_students": 30,
                },
            )
            classrooms.append(classroom)
            if created:
                created_counts["classrooms"] += 1

            invitation, invitation_created = ClassroomInvitation.objects.update_or_create(
                classroom=classroom,
                code=f"CLS{index:05d}",
                defaults={
                    "created_by": teacher,
                    "expires_at": now + timedelta(days=90),
                    "max_uses": 25,
                    "use_count": 0,
                    "is_active": True,
                },
            )
            if invitation_created:
                created_counts["invitations"] += 1

        for student_index, student in enumerate(students):
            for offset in range(2):
                classroom = classrooms[(student_index + offset) % len(classrooms)]
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    classroom=classroom,
                    defaults={"is_active": True, "is_approved": True},
                )
                if not created and (not enrollment.is_active or not enrollment.is_approved):
                    enrollment.is_active = True
                    enrollment.is_approved = True
                    enrollment.save(update_fields=["is_active", "is_approved"])
                if created:
                    created_counts["enrollments"] += 1

        for teacher in teachers:
            unique_students = (
                User.objects.filter(
                    enrollments__classroom__teacher=teacher,
                    enrollments__is_active=True,
                    role=UserRole.STUDENT,
                )
                .distinct()
                .count()
            )
            TeacherProfile.objects.filter(user=teacher).update(total_students=unique_students)

        for index in range(1, count + 1):
            topic = TOPIC_PACKS[index - 1]
            classroom = classrooms[index - 1]
            teacher = classroom.teacher

            course, created = Course.objects.get_or_create(
                title=topic["course"],
                classroom=classroom,
                teacher=teacher,
                defaults={
                    "description": (
                        "Gamifikatsiya elementlarini dars jarayoniga qo'shish, "
                        "rag'batlantirish va sog'lom raqobatni boshqarish bo'yicha demo kurs."
                    ),
                    "order": index,
                    "is_published": True,
                    "xp_reward": 25,
                    "coin_reward": 10,
                },
            )
            if created:
                created_counts["courses"] += 1

            for lesson_order in range(1, count + 1):
                lesson, lesson_created = Lesson.objects.get_or_create(
                    course=course,
                    order=lesson_order,
                    defaults={
                        "title": f"{topic['subject']} darsi {lesson_order}",
                        "content": (
                            f"{topic['subject']} fanida gamifikatsiya asosida {lesson_order}-mavzu. "
                            "Unda badge, ball, reyting va challenge usullari ishlatiladi."
                        ),
                        "lesson_type": LESSON_TYPES[(lesson_order - 1) % len(LESSON_TYPES)],
                        "duration_minutes": 12 + lesson_order,
                        "xp_reward": 5 + lesson_order,
                        "coin_reward": 2 + (lesson_order % 3),
                        "is_published": True,
                    },
                )
                if lesson_created:
                    created_counts["lessons"] += 1

            quiz, quiz_created = Quiz.objects.get_or_create(
                title=topic["quiz"],
                classroom=classroom,
                created_by=teacher,
                defaults={
                    "course": course,
                    "description": (
                        "Gamifikatsiya elementlari bo'yicha tayyorlangan demo test. "
                        "O'quvchi ball, badge va challenge tushunchalarini mustahkamlaydi."
                    ),
                    "quiz_type": "practice",
                    "time_limit_seconds": 900,
                    "max_attempts": 3,
                    "pass_percentage": 60,
                    "xp_reward": 20,
                    "coin_reward": 8,
                    "is_active": True,
                    "show_answers": True,
                    "available_from": now - timedelta(days=1),
                    "available_until": now + timedelta(days=120),
                },
            )
            if quiz_created:
                created_counts["quizzes"] += 1

            for question_order in range(1, count + 1):
                question, question_created = Question.objects.get_or_create(
                    quiz=quiz,
                    order=question_order,
                    defaults={
                        "question_text": (
                            f"{topic['subject']} darsida {question_order}-savol: "
                            "qaysi gamifikatsiya elementi o'quvchini ko'proq rag'batlantiradi?"
                        ),
                        "question_type": "multiple_choice",
                        "difficulty": "medium",
                        "points": 2,
                        "explanation": (
                            "To'g'ri javob o'quvchini rag'batlantirish, kuzatish va "
                            "qayta aloqa berishga yordam beradigan elementni tanlaydi."
                        ),
                        "is_active": True,
                    },
                )
                if question_created:
                    created_counts["questions"] += 1

                choices = [
                    ("Badge va ball tizimi", True),
                    ("Qiziqarsiz bir xil topshiriqlar", False),
                    ("Hech qanday fikr bildirmaslik", False),
                    ("Faollikni umuman baholamaslik", False),
                ]
                for choice_order, (choice_text, is_correct) in enumerate(choices, start=1):
                    _, choice_created = AnswerChoice.objects.get_or_create(
                        question=question,
                        order=choice_order,
                        defaults={
                            "choice_text": choice_text,
                            "is_correct": is_correct,
                        },
                    )
                    if choice_created:
                        created_counts["choices"] += 1

        for badge_index, definition in enumerate(BADGE_DEFINITIONS[:count], start=1):
            _, badge_created = Badge.objects.get_or_create(
                name=definition[0],
                defaults={
                    "description": definition[1],
                    "badge_type": definition[2],
                    "condition_type": definition[3],
                    "condition_value": definition[4],
                    "xp_bonus": definition[5],
                    "coin_bonus": definition[6],
                    "rarity": definition[7],
                    "is_active": True,
                },
            )
            if badge_created:
                created_counts["badges"] += 1

        for level, title, min_xp, max_xp in LEVEL_TITLES[:count]:
            _, level_created = LevelTitle.objects.get_or_create(
                level=level,
                defaults={
                    "title": title,
                    "min_xp": min_xp,
                    "max_xp": max_xp,
                },
            )
            if level_created:
                created_counts["level_titles"] += 1

        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar tayyor bo'ldi."))
        self.stdout.write(
            "Demo user paroli: "
            + self.style.WARNING(password)
            + "  (yaratilgan yoki reset qilingan userlar uchun)"
        )
        for key, value in created_counts.items():
            self.stdout.write(f"- {key}: {value}")

    def _upsert_user(
        self,
        *,
        username,
        email,
        password,
        role,
        first_name,
        last_name,
        phone,
        bio,
        reset_passwords,
        parent=None,
    ):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": role,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "bio": bio,
                "parent": parent,
            },
        )

        needs_save = False
        if user.email != email:
            user.email = email
            needs_save = True
        if user.role != role:
            user.role = role
            needs_save = True
        if user.first_name != first_name:
            user.first_name = first_name
            needs_save = True
        if user.last_name != last_name:
            user.last_name = last_name
            needs_save = True
        if user.phone != phone:
            user.phone = phone
            needs_save = True
        if user.bio != bio:
            user.bio = bio
            needs_save = True
        if user.parent != parent:
            user.parent = parent
            needs_save = True

        if created or reset_passwords:
            user.set_password(password)
            needs_save = True

        if needs_save:
            user.save()

        return user, created
