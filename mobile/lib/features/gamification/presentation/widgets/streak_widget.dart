import 'package:flutter/material.dart';
import '../../data/repositories/gamification_repository.dart';

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

class GameBadgeWidget extends StatelessWidget {
  final GameBadge badge;

  const GameBadgeWidget({super.key, required this.badge});

  @override
  Widget build(BuildContext context) {
    return Container();
  }
}
