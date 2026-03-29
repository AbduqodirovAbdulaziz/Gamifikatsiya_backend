import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';

class AnswerOption extends StatelessWidget {
  final String answer;
  final int index;
  final bool isSelected;
  final bool isCorrect;
  final bool isWrong;
  final VoidCallback onTap;

  const AnswerOption({
    super.key,
    required this.answer,
    required this.index,
    required this.isSelected,
    required this.isCorrect,
    required this.isWrong,
    required this.onTap,
  });

  String get _optionLetter {
    return String.fromCharCode(65 + index);
  }

  Color get _borderColor {
    if (isCorrect) return AppColors.success;
    if (isWrong) return AppColors.error;
    if (isSelected) return AppColors.primary;
    return AppColors.divider;
  }

  Color get _backgroundColor {
    if (isCorrect) return AppColors.success.withOpacity(0.1);
    if (isWrong) return AppColors.error.withOpacity(0.1);
    if (isSelected) return AppColors.primary.withOpacity(0.1);
    return Colors.white;
  }

  IconData? get _trailingIcon {
    if (isCorrect) return Icons.check_circle;
    if (isWrong) return Icons.cancel;
    return null;
  }

  Color? get _iconColor {
    if (isCorrect) return AppColors.success;
    if (isWrong) return AppColors.error;
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: _backgroundColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: _borderColor,
              width: isSelected || isCorrect || isWrong ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: isSelected || isCorrect || isWrong
                      ? _borderColor.withOpacity(0.2)
                      : AppColors.divider,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Center(
                  child: Text(
                    _optionLetter,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: isSelected || isCorrect || isWrong
                          ? _borderColor
                          : AppColors.textSecondary,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  answer,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight:
                        isSelected ? FontWeight.w600 : FontWeight.normal,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
              if (_trailingIcon != null)
                Icon(_trailingIcon, color: _iconColor, size: 24),
            ],
          ),
        ),
      ),
    );
  }
}
