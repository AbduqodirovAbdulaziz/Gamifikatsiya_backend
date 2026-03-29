# EduGame - Gamifikatsiya Asosidagi Ta'lim Platformasi

![EduGame Banner](docs/banner.png)

## 🎯 Loyiha Haqida

EduGame - bu gamifikatsiya elementlari asosida ishlaydigan zamonaviy ta'lim platformasi. Bu loyiha orqali o'quvchilar o'yinlashgan muhitda o'rganishlari, musobaqalarda qatnashishlari va reytinglarda bellashishlari mumkin.

## ✨ Asosiy Xususiyatlar

- **📚 Kurslar va Darslar** - Fanlar bo'yicha kurslar va darslar
- **🧠 Testlar** - Interaktiv testlar va imtihonlar
- **🏆 Gamifikatsiya** - XP, Level, Badge, Streak tizimlari
- **📊 Leaderboard** - Global va sinf reytinglari
- **⚔️ Musobaqalar** - 1v1 Challenge va Turnirlar
- **💬 Real-time Chat** - Sinf chat va WebSocket

## 🛠️ Texnologiyalar

### Backend
- **Django 4.2** - Web Framework
- **Django REST Framework** - API
- **PostgreSQL** - Ma'lumotlar bazasi
- **Redis** - Cache va WebSocket
- **JWT** - Autentifikatsiya

### Mobile
- **Flutter 3.19+** - Cross-platform
- **BLoC** - State Management
- **Dio** - HTTP Client

## 🚀 Tezkor Boshlash

### Backend (Render.com) — serverga faqat backend

GitHub repositoriyada `backend/` va `mobile/` birga turishi normal: bitta repoga push qilasiz. **Render serverda faqat `backend` papkasini** ishlatadi (`render.yaml` ichida `rootDir: backend`). `mobile` kodlari build yoki containerga kiritilmaydi.

- Blueprint: repo ildizidagi `render.yaml`, branch `main`.
- Yoki oddiy **Web Service** ochgan bo‘lsangiz: **Settings → Root Directory** = `backend` bo‘lishi shart.

Batafsil: [backend/README.md](backend/README.md) (Render Deploy bo‘limi).

```bash
# GitHub ga yuklash (butun monorepo; server yana ham faqat backendni oladi)
git add .
git commit -m "Your message"
git push origin main
```

Keyin [Render.com](https://render.com) da deploy qiling.

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

## 📁 Loyiha Tuzilmasi

```
edugame/
├── backend/              # Django REST API
│   ├── apps/
│   │   ├── users/       # Foydalanuvchilar
│   │   ├── classroom/   # Sinfxonalar
│   │   ├── courses/     # Kurslar
│   │   ├── quizzes/     # Testlar
│   │   ├── gamification/ # Gamifikatsiya
│   │   ├── competition/  # Musobaqalar
│   │   └── notifications/ # Bildirishnomalar
│   └── config/          # Django sozlamalari
│
├── mobile/              # Flutter ilova
│   └── lib/
│       ├── core/       # Umumiy kodlar
│       ├── features/   # Feature modullari
│       └── shared/    # Ulashilgan komponentlar
│
└── docs/               # Hujjatlar
```

## 🏆 Gamifikatsiya Tizimi

| Element | Tavsif |
|---------|--------|
| XP | Tajriba ballari |
| Level | Daraja (formula: `√(XP/100) + 1`) |
| Coins | Virtual valyuta |
| Streak | Ketma-ket kunlar |
| Badges | Yutuqlar |

## 📝 API Dokumentatsiya

Deploy qilingandan so'ng:
- Swagger UI: `https://your-app.onrender.com/api/docs/`
- OpenAPI Schema: `https://your-app.onrender.com/api/schema/`

## 🤝 Hissa Qo'shish

1. Fork qiling
2. Branch yarating (`git checkout -b feature/amazing`)
3. Commit qiling (`git commit -m 'Add amazing feature'`)
4. Push qiling (`git push origin feature/amazing`)
5. Pull Request oching

## 📄 Litsenziya

MIT License - batafsil [LICENSE](LICENSE) faylida.

## 👨‍💻 Muallif

EduGame Team

---

⭐ Agar bu loyiha sizga yoqsa, yulduzcha qo'yishingizni so'raymiz!
