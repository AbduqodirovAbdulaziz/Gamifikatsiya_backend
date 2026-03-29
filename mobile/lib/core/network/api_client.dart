import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  // Local development: use your machine's IP for physical device testing
  // For Android emulator use: http://10.0.2.2:8000/api/v1
  // For iOS simulator use: http://localhost:8000/api/v1
  // For physical device use: http://YOUR_LOCAL_IP:8000/api/v1
  static String get baseUrl {
    const envUrl = String.fromEnvironment('API_URL');
    if (envUrl.isNotEmpty) return envUrl;

    // Default to local network IP for testing
    if (kIsWeb) {
      return 'http://localhost:8000/api/v1';
    }
    // For Android emulator, 10.0.2.2 maps to host machine's localhost
    return 'http://10.0.2.2:8000/api/v1';
  }

  static String get wsBaseUrl {
    const envWsUrl = String.fromEnvironment('WS_URL');
    if (envWsUrl.isNotEmpty) return envWsUrl;

    if (kIsWeb) {
      return 'ws://localhost:8000/ws';
    }
    return 'ws://10.0.2.2:8000/ws';
  }

  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: 'access_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          if (kDebugMode) {
            print('REQUEST: ${options.method} ${options.path}');
          }
          return handler.next(options);
        },
        onResponse: (response, handler) {
          if (kDebugMode) {
            print(
                'RESPONSE: ${response.statusCode} ${response.requestOptions.path}');
          }
          return handler.next(response);
        },
        onError: (error, handler) async {
          if (kDebugMode) {
            print(
                'ERROR: ${error.response?.statusCode} ${error.requestOptions.path}');
            print('ERROR TYPE: ${error.type}');
            print('ERROR MESSAGE: ${error.message}');
            if (error.response != null) {
              print('ERROR BODY: ${error.response?.data}');
            }
          }
          if (error.response?.statusCode == 401) {
            final refreshed = await _refreshToken();
            if (refreshed) {
              final token = await _storage.read(key: 'access_token');
              error.requestOptions.headers['Authorization'] = 'Bearer $token';
              final response = await _dio.fetch(error.requestOptions);
              return handler.resolve(response);
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;

      final response = await _dio.post(
        '/auth/refresh/',
        data: {'refresh': refreshToken},
        options: Options(headers: {}),
      );

      if (response.statusCode == 200) {
        await _storage.write(
          key: 'access_token',
          value: response.data['access'],
        );
        return true;
      }
    } catch (e) {
      await logout();
    }
    return false;
  }

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await _storage.write(key: 'access_token', value: accessToken);
    await _storage.write(key: 'refresh_token', value: refreshToken);
  }

  Future<void> logout() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) {
    return _dio.get(path, queryParameters: queryParameters);
  }

  Future<Response> post(String path, {dynamic data}) {
    return _dio.post(path, data: data);
  }

  Future<Response> put(String path, {dynamic data}) {
    return _dio.put(path, data: data);
  }

  Future<Response> patch(String path, {dynamic data}) {
    return _dio.patch(path, data: data);
  }

  Future<Response> delete(String path) {
    return _dio.delete(path);
  }

  Future<Response> uploadFile(
    String path,
    String filePath,
    String fieldName,
  ) async {
    final formData = FormData.fromMap({
      fieldName: await MultipartFile.fromFile(filePath),
    });
    return _dio.post(path, data: formData);
  }
}

class ApiEndpoints {
  // Auth
  static const String register = '/auth/register/';
  static const String login = '/auth/login/';
  static const String refresh = '/auth/refresh/';
  static const String me = '/auth/me/';

  // User
  static const String profile = '/users/profile/';
  static const String studentProfile = '/users/profile/student/';
  static const String teacherProfile = '/users/profile/teacher/';
  static const String changePassword = '/users/change-password/';
  static const String avatar = '/users/avatar/';

  // Classroom
  static const String classrooms = '/classrooms/';
  static const String myClassrooms = '/my-classrooms/';
  static String classroomDetail(String id) => '/classrooms/$id/';
  static String classroomStudents(String id) => '/classrooms/$id/students/';
  static const String joinClassroom = '/classrooms/join/';

  // Courses
  static const String courses = '/courses/';
  static String courseDetail(String id) => '/courses/$id/';
  static String courseLessons(String id) => '/courses/$id/lessons/';
  static String lessonDetail(String id) => '/lessons/$id/';
  static String lessonComplete(String id) => '/lessons/$id/complete/';

  // Quizzes
  static const String quizzes = '/quizzes/';
  static String quizDetail(String id) => '/quizzes/$id/';
  static String quizStart(String id) => '/quizzes/$id/start/';
  static String quizSubmit(String id) => '/quizzes/$id/submit/';
  static String quizResults(String id) => '/quizzes/$id/results/';
  static String quizLeaderboard(String id) => '/quizzes/$id/leaderboard/';

  // Gamification
  static const String gamificationProfile = '/gamification/profile/';
  static const String badges = '/gamification/badges/';
  static const String earnedBadges = '/gamification/user-badges/earned/';
  static const String xpHistory = '/gamification/xp-history/';
  static const String streak = '/gamification/streak/';
  static const String quests = '/gamification/quests/';
  static const String leaderboard = '/gamification/leaderboard/';
  static const String dailyBonus = '/gamification/daily-bonus/';

  // Competition
  static const String tournaments = '/tournaments/';
  static String tournamentDetail(String id) => '/tournaments/$id/';
  static String tournamentJoin(String id) => '/tournaments/$id/join/';
  static String tournamentStandings(String id) => '/tournaments/$id/standings/';
  static const String challenges = '/challenges/';
  static String challengeAccept(String id) => '/challenges/$id/accept/';
  static String challengeDecline(String id) => '/challenges/$id/decline/';

  // Notifications
  static const String notifications = '/notifications/';
  static String markRead(String id) => '/notifications/$id/read/';
  static const String markAllRead = '/notifications/mark_all_read/';
  static const String unreadCount = '/notifications/unread_count/';

  // Chat
  static String chatRoomMessages(String roomId) =>
      '/chat/rooms/$roomId/messages/';
  static const String chatRooms = '/chat/rooms/';
}
