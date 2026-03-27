import '../../../../core/network/api_client.dart';

class GamificationRepository {
  final ApiClient _apiClient;

  GamificationRepository(this._apiClient);

  Future<GamificationProfile> getProfile() async {
    final response = await _apiClient.get(ApiEndpoints.gamificationProfile);
    return GamificationProfile.fromJson(response.data);
  }

  Future<List<Badge>> getBadges() async {
    final response = await _apiClient.get(ApiEndpoints.badges);
    return (response.data as List).map((e) => Badge.fromJson(e)).toList();
  }

  Future<List<Badge>> getEarnedBadges() async {
    final response = await _apiClient.get(ApiEndpoints.earnedBadges);
    return (response.data as List)
        .map((e) => Badge.fromJson(e['badge']))
        .toList();
  }

  Future<List<XPTransaction>> getXPHistory() async {
    final response = await _apiClient.get(ApiEndpoints.xpHistory);
    return (response.data as List)
        .map((e) => XPTransaction.fromJson(e))
        .toList();
  }

  Future<Streak> getStreak() async {
    final response = await _apiClient.get(ApiEndpoints.streak);
    return Streak.fromJson(response.data);
  }

  Future<List<DailyQuest>> getDailyQuests() async {
    final response = await _apiClient.get(ApiEndpoints.quests);
    return (response.data as List).map((e) => DailyQuest.fromJson(e)).toList();
  }

  Future<LeaderboardResponse> getLeaderboard({
    String period = 'weekly',
    String? classroomId,
  }) async {
    final params = <String, dynamic>{'period': period};
    if (classroomId != null) params['classroom_id'] = classroomId;
    final response = await _apiClient.get(
      ApiEndpoints.leaderboard,
      queryParameters: params,
    );
    return LeaderboardResponse.fromJson(response.data);
  }

  Future<DailyBonusResponse> claimDailyBonus() async {
    final response = await _apiClient.post(ApiEndpoints.dailyBonus);
    return DailyBonusResponse.fromJson(response.data);
  }
}

class GamificationProfile {
  final int xpPoints;
  final int level;
  final String levelTitle;
  final int coins;
  final int streakDays;
  final int totalQuizzes;
  final int totalCorrect;
  final int? rankPosition;
  final int xpToNextLevel;
  final LevelProgress levelProgress;

  GamificationProfile({
    required this.xpPoints,
    required this.level,
    required this.levelTitle,
    required this.coins,
    required this.streakDays,
    required this.totalQuizzes,
    required this.totalCorrect,
    this.rankPosition,
    required this.xpToNextLevel,
    required this.levelProgress,
  });

  factory GamificationProfile.fromJson(Map<String, dynamic> json) {
    return GamificationProfile(
      xpPoints: json['xp_points'],
      level: json['level'],
      levelTitle: json['level_title'],
      coins: json['coins'],
      streakDays: json['streak_days'],
      totalQuizzes: json['total_quizzes'],
      totalCorrect: json['total_correct'],
      rankPosition: json['rank_position'],
      xpToNextLevel: json['xp_to_next_level'],
      levelProgress: LevelProgress.fromJson(json['level_progress']),
    );
  }
}

class LevelProgress {
  final int level;
  final String title;
  final int currentXp;
  final int xpInLevel;
  final int xpNeeded;
  final double progress;

  LevelProgress({
    required this.level,
    required this.title,
    required this.currentXp,
    required this.xpInLevel,
    required this.xpNeeded,
    required this.progress,
  });

  factory LevelProgress.fromJson(Map<String, dynamic> json) {
    return LevelProgress(
      level: json['level'],
      title: json['title'],
      currentXp: json['current_xp'],
      xpInLevel: json['xp_in_level'],
      xpNeeded: json['xp_needed'],
      progress: (json['progress'] as num).toDouble(),
    );
  }
}

class Badge {
  final String id;
  final String name;
  final String description;
  final String? icon;
  final String badgeType;
  final String rarity;
  final int xpBonus;

  Badge({
    required this.id,
    required this.name,
    required this.description,
    this.icon,
    required this.badgeType,
    required this.rarity,
    required this.xpBonus,
  });

