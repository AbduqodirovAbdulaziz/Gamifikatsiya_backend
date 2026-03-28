import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/utils/dependency_injection.dart';
import '../bloc/auth_bloc.dart';
import 'register_page.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _onLogin() {
    if (_formKey.currentState!.validate()) {
      context.read<AuthBloc>().add(
            AuthLoginRequested(
              username: _usernameController.text.trim(),
              password: _passwordController.text,
            ),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlocConsumer<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: AppColors.error,
              ),
            );
          }
        },
        builder: (context, state) {
          return SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(AppSizes.paddingL),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const SizedBox(height: 60),
                    Icon(Icons.school, size: 80, color: AppColors.primary),
                    const SizedBox(height: AppSizes.paddingM),
                    Text(
                      AppStrings.appName,
                      style: Theme.of(context).textTheme.displaySmall?.copyWith(
                            color: AppColors.primary,
                            fontWeight: FontWeight.bold,
                          ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: AppSizes.paddingS),
                    Text(
                      AppStrings.tagline,
                      style: Theme.of(context).textTheme.bodyMedium,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: AppSizes.paddingXL),
                    Text(
                      AppStrings.welcomeBack,
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: AppSizes.paddingL),
                    TextFormField(
                      controller: _usernameController,
                      keyboardType: TextInputType.text,
                      decoration: const InputDecoration(
                        labelText: 'Username',
                        prefixIcon: Icon(Icons.person_outlined),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Username kiritilmadi';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: AppSizes.paddingM),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      decoration: InputDecoration(
                        labelText: AppStrings.password,
                        prefixIcon: const Icon(Icons.lock_outlined),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Parol kiritilmadi';
                        }
                        if (value.length < 6) {
                          return 'Parol kamida 6 ta belgi';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: AppSizes.paddingS),
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () {},
                        child: const Text(AppStrings.forgotPassword),
                      ),
                    ),
                    const SizedBox(height: AppSizes.paddingL),
                    ElevatedButton(
                      onPressed: state is AuthLoading ? null : _onLogin,
                      child: state is AuthLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text(AppStrings.login),
                    ),
                    const SizedBox(height: AppSizes.paddingL),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text('Hisobingiz yo\'qmi? '),
                        TextButton(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => BlocProvider(
                                  create: (_) => getIt<AuthBloc>(),
                                  child: const RegisterPage(),
                                ),
                              ),
                            );
                          },
                          child: const Text(AppStrings.register),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
