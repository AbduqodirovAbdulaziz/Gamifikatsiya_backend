# EduGame Mobile - Local Development Setup

## Prerequisites
- Flutter SDK 3.2.0+
- Android Studio / Xcode
- Backend running at `http://localhost:8000`

## Quick Start

### 1. Install dependencies
```bash
cd mobile
flutter pub get
```

### 2. Run on Android Emulator
```bash
flutter run
```
The app will connect to `http://10.0.2.2:8000/api/v1` (emulator maps this to host localhost).

### 3. Run on iOS Simulator
```bash
flutter run
```
The app will connect to `http://localhost:8000/api/v1`.

### 4. Run on Physical Device
Update the base URL in `lib/core/network/api_client.dart` to your machine's local IP:
```dart
return 'http://YOUR_IP:8000/api/v1';
```

### 5. Custom API URL via build flag
```bash
flutter run --dart-define=API_URL=http://192.168.1.100:8000/api/v1
```

## Project Structure
```
lib/
├── main.dart
├── core/
│   ├── constants/     # App colors, strings, sizes
│   ├── di/            # Dependency injection
│   ├── network/       # API client & endpoints
│   └── storage/       # Local storage utilities
├── features/
│   ├── auth/          # Login, register, auth bloc
│   ├── dashboard/     # Main dashboard with stats
│   ├── quiz/          # Quiz play, results
│   ├── gamification/  # XP, badges, leaderboard
│   ├── competition/   # Challenges, tournaments
│   ├── classroom/     # Classroom management
│   ├── courses/       # Course listing
│   ├── chat/          # WebSocket chat
│   ├── notifications/ # Push notifications
│   └── profile/       # User profile
└── shared/
    ├── theme/         # App theme configuration
    └── widgets/       # Shared UI components
```

## Architecture
- **State Management**: flutter_bloc (BLoC pattern)
- **HTTP Client**: Dio with JWT auth interceptor
- **WebSocket**: web_socket_channel for real-time features
- **Local Storage**: flutter_secure_storage for tokens
- **DI**: get_it for dependency injection
