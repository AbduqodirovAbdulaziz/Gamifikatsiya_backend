import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../data/repositories/gamification_repository.dart';

// Events
abstract class GamificationEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadProfile extends GamificationEvent {}

class LoadBadges extends GamificationEvent {}

class LoadLeaderboard extends GamificationEvent {
  final String period;
  final String? classroomId;

  LoadLeaderboard({this.period = 'weekly', this.classroomId});

  @override
  List<Object?> get props => [period, classroomId];
}

class ClaimDailyBonus extends GamificationEvent {}

class LoadDailyQuests extends GamificationEvent {}

// States
abstract class GamificationState extends Equatable {
  @override
  List<Object?> get props => [];
}

class GamificationInitial extends GamificationState {}

class GamificationLoading extends GamificationState {}

class GamificationLoaded extends GamificationState {
  final GamificationProfile profile;
  final List<Badge> earnedBadges;
  final List<DailyQuest> dailyQuests;
  final LeaderboardResponse? leaderboard;
  final bool bonusClaimed;
  final int? bonusXp;

  GamificationLoaded({
    required this.profile,
    this.earnedBadges = const [],
    this.dailyQuests = const [],
    this.leaderboard,
    this.bonusClaimed = false,
    this.bonusXp,
  });

  GamificationLoaded copyWith({
    GamificationProfile? profile,
    List<Badge>? earnedBadges,
    List<DailyQuest>? dailyQuests,
    LeaderboardResponse? leaderboard,
    bool? bonusClaimed,
    int? bonusXp,
  }) {
    return GamificationLoaded(
      profile: profile ?? this.profile,
      earnedBadges: earnedBadges ?? this.earnedBadges,
      dailyQuests: dailyQuests ?? this.dailyQuests,
      leaderboard: leaderboard ?? this.leaderboard,
      bonusClaimed: bonusClaimed ?? this.bonusClaimed,
      bonusXp: bonusXp ?? this.bonusXp,
    );
  }

  @override
  List<Object?> get props => [
    profile,
    earnedBadges,
    dailyQuests,
    leaderboard,
    bonusClaimed,
  ];
}

class GamificationError extends GamificationState {
  final String message;

  GamificationError(this.message);

  @override
  List<Object?> get props => [message];
}

// BLoC
class GamificationBloc extends Bloc<GamificationEvent, GamificationState> {
  final GamificationRepository _repository;

  GamificationBloc(this._repository) : super(GamificationInitial()) {
    on<LoadProfile>(_onLoadProfile);
    on<LoadBadges>(_onLoadBadges);
    on<LoadLeaderboard>(_onLoadLeaderboard);
    on<ClaimDailyBonus>(_onClaimDailyBonus);
    on<LoadDailyQuests>(_onLoadDailyQuests);
  }

  Future<void> _onLoadProfile(
    LoadProfile event,
    Emitter<GamificationState> emit,
  ) async {
    emit(GamificationLoading());
    try {
      final profile = await _repository.getProfile();
      final badges = await _repository.getEarnedBadges();
      final quests = await _repository.getDailyQuests();
      emit(
        GamificationLoaded(
          profile: profile,
          earnedBadges: badges,
          dailyQuests: quests,
        ),
      );
    } catch (e) {
      emit(GamificationError('Profilni yuklashda xatolik'));
    }
  }

  Future<void> _onLoadBadges(
    LoadBadges event,
    Emitter<GamificationState> emit,
  ) async {
    if (state is GamificationLoaded) {
      final currentState = state as GamificationLoaded;
      try {
        final badges = await _repository.getEarnedBadges();
        emit(currentState.copyWith(earnedBadges: badges));
      } catch (e) {
        // Ignore errors for badges
      }
    }
  }

  Future<void> _onLoadLeaderboard(
    LoadLeaderboard event,
    Emitter<GamificationState> emit,
  ) async {
    if (state is GamificationLoaded) {
      final currentState = state as GamificationLoaded;
      try {
        final leaderboard = await _repository.getLeaderboard(
          period: event.period,
          classroomId: event.classroomId,
        );
        emit(currentState.copyWith(leaderboard: leaderboard));
      } catch (e) {
        // Ignore errors for leaderboard
      }
    }
  }

  Future<void> _onClaimDailyBonus(
    ClaimDailyBonus event,
    Emitter<GamificationState> emit,
  ) async {
    if (state is GamificationLoaded) {
      final currentState = state as GamificationLoaded;
      try {
        final response = await _repository.claimDailyBonus();
        if (response.claimed) {
          emit(
            currentState.copyWith(
              bonusClaimed: true,
              bonusXp: response.xpEarned,
            ),
          );
          add(LoadProfile());
        }
      } catch (e) {
        // Ignore errors
      }
    }
  }

  Future<void> _onLoadDailyQuests(
    LoadDailyQuests event,
    Emitter<GamificationState> emit,
  ) async {
    if (state is GamificationLoaded) {
      final currentState = state as GamificationLoaded;
      try {
        final quests = await _repository.getDailyQuests();
        emit(currentState.copyWith(dailyQuests: quests));
      } catch (e) {
        // Ignore errors
      }
    }
  }
}
