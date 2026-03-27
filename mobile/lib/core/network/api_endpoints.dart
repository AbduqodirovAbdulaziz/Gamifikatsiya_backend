class ApiEndpoints {
  static const String baseUrl = 'http://localhost:8000/api/v1';
  static const String wsUrl = 'ws://localhost:8000/ws';

  static const String register = '/auth/register/';
  static const String login = '/auth/login/';
  static const String refresh = '/auth/refresh/';
  static const String logout = '/auth/logout/';
  static const String me = '/auth/me/';

  static const String profile = '/users/profile/';
  static const String studentProfile = '/users/profile/student/';
  static const String teacherProfile = '/users/profile/teacher/';
  static const String changePassword = '/users/change-password/';
  static const String avatarUpload = '/users/avatar/';

  static const String classrooms = '/classrooms/';
  static const String myClassrooms = '/my-classrooms/';
  static const String joinClassroom = '/classrooms/join/';

  static const String courses = '/courses/';
  static const String myCourses = '/courses/my_courses/';

  static const String lessons = '/lessons/';

  static const String quizzes = '/quizzes/';
  static const String attempts = '/attempts/';

  static const String gamificationProfile = '/gamification/profile/';
  static const String badges = '/gamification/badges/';
  static const String earnedBadges = '/gamification/user-badges/earned/';
  static const String xpHistory = '/gamification/xp-history/';
  static const String leaderboard = '/gamification/leaderboard/';
  static const String streak = '/gamification/streak/';
  static const String dailyBonus = '/gamification/daily-bonus/';
  static const String quests = '/gamification/quests/';

  static const String challenges = '/challenges/';
  static const String pendingChallenges = '/challenges/pending/';
  static const String sentChallenges = '/challenges/sent/';

  static const String tournaments = '/tournaments/';

  static const String notifications = '/notifications/';
  static const String unreadCount = '/notifications/unread_count/';

  static const String wsChat = '/ws/chat/';
  static const String wsQuizLive = '/ws/quiz/';
  static const String wsNotifications = '/ws/notifications/';
}
