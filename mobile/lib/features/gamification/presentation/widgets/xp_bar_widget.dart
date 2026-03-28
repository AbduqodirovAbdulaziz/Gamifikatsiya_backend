import 'package:flutter/material.dart';
import '../../data/repositories/gamification_repository.dart';
import '../../../../core/constants/app_constants.dart';

class XPBarWidget extends StatelessWidget {
  final double progress;

  const XPBarWidget({super.key, required this.progress});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          height: 12,
          decoration: BoxDecoration(
            color: AppColors.divider,
            borderRadius: BorderRadius.circular(6),
          ),
          child: FractionallySizedBox(
            alignment: Alignment.centerLeft,
            widthFactor: progress.clamp(0.0, 1.0),
            child: Container(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primary, AppColors.secondary],
                ),
                borderRadius: BorderRadius.circular(6),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

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
    Color streakColor;
    if (streakDays >= 30) {
      streakColor = AppColors.streakMax;
    } else if (streakDays >= 7) {
      streakColor = AppColors.streakHigh;
    } else if (streakDays >= 3) {
      streakColor = AppColors.streakMedium;
    } else {
      streakColor = AppColors.streakLow;
    }

    return Container(
      padding: const EdgeInsets.all(AppSizes.paddingM),
      decoration: BoxDecoration(
        color: streakColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppSizes.radiusM),
        border: Border.all(color: streakColor.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(Icons.local_fire_department, color: streakColor, size: 32),
          const SizedBox(width: AppSizes.paddingM),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$streakDays kun',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 20,
                  color: streakColor,
                ),
              ),
              Text(
                'Eng uzun: $longestStreak kun',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class BadgeWidget extends StatelessWidget {
  final GameBadge badge;
  final bool showName;

  const BadgeWidget({super.key, required this.badge, this.showName = true});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            color: _getRarityColor().withOpacity(0.1),
            shape: BoxShape.circle,
            border: Border.all(color: _getRarityColor(), width: 2),
          ),
          child: Icon(_getBadgeIcon(), color: _getRarityColor(), size: 28),
        ),
        if (showName) ...[
          const SizedBox(height: AppSizes.paddingXS),
          Text(
            badge.name,
            style: Theme.of(context).textTheme.bodySmall,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ],
    );
  }

  Color _getRarityColor() {
    switch (badge.rarity) {
      case 'legendary':
        return AppColors.badgeLegendary;
      case 'epic':
        return AppColors.badgeEpic;
      case 'rare':
        return AppColors.badgeRare;
      default:
        return AppColors.badgeCommon;
    }
  }

  IconData _getBadgeIcon() {
    switch (badge.badgeType) {
      case 'streak':
        return Icons.local_fire_department;
      case 'quiz':
        return Icons.quiz;
      case 'lesson':
        return Icons.menu_book;
      case 'social':
        return Icons.people;
      case 'special':
        return Icons.star;
      default:
        return Icons.emoji_events;
    }
  }
}

class LevelBadgeWidget extends StatelessWidget {
  final int level;
  final String? title;

  const LevelBadgeWidget({super.key, required this.level, this.title});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSizes.paddingM,
        vertical: AppSizes.paddingS,
      ),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.primaryDark],
        ),
        borderRadius: BorderRadius.circular(AppSizes.radiusL),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.star, color: Colors.white, size: 20),
          const SizedBox(width: 4),
          Text(
            'Lv.$level',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          if (title != null) ...[
            const SizedBox(width: 8),
            Text(
              title!,
              style: const TextStyle(color: Colors.white70, fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}
