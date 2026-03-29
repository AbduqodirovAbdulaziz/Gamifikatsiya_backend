import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/api_client.dart';

class TournamentPage extends StatefulWidget {
  const TournamentPage({super.key});

  @override
  State<TournamentPage> createState() => _TournamentPageState();
}

class _TournamentPageState extends State<TournamentPage> {
  List<dynamic> _tournaments = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadTournaments();
  }

  Future<void> _loadTournaments() async {
    try {
      final apiClient = getIt<ApiClient>();
      final response = await apiClient.get('/tournaments/');
      if (mounted) {
        setState(() {
          _tournaments = response.data['results'] ?? response.data ?? [];
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Turnirlar'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _tournaments.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.emoji_events_outlined,
                          size: 64, color: AppColors.textHint),
                      const SizedBox(height: 16),
                      Text(
                        'Hali turnirlar yo\'q',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 16,
                        ),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadTournaments,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _tournaments.length,
                    itemBuilder: (context, index) {
                      return _buildTournamentCard(_tournaments[index]);
                    },
                  ),
                ),
    );
  }

  Widget _buildTournamentCard(dynamic tournament) {
    final status = tournament['status'] ?? 'upcoming';
    final startDate = tournament['start_date'] != null
        ? DateTime.tryParse(tournament['start_date'])
        : null;
    final dateFormat = DateFormat('dd MMM, yyyy');

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
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
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: _getStatusColor(status).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    Icons.emoji_events,
                    color: _getStatusColor(status),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        tournament['name'] ?? 'Turnir',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      Text(
                        '${tournament['participant_count'] ?? 0} ishtirokchi',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                _buildStatusBadge(status),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(Icons.calendar_today, size: 16, color: AppColors.textHint),
                const SizedBox(width: 4),
                Text(
                  startDate != null
                      ? dateFormat.format(startDate)
                      : 'Sanasi noma\'lum',
                  style: TextStyle(color: AppColors.textHint, fontSize: 12),
                ),
                const SizedBox(width: 16),
                Icon(Icons.timer, size: 16, color: AppColors.textHint),
                const SizedBox(width: 4),
                Text(
                  '${tournament['duration_minutes'] ?? 60} daqiqa',
                  style: TextStyle(color: AppColors.textHint, fontSize: 12),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.xpYellow.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.star, size: 14, color: AppColors.xpYellow),
                      const SizedBox(width: 4),
                      Text(
                        '+${tournament['xp_reward'] ?? 0} XP',
                        style: TextStyle(
                          color: AppColors.xpYellow,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                if (status == 'upcoming')
                  ElevatedButton(
                    onPressed: () => _joinTournament(tournament['id']),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 24, vertical: 8),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text('Qo\'shilish'),
                  )
                else if (status == 'in_progress')
                  ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.secondary,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Davom etish'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color color;
    String label;

    switch (status) {
      case 'upcoming':
        color = AppColors.accent;
        label = 'Kutilmoqda';
        break;
      case 'in_progress':
        color = AppColors.success;
        label = 'Davom etmoqda';
        break;
      case 'completed':
        color = AppColors.textHint;
        label = 'Yakunlangan';
        break;
      default:
        color = AppColors.textHint;
        label = status;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'upcoming':
        return AppColors.accent;
      case 'in_progress':
        return AppColors.success;
      case 'completed':
        return AppColors.textHint;
      default:
        return AppColors.primary;
    }
  }

  Future<void> _joinTournament(String tournamentId) async {
    try {
      final apiClient = getIt<ApiClient>();
      await apiClient.post('/tournaments/$tournamentId/join/');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Muvaffaqiyatli qo\'shildingiz!')),
        );
        _loadTournaments();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Xatolik yuz berdi')),
        );
      }
    }
  }
}
