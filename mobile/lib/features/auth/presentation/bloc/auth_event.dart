part of 'auth_bloc.dart';

abstract class AuthEvent extends Equatable {
  const AuthEvent();

  @override
  List<Object?> get props => [];
}

class CheckAuthStatus extends AuthEvent {}

class LoginRequested extends AuthEvent {
  final String email;
  final String password;

  const LoginRequested({required this.email, required this.password});

  @override
  List<Object?> get props => [email, password];
}

class RegisterRequested extends AuthEvent {
  final String email;
  final String username;
  final String password;
  final String passwordConfirm;
  final String role;
  final String firstName;
  final String lastName;

  const RegisterRequested({
    required this.email,
    required this.username,
    required this.password,
    required this.passwordConfirm,
    required this.role,
    required this.firstName,
    required this.lastName,
  });

  @override
  List<Object?> get props =>
      [email, username, password, role, firstName, lastName];
}

class LogoutRequested extends AuthEvent {}
