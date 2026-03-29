from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GamificationProfileView,
    BadgeViewSet,
    UserBadgeViewSet,
    XPHistoryView,
    CoinHistoryView,
    StreakView,
    DailyQuestView,
    LeaderboardView,
    DailyBonusView,
    UpdateQuestProgressView,
    CheckLevelUpView,
    ShopView,
    PurchaseView,
    BuyStreakFreezeView,
)

router = DefaultRouter()
router.register(r"badges", BadgeViewSet, basename="badge")
router.register(r"user-badges", UserBadgeViewSet, basename="user-badge")

urlpatterns = [
    path("profile/", GamificationProfileView.as_view(), name="gamification-profile"),
    path("xp-history/", XPHistoryView.as_view(), name="xp-history"),
    path("coin-history/", CoinHistoryView.as_view(), name="coin-history"),
    path("streak/", StreakView.as_view(), name="streak"),
    path("quests/", DailyQuestView.as_view(), name="daily-quests"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("daily-bonus/", DailyBonusView.as_view(), name="daily-bonus"),
    path("update-quest/", UpdateQuestProgressView.as_view(), name="update-quest"),
    path("level-up/", CheckLevelUpView.as_view(), name="check-level-up"),
    path("shop/", ShopView.as_view(), name="shop"),
    path("purchase/", PurchaseView.as_view(), name="purchase"),
    path("buy-streak-freeze/", BuyStreakFreezeView.as_view(), name="buy-streak-freeze"),
    path("", include(router.urls)),
]
