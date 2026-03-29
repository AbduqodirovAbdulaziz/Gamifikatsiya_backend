import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/api_client.dart';
import '../../data/repositories/gamification_repository.dart';

class BadgesPage extends StatefulWidget {
  const BadgesPage({super.key});

  @override
  State<BadgesPage> createState() => _BadgesPageState();
}

class _BadgesPageState extends State<BadgesPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<GameBadge> _allBadges = [];
  List<GameBadge> _earnedBadges = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadBadges();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadBadges() async {
    try {
      final apiClient = getIt<ApiClient>();
      final allResponse = await apiClient.get(ApiEndpoints.badges);
      final earnedResponse = await apiClient.get(ApiEndpoints.earnedBadges);

      if (mounted) {
        setState(() {
          _allBadges = (allResponse.data as List)
              .map((e) => GameBadge.fromJson(e))
              .toList();
          _earnedBadges = (earnedResponse.data as List)
              .map((e) => GameBadge.fromJson(e['badge']))
              .toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TabBar(
          controller: _tabController,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textSecondary,
          indicatorColor: AppColors.primary,
          tabs: [
            Tab(text: 'Hammasi (${_allBadges.length})'),
            Tab(text: 'Olinganlar (${_earnedBadges.length})'),
          ],
        ),
        Expanded(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildBadgeGrid(_allBadges, _earnedBadges),
                    _buildBadgeGrid(_earnedBadges, _earnedBadges),
                  ],
                ),
        ),
      ],
    );
  }

  Widget _buildBadgeGrid(List<GameBadge> badges, List<GameBadge> earned) {
    if (badges.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.emoji_events_outlined,
                size: 64, color: AppColors.textHint),
            const SizedBox(height: 16),
            Text(
              'Badge lar yo\'q',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 16),
            ),
          ],
        ),
      );
    }

    final earnedIds = earned.map((e) => e.id).toSet();

    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.85,
      ),
      itemCount: badges.length,
      itemBuilder: (context, index) {
        final badge = badges[index];
        final isEarned = earnedIds.contains(badge.id);
        return _buildBadgeCard(badge, isEarned);
      },
    );
  }

  Widget _buildBadgeCard(GameBadge badge, bool isEarned) {
    return GestureDetector(
      onTap: () => _showBadgeDetail(badge, isEarned),
      child: Container(
        decoration: BoxDecoration(
          color: isEarned ? Colors.white : Colors.grey[100],
          borderRadius: BorderRadius.circular(16),
          border: isEarned
              ? Border.all(color: _getRarityColor(badge.rarity), width: 2)
              : null,
          boxShadow: isEarned
              ? [
                  BoxShadow(
                    color: _getRarityColor(badge.rarity).withOpacity(0.2),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: isEarned
                    ? _getRarityColor(badge.rarity).withOpacity(0.1)
                    : AppColors.divider,
                shape: BoxShape.circle,
              ),
              child: Icon(
                _getBadgeIcon(badge.badgeType),
                size: 28,
                color: isEarned
                    ? _getRarityColor(badge.rarity)
                    : AppColors.textHint,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              badge.name,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: isEarned ? AppColors.textPrimary : AppColors.textHint,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            if (!isEarned)
              Icon(Icons.lock, size: 14, color: AppColors.textHint),
          ],
        ),
      ),
    );
  }

  void _showBadgeDetail(GameBadge badge, bool isEarned) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: isEarned
                    ? _getRarityColor(badge.rarity).withOpacity(0.1)
                    : AppColors.divider,
                shape: BoxShape.circle,
              ),
              child: Icon(
                _getBadgeIcon(badge.badgeType),
                size: 40,
                color: isEarned
                    ? _getRarityColor(badge.rarity)
                    : AppColors.textHint,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              badge.name,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: _getRarityColor(badge.rarity).withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                badge.rarity,
                style: TextStyle(
                  color: _getRarityColor(badge.rarity),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              badge.description,
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.star, color: AppColors.xpYellow, size: 20),
                const SizedBox(width: 4),
                Text(
                  '+${badge.xpBonus} XP',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            if (!isEarned)
              Text(
                'Badgeni olish uchun topshiriqni bajaring!',
                style: TextStyle(color: AppColors.textHint),
              ),
          ],
        ),
      ),
    );
  }

  Color _getRarityColor(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'common':
        return AppColors.primary;
      case 'rare':
        return Colors.blue;
      case 'epic':
        return Colors.purple;
      case 'legendary':
        return AppColors.xpYellow;
      default:
        return AppColors.primary;
    }
  }

  IconData _getBadgeIcon(String type) {
    switch (type.toLowerCase()) {
      case 'quiz':
        return Icons.quiz;
      case 'streak':
        return Icons.local_fire_department;
      case 'social':
        return Icons.people;
      case 'achievement':
        return Icons.emoji_events;
      case 'level':
        return Icons.trending_up;
      default:
        return Icons.star;
    }
  }
}
