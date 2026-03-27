from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import (
    Badge,
    UserBadge,
    XPTransaction,
    Streak,
    DailyQuest,
    LeaderboardEntry,
)
from .serializers import (
    BadgeSerializer,
    UserBadgeSerializer,
    XPTransactionSerializer,
    StreakSerializer,
    DailyQuestSerializer,
    GamificationProfileSerializer,
    LeaderboardSerializer,
)
from .services import GamificationService


class GamificationProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        from apps.users.models import StudentProfile

        try:
            profile = StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            profile = StudentProfile.objects.create(user=user)

        xp_progress = GamificationService.get_xp_progress(profile.xp_points)

        data = {
            "xp_points": profile.xp_points,
            "level": profile.level,
            "level_title": xp_progress["title"],
            "level_progress": xp_progress,
            "coins": profile.coins,
            "streak_days": profile.streak_days,
            "total_quizzes": profile.total_quizzes_completed,
            "total_correct": profile.total_correct_answers,
            "rank_position": profile.rank_position,
            "xp_to_next_level": xp_progress["xp_needed"] - xp_progress["xp_in_level"],
        }

        return Response(data)


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BadgeSerializer
    queryset = Badge.objects.filter(is_active=True)


class UserBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserBadgeSerializer

    def get_queryset(self):
        return UserBadge.objects.filter(student=self.request.user)

    @action(detail=False, methods=["get"])
    def earned(self, request):
        badges = self.get_queryset().select_related("badge")
        serializer = self.get_serializer(badges, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def toggle_display(self, request, pk=None):
        user_badge = self.get_object()
        user_badge.is_displayed = not user_badge.is_displayed
        user_badge.save()
        return Response({"is_displayed": user_badge.is_displayed})


class XPHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = XPTransactionSerializer

    def get_queryset(self):
        return XPTransaction.objects.filter(student=self.request.user)[:50]


class StreakView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StreakSerializer

    def get_object(self):
        streak, _ = Streak.objects.get_or_create(student=self.request.user)
        return streak


class DailyQuestView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DailyQuestSerializer

    def get_queryset(self):
        from datetime import date

        today = date.today()
        quests = DailyQuest.objects.filter(student=self.request.user, date=today)

        if not quests.exists():
            quests = GamificationService.generate_daily_quests(self.request.user)
            quests = DailyQuest.objects.filter(student=self.request.user, date=today)

        return quests


class LeaderboardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LeaderboardSerializer

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "weekly")
        classroom_id = request.query_params.get("classroom_id")

        entries = GamificationService.get_leaderboard(period, classroom_id)

        user_rank = None
        user_id = str(request.user.id)
        for entry in entries:
            if str(entry.get("student", {}).get("id")) == user_id:
                user_rank = entry.get("rank")
                break

        return Response(
            {
                "period": period,
                "classroom_id": classroom_id,
                "entries": entries,
                "user_rank": user_rank,
            }
        )


class DailyBonusView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result = GamificationService.claim_daily_bonus(request.user.id)
        return Response(result)


class UpdateQuestProgressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        quest_type = request.data.get("quest_type")
        increment = request.data.get("increment", 1)

        if not quest_type:
            return Response(
                {"error": "quest_type talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quest = GamificationService.update_quest_progress(
            request.user.id, quest_type, increment
        )

        if not quest:
            return Response(
                {"error": "Vazifa topilmadi"}, status=status.HTTP_404_NOT_FOUND
            )

        from .serializers import DailyQuestSerializer

        return Response(DailyQuestSerializer(quest).data)


class CheckLevelUpView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.users.models import StudentProfile

        profile = get_object_or_404(StudentProfile, user=request.user)
        xp_progress = GamificationService.get_xp_progress(profile.xp_points)

        return Response(
            {
                "level": profile.level,
                "level_title": xp_progress["title"],
                "xp_points": profile.xp_points,
                "progress": xp_progress,
            }
        )
