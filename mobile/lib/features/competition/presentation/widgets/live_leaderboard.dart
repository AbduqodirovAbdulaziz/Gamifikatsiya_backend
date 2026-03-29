import 'dart:async';
import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/network/api_client.dart';

class LiveLeaderboard extends StatefulWidget {
  final String quizId;
  final bool isLive;

  const LiveLeaderboard({
    super.key,
    required this.quizId,
    this.isLive = true,
  });

  @override
  State<LiveLeaderboard> createState() => _LiveLeaderboardState();
}

class _LiveLeaderboardState extends State<LiveLeaderboard> {
  List<dynamic> _participants = [];
  bool _isLoading = true;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _loadLeaderboard();
    if (widget.isLive) {
      _startAutoRefresh();
    }
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  void _startAutoRefresh() {
    _refreshTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _loadLeaderboard();
    });
  }

  Future<void> _loadLeaderboard() async {
    try {
      final apiClient = ApiClient();
      final response =
          await apiClient.get('/quizzes/${widget.quizId}/leaderboard/');
      if (mounted) {
        setState(() {
          _participants = response.data['leaderboard'] ?? [];
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
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.leaderboard, color: AppColors.primary),
                const SizedBox(width: 8),
                const Text(
                  'Live Reyting',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const Spacer(),
                if (widget.isLive)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.success.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: AppColors.success,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Text(
                          'LIVE',
                          style: TextStyle(
                            color: AppColors.success,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _participants.isEmpty
                    ? Center(
                        child: Text(
                          'Hali ishtirokchilar yo\'q',
                          style: TextStyle(color: AppColors.textHint),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        itemCount: _participants.length > 10
                            ? 10
                            : _participants.length,
                        itemBuilder: (context, index) {
                          return _buildParticipantItem(
                              _participants[index], index);
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildParticipantItem(dynamic participant, int index) {
    final rank = participant['rank'] ?? (index + 1);
    final username = participant['username'] ?? 'Unknown';
    final score = participant['score'] ?? 0;
    final isCurrentUser = participant['is_current_user'] ?? false;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: isCurrentUser ? AppColors.primary.withOpacity(0.05) : null,
      child: Row(
        children: [
          SizedBox(
            width: 32,
            child: _buildRankWidget(rank),
          ),
          const SizedBox(width: 8),
          CircleAvatar(
            radius: 16,
            backgroundColor: AppColors.primary.withOpacity(0.1),
            child: Text(
              username.isNotEmpty ? username[0].toUpperCase() : '?',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: AppColors.primary,
                fontSize: 12,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              username,
              style: TextStyle(
                fontWeight: isCurrentUser ? FontWeight.bold : FontWeight.normal,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Text(
            '$score',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: rank <= 3 ? _getRankColor(rank) : AppColors.textPrimary,
            ),
          ),
          const SizedBox(width: 4),
          Text(
            'xp',
            style: TextStyle(
              fontSize: 10,
              color: AppColors.textHint,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRankWidget(int rank) {
    if (rank <= 3) {
      final medals = ['🥇', '🥈', '🥉'];
      return Text(
        medals[rank - 1],
        style: const TextStyle(fontSize: 18),
      );
    }
    return Text(
      '#$rank',
      style: TextStyle(
        fontWeight: FontWeight.bold,
        color: AppColors.textSecondary,
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
        return AppColors.textPrimary;
    }
  }
}
