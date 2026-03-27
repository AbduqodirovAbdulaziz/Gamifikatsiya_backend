import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';

class User {
  final String id;
  final String email;
  final String username;
  final String? firstName;
  final String? lastName;
  final String role;
  final String? avatar;
  final Map<String, dynamic>? studentProfile;
  final Map<String, dynamic>? teacherProfile;

  User({
    required this.id,
    required this.email,
    required this.username,
    this.firstName,
    this.lastName,
    required this.role,
    this.avatar,
    this.studentProfile,
    this.teacherProfile,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'].toString(),
      email: json['email'] ?? '',
      username: json['username'] ?? '',
      firstName: json['first_name'],
      lastName: json['last_name'],
      role: json['role'] ?? 'student',
      avatar: json['avatar'],
      studentProfile: json['student_profile'],
      teacherProfile: json['teacher_profile'],
    );
  }

  String get displayName => firstName?.isNotEmpty == true
      ? '$firstName ${lastName ?? ''}'.trim()
      : username;
}
