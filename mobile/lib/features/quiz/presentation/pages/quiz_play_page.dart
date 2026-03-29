import 'dart:async';
import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/api_client.dart';
import '../widgets/question_card.dart';
import '../widgets/timer_widget.dart';
import '../widgets/answer_option.dart';
import 'quiz_result_page.dart';

class QuizPlayPage extends StatefulWidget {
  final String quizId;

  const QuizPlayPage({super.key, required this.quizId});

  @override
  State<QuizPlayPage> createState() => _QuizPlayPageState();
}

class _QuizPlayPageState extends State<QuizPlayPage> {
  List<dynamic> _questions = [];
  int _currentIndex = 0;
  int _correctAnswers = 0;
  int _timeRemaining = 0;
  Timer? _timer;
  bool _isLoading = true;
  bool _answered = false;
  String? _selectedAnswer;
  Map<int, String> _userAnswers = {};

  @override
  void initState() {
    super.initState();
    _loadQuiz();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _loadQuiz() async {
    try {
      final apiClient = getIt<ApiClient>();
      final response = await apiClient.get('/quizzes/${widget.quizId}/');
      if (mounted) {
        setState(() {
          _questions = response.data['questions'] ?? [];
          _timeRemaining = response.data['time_limit_seconds'] ?? 1800;
          _isLoading = false;
        });
        if (_timeRemaining > 0) {
          _startTimer();
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Xatolik yuz berdi')),
        );
      }
    }
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          if (_timeRemaining > 0) {
            _timeRemaining--;
          } else {
            _finishQuiz();
          }
        });
      }
    });
  }

  void _selectAnswer(String answer) {
    if (_answered) return;

    setState(() {
      _selectedAnswer = answer;
      _answered = true;
      _userAnswers[_currentIndex] = answer;

      final currentQuestion = _questions[_currentIndex];
      if (answer == currentQuestion['correct_answer']) {
        _correctAnswers++;
      }
    });
  }

  void _nextQuestion() {
    if (_currentIndex < _questions.length - 1) {
      setState(() {
        _currentIndex++;
        _answered = false;
        _selectedAnswer = null;
      });
    } else {
      _finishQuiz();
    }
  }

  void _finishQuiz() {
    _timer?.cancel();
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => QuizResultPage(
          totalQuestions: _questions.length,
          correctAnswers: _correctAnswers,
          quizId: widget.quizId,
          userAnswers: _userAnswers,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Test')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_questions.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Test')),
        body: const Center(child: Text('Savollar topilmadi')),
      );
    }

    final currentQuestion = _questions[_currentIndex];
    final answers = currentQuestion['answers'] as List<dynamic>? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: Text('Savol ${_currentIndex + 1}/${_questions.length}'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TimerWidget(seconds: _timeRemaining),
          ),
        ],
      ),
      body: Column(
        children: [
          LinearProgressIndicator(
            value: (_currentIndex + 1) / _questions.length,
            backgroundColor: AppColors.divider,
            valueColor: AlwaysStoppedAnimation(AppColors.primary),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  QuestionCard(
                    question: currentQuestion['question'] ?? '',
                    questionNumber: _currentIndex + 1,
                    totalQuestions: _questions.length,
                  ),
                  const SizedBox(height: 24),
                  ...answers.asMap().entries.map((entry) {
                    final index = entry.key;
                    final answer = entry.value;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: AnswerOption(
                        answer: answer,
                        index: index,
                        isSelected: _selectedAnswer == answer,
                        isCorrect: _answered &&
                            answer == currentQuestion['correct_answer'],
                        isWrong: _answered &&
                            _selectedAnswer == answer &&
                            answer != currentQuestion['correct_answer'],
                        onTap: () => _selectAnswer(answer),
                      ),
                    );
                  }),
                ],
              ),
            ),
          ),
          if (_answered)
            Padding(
              padding: const EdgeInsets.all(16),
              child: ElevatedButton(
                onPressed: _nextQuestion,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: Text(
                  _currentIndex < _questions.length - 1
                      ? 'Keyingi savol'
                      : 'Natijalarni ko\'rish',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
