import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/network/api_client.dart';

class ClassroomPage extends StatefulWidget {
  const ClassroomPage({super.key});

  @override
  State<ClassroomPage> createState() => _ClassroomPageState();
}

class _ClassroomPageState extends State<ClassroomPage> {
  List<dynamic> _classrooms = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadClassrooms();
  }

  Future<void> _loadClassrooms() async {
    try {
      final apiClient = getIt<ApiClient>();
      final response = await apiClient.get('/classrooms/');
      if (mounted) {
        setState(() {
          _classrooms = response.data['results'] ?? response.data ?? [];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sinfxonalar'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showJoinDialog(),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _classrooms.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.class_outlined,
                          size: 64, color: AppColors.textHint),
                      const SizedBox(height: 16),
                      Text(
                        'Hali sinfxonalar yo\'q',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: () => _showJoinDialog(),
                        icon: const Icon(Icons.add),
                        label: const Text('Qo\'shilish'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadClassrooms,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _classrooms.length,
                    itemBuilder: (context, index) {
                      return _buildClassroomCard(_classrooms[index]);
                    },
                  ),
                ),
    );
  }

  Widget _buildClassroomCard(dynamic classroom) {
    final name = classroom['name'] ?? 'Sinfxona';
    final subject = classroom['subject'] ?? '';
    final studentCount = classroom['student_count'] ?? 0;
    final teacher = classroom['teacher'] ?? {};
    final teacherName = teacher['username'] ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {},
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.school,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            name,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          if (subject.isNotEmpty)
                            Text(
                              subject,
                              style: TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 12,
                              ),
                            ),
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right, color: AppColors.textHint),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Icon(Icons.person, size: 16, color: AppColors.textHint),
                    const SizedBox(width: 4),
                    Text(
                      teacherName,
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Icon(Icons.people, size: 16, color: AppColors.textHint),
                    const SizedBox(width: 4),
                    Text(
                      '$studentCount o\'quvchi',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showJoinDialog() {
    final codeController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sinfxonaga qo\'shilish'),
        content: TextField(
          controller: codeController,
          decoration: const InputDecoration(
            labelText: 'Kod',
            hintText: 'Sinfxona kodini kiriting',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Bekor'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _joinClassroom(codeController.text);
            },
            child: const Text('Qo\'shilish'),
          ),
        ],
      ),
    );
  }

  Future<void> _joinClassroom(String code) async {
    try {
      final apiClient = getIt<ApiClient>();
      await apiClient.post('/classrooms/join/', data: {'code': code});
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Muvaffaqiyatli qo\'shildingiz!')),
        );
        _loadClassrooms();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Xatolik yuz berdi')),
        );
      }
    }
  }
}