  factory Badge.fromJson(Map<String, dynamic> json) {
    return Badge(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      icon: json['icon'],
      badgeType: json['badge_type'],
      rarity: json['rarity'],
      xpBonus: json['xp_bonus'],
    );
  }
}

class XPTransaction {
  final String id;
  final int amount;
  final String transactionType;
  final String description;
  final DateTime createdAt;

  XPTransaction({
    required this.id,
    required this.amount,
    required this.transactionType,
    required this.description,
    required this.createdAt,
  });

  factory XPTransaction.fromJson(Map<String, dynamic> json) {
    return XPTransaction(
      id: json['id'],
      amount: json['amount'],
      transactionType: json['transaction_type'],
      description: json['description'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class Streak {
  final int currentStreak;
  final int longestStreak;
  final DateTime? lastActivityDate;
  final int streakFreezeCount;

  Streak({
    required this.currentStreak,
    required this.longestStreak,
    this.lastActivityDate,
    required this.streakFreezeCount,
  });

  factory Streak.fromJson(Map<String, dynamic> json) {
    return Streak(
      currentStreak: json['current_streak'],
      longestStreak: json['longest_streak'],
      lastActivityDate: json['last_activity_date'] != null
          ? DateTime.parse(json['last_activity_date'])
          : null,
      streakFreezeCount: json['streak_freeze_count'],
    );
  }
}

class DailyQuest {
  final String id;
  final String questType;
  final String questTypeDisplay;
  final int targetCount;
  final int currentCount;
  final int xpReward;
  final bool isCompleted;
  final DateTime date;

  DailyQuest({
    required this.id,
    required this.questType,
    required this.questTypeDisplay,
    required this.targetCount,
    required this.currentCount,
    required this.xpReward,
    required this.isCompleted,
    required this.date,
  });

  factory DailyQuest.fromJson(Map<String, dynamic> json) {
    return DailyQuest(
      id: json['id'],
      questType: json['quest_type'],
      questTypeDisplay: json['quest_type_display'],
      targetCount: json['target_count'],
      currentCount: json['current_count'],
      xpReward: json['xp_reward'],
      isCompleted: json['is_completed'],
      date: DateTime.parse(json['date']),
    );
  }

  double get progress => currentCount / targetCount;
}

class LeaderboardEntry {
  final int rank;
  final LeaderboardStudent student;
  final int xpPoints;
  final int level;

  LeaderboardEntry({
    required this.rank,
    required this.student,
    required this.xpPoints,
    required this.level,
  });

  factory LeaderboardEntry.fromJson(Map<String, dynamic> json) {
    return LeaderboardEntry(
      rank: json['rank'],
      student: LeaderboardStudent.fromJson(json['student']),
      xpPoints: json['xp_points'],
      level: json['level'],
    );
  }
}

class LeaderboardStudent {
  final String id;
  final String username;
  final String? avatar;

  LeaderboardStudent({required this.id, required this.username, this.avatar});

  factory LeaderboardStudent.fromJson(Map<String, dynamic> json) {
    return LeaderboardStudent(
      id: json['id'],
      username: json['username'],
      avatar: json['avatar'],
    );
  }
}

class LeaderboardResponse {
  final String period;
  final String? classroomId;
  final List<LeaderboardEntry> entries;
  final int? userRank;

  LeaderboardResponse({
    required this.period,
    this.classroomId,
    required this.entries,
    this.userRank,
  });

  factory LeaderboardResponse.fromJson(Map<String, dynamic> json) {
    return LeaderboardResponse(
      period: json['period'],
      classroomId: json['classroom_id'],
      entries: (json['entries'] as List)
          .map((e) => LeaderboardEntry.fromJson(e))
          .toList(),
      userRank: json['user_rank'],
    );
  }
}

class DailyBonusResponse {
  final bool claimed;
  final int? xpEarned;
  final String? message;

  DailyBonusResponse({required this.claimed, this.xpEarned, this.message});

  factory DailyBonusResponse.fromJson(Map<String, dynamic> json) {
    return DailyBonusResponse(
      claimed: json['claimed'],
      xpEarned: json['xp_earned'],
      message: json['message'],
    );
  }
}
