from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Tournament, TournamentParticipant, Challenge, ChallengeAttempt
from .serializers import (
    TournamentListSerializer,
    TournamentDetailSerializer,
    TournamentCreateSerializer,
    TournamentStandingsSerializer,
    TournamentParticipantSerializer,
    ChallengeSerializer,
    ChallengeCreateSerializer,
)
from apps.quizzes.models import QuizAttempt


def check_challenge_access(challenge, user):
    if user.role == "admin" or user.is_staff:
        return True
    return challenge.challenger == user or challenge.opponent == user


class TournamentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return Tournament.objects.filter(created_by=user)
        return Tournament.objects.filter(
            classroom__enrollments__student=user, classroom__enrollments__is_active=True
        ).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return TournamentListSerializer
        elif self.action == "create":
            return TournamentCreateSerializer
        return TournamentDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        tournament = self.get_object()
        user = request.user

        if tournament.status != "upcoming":
            return Response(
                {"error": "Turnirga qo'shilish mumkin emas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if tournament.participant_count >= tournament.max_participants:
            return Response(
                {"error": "Turnir to'lgan"}, status=status.HTTP_400_BAD_REQUEST
            )

        participant, created = TournamentParticipant.objects.get_or_create(
            tournament=tournament, student=user
        )

        if not created:
            return Response(
                {"error": "Siz allaqachon bu turnirga qo'shilgansiz"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Turnirga muvaffaqiyatli qo'shildingiz",
                "participant": TournamentParticipantSerializer(participant).data,
            }
        )

    @action(detail=True, methods=["get"])
    def standings(self, request, pk=None):
        tournament = self.get_object()
        participants = (
            tournament.participants.filter(is_active=True)
            .select_related("student__student_profile")
            .order_by("-score", "completed_at")
        )

        standings = []
        for rank, participant in enumerate(participants, 1):
            participant.rank_position = rank
            participant.save()
            standings.append(
                {
                    "rank": rank,
                    "student_id": str(participant.student.id),
                    "username": participant.student.username,
                    "avatar": participant.student.avatar.url
                    if participant.student.avatar
                    else None,
                    "level": participant.student.student_profile.level
                    if hasattr(participant.student, "student_profile")
                    else 1,
                    "score": participant.score,
                    "is_current_user": participant.student == request.user,
                }
            )

        return Response(standings)

    @action(detail=True, methods=["post"])
    def submit_score(self, request, pk=None):
        tournament = self.get_object()
        user = request.user
        score = request.data.get("score", 0)

        participant = get_object_or_404(
            TournamentParticipant, tournament=tournament, student=user
        )

        if participant.completed_at:
            return Response(
                {"error": "Siz allaqachon ball topshirdingiz"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant.score = score
        participant.completed_at = timezone.now()
        participant.save()

        all_completed = not tournament.participants.filter(
            is_active=True, completed_at__isnull=True
        ).exists()

        if all_completed:
            tournament.status = "finished"
            tournament.save()
            self._award_prizes(tournament)

        return Response({"message": "Ball qabul qilindi", "score": score})

    def _award_prizes(self, tournament):
        from apps.gamification.services import GamificationService

        standings = tournament.participants.filter(is_active=True).order_by("-score")[
            :3
        ]

        prizes = {
            1: tournament.first_prize_xp,
            2: tournament.second_prize_xp,
            3: tournament.third_prize_xp,
        }

        for rank, participant in enumerate(standings, 1):
            xp_prize = prizes.get(rank, 0)
            if xp_prize > 0:
                GamificationService.award_xp(
                    participant.student.id,
                    xp_prize,
                    "tournament_win",
                    f"{tournament.title} turnirida {rank}-o'rin",
                )


class ChallengeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChallengeSerializer

    def get_queryset(self):
        user = self.request.user
        return Challenge.objects.filter(
            Q(challenger=user) | Q(opponent=user)
        ).distinct()

    def create(self, request):
        serializer = ChallengeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        opponent_id = serializer.validated_data["opponent_id"]
        quiz_id = serializer.validated_data["quiz_id"]
        xp_stake = serializer.validated_data["xp_stake"]

        if str(opponent_id) == str(user.id):
            return Response(
                {"error": "O'zingizga challenge yubora olmaysiz"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at = timezone.now() + timezone.timedelta(hours=24)

        challenge = Challenge.objects.create(
            challenger=user,
            opponent_id=opponent_id,
            quiz_id=quiz_id,
            xp_stake=xp_stake,
            expires_at=expires_at,
        )

        return Response(
            ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        challenge = self.get_object()
        user = request.user

        if challenge.opponent != user:
            return Response(
                {"error": "Faqat qabul qiluvchi qabul qilishi mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if challenge.status != "pending":
            return Response(
                {"error": "Challenge holatini o'zgartirib bo'lmaydi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        challenge.status = "accepted"
        challenge.save()

        return Response({"message": "Challenge qabul qilindi"})

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        challenge = self.get_object()
        user = request.user

        if challenge.opponent != user:
            return Response(
                {"error": "Faqat qabul qiluvchi rad qilishi mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        challenge.status = "declined"
        challenge.save()

        return Response({"message": "Challenge rad qilindi"})

    @action(detail=True, methods=["post"])
    def submit_result(self, request, pk=None):
        challenge = self.get_object()
        user = request.user
        score = request.data.get("score", 0)

        if score < 0:
            return Response(
                {"error": "Score manfiy bo'lishi mumkin emas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if challenge.expires_at and timezone.now() > challenge.expires_at:
            return Response(
                {"error": "Challenge muddati o'tgan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if challenge.status == "completed":
            return Response(
                {"error": "Challenge yakunlangan"}, status=status.HTTP_400_BAD_REQUEST
            )

        if challenge.challenger == user:
            challenge.challenger_score = score
        elif challenge.opponent == user:
            challenge.opponent_score = score
        else:
            return Response(
                {"error": "Siz bu challengeda ishtirok etmaysiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        challenge.status = "in_progress"
        challenge.save()

        if (
            challenge.challenger_score is not None
            and challenge.opponent_score is not None
        ):
            if challenge.challenger_score > challenge.opponent_score:
                challenge.winner = challenge.challenger
            elif challenge.opponent_score > challenge.challenger_score:
                challenge.winner = challenge.opponent
            else:
                challenge.winner = None

            challenge.status = "completed"
            challenge.completed_at = timezone.now()
            challenge.save()

            from apps.gamification.services import GamificationService

            if challenge.winner:
                GamificationService.award_xp(
                    challenge.winner.id,
                    challenge.xp_stake,
                    "challenge_win",
                    f"Challenge g'alabasi",
                )

        return Response(
            {
                "message": "Natija qabul qilildi",
                "challenger_score": challenge.challenger_score,
                "opponent_score": challenge.opponent_score,
            }
        )

    @action(detail=False, methods=["get"])
    def pending(self, request):
        challenges = Challenge.objects.filter(
            opponent=request.user, status="pending"
        ).select_related("challenger", "quiz")
        return Response(ChallengeSerializer(challenges, many=True).data)

    @action(detail=False, methods=["get"])
    def sent(self, request):
        challenges = Challenge.objects.filter(challenger=request.user).select_related(
            "opponent", "quiz"
        )
        return Response(ChallengeSerializer(challenges, many=True).data)
