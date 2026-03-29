# EduGame Backend

Django REST Framework bilan yozilgan backend API.

## Render Deploy

### Blueprint orqali deploy

Repo ichida `backend` va `mobile` birga turadi, lekin Render faqat `backend` papkani deploy qiladi. Buning uchun repo ildizidagi `render.yaml` ishlatiladi.

1. [Render.com](https://render.com) ga kiring.
2. `New +` -> `Blueprint` ni tanlang.
3. GitHub repositoriyani ulang.
4. Quyidagilarni kiriting:
   - `Blueprint Name`: `gamifikatsiya-backend-prod`
   - `Branch`: `main`
   - `Blueprint Path`: `render.yaml`

### Blueprint nima qiladi

- Repo ildizidagi `render.yaml` ni o'qiydi.
- `rootDir: backend` sabab faqat `backend` papkani build qiladi.
- `mobile` papkasini deployga qo'shmaydi.
- `bash ./build.sh` orqali backendni yig'adi.
- `daphne` bilan ASGI serverni ishga tushiradi.

### PostgreSQL yaratish

1. `New +` -> `PostgreSQL` ni tanlang.
2. Region sifatida web service bilan bir xil regionni tanlang.
3. Plan sifatida `Free` ni tanlang.
4. Database yaratilgandan so'ng `Internal Database URL` ni nusxa oling.

### Environment variables

Web service ichida kamida quyidagilarni tekshiring:

- `DATABASE_URL`: PostgreSQL internal URL
- `DJANGO_SETTINGS_MODULE`: `config.settings.production`
- `SECRET_KEY`: Render avtomatik yaratadi

Agar web frontend bo'lsa, qo'shing:

- `FRONTEND_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`

### Free plan uchun migratsiyalar

Free plan da `preDeployCommand` ishlamaydi, shuning uchun migratsiyalarni deploydan keyin qo'lda ishga tushiring.

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Tekshiruv

Deploy tugagach quyidagilarni tekshiring:

- `https://<render-domain>/health/`
- `https://<render-domain>/admin/`
- `https://<render-domain>/api/docs/`

`/health/` endpoint `{"status":"ok"}` qaytarishi kerak.

## Loyiha Tuzilmasi

```text
backend/
|-- apps/
|   |-- users/
|   |-- classroom/
|   |-- courses/
|   |-- quizzes/
|   |-- gamification/
|   |-- competition/
|   |-- notifications/
|   `-- chat/
|-- config/
|   |-- settings/
|   |-- urls.py
|   |-- wsgi.py
|   `-- asgi.py
|-- requirements.txt
|-- manage.py
`-- Procfile
```

## Asosiy Endpointlar

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `GET /api/v1/users/profile/`
- `GET /api/v1/classrooms/`
- `GET /api/v1/courses/`
- `GET /api/v1/quizzes/`
- `GET /api/v1/gamification/profile/`
- `GET /api/v1/leaderboard/`

## Mahalliy Ishga Tushurish

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
