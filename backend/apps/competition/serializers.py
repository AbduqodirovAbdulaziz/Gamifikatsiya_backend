from rest_framework import serializers
from .models import Tournament, TournamentParticipant, Challenge, ChallengeAttempt


class TournamentParticipantSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source="student.username", read_only=True)
    student_avatar = serializers.ImageField(source="student.avatar", read_only=True)
    level = serializers.IntegerField(
        source="student.student_profile.level", read_only=True
    )

    class Meta:
        model = TournamentParticipant
        fields = [
            "id",
            "student",
            "student_username",
            "student_avatar",
            "level",
            "score",
            "rank_position",
            "registered_at",
        ]


class TournamentListSerializer(serializers.ModelSerializer):
    participant_count = serializers.IntegerField(read_only=True)
    creator_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "description",
            "tournament_type",
            "status",
            "max_participants",
            "participant_count",
            "start_time",
            "end_time",
            "first_prize_xp",
            "second_prize_xp",
            "third_prize_xp",
            "creator_name",
            "created_at",
        ]


class TournamentDetailSerializer(serializers.ModelSerializer):
    participants = TournamentParticipantSerializer(many=True, read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "description",
            "classroom",
            "quiz",
            "quiz_title",
            "tournament_type",
            "status",
            "max_participants",
            "participant_count",
            "participants",
            "start_time",
            "end_time",
            "first_prize_xp",
            "second_prize_xp",
            "third_prize_xp",
            "created_by",
            "created_at",
            "updated_at",
        ]


class TournamentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = [
            "title",
            "description",
            "quiz",
            "classroom",
            "tournament_type",
            "max_participants",
            "start_time",
            "end_time",
            "first_prize_xp",
            "second_prize_xp",
            "third_prize_xp",
        ]


class TournamentStandingsSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    student_id = serializers.UUIDField()
    username = serializers.CharField()
    avatar = serializers.ImageField(allow_null=True)
    level = serializers.IntegerField()
    score = serializers.FloatField()
    is_current_user = serializers.BooleanField()


class ChallengeSerializer(serializers.ModelSerializer):
    challenger_username = serializers.CharField(
        source="challenger.username", read_only=True
    )
    challenger_avatar = serializers.ImageField(
        source="challenger.avatar", read_only=True
    )
    challenger_level = serializers.IntegerField(
        source="challenger.student_profile.level", read_only=True
    )
    opponent_username = serializers.CharField(
        source="opponent.username", read_only=True
    )
    opponent_avatar = serializers.ImageField(source="opponent.avatar", read_only=True)
    opponent_level = serializers.IntegerField(
        source="opponent.student_profile.level", read_only=True
    )
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    expires_in_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "challenger",
            "challenger_username",
            "challenger_avatar",
            "challenger_level",
            "opponent",
            "opponent_username",
            "opponent_avatar",
            "opponent_level",
            "quiz",
            "quiz_title",
            "classroom",
            "status",
            "challenger_score",
            "opponent_score",
            "winner",
            "xp_stake",
            "expires_at",
            "expires_in_seconds",
            "created_at",
        ]

    def get_expires_in_seconds(self, obj):
        from django.utils import timezone

        delta = obj.expires_at - timezone.now()
        return max(0, int(delta.total_seconds()))


class ChallengeCreateSerializer(serializers.Serializer):
    opponent_id = serializers.UUIDField()
    quiz_id = serializers.UUIDField()
    xp_stake = serializers.IntegerField(default=10, min_value=1, max_value=100)


class ChallengeResultSerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField()
    winner_id = serializers.UUIDField()
    challenger_score = serializers.FloatField()
    opponent_score = serializers.FloatField()
    xp_transferred = serializers.IntegerField()
