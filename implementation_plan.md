# 🎮 EduGame — Gamifikatsiya Asosidagi Ta'lim Platformasi
## Implementation Plan v1.0

**Loyiha nomi:** EduGame  
**Stack:** Flutter (Mobile) + Django REST Framework (Backend)  
**Maqsad:** Dars jarayonida gamifikatsiya elementlari orqali raqobat va rag'batlantirish muhitini yaratish  
**Litsenziya:** MIT Open Source  

---

## 📋 MUNDARIJA

1. [Loyiha Arxitekturasi](#arxitektura)
2. [Database Schema](#database)
3. [Backend — Django API](#backend)
4. [Mobile — Flutter App](#flutter)
5. [Gamifikatsiya Logikasi](#gamification)
6. [Real-time Tizim](#realtime)
7. [Xavfsizlik](#security)
8. [Deployment](#deployment)
9. [Sprint Rejasi](#sprints)
10. [Fayl Tuzilmasi](#structure)

---

## 1. LOYIHA ARXITEKTURASI {#arxitektura}

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                              │
│   Flutter App (iOS/Android)    Admin Panel (Web)            │
└───────────────────┬────────────────────────┬────────────────┘
                    │ HTTPS/WSS              │ HTTPS
┌───────────────────▼────────────────────────▼────────────────┐
│                     NGINX (Reverse Proxy)                    │
└───────────────────┬────────────────────────┬────────────────┘
                    │                        │
       ┌────────────▼──────────┐  ┌──────────▼──────────────┐
       │   Django REST API     │  │   Django Channels       │
       │   (Gunicorn)          │  │   (Daphne / ASGI)       │
       └────────────┬──────────┘  └──────────┬──────────────┘
                    │                        │
       ┌────────────▼────────────────────────▼──────────────┐
       │              Django Application Layer               │
       │  users │ courses │ quizzes │ gamification │ chat   │
       └────────────┬────────────────────────┬──────────────┘
                    │                        │
          ┌─────────▼──────────┐   ┌────────▼──────────┐
          │    PostgreSQL      │   │      Redis         │
          │  (Main Database)   │   │  (Cache/Channels)  │
          └────────────────────┘   └───────────────────┘
                    │
          ┌─────────▼──────────┐
          │  AWS S3 / Cloudinary│
          │  (Media Files)      │
          └────────────────────┘
```

---

## 2. DATABASE SCHEMA {#database}

### 2.1 Users & Roles

```sql
-- Foydalanuvchi modeli
Table: users_customuser
├── id (UUID, PK)
├── username (VARCHAR 150, UNIQUE)
├── email (VARCHAR 254, UNIQUE)
├── password (VARCHAR 128)
├── role (ENUM: student | teacher | parent | admin)
├── avatar (VARCHAR - image URL)
├── date_of_birth (DATE, nullable)
├── is_active (BOOLEAN, default: true)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- O'quvchi profili
Table: users_studentprofile
├── id (UUID, PK)
├── user_id (FK → users_customuser)
├── xp_points (INTEGER, default: 0)
├── level (INTEGER, default: 1)
├── coins (INTEGER, default: 0)       -- virtual valyuta
├── streak_days (INTEGER, default: 0)
├── last_activity (DATE)
├── total_quizzes_completed (INTEGER, default: 0)
├── total_correct_answers (INTEGER, default: 0)
└── rank_position (INTEGER, nullable) -- global reyting

-- O'qituvchi profili
Table: users_teacherprofile
├── id (UUID, PK)
├── user_id (FK → users_customuser)
├── subject_expertise (VARCHAR 200)
├── school (VARCHAR 200)
└── total_students (INTEGER, default: 0)
```

### 2.2 Classroom & Courses

```sql
-- Sinf xonasi
Table: classroom_classroom
├── id (UUID, PK)
├── name (VARCHAR 100)
├── code (VARCHAR 10, UNIQUE) -- qo'shilish kodi
├── teacher_id (FK → users_customuser)
├── subject (VARCHAR 100)
├── academic_year (VARCHAR 9)  -- "2024-2025"
├── is_active (BOOLEAN, default: true)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

-- Sinf a'zolari
Table: classroom_enrollment
├── id (UUID, PK)
├── student_id (FK → users_customuser)
├── classroom_id (FK → classroom_classroom)
├── joined_at (TIMESTAMP)
└── is_active (BOOLEAN, default: true)

-- Fan
Table: courses_course
├── id (UUID, PK)
├── title (VARCHAR 200)
├── description (TEXT)
├── classroom_id (FK → classroom_classroom)
├── order (INTEGER)
├── is_published (BOOLEAN, default: false)
├── xp_reward (INTEGER, default: 10)
└── created_at (TIMESTAMP)

-- Dars
Table: courses_lesson
├── id (UUID, PK)
├── course_id (FK → courses_course)
├── title (VARCHAR 200)
├── content (TEXT)             -- HTML/Markdown
├── lesson_type (ENUM: text | video | interactive)
├── video_url (VARCHAR 500, nullable)
├── duration_minutes (INTEGER, default: 10)
├── order (INTEGER)
├── xp_reward (INTEGER, default: 5)
└── is_published (BOOLEAN, default: false)

-- O'quvchi dars progressi
Table: courses_lessonprogress
├── id (UUID, PK)
├── student_id (FK → users_customuser)
├── lesson_id (FK → courses_lesson)
├── is_completed (BOOLEAN, default: false)
├── time_spent_seconds (INTEGER, default: 0)
├── completed_at (TIMESTAMP, nullable)
└── created_at (TIMESTAMP)
```

### 2.3 Quiz & Assessment

```sql
-- Test
Table: quizzes_quiz
├── id (UUID, PK)
├── title (VARCHAR 200)
├── course_id (FK → courses_course, nullable)
├── classroom_id (FK → classroom_classroom)
├── quiz_type (ENUM: practice | exam | challenge | tournament)
├── time_limit_seconds (INTEGER, nullable)  -- null = cheksiz vaqt
├── max_attempts (INTEGER, default: 3)
├── pass_percentage (INTEGER, default: 60)
├── xp_reward (INTEGER, default: 20)
├── coin_reward (INTEGER, default: 10)
├── is_active (BOOLEAN, default: true)
├── available_from (TIMESTAMP, nullable)
├── available_until (TIMESTAMP, nullable)
└── created_by (FK → users_customuser)

-- Savol
Table: quizzes_question
├── id (UUID, PK)
├── quiz_id (FK → quizzes_quiz)
├── question_text (TEXT)
├── question_type (ENUM: multiple_choice | true_false | short_answer | matching | ordering)
├── image (VARCHAR, nullable)
├── difficulty (ENUM: easy | medium | hard)
├── points (INTEGER, default: 1)
├── time_limit_seconds (INTEGER, nullable)  -- per-question timer
├── explanation (TEXT, nullable)            -- javob izohi
└── order (INTEGER)

-- Javob varianti
Table: quizzes_answerchoice
├── id (UUID, PK)
├── question_id (FK → quizzes_question)
├── choice_text (VARCHAR 500)
├── is_correct (BOOLEAN)
└── order (INTEGER)

-- O'quvchi test urinishi
Table: quizzes_quizattempt
├── id (UUID, PK)
├── student_id (FK → users_customuser)
├── quiz_id (FK → quizzes_quiz)
├── attempt_number (INTEGER)
├── score (FLOAT, default: 0)
├── total_points (INTEGER)
├── earned_points (INTEGER)
├── percentage (FLOAT)
├── is_passed (BOOLEAN)
├── time_taken_seconds (INTEGER)
├── started_at (TIMESTAMP)
├── completed_at (TIMESTAMP, nullable)
└── xp_earned (INTEGER, default: 0)

-- O'quvchi berilgan javob
Table: quizzes_studentanswer
├── id (UUID, PK)
├── attempt_id (FK → quizzes_quizattempt)
├── question_id (FK → quizzes_question)
├── selected_choice_id (FK → quizzes_answerchoice, nullable)
├── text_answer (TEXT, nullable)
├── is_correct (BOOLEAN)
├── points_earned (INTEGER, default: 0)
└── time_taken_seconds (INTEGER, nullable)
```

### 2.4 Gamification

```sql
-- Badge/Yutuq turi
Table: gamification_badge
├── id (UUID, PK)
├── name (VARCHAR 100)
├── description (TEXT)
├── icon (VARCHAR)            -- image URL
├── badge_type (ENUM: streak | quiz | lesson | social | special)
├── condition_type (ENUM: count | streak | percentage | custom)
├── condition_value (INTEGER)  -- masalan: 10 (10 ta quiz yechish)
├── xp_bonus (INTEGER, default: 0)
└── rarity (ENUM: common | rare | epic | legendary)

-- O'quvchi olgan badge
Table: gamification_userbadge
├── id (UUID, PK)
├── student_id (FK → users_customuser)
├── badge_id (FK → gamification_badge)
├── earned_at (TIMESTAMP)
└── is_displayed (BOOLEAN, default: true)

-- XP Tranzaksiyalari (audit log)
Table: gamification_xptransaction
├── id (UUID, PK)
├── student_id (FK → users_customuser)
├── amount (INTEGER)               -- musbat yoki manfiy
├── transaction_type (ENUM: quiz_complete | lesson_complete | badge_earn | streak_bonus | challenge_win | daily_bonus | penalty)
├── description (VARCHAR 200)
├── related_object_id (UUID, nullable)
├── related_object_type (VARCHAR 50, nullable)
└── created_at (TIMESTAMP)

-- Leaderboard (Redis'dan sinxron qilinadi)
Table: gamification_leaderboardentry
├── id (UUID, PK)
├── student_id (FK → users_customuser)
├── classroom_id (FK → classroom_classroom, nullable)
├── period (ENUM: daily | weekly | monthly | all_time)
├── xp_points (INTEGER)
├── rank_position (INTEGER)
└── updated_at (TIMESTAMP)

-- Daily Streak
Table: gamification_streak
├── id (UUID, PK)
├── student_id (FK → users_customuser, UNIQUE)
├── current_streak (INTEGER, default: 0)
├── longest_streak (INTEGER, default: 0)
├── last_activity_date (DATE)
└── streak_freeze_count (INTEGER, default: 0)  -- streak'ni himoya qilish
```

### 2.5 Competition

```sql
-- Musobaqa/Turnir
Table: competition_tournament
├── id (UUID, PK)
├── title (VARCHAR 200)
├── classroom_id (FK → classroom_classroom)
├── quiz_id (FK → quizzes_quiz)
├── tournament_type (ENUM: single_elimination | round_robin | time_attack)
├── max_participants (INTEGER, nullable)
├── status (ENUM: upcoming | active | finished | cancelled)
├── start_time (TIMESTAMP)
├── end_time (TIMESTAMP)
├── first_prize_xp (INTEGER, default: 100)
├── second_prize_xp (INTEGER, default: 50)
├── third_prize_xp (INTEGER, default: 25)
└── created_by (FK → users_customuser)

-- Turnir ishtirokchisi
Table: competition_tournamentparticipant
├── id (UUID, PK)
├── tournament_id (FK → competition_tournament)
├── student_id (FK → users_customuser)
├── score (FLOAT, default: 0)
├── rank_position (INTEGER, nullable)
├── registered_at (TIMESTAMP)
└── is_active (BOOLEAN, default: true)

-- 1v1 Challenge
Table: competition_challenge
├── id (UUID, PK)
├── challenger_id (FK → users_customuser)
├── opponent_id (FK → users_customuser)
├── quiz_id (FK → quizzes_quiz)
├── status (ENUM: pending | accepted | in_progress | completed | declined | expired)
├── challenger_score (FLOAT, nullable)
├── opponent_score (FLOAT, nullable)
├── winner_id (FK → users_customuser, nullable)
├── xp_stake (INTEGER, default: 10)  -- g'olib oladigan XP
├── expires_at (TIMESTAMP)
└── created_at (TIMESTAMP)
```

### 2.6 Notifications

```sql
Table: notifications_notification
├── id (UUID, PK)
├── recipient_id (FK → users_customuser)
├── notification_type (ENUM: badge_earned | level_up | challenge_received | tournament_start | rank_changed | streak_reminder | quiz_result)
├── title (VARCHAR 200)
├── message (TEXT)
├── data (JSONB, nullable)      -- qo'shimcha ma'lumotlar
├── is_read (BOOLEAN, default: false)
├── is_sent_push (BOOLEAN, default: false)
└── created_at (TIMESTAMP)
```

---

## 3. BACKEND — DJANGO API {#backend}

### 3.1 Loyiha Tuzilmasi

```
edugame_backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   └── tests.py
│   ├── classroom/
│   ├── courses/
│   ├── quizzes/
│   ├── gamification/
│   │   ├── models.py
│   │   ├── services.py      ← Asosiy biznes logika
│   │   ├── signals.py       ← Badge trigger'lari
│   │   ├── tasks.py         ← Celery async tasks
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── competition/
│   ├── notifications/
│   │   ├── models.py
│   │   ├── services.py
│   │   └── fcm.py          ← Firebase push notification
│   └── chat/
│       ├── consumers.py     ← WebSocket consumer
│       ├── routing.py
│       └── models.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

### 3.2 Asosiy API Endpointlar

#### Authentication
```
POST   /api/v1/auth/register/           → Ro'yxatdan o'tish
POST   /api/v1/auth/login/              → Kirish (JWT token olish)
POST   /api/v1/auth/refresh/            → Token yangilash
POST   /api/v1/auth/logout/             → Chiqish
POST   /api/v1/auth/password-reset/     → Parol tiklash
GET    /api/v1/auth/me/                 → Joriy foydalanuvchi
```

#### Users & Profiles
```
GET    /api/v1/users/profile/           → Profil ko'rish
PATCH  /api/v1/users/profile/           → Profil tahrirlash
POST   /api/v1/users/avatar/            → Avatar yuklash
GET    /api/v1/users/{id}/public/       → Boshqa o'quvchi profili
```

#### Classroom
```
POST   /api/v1/classrooms/              → Sinf yaratish (teacher)
GET    /api/v1/classrooms/              → Sinflar ro'yxati
GET    /api/v1/classrooms/{id}/         → Sinf detali
POST   /api/v1/classrooms/join/         → Sinfga qo'shilish (code bilan)
GET    /api/v1/classrooms/{id}/students/→ Sinf o'quvchilari
DELETE /api/v1/classrooms/{id}/leave/   → Sinfdan chiqish
```

#### Courses & Lessons
```
GET    /api/v1/classrooms/{id}/courses/ → Sinfning kursları
POST   /api/v1/courses/                 → Kurs yaratish
GET    /api/v1/courses/{id}/            → Kurs detali
GET    /api/v1/courses/{id}/lessons/    → Kurs darslari
POST   /api/v1/lessons/{id}/complete/   → Darsni tugatish
GET    /api/v1/lessons/{id}/progress/   → Progress ko'rish
```

#### Quizzes
```
GET    /api/v1/quizzes/                 → Testlar ro'yxati
POST   /api/v1/quizzes/                 → Test yaratish (teacher)
GET    /api/v1/quizzes/{id}/            → Test detali
POST   /api/v1/quizzes/{id}/start/      → Testni boshlash
POST   /api/v1/quizzes/{id}/submit/     → Javoblarni topshirish
GET    /api/v1/quizzes/{id}/results/    → Natijalar
GET    /api/v1/quizzes/{id}/leaderboard/→ Test reytingi
```

#### Gamification
```
GET    /api/v1/gamification/profile/           → XP, level, coin, streak
GET    /api/v1/gamification/badges/            → Barcha badge'lar
GET    /api/v1/gamification/badges/earned/     → Olingan badge'lar
GET    /api/v1/gamification/leaderboard/       → Global reyting
GET    /api/v1/gamification/leaderboard/class/ → Sinf reytingi
GET    /api/v1/gamification/xp-history/        → XP tarixi
POST   /api/v1/gamification/daily-bonus/       → Kunlik bonus olish
GET    /api/v1/gamification/streak/            → Streak holati
```

#### Competition
```
POST   /api/v1/challenges/                  → Challenge yuborish
GET    /api/v1/challenges/                  → Kelgan challengelar
POST   /api/v1/challenges/{id}/accept/      → Challengeni qabul qilish
POST   /api/v1/challenges/{id}/decline/     → Challengeni rad etish
GET    /api/v1/tournaments/                 → Turnirlar ro'yxati
POST   /api/v1/tournaments/                 → Turnir yaratish (teacher)
POST   /api/v1/tournaments/{id}/join/       → Turnirga qo'shilish
GET    /api/v1/tournaments/{id}/standings/  → Turnir jadvali
```

#### Notifications
```
GET    /api/v1/notifications/          → Bildirishnomalar
PATCH  /api/v1/notifications/{id}/read/→ O'qilgan deb belgilash
PATCH  /api/v1/notifications/read-all/ → Barchasini o'qilgan qilish
POST   /api/v1/notifications/fcm-token/→ FCM token saqlash
```

### 3.3 Gamification Service (Asosiy Logika)

```python
# apps/gamification/services.py

class GamificationService:
    
    # XP berish
    @staticmethod
    def award_xp(student_id, amount, transaction_type, description, related_id=None):
        """
        1. XPTransaction yaratadi
        2. StudentProfile.xp_points yangilaydi
        3. Level tekshiradi → level_up bo'lsa trigger
        4. Leaderboard yangilaydi (Redis)
        5. Badge tekshiradi
        """
    
    # Level hisoblash
    @staticmethod
    def calculate_level(total_xp):
        """
        Level formula: level = floor(sqrt(total_xp / 100)) + 1
        Level 1:     0    XP
        Level 2:     100  XP
        Level 5:     1600 XP
        Level 10:    8100 XP
        Level 20:    36100 XP
        """
    
    # Streak yangilash
    @staticmethod
    def update_streak(student_id):
        """
        1. last_activity_date ni tekshiradi
        2. Bugun faollik bo'lganmi?
        3. Kecha faollik bo'lganmi? → streak davom etadi
        4. Ikki kun bo'ldimi? → streak reset (agar freeze yo'q)
        5. Streak milestone'larda bonus XP beradi
        """
    
    # Badge tekshirish
    @staticmethod
    def check_and_award_badges(student_id, event_type, context=None):
        """
        Badge condition'larini tekshiradi va award qiladi
        event_type: 'quiz_completed', 'lesson_completed', 'streak_updated', etc.
        """
    
    # Leaderboard yangilash (Redis sorted set)
    @staticmethod
    def update_leaderboard(student_id, xp_amount):
        """
        Redis ZADD orqali leaderboard yangilaydi
        Har bir period uchun alohida key:
        - leaderboard:all_time
        - leaderboard:weekly:{week_number}
        - leaderboard:daily:{date}
        - leaderboard:class:{classroom_id}:weekly
        """
```

### 3.4 WebSocket (Real-time)

```python
# apps/chat/consumers.py

# WebSocket URL patterns:
# ws://domain/ws/classroom/{classroom_id}/     → Sinf chati
# ws://domain/ws/quiz/{quiz_id}/live/           → Live quiz natijalar
# ws://domain/ws/tournament/{tournament_id}/    → Turnir real-time
# ws://domain/ws/notifications/                 → Push notifications

# Channels groups:
# classroom_{id}       → Sinfxona xabarlari
# quiz_live_{id}       → Live quiz leaderboard
# tournament_{id}      → Turnir yangilanishlari
# user_{id}            → Shaxsiy bildirishnomalar
```

### 3.5 Requirements

```txt
# requirements/base.txt
Django==4.2.x
djangorestframework==3.14.x
djangorestframework-simplejwt==5.3.x
django-channels==4.0.x
channels-redis==4.1.x
celery==5.3.x
redis==5.0.x
psycopg2-binary==2.9.x
django-cors-headers==4.3.x
Pillow==10.x
boto3==1.34.x              # AWS S3
firebase-admin==6.4.x      # FCM Push notifications
django-filter==23.x
drf-spectacular==0.27.x    # API dokumentatsiya (Swagger)
```

---

## 4. FLUTTER APP {#flutter}

### 4.1 Loyiha Tuzilmasi

```
edugame_flutter/
├── lib/
│   ├── main.dart
│   ├── core/
│   │   ├── constants/
│   │   │   ├── app_colors.dart
│   │   │   ├── app_strings.dart
│   │   │   └── app_assets.dart
│   │   ├── network/
│   │   │   ├── api_client.dart        ← Dio HTTP client
│   │   │   ├── api_endpoints.dart
│   │   │   └── interceptors/
│   │   │       ├── auth_interceptor.dart
│   │   │       └── error_interceptor.dart
│   │   ├── storage/
│   │   │   └── secure_storage.dart    ← JWT token saqlash
│   │   ├── websocket/
│   │   │   └── ws_client.dart
│   │   └── utils/
│   │       ├── validators.dart
│   │       └── formatters.dart
│   ├── features/
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── models/
│   │   │   │   └── repositories/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   └── usecases/
│   │   │   └── presentation/
│   │   │       ├── bloc/              ← State management
│   │   │       ├── pages/
│   │   │       │   ├── login_page.dart
│   │   │       │   └── register_page.dart
│   │   │       └── widgets/
│   │   ├── dashboard/
│   │   ├── courses/
│   │   ├── quiz/
│   │   │   └── presentation/
│   │   │       ├── pages/
│   │   │       │   ├── quiz_list_page.dart
│   │   │       │   ├── quiz_play_page.dart   ← Asosiy o'yin ekrani
│   │   │       │   └── quiz_result_page.dart
│   │   │       └── widgets/
│   │   │           ├── question_card.dart
│   │   │           ├── timer_widget.dart
│   │   │           └── answer_option.dart
│   │   ├── gamification/
│   │   │   └── presentation/
│   │   │       ├── pages/
│   │   │       │   ├── leaderboard_page.dart
│   │   │       │   ├── badges_page.dart
│   │   │       │   └── xp_history_page.dart
│   │   │       └── widgets/
│   │   │           ├── xp_bar_widget.dart
│   │   │           ├── level_badge_widget.dart
│   │   │           ├── streak_widget.dart
│   │   │           └── achievement_popup.dart ← Level up animatsiya
│   │   ├── competition/
│   │   │   └── presentation/
│   │   │       ├── pages/
│   │   │       │   ├── tournament_page.dart
│   │   │       │   └── challenge_page.dart
│   │   │       └── widgets/
│   │   │           └── live_leaderboard.dart  ← WebSocket bilan
│   │   ├── profile/
│   │   └── notifications/
│   └── shared/
│       ├── widgets/
│       │   ├── app_button.dart
│       │   ├── app_text_field.dart
│       │   ├── loading_widget.dart
│       │   └── error_widget.dart
│       └── theme/
│           ├── app_theme.dart
│           └── text_styles.dart
├── assets/
│   ├── images/
│   ├── animations/           ← Lottie JSON fayllar
│   │   ├── level_up.json
│   │   ├── badge_earned.json
│   │   ├── confetti.json
│   │   └── streak_fire.json
│   └── sounds/               ← Ovoz effektlari
│       ├── correct_answer.mp3
│       ├── wrong_answer.mp3
│       └── level_up.mp3
├── pubspec.yaml
└── README.md
```

### 4.2 Asosiy Packagelar

```yaml
# pubspec.yaml

dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5
  
  # Network
  dio: ^5.4.0
  web_socket_channel: ^2.4.0
  
  # Local Storage
  flutter_secure_storage: ^9.0.0
  shared_preferences: ^2.2.2
  hive_flutter: ^1.1.0        # Offline cache
  
  # UI/Animations
  lottie: ^3.0.0              # Lottie animatsiyalar
  flutter_animate: ^4.5.0     # Micro-animatsiyalar
  confetti: ^0.7.0            # Konfetti effekti
  fl_chart: ^0.67.0           # Statistika grafiklari
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0             # Loading skeleton
  
  # Firebase
  firebase_core: ^2.27.0
  firebase_messaging: ^14.7.19  # Push notifications
  
  # Audio
  audioplayers: ^6.0.0        # Ovoz effektlari
  
  # Utils
  intl: ^0.19.0
  timeago: ^3.6.0
  get_it: ^7.6.7              # Dependency injection
  auto_route: ^8.1.0          # Navigation
```

### 4.3 Ekranlar Tavsifi

#### Dashboard (Bosh ekran)
```
┌─────────────────────────────────┐
│  👋 Salom, Alisher!             │
│  🔥 15 kunlik streak            │
├─────────────────────────────────┤
│  ⭐ 2,450 XP  |  Lv.8          │
│  ████████░░ 80%                 │
├─────────────────────────────────┤
│  📋 BUGUNGI VAZIFALAR           │
│  ✅ 1 dars o'qi     (+5 XP)    │
│  ⬜ 1 test yech     (+20 XP)   │
│  ⬜ Do'stga challenge (+5 XP)  │
├─────────────────────────────────┤
│  🏆 REYTING (Sinf)              │
│  🥇 Bobur     3,200 XP         │
│  🥈 Siz       2,450 XP  ←      │
│  🥉 Malika    2,100 XP         │
└─────────────────────────────────┘
```

#### Quiz O'yin Ekrani
```
┌─────────────────────────────────┐
│  Savol 3/10        ⏱ 00:18     │
│  ━━━━━━━━░░░░░░░░░░░            │
├─────────────────────────────────┤
│                                 │
│  Quyidagi qaysi son tub son?    │
│                                 │
├─────────────────────────────────┤
│  🅐  12                         │
│  🅑  17  ← (tanlangan)         │
│  🅒  21                         │
│  🅓  25                         │
├─────────────────────────────────┤
│        [ KEYINGISI → ]          │
└─────────────────────────────────┘
```

---

## 5. GAMIFIKATSIYA LOGIKASI {#gamification}

### 5.1 XP Tizimi

| Harakat | XP |
|---|---|
| Dars o'qish | +5 |
| Test topshirish (60-79%) | +10 |
| Test topshirish (80-99%) | +20 |
| Test topshirish (100%) | +50 |
| Kunlik kirish | +3 |
| 7 kunlik streak | +25 bonus |
| 30 kunlik streak | +100 bonus |
| Challenge g'alaba | +30 |
| Turnir 1-o'rin | +200 |
| Turnir 2-o'rin | +100 |
| Turnir 3-o'rin | +50 |
| Do'stni taklif qilish | +20 |

### 5.2 Level Tizimi

| Level | Kerakli XP | Unvon |
|---|---|---|
| 1 | 0 | Yangi Talaba |
| 2 | 100 | Izlovchi |
| 3 | 400 | O'rganuvchi |
| 5 | 1,600 | Bilimdon |
| 8 | 6,400 | Ustoz Shogird |
| 10 | 10,000 | Bilim Masteri |
| 15 | 22,500 | Ilm Elchisi |
| 20 | 40,000 | Akademik |
| 30 | 90,000 | Grand Master |

### 5.3 Badge Tizimi

```
STREAK BADGE'LAR:
├── 🔥 "3 kunlik olov"          → 3 kun streak
├── 🔥🔥 "Haftalik jasorat"     → 7 kun streak
├── 🔥🔥🔥 "Oylik qahramonlik" → 30 kun streak
└── 💎 "Temir iroda"            → 100 kun streak

QUIZ BADGE'LAR:
├── ⚡ "Birinchi qadam"          → 1 ta test
├── 🎯 "Aniq nishot"            → 10 ta test 100% bilan
├── 🏃 "Tez muqim"              → 50 ta test yechdi
└── 🧠 "Bilim quyoshi"          → 500 ta test yechdi

ACADEMIC BADGE'LAR:
├── 📚 "O'quvchi"               → 10 dars o'qidi
├── 🎓 "Kurs yakunlovchi"       → 1 ta kursni tugatdi
└── 🌟 "Fanda ustun"            → Sinfda 1-o'rin 1 hafta

IJTIMOIY BADGE'LAR:
├── 🤝 "Do'stona"               → 1 ta challenge g'alaba
├── ⚔️ "Jangchi"               → 10 ta challenge g'alaba
└── 🏆 "Chempion"               → Turnirda g'alaba
```

### 5.4 Kunlik Vazifalar Tizimi

```
Har kuni saat 00:00 da reset qilinadi (server vaqti)
O'quvchi ilovaga kirganida yangi vazifalar ko'rsatiladi

Vazifalar kategoriyasi:
1. O'qish vazifasi    → N ta darsni o'qi
2. Test vazifasi      → N ta test yech
3. Ijtimoiy vazifa    → Do'stga challenge yubor
4. Streak vazifasi    → Bugun ham kir (streak uzma)

Vazifani bajarilganda:
- XP beriladi
- Progress bar to'ladi
- Animatsiya ko'rsatiladi
- Agar barcha 4 ta vazifa bajarilsa → Kunlik jackpot (+50 XP)
```

---

## 6. REAL-TIME TIZIM {#realtime}

### 6.1 WebSocket Events

```json
// Client → Server: Quiz javob yuborish
{
  "type": "quiz.answer",
  "quiz_id": "uuid",
  "question_id": "uuid",
  "selected_choice_id": "uuid",
  "time_taken_seconds": 12
}

// Server → Client: Live leaderboard yangilanishi
{
  "type": "leaderboard.update",
  "data": [
    {"rank": 1, "name": "Bobur", "score": 85, "avatar": "url"},
    {"rank": 2, "name": "Siz", "score": 72, "avatar": "url"}
  ]
}

// Server → Client: Badge qozonildi
{
  "type": "badge.earned",
  "badge": {
    "name": "Tez muqim",
    "icon": "url",
    "xp_bonus": 50
  }
}

// Server → Client: Level oshdi
{
  "type": "level.up",
  "old_level": 7,
  "new_level": 8,
  "title": "Bilimdon"
}

// Server → Client: Challenge keldi
{
  "type": "challenge.received",
  "challenger": {"name": "Bobur", "avatar": "url", "level": 10},
  "quiz": {"title": "Matematika", "question_count": 5},
  "expires_in_seconds": 300
}
```

---

## 7. XAVFSIZLIK {#security}

### 7.1 Authentication
- JWT Access Token: 15 daqiqa amal qiladi
- JWT Refresh Token: 7 kun, HttpOnly cookie'da saqlanadi
- Token rotation: Har refresh'da yangi token
- Brute force himoya: Rate limiting (IP bo'yicha)

### 7.2 API Xavfsizlik
```python
# Rate Limiting (settings.py)
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'quiz_submit': '30/hour',   # Custom throttle
    }
}
```

### 7.3 Anti-Cheat (Quiz)
- Server tomonida vaqt tekshirish
- Duplicate submission bloklash
- Answer hashing (predictable ID'larni oldini olish)
- Attempt limit tekshirish

---

## 8. DEPLOYMENT {#deployment}

### 8.1 Docker Compose

```yaml
# docker-compose.yml
services:
  web:
    build: .
    ports: ["8000:8000"]
    depends_on: [db, redis]
    env_file: .env
  
  db:
    image: postgres:15
    volumes: [postgres_data:/var/lib/postgresql/data]
  
  redis:
    image: redis:7-alpine
  
  celery:
    build: .
    command: celery -A config worker -l info
    depends_on: [db, redis]
  
  celery-beat:
    build: .
    command: celery -A config beat -l info
    depends_on: [db, redis]
  
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    depends_on: [web]

volumes:
  postgres_data:
```

### 8.2 CI/CD (GitHub Actions)

```yaml
# .github/workflows/main.yml
on: [push to main]
jobs:
  test → lint → build → deploy
```

---

## 9. SPRINT REJASI {#sprints}

### Sprint 1 (2 hafta) — Foundation
- [ ] Django loyihasini sozlash (settings, auth, CORS)
- [ ] CustomUser modeli va JWT auth
- [ ] Flutter loyihasini sozlash (folder structure, theme)
- [ ] Login / Register ekranlari
- [ ] API client (Dio) sozlash

### Sprint 2 (2 hafta) — Classroom & Courses
- [ ] Classroom modeli va API
- [ ] Course va Lesson modeli va API
- [ ] Flutter: Sinfxona ekrani
- [ ] Flutter: Kurslar va darslar ekrani
- [ ] Lesson progress tracking

### Sprint 3 (2 hafta) — Quiz System
- [ ] Quiz, Question, AnswerChoice modellari
- [ ] Quiz attempt va scoring logikasi
- [ ] Flutter: Quiz o'yin ekrani (timer bilan)
- [ ] Flutter: Quiz natijalar ekrani
- [ ] Anti-cheat mexanizmi

### Sprint 4 (2 hafta) — Gamification Core
- [ ] XP, Level, Streak tizimi (backend)
- [ ] Badge tizimi va trigger'lar
- [ ] Leaderboard (Redis bilan)
- [ ] Daily quests tizimi
- [ ] Flutter: XP bar, level badge widget'lari
- [ ] Flutter: Leaderboard ekrani
- [ ] Level up / Badge earned animatsiyalar

### Sprint 5 (2 hafta) — Competition
- [ ] Tournament modeli va API
- [ ] 1v1 Challenge tizimi
- [ ] Django Channels (WebSocket sozlash)
- [ ] Live quiz leaderboard
- [ ] Flutter: Turnir ekrani
- [ ] Flutter: Challenge ekrani

### Sprint 6 (2 hafta) — Notifications & Polish
- [ ] Firebase FCM integratsiyasi
- [ ] In-app notifications
- [ ] Push notifications (streak reminder, challenge)
- [ ] Flutter: Notifications ekrani
- [ ] UI/UX polish va animatsiyalar
- [ ] Performance optimizatsiya

### Sprint 7 (1 hafta) — Testing & Launch
- [ ] Unit testlar (backend)
- [ ] Widget testlar (flutter)
- [ ] Integration testlar
- [ ] Bug fix
- [ ] App Store / Play Store tayyorlash
- [ ] Server deploy (production)

---

## 10. FAYL TUZILMASI (Open Source) {#structure}

```
edugame/                          ← Root repository
├── README.md
├── CONTRIBUTING.md
├── LICENSE (MIT)
├── .github/
│   ├── workflows/
│   │   ├── backend-ci.yml
│   │   └── flutter-ci.yml
│   └── ISSUE_TEMPLATE/
├── backend/                      ← Django loyihasi
│   ├── (yuqoridagi tuzilma)
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements/
├── mobile/                       ← Flutter loyihasi
│   ├── (yuqoridagi tuzilma)
│   └── README.md
├── docs/                         ← Dokumentatsiya
│   ├── api/                      ← Swagger/OpenAPI
│   ├── database/                 ← ERD diagramma
│   ├── architecture.md
│   └── setup-guide.md
└── docker-compose.yml
```

---

## 📊 Texnologiyalar Xulosasi

| Qatlam | Texnologiya | Versiya |
|---|---|---|
| Mobile Framework | Flutter | 3.19+ |
| State Management | flutter_bloc | 8.x |
| Backend Framework | Django | 4.2 LTS |
| API Layer | Django REST Framework | 3.14 |
| Auth | JWT (SimpleJWT) | 5.3 |
| Real-time | Django Channels | 4.0 |
| Database | PostgreSQL | 15 |
| Cache/Queue | Redis | 7 |
| Task Queue | Celery | 5.3 |
| Push Notifications | Firebase FCM | - |
| Media Storage | AWS S3 / Cloudinary | - |
| API Docs | drf-spectacular (Swagger) | 0.27 |
| Containerization | Docker + Docker Compose | - |
| Web Server | Nginx + Gunicorn | - |

---

*EduGame Implementation Plan v1.0 — MIT License*
*Mualliflar: Open Source Community*
