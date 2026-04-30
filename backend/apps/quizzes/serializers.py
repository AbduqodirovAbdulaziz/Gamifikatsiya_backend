from rest_framework import serializers
from .models import Quiz, Question, AnswerChoice, QuizAttempt, StudentAnswer


class AnswerChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = ["id", "choice_text", "is_correct", "order"]
        read_only_fields = ["id"]


class AnswerChoiceSerializerForStudent(serializers.ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = ["id", "choice_text", "order"]
        read_only_fields = ["id"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = AnswerChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "question_type",
            "image",
            "difficulty",
            "points",
            "time_limit_seconds",
            "explanation",
            "order",
            "choices",
        ]
        read_only_fields = ["id"]


class QuestionSerializerForStudent(serializers.ModelSerializer):
    choices = AnswerChoiceSerializerForStudent(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "question_type",
            "image",
            "difficulty",
            "points",
            "time_limit_seconds",
            "order",
            "choices",
        ]


class QuestionCreateSerializer(serializers.ModelSerializer):
    choices = AnswerChoiceSerializer(many=True, required=False)
    quiz = serializers.CharField(write_only=True, help_text="Quiz ID")

    class Meta:
        model = Question
        fields = [
            "quiz",
            "question_text",
            "question_type",
            "image",
            "difficulty",
            "points",
            "time_limit_seconds",
            "explanation",
            "order",
            "choices",
        ]

    def validate_choices(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Kamida 2 ta variant bo'lishi kerak")
        correct_count = sum(1 for choice in value if choice.get("is_correct"))
        if correct_count != 1:
            raise serializers.ValidationError(
                "Aynan bitta to'g'ri javob belgilanishi kerak"
            )
        return value

    def create(self, validated_data):
        choices_data = validated_data.pop("choices", [])
        # `quiz` may come from serializer.save(quiz=...) in the view.
        # Keep model instances and only drop raw string input to avoid NOT NULL quiz_id errors.
        quiz_value = validated_data.pop("quiz", None)
        question_kwargs = dict(validated_data)
        if isinstance(quiz_value, Quiz):
            question_kwargs["quiz"] = quiz_value
        question = Question.objects.create(**question_kwargs)
        for choice_data in choices_data:
            AnswerChoice.objects.create(question=question, **choice_data)
        return question


class QuizListSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)
    total_points = serializers.IntegerField(read_only=True)
    creator_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "quiz_type",
            "time_limit_seconds",
            "max_attempts",
            "pass_percentage",
            "xp_reward",
            "coin_reward",
            "is_active",
            "question_count",
            "total_points",
            "creator_name",
            "available_from",
            "available_until",
            "created_at",
        ]


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.IntegerField(read_only=True)
    total_points = serializers.IntegerField(read_only=True)
    creator_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    attempt_count = serializers.SerializerMethodField()
    best_score = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "course",
            "classroom",
            "quiz_type",
            "time_limit_seconds",
            "max_attempts",
            "pass_percentage",
            "xp_reward",
            "coin_reward",
            "is_active",
            "show_answers",
            "randomize_questions",
            "randomize_answers",
            "available_from",
            "available_until",
            "questions",
            "question_count",
            "total_points",
            "creator_name",
            "attempt_count",
            "best_score",
            "created_at",
        ]

    def get_attempt_count(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if user:
            return obj.attempts.filter(student=user).count()
        return 0

    def get_best_score(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if user:
            attempt = (
                obj.attempts.filter(student=user, is_completed=True)
                .order_by("-percentage")
                .first()
            )
            return attempt.percentage if attempt else None
        return None


class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            "title",
            "description",
            "course",
            "classroom",
            "quiz_type",
            "time_limit_seconds",
            "max_attempts",
            "pass_percentage",
            "xp_reward",
            "coin_reward",
            "show_answers",
            "randomize_questions",
            "randomize_answers",
            "available_from",
            "available_until",
        ]


class StudentAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(
        source="question.question_text", read_only=True
    )
    correct_answer = serializers.SerializerMethodField()
    explanation = serializers.CharField(source="question.explanation", read_only=True)

    class Meta:
        model = StudentAnswer
        fields = [
            "id",
            "question",
            "question_text",
            "selected_choice",
            "text_answer",
            "is_correct",
            "points_earned",
            "time_taken_seconds",
            "correct_answer",
            "explanation",
        ]

    def get_correct_answer(self, obj):
        correct = obj.question.choices.filter(is_correct=True).first()
        if correct:
            return AnswerChoiceSerializer(correct).data
        return None


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "attempt_number",
            "score",
            "total_points",
            "earned_points",
            "percentage",
            "is_passed",
            "time_taken_seconds",
            "started_at",
            "completed_at",
            "xp_earned",
            "coin_earned",
            "is_completed",
            "answers",
        ]


class QuizAttemptListSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "attempt_number",
            "percentage",
            "is_passed",
            "time_taken_seconds",
            "started_at",
            "completed_at",
            "xp_earned",
            "coin_earned",
            "is_completed",
        ]


class QuizStartSerializer(serializers.Serializer):
    quiz_id = serializers.UUIDField()


class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.DictField(), allow_empty=True, max_length=100
    )
    time_taken_seconds = serializers.IntegerField(min_value=0, max_value=7200)

    def validate_answers(self, value):
        normalized = []
        for answer in value:
            question_id = answer.get("question_id")
            selected_choice_id = answer.get("selected_choice_id") or answer.get("choice_id")
            normalized.append(
                {
                    "question_id": question_id,
                    "selected_choice_id": selected_choice_id,
                    "time_taken_seconds": answer.get("time_taken_seconds", 0),
                }
            )
        return normalized
