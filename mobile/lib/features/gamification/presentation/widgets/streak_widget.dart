import 'package:flutter/material.dart';
import '../../../gamification/data/repositories/gamification_repository.dart';

class StreakWidget extends StatelessWidget {
  final int streakDays;
  final int longestStreak;

  const StreakWidget({
    super.key,
    required this.streakDays,
    required this.longestStreak,
  });

  @override
  Widget build(BuildContext context) {
    return Container();
  }
}

class BadgeWidget extends StatelessWidget {
  final Badge badge;

  const BadgeWidget({super.key, required this.badge});

  @override
  Widget build(BuildContext context) {
    return Container();
  }
}
