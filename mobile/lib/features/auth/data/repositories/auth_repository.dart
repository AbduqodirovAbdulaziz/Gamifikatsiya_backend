import 'package:edugame/core/network/api_client.dart';

class AuthRepository {
  final ApiClient _apiClient;

  AuthRepository(this._apiClient);

  Future<AuthResponse> register({
    required String email,
    required String username,
    required String password,
    required String passwordConfirm,
    required String role,
    String? firstName,
    String? lastName,
  }) async {
    final response = await _apiClient.post(
      ApiEndpoints.register,
      data: {
        'email': email,
        'username': username,
        'password': password,
        'password_confirm': passwordConfirm,
        'role': role,
        'first_name': firstName,
        'last_name': lastName,
      },
    );

    await _apiClient.saveTokens(
      response.data['tokens']['access'],
      response.data['tokens']['refresh'],
    );

    return AuthResponse.fromJson(response.data);
  }

  Future<AuthResponse> login({
    required String username,
    required String password,
  }) async {
    final response = await _apiClient.post(
      ApiEndpoints.login,
      data: {'username': username, 'password': password},
    );

    await _apiClient.saveTokens(
      response.data['access'],
      response.data['refresh'],
    );

    return AuthResponse(
      accessToken: response.data['access'],
      refreshToken: response.data['refresh'],
    );
  }

  Future<User> getCurrentUser() async {
    final response = await _apiClient.get(ApiEndpoints.profile);
    return User.fromJson(response.data);
  }

  Future<void> logout() async {
    await _apiClient.logout();
  }

  Future<User> updateProfile({
    String? firstName,
    String? lastName,
    String? bio,
    String? phone,
  }) async {
    final response = await _apiClient.patch(
      ApiEndpoints.profile,
      data: {
        if (firstName != null) 'first_name': firstName,
        if (lastName != null) 'last_name': lastName,
        if (bio != null) 'bio': bio,
        if (phone != null) 'phone': phone,
      },
    );
    return User.fromJson(response.data);
  }

  Future<String> uploadAvatar(String filePath) async {
    final response = await _apiClient.uploadFile(
      ApiEndpoints.avatar,
      filePath,
      'avatar',
    );
    return response.data['avatar_url'];
  }

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    await _apiClient.post(
      ApiEndpoints.changePassword,
      data: {'old_password': oldPassword, 'new_password': newPassword},
    );
  }
}

class AuthResponse {
  final String? accessToken;
  final String? refreshToken;
  final User? user;
  final String? message;

  AuthResponse({this.accessToken, this.refreshToken, this.user, this.message});

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    final tokens = json['tokens'];
    return AuthResponse(
      accessToken: tokens?['access'],
      refreshToken: tokens?['refresh'],
      user: json['user'] != null ? User.fromJson(json['user']) : null,
      message: json['message'],
    );
  }
}

class User {
  final String id;
  final String email;
  final String username;
  final String? firstName;
  final String? lastName;
  final String role;
  final String? avatar;
  final String? bio;

  User({
    required this.id,
    required this.email,
    required this.username,
    this.firstName,
    this.lastName,
    required this.role,
    this.avatar,
    this.bio,
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
      bio: json['bio'],
    );
  }
}
