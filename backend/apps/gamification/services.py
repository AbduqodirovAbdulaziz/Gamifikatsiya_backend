import math
import random
from datetime import date, timedelta
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

from .models import (
    Badge,
    UserBadge,
    XPTransaction,
    LeaderboardEntry,
    Streak,
    DailyQuest,
    LevelTitle,
)


class GamificationService:
    @staticmethod
    @transaction.atomic
    def award_xp(user_id, amount, transaction_type, description, related_id=None):
        from apps.users.models import StudentProfile
        from apps.notifications.services import NotificationService

        try:
            profile = StudentProfile.objects.select_for_update().get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return None

        old_level = profile.level

        profile.xp_points += amount
        profile.total_points_earned += amount
        new_level = GamificationService.calculate_level(profile.xp_points)
        level_up = new_level > old_level
        profile.level = new_level
        profile.save()

        XPTransaction.objects.create(
            student_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            related_object_id=related_id,
        )

        GamificationService.update_leaderboard(user_id, amount)

        if level_up:
            level_title = GamificationService.get_level_title(profile.level)
            GamificationService.check_and_award_badges(
                user_id, "level_up", {"level": profile.level}
            )
            NotificationService.notify_level_up(
                str(user_id), profile.level, level_title
            )

        GamificationService.check_and_award_badges(user_id, transaction_type)

        return {
            "xp_earned": amount,
            "total_xp": profile.xp_points,
            "level": profile.level,
            "level_up": level_up,
            "new_badges": [],
        }

    @staticmethod
    def calculate_level(total_xp):
        return math.floor(math.sqrt(total_xp / 100)) + 1

    @staticmethod
    def calculate_xp_for_level(level):
        return (level - 1) ** 2 * 100

    @staticmethod
    def get_xp_progress(total_xp):
        level = GamificationService.calculate_level(total_xp)
        current_level_xp = GamificationService.calculate_xp_for_level(level)
        next_level_xp = GamificationService.calculate_xp_for_level(level + 1)
        xp_in_level = total_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        progress = (xp_in_level / xp_needed) * 100 if xp_needed > 0 else 100

        return {
            "level": level,
            "title": GamificationService.get_level_title(level),
            "current_xp": total_xp,
            "xp_in_level": xp_in_level,
            "xp_needed": xp_needed,
            "progress": min(progress, 100),
        }

    @staticmethod
    def get_level_title(level):
        try:
            return LevelTitle.objects.get(level=level).title
        except LevelTitle.DoesNotExist:
            titles = {
                1: "Yangi Talaba",
                2: "Izlovchi",
                3: "O'rganuvchi",
                5: "Bilimdon",
                8: "Ustoz Shogird",
                10: "Bilim Masteri",
                15: "Ilm Elchisi",
                20: "Akademik",
                30: "Grand Master",
            }
            return titles.get(level, f"Level {level}")

    @staticmethod
    @transaction.atomic
    def award_coins(user_id, amount, description, related_id=None):
        from apps.users.models import StudentProfile

        try:
            profile = StudentProfile.objects.select_for_update().get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return None

        profile.coins += amount
        profile.save()

        return {
            "coins_earned": amount,
            "total_coins": profile.coins,
        }

    @staticmethod
    @transaction.atomic
    def spend_coins(user_id, amount, description):
        from apps.users.models import StudentProfile

        if amount <= 0:
            return {"success": False, "error": "Coin miqdori musbat bo'lishi kerak"}

        try:
            profile = StudentProfile.objects.select_for_update().get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return {"success": False, "error": "Profil topilmadi"}

        if profile.coins < amount:
            return {
                "success": False,
                "error": "Yetarli coins yo'q",
                "required": amount,
                "available": profile.coins,
            }

        profile.coins -= amount
        profile.save()

        return {
            "success": True,
            "coins_spent": amount,
            "remaining_coins": profile.coins,
            "description": description,
        }

    @staticmethod
    @transaction.atomic
    def update_streak(user_id):
        from apps.notifications.services import NotificationService

        streak, _ = Streak.objects.get_or_create(student_id=user_id)
        today = date.today()

        if streak.last_activity_date == today:
            return streak

        if streak.last_activity_date == today - timedelta(days=1):
            streak.current_streak += 1
        elif (
            streak.last_activity_date
            and streak.last_activity_date < today - timedelta(days=1)
        ):
            if streak.streak_freeze_count > 0:
                streak.streak_freeze_count -= 1
            else:
                streak.current_streak = 1

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_activity_date = today
        streak.save()

        GamificationService.check_and_award_badges(
            user_id, "streak_updated", {"streak": streak.current_streak}
        )

        if streak.current_streak in [7, 30, 100]:
            bonus_xp = {7: 25, 30: 100, 100: 500}.get(streak.current_streak, 0)
            GamificationService.award_xp(
                user_id,
                bonus_xp,
                "streak_bonus",
                f"{streak.current_streak} kunlik streak bonus",
            )

        return streak

    @staticmethod
    def check_and_award_badges(user_id, event_type, context=None):
        from apps.users.models import StudentProfile
        from apps.notifications.services import NotificationService

        new_badges = []
        context = context or {}

        try:
            profile = StudentProfile.objects.get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return new_badges

        badges_to_check = Badge.objects.filter(is_active=True)

        for badge in badges_to_check:
            if UserBadge.objects.filter(student_id=user_id, badge=badge).exists():
                continue

            earned = False

            if badge.condition_type == "count":
                if event_type == "quiz_complete":
                    if profile.total_quizzes_completed >= badge.condition_value:
                        earned = True
                elif event_type == "lesson_complete":
                    if (
                        hasattr(profile, "lessons_completed")
                        and profile.lessons_completed >= badge.condition_value
                    ):
                        earned = True

            elif badge.condition_type == "streak":
                if event_type == "streak_updated":
                    streak = context.get("streak", 0)
                    if streak >= badge.condition_value:
                        earned = True
            elif badge.condition_type == "percentage":
                if event_type == "quiz_complete":
                    percentage = context.get("percentage", 0)
                    if percentage >= badge.condition_value:
                        earned = True

            if earned:
                user_badge = UserBadge.objects.create(student_id=user_id, badge=badge)
                new_badges.append(user_badge)

                NotificationService.notify_badge_earned(
                    str(user_id), badge.name, badge.icon.url if badge.icon else None
                )

                if badge.xp_bonus > 0:
                    GamificationService.award_xp(
                        user_id,
                        badge.xp_bonus,
                        "badge_earn",
                        f"{badge.name} badge uchun bonus",
                    )

                if badge.coin_bonus > 0:
                    GamificationService.award_coins(
                        user_id, badge.coin_bonus, f"{badge.name} badge uchun bonus"
                    )

        return new_badges

    @staticmethod
    def update_leaderboard(user_id, xp_amount=None):
        from apps.users.models import StudentProfile

        try:
            profile = StudentProfile.objects.get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return

        if xp_amount is None:
            xp_amount = profile.xp_points

        LeaderboardEntry.objects.update_or_create(
            student_id=user_id,
            classroom=None,
            period="all_time",
            defaults={"xp_points": profile.xp_points},
        )

        cache_key = f"leaderboard:all_time"
        try:
            from django_redis import get_redis_connection

            redis = get_redis_connection()
            redis.zadd(cache_key, {str(user_id): profile.xp_points})
        except:
            pass

    @staticmethod
    def get_leaderboard(period="weekly", classroom_id=None, limit=20, user_id=None):
        from apps.users.serializers import UserPublicSerializer

        if classroom_id:
            cache_key = f"leaderboard:{period}:class:{classroom_id}"
        else:
            cache_key = f"leaderboard:{period}:global"

        cached = cache.get(cache_key)
        if cached:
            entries = cached
        else:
            if classroom_id:
                from apps.classroom.models import Enrollment

                enrolled_students = Enrollment.objects.filter(
                    classroom_id=classroom_id, is_active=True
                ).select_related("student", "student__student_profile")

                entries = []
                for enrollment in enrolled_students:
                    profile = enrollment.student.student_profile
                    entries.append(
                        {
                            "student": UserPublicSerializer(enrollment.student).data,
                            "xp_points": profile.xp_points,
                            "level": profile.level,
                            "rank": 0,
                        }
                    )
            else:
                from apps.users.models import StudentProfile

                profiles = StudentProfile.objects.select_related("user").order_by(
                    "-xp_points"
                )[:limit]
                entries = [
                    {
                        "student": UserPublicSerializer(p.user).data,
                        "xp_points": p.xp_points,
                        "level": p.level,
                        "rank": 0,
                    }
                    for p in profiles
                ]

            entries.sort(key=lambda x: x["xp_points"], reverse=True)
            cache.set(cache_key, entries, 300)

        for i, entry in enumerate(entries, 1):
            entry["rank"] = i

        user_rank = None
        if user_id:
            for entry in entries:
                if entry["student"]["id"] == str(user_id):
                    user_rank = entry["rank"]
                    break

        return {"entries": entries, "user_rank": user_rank, "period": period}

    @staticmethod
    def claim_daily_bonus(user_id):
        today = date.today()
        cache_key = f"daily_bonus:{user_id}:{today}"

        if cache.get(cache_key):
            return {"claimed": False, "message": "Bugungi bonus allaqachon olingan"}

        bonus_xp = 5
        bonus_coins = 2

        GamificationService.award_xp(
            user_id, bonus_xp, "daily_bonus", "Kunlik kirish bonusi"
        )
        GamificationService.award_coins(user_id, bonus_coins, "Kunlik coins bonus")
        GamificationService.update_streak(user_id)

        cache.set(cache_key, True, 86400)

        return {"claimed": True, "xp_earned": bonus_xp, "coins_earned": bonus_coins}

    @staticmethod
    def generate_daily_quests(user_id):
        today = date.today()

        existing_quests = DailyQuest.objects.filter(student_id=user_id, date=today)
        if existing_quests.exists():
            return list(existing_quests)

        quests = [
            DailyQuest(
                student_id=user_id,
                quest_type="lesson",
                target_count=1,
                xp_reward=5,
                coin_reward=1,
                date=today,
            ),
            DailyQuest(
                student_id=user_id,
                quest_type="quiz",
                target_count=1,
                xp_reward=10,
                coin_reward=2,
                date=today,
            ),
            DailyQuest(
                student_id=user_id,
                quest_type="social",
                target_count=1,
                xp_reward=5,
                coin_reward=1,
                date=today,
            ),
            DailyQuest(
                student_id=user_id,
                quest_type="streak",
                target_count=1,
                xp_reward=3,
                coin_reward=1,
                date=today,
            ),
        ]

        DailyQuest.objects.bulk_create(quests)
        return quests

    @staticmethod
    @transaction.atomic
    def update_quest_progress(user_id, quest_type, increment=1):
        from apps.notifications.services import NotificationService

        today = date.today()

        try:
            quest = DailyQuest.objects.select_for_update().get(
                student_id=user_id, quest_type=quest_type, date=today
            )
        except DailyQuest.DoesNotExist:
            return None

        if quest.is_completed:
            return quest

        quest.current_count += increment
        if quest.current_count >= quest.target_count:
            quest.is_completed = True
            quest.completed_at = timezone.now()
            quest.save()

            GamificationService.award_xp(
                user_id,
                quest.xp_reward,
                "quest_complete",
                f"Kunlik vazifa: {quest.get_quest_type_display()}",
            )

            if hasattr(quest, "coin_reward") and quest.coin_reward:
                GamificationService.award_coins(
                    user_id, quest.coin_reward, f"Kunlik vazifa bonus"
                )

            all_completed = not DailyQuest.objects.filter(
                student_id=user_id, date=today, is_completed=False
            ).exists()

            if all_completed:
                GamificationService.award_xp(
                    user_id, 50, "daily_jackpot", "Barcha kunlik vazifalarni bajarish"
                )
                GamificationService.award_coins(user_id, 10, "Kunlik jackpot bonus")

        return quest

    @staticmethod
    @transaction.atomic
    def buy_streak_freeze(user_id):
        price = 50
        result = GamificationService.spend_coins(
            user_id, price, "Streak freeze sotib olish"
        )

        if result["success"]:
            streak, _ = Streak.objects.get_or_create(student_id=user_id)
            streak.streak_freeze_count += 1
            streak.save()

        return result

    @staticmethod
    def get_shop_items():
        return [
            {
                "id": "streak_freeze",
                "name": "Streak Freeze",
                "description": "Kunlik streak buzilishdan saqlaydi",
                "price": 50,
                "type": "consumable",
                "icon": "snowflake",
            },
            {
                "id": "xp_boost_small",
                "name": "XP Boost (Kichik)",
                "description": "30 daqiqa davomida 2x XP",
                "price": 100,
                "type": "consumable",
                "duration_minutes": 30,
                "multiplier": 2,
                "icon": "bolt",
            },
            {
                "id": "xp_boost_large",
                "name": "XP Boost (Katta)",
                "description": "60 daqiqa davomida 3x XP",
                "price": 200,
                "type": "consumable",
                "duration_minutes": 60,
                "multiplier": 3,
                "icon": "bolt",
            },
            {
                "id": "avatar_frame",
                "name": "Avatar Ramkasi",
                "description": "Profilingizda maxsus ramka",
                "price": 150,
                "type": "permanent",
                "icon": "frame",
            },
        ]

    @staticmethod
    @transaction.atomic
    def purchase_item(user_id, item_id):
        items = GamificationService.get_shop_items()
        item = next((i for i in items if i["id"] == item_id), None)

        if not item:
            return {"success": False, "error": "Mahsulot topilmadi"}

        result = GamificationService.spend_coins(
            user_id, item["price"], f"{item['name']} sotib olish"
        )

        if not result["success"]:
            return result

        if item["id"] == "streak_freeze":
            streak, _ = Streak.objects.get_or_create(student_id=user_id)
            streak.streak_freeze_count += 1
            streak.save()

        return {
            "success": True,
            "item": item,
            "coins_spent": item["price"],
            "remaining_coins": result["remaining_coins"],
        }

    @staticmethod
    def get_randomized_questions(quiz, limit=None):
        questions = list(quiz.questions.filter(is_active=True))

        if quiz.randomize_questions:
            random.shuffle(questions)

        if limit:
            questions = questions[:limit]

        if quiz.randomize_answers:
            for question in questions:
                choices = list(question.choices.all())
                random.shuffle(choices)
                question._cached_choices = choices

        return questions

    @staticmethod
    def get_progress_summary(student_id):
        """
        Returns shared progress summary contract for parent/teacher views.
        Includes: gamification, quiz_stats, courses_progress, badges, recent_activities
        """
        from apps.users.models import StudentProfile
        from apps.courses.models import CourseCompletion, LessonProgress
        from apps.quizzes.models import QuizAttempt
        from django.db.models import Avg, Count

        try:
            profile = StudentProfile.objects.get(user_id=student_id)
        except StudentProfile.DoesNotExist:
            profile = None

        # Gamification data
        gamification_data = {
            "xp_points": profile.xp_points if profile else 0,
            "level": profile.level if profile else 1,
            "coins": profile.coins if profile else 0,
            "streak_days": profile.streak_days if profile else 0,
        }

        # Quiz stats
        quiz_attempts = QuizAttempt.objects.filter(
            student_id=student_id, is_completed=True
        )
        quiz_stats = {
            "total_quizzes": quiz_attempts.count(),
            "average_score": float(
                quiz_attempts.aggregate(avg=Avg("percentage"))["avg"] or 0
            ),
            "total_correct_answers": profile.total_correct_answers if profile else 0,
        }

        # Course progress
        courses_completed = CourseCompletion.objects.filter(
            student_id=student_id
        ).count()
        lessons_completed = LessonProgress.objects.filter(
            student_id=student_id, is_completed=True
        ).count()
        courses_progress = {
            "courses_completed": courses_completed,
            "lessons_completed": lessons_completed,
        }

        # Badges
        badges = UserBadge.objects.filter(student_id=student_id).select_related(
            "badge"
        )
        badges_data = [
            {
                "id": str(badge.id),
                "name": badge.badge.name,
                "icon": badge.badge.icon.url if badge.badge.icon else None,
                "rarity": badge.badge.rarity,
                "earned_at": badge.earned_at.isoformat(),
            }
            for badge in badges
        ]

        # Recent activities (last 5 completed quizzes)
        recent_attempts = quiz_attempts.order_by("-completed_at")[:5]
        recent_activities = [
            {
                "type": "quiz_completed",
                "title": attempt.quiz.title if attempt.quiz else "Noma'lum",
                "score": attempt.percentage,
                "completed_at": attempt.completed_at.isoformat()
                if attempt.completed_at
                else None,
            }
            for attempt in recent_attempts
        ]

        return {
            "gamification": gamification_data,
            "quiz_stats": quiz_stats,
            "courses_progress": courses_progress,
            "badges": badges_data,
            "recent_activities": recent_activities,
        }
