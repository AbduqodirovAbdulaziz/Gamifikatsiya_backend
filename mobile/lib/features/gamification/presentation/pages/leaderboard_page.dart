import 'package:flutter/material.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/api_client.dart';

class LeaderboardPage extends StatefulWidget {
  const LeaderboardPage({super.key});

  @override
  State<LeaderboardPage> createState() => _LeaderboardPageState();
}

class _LeaderboardPageState extends State<LeaderboardPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _leaderboard = [];
  bool _isLoading = true;
  String _period = 'weekly';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadLeaderboard();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadLeaderboard() async {
    try {
      final apiClient = getIt<ApiClient>();
      final response = await apiClient.get(
        '/gamification/leaderboard/',
        queryParameters: {'period': _period},
      );
      if (mounted) {
        setState(() {
          _leaderboard = response.data['entries'] ?? [];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
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
          tabs: const [
            Tab(text: 'Kunlik'),
            Tab(text: 'Haftalik'),
            Tab(text: 'Oylik'),
            Tab(text: 'Umumiy'),
          ],
          onTap: (index) {
            setState(() {
              switch (index) {
                case 0:
                  _period = 'daily';
                  break;
                case 1:
                  _period = 'weekly';
                  break;
                case 2:
                  _period = 'monthly';
                  break;
                case 3:
                  _period = 'all_time';
                  break;
              }
              _isLoading = true;
            });
            _loadLeaderboard();
          },
        ),
        Expanded(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _leaderboard.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.leaderboard_outlined,
                              size: 64, color: AppColors.textHint),
                          const SizedBox(height: 16),
                          Text(
                            'Hali reyting yo\'q',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _leaderboard.length,
                      itemBuilder: (context, index) {
                        final entry = _leaderboard[index];
                        return _buildLeaderboardItem(entry, index);
                      },
                    ),
        ),
      ],
    );
  }

  Widget _buildLeaderboardItem(dynamic entry, int index) {
    final rank = entry['rank'] ?? (index + 1);
    final student = entry['student'] ?? {};
    final username = student['username'] ?? 'Unknown';
    final xpPoints = entry['xp_points'] ?? 0;
    final level = entry['level'] ?? 1;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: rank <= 3 ? _getRankColor(rank).withOpacity(0.1) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border:
            rank <= 3 ? Border.all(color: _getRankColor(rank), width: 2) : null,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          _buildRankBadge(rank),
          const SizedBox(width: 12),
          CircleAvatar(
            radius: 24,
            backgroundColor: AppColors.primary.withOpacity(0.1),
            child: Text(
              username.isNotEmpty ? username[0].toUpperCase() : '?',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: AppColors.primary,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  username,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                Text(
                  'Level $level',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Row(
                children: [
                  Icon(Icons.star, size: 18, color: AppColors.xpYellow),
                  const SizedBox(width: 4),
                  Text(
                    '$xpPoints',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      color: AppColors.xpYellow,
                    ),
                  ),
                ],
              ),
              Text(
                'XP',
                style: TextStyle(
                  color: AppColors.textHint,
                  fontSize: 10,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRankBadge(int rank) {
    if (rank > 3) {
      return Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: AppColors.divider,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            '#$rank',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
        ),
      );
    }

    final medals = ['🥇', '🥈', '🥉'];
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: _getRankColor(rank).withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Center(
        child: Text(
          medals[rank - 1],
          style: const TextStyle(fontSize: 20),
        ),
      ),
    );
  }

  Color _getRankColor(int rank) {
    switch (rank) {
      case 1:
        return AppColors.gold;
      case 2:
        return AppColors.silver;
      case 3:
        return AppColors.bronze;
      default:
        return AppColors.textHint;
    }
  }
}
