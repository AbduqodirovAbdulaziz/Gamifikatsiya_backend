# EduGame Backend - Gamifikatsiya Asosidagi Ta'lim Platformasi

Django REST Framework bilan yozilgan backend API.

## 🚀 Render.com da Deploy Qilish

### 1. GitHub ga yuklash

```bash
# GitHub da yangi repo yarating, keyin:
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/edugame-backend.git
git push -u origin main
```

### 2. Render.com da Deploy

1. [Render.com](https://render.com) ga kiring
2. **"New +"** → **"Web Service"** tanlang
3. GitHub repositoriyani ulang
4. Sozlamalar:
   - **Name:** `edugame-api`
   - **Region:** Oregon (yoki sizga yaqin)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2`

5. **Environment** bo'limida:
   - `SECRET_KEY` - ixtiyoriy (Render avtomatik yaratadi)
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `edugame-api.onrender.com`

6. **"Create Web Service"** tugmasini bosing

### 3. PostgreSQL yaratish

1. **"New +"** → **"PostgreSQL"** tanlang
2. **Name:** `edugame-db`
3. **Region:** Web service bilan bir xil
4. **Plan:** Free
5. **"Create Database"** tugmasini bosing
6. Database yaratilgandan so'ng, **"Connection Details"** → **"Internal Connection String"** ni nusxa oling

### 4. Web Service ni yangilash

1. Web service sozlamariga o'ting
2. **Environment** bo'limida yangi variable qo'shing:
   - `DATABASE_URL` = (nusxa olgan connection string)

### 5. Migrations qo'llash

1. Web service dashboardda **"Shell"** tugmasini bosing
2. Quyidagi buyruqlarni kiriting:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## 📁 Loyiha Tuzilmasi

```
backend/
├── apps/
│   ├── users/          # Foydalanuvchilar
│   ├── classroom/      # Sinfxonalar
│   ├── courses/        # Kurslar
│   ├── quizzes/        # Testlar
│   ├── gamification/   # Gamifikatsiya
│   ├── competition/    # Musobaqalar
│   ├── notifications/  # Bildirishnomalar
│   └── chat/          # Chat
├── config/
│   ├── settings/      # Django sozlamalari
│   ├── urls.py        # URL marshrutlari
│   ├── wsgi.py        # WSGI
│   └── asgi.py        # ASGI
├── requirements.txt    # Kutubxonalar
├── manage.py          # Django CLI
└── Procfile           # Render uchun
```

## 🔌 API Endpoints

| Endpoint | Tavsif |
|----------|--------|
| `POST /api/v1/auth/register/` | Ro'yxatdan o'tish |
| `POST /api/v1/auth/login/` | Kirish |
| `GET /api/v1/users/profile/` | Profil |
| `GET /api/v1/classrooms/` | Sinfxonalar |
| `GET /api/v1/courses/` | Kurslar |
| `GET /api/v1/quizzes/` | Testlar |
| `GET /api/v1/gamification/profile/` | XP, Level, Badge |
| `GET /api/v1/leaderboard/` | Reyting |

## 🛠 Mahalliy Ishga Tushurish

```bash
cd backend

# Virtual environment yaratish
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt

# Migratsiyalar
python manage.py migrate

# Serverni ishga tushurish
python manage.py runserver
```

## 📚 Hujjatlar

- [API Dokumentatsiya](https://edugame-api.onrender.com/api/docs/) - Swagger UI
- [Implementation Plan](../implementation_plan.md) - Loyiha rejalashtirish

## 🛡 Xavfsizlik

- JWT Authentication
- Parol hash
- CORS himoyasi
- Rate limiting

## 📄 Litsenziya

MIT License
