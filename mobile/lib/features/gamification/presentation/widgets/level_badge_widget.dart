// LevelBadgeWidget with detailed level display
import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';

class LevelBadgeWidget extends StatelessWidget {
  final int level;
  final String title;
  final double progress;
  final bool showProgress;
  final bool isLarge;

  const LevelBadgeWidget({
    super.key,
    required this.level,
    required this.title,
    required this.progress,
    this.showProgress = true,
    this.isLarge = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: isLarge ? 100 : 64,
              height: isLarge ? 100 : 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    _getLevelColor(level),
                    _getLevelColor(level).withOpacity(0.6),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: [
                  BoxShadow(
                    color: _getLevelColor(level).withOpacity(0.4),
                    blurRadius: isLarge ? 20 : 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Center(
                child: Text(
                  '$level',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: isLarge ? 36 : 24,
                  ),
                ),
              ),
            ),
            if (level < 50)
              Positioned(
                bottom: 0,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _getLevelColor(level),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    title,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 8,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
          ],
        ),
        if (showProgress) ...[
          const SizedBox(height: 8),
          SizedBox(
            width: isLarge ? 100 : 64,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress,
                backgroundColor: AppColors.divider,
                valueColor: AlwaysStoppedAnimation(_getLevelColor(level)),
                minHeight: isLarge ? 8 : 6,
              ),
            ),
          ),
        ],
      ],
    );
  }

  Color _getLevelColor(int level) {
    if (level >= 40) return const Color(0xFF9B59B6);
    if (level >= 30) return const Color(0xFFE67E22);
    if (level >= 20) return const Color(0xFF3498DB);
    if (level >= 10) return const Color(0xFF2ECC71);
    return AppColors.primary;
  }
}
