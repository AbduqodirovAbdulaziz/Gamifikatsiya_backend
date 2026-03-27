import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/api_client.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../auth/presentation/pages/login_page.dart';
import '../../../courses/presentation/pages/courses_page.dart';
import '../../../quiz/presentation/pages/quiz_list_page.dart';
import '../../../gamification/presentation/pages/leaderboard_page.dart';
import '../../../competition/presentation/pages/challenge_page.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  int _currentIndex = 0;
  Map<String, dynamic>? _gamificationData;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadGamificationData();
  }

  Future<void> _loadGamificationData() async {
    try {
      final apiClient = getIt<ApiClient>();
      final response = await apiClient.get('/gamification/profile/');
      if (mounted) {
        setState(() {
          _gamificationData = response.data;
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
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) {
        if (state is AuthUnauthenticated) {
          Navigator.of(context).pushAndRemoveUntil(
            MaterialPageRoute(builder: (_) => const LoginPage()),
            (route) => false,
          );
        }
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text(AppStrings.appName),
          actions: [
            IconButton(
              icon: const Icon(Icons.notifications_outlined),
              onPressed: () {},
            ),
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: () {
                context.read<AuthBloc>().add(AuthLogoutRequested());
              },
            ),
          ],
        ),
        body: IndexedStack(
          index: _currentIndex,
          children: [
            _buildHomeTab(),
            const CoursesPage(),
            const QuizListPage(),
            const LeaderboardPage(),
            const ChallengePage(),
          ],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _currentIndex,
          onDestinationSelected: (index) {
            setState(() {
              _currentIndex = index;
            });
          },
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home),
              label: 'Home',
            ),
            NavigationDestination(
              icon: Icon(Icons.book_outlined),
              selectedIcon: Icon(Icons.book),
              label: 'Kurslar',
            ),
            NavigationDestination(
              icon: Icon(Icons.quiz_outlined),
              selectedIcon: Icon(Icons.quiz),
              label: 'Testlar',
            ),
            NavigationDestination(
              icon: Icon(Icons.leaderboard_outlined),
              selectedIcon: Icon(Icons.leaderboard),
              label: 'Reyting',
            ),
            NavigationDestination(
              icon: Icon(Icons.emoji_events_outlined),
              selectedIcon: Icon(Icons.emoji_events),
              label: 'Bellashuv',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHomeTab() {
    return RefreshIndicator(
      onRefresh: _loadGamificationData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildWelcomeCard(),
            const SizedBox(height: 16),
            _buildStatsRow(),
            const SizedBox(height: 16),
            _buildProgressCard(),
            const SizedBox(height: 16),
            _buildDailyQuestsCard(),
            const SizedBox(height: 16),
            _buildQuickActionsCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildWelcomeCard() {
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        String name = 'Foydalanuvchi';
        if (state is AuthAuthenticated) {
          name = state.user.username ?? 'Foydalanuvchi';
        }
        return Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppColors.primary, AppColors.primaryDark],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Text('👋', style: TextStyle(fontSize: 28)),
                  const SizedBox(width: 8),
                  Text(
                    'Salom, $name!',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '🔥 ${_gamificationData?['streak_days'] ?? 0} kunlik streak',
                style: const TextStyle(color: Colors.white70),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatsRow() {
    return Row(
      children: [
        Expanded(
            child: _buildStatCard(
          icon: Icons.star,
          iconColor: AppColors.xpYellow,
          label: 'XP',
          value: '${_gamificationData?['xp_points'] ?? 0}',
        )),
        const SizedBox(width: 12),
        Expanded(
            child: _buildStatCard(
          icon: Icons.military_tech,
          iconColor: AppColors.primary,
          label: 'Level',
          value: '${_gamificationData?['level'] ?? 1}',
        )),
        const SizedBox(width: 12),
        Expanded(
            child: _buildStatCard(
          icon: Icons.monetization_on,
          iconColor: AppColors.coinGold,
          label: 'Coins',
          value: '${_gamificationData?['coins'] ?? 0}',
        )),
      ],
    );
  }

  Widget _buildStatCard(
      {IconData? icon, Color? iconColor, String? label, String? value}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, color: iconColor, size: 28),
          const SizedBox(height: 8),
          Text(value ?? '0',
              style:
                  const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          Text(label ?? '',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildProgressCard() {
    final level = _gamificationData?['level'] ?? 1;
    final progress = _gamificationData?['level_progress'];
    final xpInLevel = progress?['xp_in_level'] ?? 0;
    final xpNeeded = progress?['xp_needed'] ?? 100;
    final percentage = xpNeeded > 0 ? (xpInLevel / xpNeeded) : 0.0;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Level $level - ${progress?['title'] ?? 'Yangi Talaba'}',
                style:
                    const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              Text('$xpInLevel / $xpNeeded XP',
                  style:
                      TextStyle(color: AppColors.textSecondary, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: percentage.clamp(0.0, 1.0),
              minHeight: 12,
              backgroundColor: AppColors.divider,
              valueColor: AlwaysStoppedAnimation(
                  AppColors.levelColors[level % AppColors.levelColors.length]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDailyQuestsCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.assignment, color: AppColors.accent),
              SizedBox(width: 8),
              Text('Kunlik vazifalar',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ],
          ),
          const SizedBox(height: 16),
          _buildQuestItem(Icons.book, '1 ta dars o\'qi', false, '+5 XP'),
          const SizedBox(height: 8),
          _buildQuestItem(Icons.quiz, '1 ta test yech', false, '+10 XP'),
          const SizedBox(height: 8),
          _buildQuestItem(Icons.group, 'Do\'stga challenge', false, '+5 XP'),
        ],
      ),
    );
  }

  Widget _buildQuestItem(
      IconData? icon, String? title, bool isCompleted, String? reward) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: isCompleted
            ? AppColors.success.withOpacity(0.1)
            : AppColors.background,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(icon,
              size: 20,
              color: isCompleted ? AppColors.success : AppColors.textSecondary),
          const SizedBox(width: 12),
          Expanded(
              child: Text(title ?? '',
                  style: TextStyle(
                      color: isCompleted
                          ? AppColors.success
                          : AppColors.textPrimary))),
          Text(reward ?? '',
              style: TextStyle(
                  color: isCompleted ? AppColors.success : AppColors.xpYellow,
                  fontWeight: FontWeight.w600)),
          const SizedBox(width: 8),
          Icon(isCompleted ? Icons.check_circle : Icons.circle_outlined,
              color: isCompleted ? AppColors.success : AppColors.textHint,
              size: 20),
        ],
      ),
    );
  }

  Widget _buildQuickActionsCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Tezkor harakatlar',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                  child: _buildActionButton(
                      Icons.play_arrow, 'Test boshlash', AppColors.primary)),
              const SizedBox(width: 12),
              Expanded(
                  child: _buildActionButton(
                      Icons.emoji_events, 'Bellashuv', AppColors.accent)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(IconData? icon, String? label, Color? color) {
    return ElevatedButton.icon(
      onPressed: () {},
      icon: Icon(icon),
      label: Text(label ?? ''),
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
