import 'package:equatable/equatable.dart';

class User extends Equatable {
  final String id;
  final String email;
  final String username;
  final String? firstName;
  final String? lastName;
  final String role;
  final String? avatar;
  final DateTime? dateOfBirth;
  final String? bio;
  final StudentProfile? studentProfile;
  final TeacherProfile? teacherProfile;

  const User({
    required this.id,
    required this.email,
    required this.username,
    this.firstName,
    this.lastName,
    required this.role,
    this.avatar,
    this.dateOfBirth,
    this.bio,
    this.studentProfile,
    this.teacherProfile,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      username: json['username'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      role: json['role'],
      avatar: json['avatar'],
      dateOfBirth: json['date_of_birth'] != null
          ? DateTime.parse(json['date_of_birth'])
          : null,
      bio: json['bio'],
      studentProfile: json['student_profile'] != null
          ? StudentProfile.fromJson(json['student_profile'])
          : null,
      teacherProfile: json['teacher_profile'] != null
          ? TeacherProfile.fromJson(json['teacher_profile'])
          : null,
    );
  }

  String get fullName {
    if (firstName != null && lastName != null) {
      return '$firstName $lastName';
    }
    return firstName ?? username;
  }

  @override
  List<Object?> get props => [id, email, username, role];
}

class StudentProfile extends Equatable {
  final int xpPoints;
  final int level;
  final int coins;
  final int streakDays;
  final DateTime? lastActivity;
  final int totalQuizzesCompleted;
  final int totalCorrectAnswers;
  final int? rankPosition;
  final int dailyLoginStreak;

  const StudentProfile({
    required this.xpPoints,
    required this.level,
    required this.coins,
    required this.streakDays,
    this.lastActivity,
    required this.totalQuizzesCompleted,
    required this.totalCorrectAnswers,
    this.rankPosition,
    required this.dailyLoginStreak,
  });

  factory StudentProfile.fromJson(Map<String, dynamic> json) {
    return StudentProfile(
      xpPoints: json['xp_points'] ?? 0,
      level: json['level'] ?? 1,
      coins: json['coins'] ?? 0,
      streakDays: json['streak_days'] ?? 0,
      lastActivity: json['last_activity'] != null
          ? DateTime.parse(json['last_activity'])
          : null,
      totalQuizzesCompleted: json['total_quizzes_completed'] ?? 0,
      totalCorrectAnswers: json['total_correct_answers'] ?? 0,
      rankPosition: json['rank_position'],
      dailyLoginStreak: json['daily_login_streak'] ?? 0,
    );
  }

  @override
  List<Object?> get props => [xpPoints, level, coins, streakDays];
}

class TeacherProfile extends Equatable {
  final String? subjectExpertise;
  final String? school;
  final int totalStudents;
  final bool isVerified;

  const TeacherProfile({
    this.subjectExpertise,
    this.school,
    required this.totalStudents,
    required this.isVerified,
  });

  factory TeacherProfile.fromJson(Map<String, dynamic> json) {
    return TeacherProfile(
      subjectExpertise: json['subject_expertise'],
      school: json['school'],
      totalStudents: json['total_students'] ?? 0,
      isVerified: json['is_verified'] ?? false,
    );
  }

  @override
  List<Object?> get props => [subjectExpertise, school, totalStudents];
}
