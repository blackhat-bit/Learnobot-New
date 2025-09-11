// lib/screens/teacher/student_profile_screen.dart
import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../models/student.dart';
import '../../models/chat_message.dart';
import '../../services/analytics_service.dart';
import '../../services/auth_service_backend.dart';

class StudentProfileScreen extends StatefulWidget {
  final Student student;
  
  const StudentProfileScreen({
    Key? key,
    required this.student,
  }) : super(key: key);

  @override
  State<StudentProfileScreen> createState() => _StudentProfileScreenState();
}

class _StudentProfileScreenState extends State<StudentProfileScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<ChatMessage> _conversationHistory = [];
  Map<String, dynamic>? _studentAnalytics;
  bool _isLoadingAnalytics = true;
  bool _isLoadingHistory = true;
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadStudentData();
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }
  
  Future<void> _loadStudentData() async {
    await Future.wait([
      _loadStudentAnalytics(),
      _loadConversationHistory(),
    ]);
  }

  Future<void> _loadStudentAnalytics() async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      final analytics = await AnalyticsService.getStudentAnalytics(
        studentId: int.parse(widget.student.id),
        token: token,
      );
      
      setState(() {
        _studentAnalytics = analytics;
        _isLoadingAnalytics = false;
      });
    } catch (e) {
      print('Error loading student analytics: $e');
      setState(() {
        _isLoadingAnalytics = false;
      });
    }
  }

  Future<void> _loadConversationHistory() async {
    try {
      // TODO: Implement real chat history API call
      // For now, show empty history until we have the API endpoint
      setState(() {
        _conversationHistory = [];
        _isLoadingHistory = false;
      });
    } catch (e) {
      print('Error loading conversation history: $e');
      setState(() {
        _isLoadingHistory = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(AppStrings.studentProfile),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () {
              _showEditProfileDialog(context);
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: AppStrings.personalDetails),
            Tab(text: AppStrings.conversationHistory),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Personal Details Tab
          _buildPersonalDetailsTab(),
          
          // Conversation History Tab
          _buildConversationHistoryTab(),
        ],
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
        color: AppColors.primary,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Back Button
            TextButton.icon(
              onPressed: () {
                Navigator.pop(context);
              },
              icon: const Icon(Icons.arrow_back, color: Colors.white),
              label: const Text(
                AppStrings.back,
                style: TextStyle(color: Colors.white),
              ),
            ),
            
            // View Profile Button (removed unwanted chat button)
            ElevatedButton.icon(
              onPressed: () {
                // Just close this screen or show info
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('פרופיל תלמיד - ניתן לערוך פרטים'),
                    backgroundColor: Colors.blue,
                  ),
                );
              },
              icon: const Icon(Icons.info_outline),
              label: const Text('פרטי תלמיד'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: AppColors.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildPersonalDetailsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Student Info Card
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  // Avatar
                  CircleAvatar(
                    radius: 50,
                    backgroundColor: AppColors.primaryLight,
                    child: Text(
                      widget.student.name.substring(0, 1),
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 36,
                      ),
                    ),
                  ),
                  const SizedBox(height: 15),
                  
                  // Name
                  Text(
                    widget.student.name,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 5),
                  
                  // Grade
                  Text(
                    'כיתה: ${widget.student.grade}',
                    style: const TextStyle(
                      fontSize: 16,
                      color: AppColors.textLight,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  
                  // Difficulty Level
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text(
                        'רמת קושי בהבנת הוראות:',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(width: 10),
                      _buildDifficultyIndicator(widget.student.difficultyLevel),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 25),
          
          // Description Section
          const Text(
            'תיאור קשיים:',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.right,
          ),
          const SizedBox(height: 10),
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            child: Padding(
              padding: const EdgeInsets.all(15),
              child: Text(
                widget.student.description.isNotEmpty
                    ? widget.student.description
                    : 'אין תיאור קשיים',
                style: const TextStyle(
                  fontSize: 16,
                  height: 1.5,
                ),
                textAlign: TextAlign.right,
              ),
            ),
          ),
          const SizedBox(height: 25),
          
          // Statistics Section
          const Text(
            'סטטיסטיקות שימוש:',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.right,
          ),
          const SizedBox(height: 10),
          _buildStatisticsCard(),
        ],
      ),
    );
  }
  
  Widget _buildDifficultyIndicator(int level) {
    final List<Color> colors = [
      Colors.green,
      Colors.lightGreen,
      Colors.orange,
      Colors.deepOrange,
      Colors.red,
    ];
    
    return Row(
      children: List.generate(
        5,
        (index) => Container(
          width: 20,
          height: 20,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          decoration: BoxDecoration(
            color: index < level ? colors[index] : Colors.grey.shade300,
            borderRadius: BorderRadius.circular(3),
          ),
        ),
      ),
    );
  }
  
  Widget _buildStatisticsCard() {
    if (_isLoadingAnalytics) {
      return Card(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Padding(
          padding: EdgeInsets.all(20),
          child: Center(
            child: CircularProgressIndicator(),
          ),
        ),
      );
    }

    final summary = _studentAnalytics?['summary'] ?? {};
    final engagement = _studentAnalytics?['engagement_metrics'] ?? {};
    final assistance = _studentAnalytics?['assistance_usage'] ?? {};

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
      ),
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          children: [
            _buildStatisticRow('מספר שיחות', '${summary['total_sessions'] ?? 0}'),
            const Divider(),
            _buildStatisticRow('זמן כולל', '${summary['total_time_minutes'] ?? 0} דקות'),
            const Divider(),
            _buildStatisticRow('מספר הודעות', '${summary['total_messages'] ?? 0}'),
            const Divider(),
            _buildStatisticRow('זמן ממוצע לשיחה', '${summary['average_session_duration_minutes']?.toStringAsFixed(1) ?? '0'} דקות'),
            const Divider(),
            _buildStatisticRow('דירוג ממוצע', '${engagement['average_satisfaction']?.toStringAsFixed(1) ?? 'N/A'}/5'),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatisticRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 16,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildConversationHistoryTab() {
    if (_isLoadingHistory) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }
    
    return _conversationHistory.isEmpty
        ? const Center(
            child: Text(
              'אין היסטוריית שיחות',
              style: TextStyle(color: AppColors.textLight, fontSize: 16),
            ),
          )
        : ListView.builder(
            padding: const EdgeInsets.all(15),
            itemCount: (_conversationHistory.length / 2).ceil(),
            itemBuilder: (context, index) {
              final startIndex = index * 2;
              if (startIndex >= _conversationHistory.length) return null;
              
              final conversation = _conversationHistory[startIndex];
              final dateString = _formatDate(conversation.timestamp);
              
              return Card(
                margin: const EdgeInsets.only(bottom: 15),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
                child: InkWell(
                  onTap: () {
                    // View full conversation
                    _showConversationDialog(context, startIndex);
                  },
                  borderRadius: BorderRadius.circular(10),
                  child: Padding(
                    padding: const EdgeInsets.all(15),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Date and Time
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              dateString,
                              style: const TextStyle(
                                color: AppColors.textLight,
                                fontSize: 14,
                              ),
                            ),
                            const Icon(
                              Icons.arrow_forward_ios,
                              size: 16,
                              color: AppColors.textLight,
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        
                        // Conversation Preview
                        Text(
                          conversation.content,
                          style: const TextStyle(fontSize: 16),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.right,
                        ),
                        if (startIndex + 1 < _conversationHistory.length) ...[
                          const SizedBox(height: 5),
                          Text(
                            _conversationHistory[startIndex + 1].content,
                            style: const TextStyle(
                              fontSize: 14,
                              color: AppColors.textLight,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            textAlign: TextAlign.right,
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              );
            },
          );
  }
  
  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inDays == 0) {
      return 'היום, ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } else if (difference.inDays == 1) {
      return 'אתמול, ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    } else if (difference.inDays < 7) {
      return 'לפני ${difference.inDays} ימים';
    } else {
      return '${date.day}/${date.month}/${date.year}';
    }
  }
  
  void _showConversationDialog(BuildContext context, int startIndex) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(15),
        ),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'שיחה',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 15),
              
              // Conversation messages
              SizedBox(
                height: 300,
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  itemCount: 5, // Show max 5 messages from the conversation
                  itemBuilder: (context, index) {
                    final messageIndex = startIndex + index;
                    if (messageIndex >= _conversationHistory.length) return null;
                    
                    final message = _conversationHistory[messageIndex];
                    final isStudent = message.sender == SenderType.student;
                    
                    return Align(
                      alignment: isStudent
                          ? Alignment.centerLeft
                          : Alignment.centerRight,
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: isStudent
                              ? AppColors.userBubble
                              : AppColors.botBubble,
                          borderRadius: BorderRadius.circular(15),
                        ),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.6,
                        ),
                        child: Text(
                          message.content,
                          style: const TextStyle(fontSize: 14),
                        ),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 15),
              
              // Close button
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('סגור'),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  void _showEditProfileDialog(BuildContext context) {
    final TextEditingController nameController = TextEditingController(
      text: widget.student.name,
    );
    final TextEditingController gradeController = TextEditingController(
      text: widget.student.grade,
    );
    final TextEditingController descriptionController = TextEditingController(
      text: widget.student.description,
    );
    int selectedDifficulty = widget.student.difficultyLevel;
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  AppStrings.updateDetails,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                
                // Name Field
                TextField(
                  controller: nameController,
                  textDirection: TextDirection.rtl,
                  decoration: const InputDecoration(
                    labelText: 'שם תלמיד',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 15, 
                      vertical: 10,
                    ),
                  ),
                ),
                const SizedBox(height: 15),
                
                // Grade Field
                TextField(
                  controller: gradeController,
                  textDirection: TextDirection.rtl,
                  decoration: const InputDecoration(
                    labelText: 'כיתה',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 15, 
                      vertical: 10,
                    ),
                  ),
                ),
                const SizedBox(height: 15),
                
                // Difficulty Level Selector
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'רמת קושי בהבנת הוראות:',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.right,
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: List.generate(
                        5,
                        (index) => InkWell(
                          onTap: () {
                            setState(() {
                              selectedDifficulty = index + 1;
                            });
                          },
                          borderRadius: BorderRadius.circular(4),
                          child: Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: selectedDifficulty == index + 1
                                  ? _getDifficultyColor(index + 1)
                                  : Colors.grey.shade200,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Center(
                              child: Text(
                                '${index + 1}',
                                style: TextStyle(
                                  color: selectedDifficulty == index + 1
                                      ? Colors.white
                                      : Colors.black,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 15),
                
                // Description Field
                TextField(
                  controller: descriptionController,
                  textDirection: TextDirection.rtl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'תיאור קשיי התלמיד',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 15, 
                      vertical: 10,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                
                // Action Buttons
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('ביטול'),
                    ),
                    ElevatedButton(
                      onPressed: () async {
                        if (nameController.text.isEmpty || 
                            gradeController.text.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('נא להזין שם וכיתה'),
                            ),
                          );
                          return;
                        }
                        
                        try {
                          // Update student in database
                          final updates = {
                            'full_name': nameController.text,
                            'grade': gradeController.text,
                            'difficulty_level': selectedDifficulty,
                            'difficulties_description': descriptionController.text,
                          };
                          
                          await AnalyticsService.updateStudentProfile(
                            studentId: int.parse(widget.student.id),
                            updates: updates,
                          );
                          
                          final updatedStudent = Student(
                            id: widget.student.id,
                            name: nameController.text,
                            grade: gradeController.text,
                            difficultyLevel: selectedDifficulty,
                            description: descriptionController.text,
                          );
                          
                          Navigator.pop(context);
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (context) => StudentProfileScreen(
                                student: updatedStudent,
                              ),
                            ),
                          );
                          
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('פרטי התלמיד עודכנו בהצלחה'),
                              backgroundColor: Colors.green,
                            ),
                          );
                        } catch (e) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('שגיאה בעדכון: $e'),
                              backgroundColor: Colors.red,
                            ),
                          );
                        }
                      },
                      child: const Text('שמור'),
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
  
  Color _getDifficultyColor(int level) {
    switch (level) {
      case 1:
        return Colors.green;
      case 2:
        return Colors.lightGreen;
      case 3:
        return Colors.orange;
      case 4:
        return Colors.deepOrange;
      case 5:
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}