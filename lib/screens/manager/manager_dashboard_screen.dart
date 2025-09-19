// lib/screens/manager/manager_dashboard_screen.dart
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:intl/intl.dart';
import '../../constants/app_colors.dart';
import '../../services/analytics_service.dart';
import '../../services/auth_service_backend.dart';
import 'ai_manager_screen.dart';
import 'research_analytics_screen.dart';
import '../auth/welcome_screen.dart';
import '../teacher/student_list_screen.dart';
import '../teacher/account_settings_screen.dart';

// Web-specific imports
import 'dart:html' as html;

class ManagerDashboardScreen extends StatefulWidget {
  const ManagerDashboardScreen({Key? key}) : super(key: key);

  @override
  State<ManagerDashboardScreen> createState() => _ManagerDashboardScreenState();
}

class _ManagerDashboardScreenState extends State<ManagerDashboardScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _dashboardData;
  String _username = 'מנהל פרויקט';

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
    _loadUsername();
  }

  Future<void> _loadUsername() async {
    try {
      final user = await AuthServiceBackend.getStoredUser();
      if (user != null && mounted) {
        setState(() {
          _username = user['full_name'] ?? user['username'] ?? 'מנהל פרויקט';
        });
      }
    } catch (e) {
      print('Error loading username: $e');
    }
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    
    try {
      final token = await AuthServiceBackend.getStoredToken();
      final data = await AnalyticsService.getDashboardSummary(token: token);
      
      setState(() {
        _dashboardData = data;
      });
    } catch (e) {
      print('Error loading dashboard data: $e');
      // Use empty data instead of mock data
      setState(() {
        _dashboardData = {
          'total_sessions': 0,
          'total_students': 0,
          'total_interactions': 0,
          'recent_activities': [],
        };
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                children: [
                  // Header
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                    color: AppColors.primary,
                    child: Row(
                      children: [
                        const CircleAvatar(
                          backgroundColor: Colors.white,
                          radius: 25,
                          child: Icon(
                            Icons.admin_panel_settings,
                            color: AppColors.primary,
                            size: 30,
                          ),
                        ),
                        const SizedBox(width: 15),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'פאנל ניהול',
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              Text(
                                'שלום, $_username! מנהל פרויקט',
                                style: const TextStyle(
                                  fontSize: 16,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                        // Logout button
                        IconButton(
                          onPressed: _showLogoutDialog,
                          icon: const Icon(
                            Icons.logout,
                            color: Colors.white,
                            size: 24,
                          ),
                          tooltip: 'התנתק',
                        ),
                      ],
                    ),
                  ),

                  // Dashboard Stats
                  Container(
                    padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 20),
                    color: AppColors.primary.withOpacity(0.8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildStatItem(
                          '${_dashboardData?['total_interactions'] ?? 3}',
                          'קריאות לעזרה',
                        ),
                        _buildStatItem(
                          '${_dashboardData?['total_sessions'] ?? 12}',
                          'שיחות היום',
                        ),
                        _buildStatItem(
                          '${_dashboardData?['total_students'] ?? 5}',
                          'תלמידים',
                        ),
                      ],
                    ),
                  ),

                  // Main Content
                  Expanded(
                    child: SingleChildScrollView(
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          children: [
                            // Manager Tools Section
                            Container(
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
                              child: Column(
                                children: [
                                  // Header
                                  Container(
                                    padding: const EdgeInsets.all(20),
                                    decoration: BoxDecoration(
                                      color: AppColors.primary.withOpacity(0.1),
                                      borderRadius: const BorderRadius.only(
                                        topLeft: Radius.circular(16),
                                        topRight: Radius.circular(16),
                                      ),
                                    ),
                                    child: const Row(
                                      children: [
                                        Icon(Icons.dashboard_outlined, 
                                             color: AppColors.primary, size: 24),
                                        SizedBox(width: 12),
                                        Text(
                                          'כלי ניהול',
                                          style: TextStyle(
                                            fontSize: 18,
                                            fontWeight: FontWeight.bold,
                                            color: AppColors.primary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  
                                  // Manager Tools
                                  _buildManagerMenuItem(
                                    icon: Icons.settings_applications,
                                    title: 'ניהול AI',
                                    subtitle: 'הגדרת ספקי AI והגדרות מתקדמות',
                                    color: Colors.purple,
                                    onTap: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => AIManagerScreen(),
                                      ),
                                    ),
                                    isFirst: true,
                                  ),
                                  
                                  _buildManagerMenuItem(
                                    icon: Icons.analytics_outlined,
                                    title: 'ניתוח מחקרי',
                                    subtitle: 'דוחות מפורטים וניתוח נתונים למחקר',
                                    color: Colors.blue,
                                    onTap: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => ResearchAnalyticsScreen(),
                                      ),
                                    ),
                                  ),
                                  
                                  _buildManagerMenuItem(
                                    icon: Icons.people_outline,
                                    title: 'מעקב תלמידים',
                                    subtitle: 'צפייה וניהול כרטיסי תלמידים',
                                    color: Colors.green,
                                    onTap: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => const StudentListScreen(),
                                      ),
                                    ),
                                  ),
                                  
                                  _buildManagerMenuItem(
                                    icon: Icons.archive_outlined,
                                    title: 'ארכיון ותיעוד',
                                    subtitle: 'היסטוריית שיחות וניתוח נתונים',
                                    color: Colors.orange,
                                    onTap: () => _showArchiveOptions(context),
                                  ),
                                  
                                  _buildManagerMenuItem(
                                    icon: Icons.settings_outlined,
                                    title: 'הגדרות מערכת',
                                    subtitle: 'צליל, תצוגה והגדרות צ׳אטבוט',
                                    color: Colors.teal,
                                    onTap: () => _showSystemSettingsDialog(context),
                                  ),
                                  
                                  _buildManagerMenuItem(
                                    icon: Icons.person_outline,
                                    title: 'הגדרות חשבון',
                                    subtitle: 'עדכון פרטים ושינוי סיסמה',
                                    color: Colors.indigo,
                                    onTap: () => Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => const AccountSettingsScreen(),
                                      ),
                                    ),
                                    isLast: true,
                                  ),
                                ],
                              ),
                            ),
                            
                            const SizedBox(height: 20),
                            
                            // Recent Activities
                            _buildRecentActivities(),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _buildStatItem(String value, String label) {
    return Flexible(
      child: Column(
        children: [
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
            ),
            textAlign: TextAlign.center,
            overflow: TextOverflow.ellipsis,
            maxLines: 2,
          ),
        ],
      ),
    );
  }

  Widget _buildManagerMenuItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
    bool isFirst = false,
    bool isLast = false,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.vertical(
          top: isFirst ? const Radius.circular(0) : Radius.zero,
          bottom: isLast ? const Radius.circular(16) : Radius.zero,
        ),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            border: Border(
              bottom: isLast 
                ? BorderSide.none 
                : BorderSide(color: Colors.grey.shade200, width: 1),
            ),
          ),
          child: Row(
            children: [
              // Icon Container
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: color,
                  size: 24,
                ),
              ),
              
              const SizedBox(width: 16),
              
              // Text Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                        height: 1.3,
                      ),
                    ),
                  ],
                ),
              ),
              
              // Arrow Icon
              Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: Colors.grey.shade400,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRecentActivities() {
    final activities = _dashboardData?['recent_activities'] ?? [];
    
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
      ),
      child: Container(
        padding: const EdgeInsets.all(15),
        width: double.infinity,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.notifications,
                  color: AppColors.primary,
                ),
                const SizedBox(width: 10),
                const Text(
                  'פעילות אחרונה',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ResearchAnalyticsScreen(),
                      ),
                    );
                  },
                  child: const Text('לכל ההתראות'),
                ),
              ],
            ),
            const Divider(),
            
            if (activities.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 20),
                child: Center(
                  child: Text(
                    'אין פעילות אחרונה',
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 16,
                    ),
                  ),
                ),
              )
            else
              ...activities.map<Widget>((activity) => 
                _buildActivityItem(
                  activity['message'] ?? 'פעילות',
                  activity['time'] ?? 'זמן לא ידוע',
                )
              ).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildActivityItem(String message, String time) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Colors.grey.shade200,
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.2),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.notifications,
              color: AppColors.primary,
              size: 20,
            ),
          ),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  message,
                  style: const TextStyle(
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  time,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showArchiveOptions(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('ארכיון ותיעוד'),
        children: [
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              _showConversationArchive(context);
            },
            child: const ListTile(
              leading: Icon(Icons.chat),
              title: Text('תיעוד שיחות'),
            ),
          ),
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              _showProgressArchive(context);
            },
            child: const ListTile(
              leading: Icon(Icons.trending_up),
              title: Text('התקדמות תלמידים'),
            ),
          ),
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              _showReportsArchive(context);
            },
            child: const ListTile(
              leading: Icon(Icons.description),
              title: Text('דוחות'),
            ),
          ),
        ],
      ),
    );
  }

  void _showSystemSettingsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('הגדרות מערכת'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.volume_up),
              title: const Text('צלילי התראות'),
              trailing: Switch(
                value: true,
                onChanged: (value) {},
                activeColor: AppColors.primary,
              ),
            ),
            ListTile(
              leading: const Icon(Icons.dark_mode),
              title: const Text('מצב כהה'),
              trailing: Switch(
                value: false,
                onChanged: (value) {},
                activeColor: AppColors.primary,
              ),
            ),
            ListTile(
              leading: const Icon(Icons.language),
              title: const Text('שפה'),
              subtitle: const Text('עברית'),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
              onTap: () {},
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('סגור'),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('התנתקות'),
        content: const Text('האם אתה בטוח שברצונך להתנתק?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ביטול'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await AuthServiceBackend.logout();
              // Navigate back to welcome screen
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const WelcomeScreen()),
                (route) => false,
              );
            },
            child: const Text(
              'התנתק',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }

  // Archive functionality methods (same as teacher panel but for admin access)
  void _showConversationArchive(BuildContext context) async {
    try {
      final conversations = await AnalyticsService.getConversationArchive();
      
      showDialog(
        context: context,
        builder: (context) => Dialog(
          child: Container(
            width: MediaQuery.of(context).size.width * 0.9,
            height: MediaQuery.of(context).size.height * 0.8,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'תיעוד שיחות',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
                const Divider(),
                Expanded(
                  child: conversations.isEmpty
                    ? const Center(child: Text('אין שיחות להצגה'))
                    : ListView.builder(
                      itemCount: conversations.length,
                      itemBuilder: (context, index) {
                        final conversation = conversations[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(vertical: 4),
                          child: ExpansionTile(
                            title: Text(
                              'שיחה עם ${conversation['student_name']}',
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('תאריך: ${DateTime.parse(conversation['started_at']).toLocal().toString().substring(0, 16)}'),
                                Text('מצב: ${conversation['mode'] == 'practice' ? 'תרגול' : 'מבחן'}'),
                                Text('מספר הודעות: ${conversation['message_count']}'),
                                if (conversation['duration_minutes'] != null)
                                  Text('משך השיחה: ${conversation['duration_minutes']} דקות'),
                              ],
                            ),
                            children: [
                              Container(
                                height: 200,
                                padding: const EdgeInsets.all(8),
                                child: ListView.builder(
                                  itemCount: conversation['messages'].length,
                                  itemBuilder: (context, msgIndex) {
                                    final message = conversation['messages'][msgIndex];
                                    return Padding(
                                      padding: const EdgeInsets.symmetric(vertical: 2),
                                      child: Row(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Icon(
                                            message['role'] == 'user' ? Icons.person : Icons.smart_toy,
                                            size: 16,
                                            color: message['role'] == 'user' ? Colors.blue : Colors.green,
                                          ),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Text(
                                              message['content'],
                                              style: const TextStyle(fontSize: 12),
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  },
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                ),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בטעינת השיחות: $e')),
      );
    }
  }

  void _showProgressArchive(BuildContext context) async {
    try {
      final students = await AnalyticsService.getAllStudents();
      
      showDialog(
        context: context,
        builder: (context) => SimpleDialog(
          title: const Text('בחר תלמיד לצפייה בהתקדמות'),
          children: students.map((student) => 
            SimpleDialogOption(
              onPressed: () {
                Navigator.pop(context);
                _showStudentProgress(context, student);
              },
              child: ListTile(
                title: Text(student['full_name']),
                subtitle: Text('כיתה: ${student['grade']} | רמה: ${student['difficulty_level']}'),
              ),
            ),
          ).toList(),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בטעינת רשימת התלמידים: $e')),
      );
    }
  }

  void _showStudentProgress(BuildContext context, Map<String, dynamic> student) async {
    try {
      final progressData = await AnalyticsService.getStudentProgressArchive(
        studentId: student['id'],
      );
      
      showDialog(
        context: context,
        builder: (context) => Dialog(
          child: Container(
            width: MediaQuery.of(context).size.width * 0.9,
            height: MediaQuery.of(context).size.height * 0.8,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'התקדמות ${progressData['student']['name']}',
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
                const Divider(),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('שם: ${progressData['student']['name']}'),
                        Text('כיתה: ${progressData['student']['grade']}'),
                        Text('רמת קושי: ${progressData['student']['difficulty_level']}'),
                        if (progressData['student']['difficulties_description'] != null)
                          Text('תיאור קשיים: ${progressData['student']['difficulties_description']}'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'התקדמות לפי שבועות',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                Expanded(
                  child: progressData['progress_timeline'].isEmpty
                    ? const Center(child: Text('אין נתוני התקדמות'))
                    : ListView.builder(
                      itemCount: progressData['progress_timeline'].length,
                      itemBuilder: (context, index) {
                        final weekData = progressData['progress_timeline'][index];
                        return Card(
                          child: ListTile(
                            title: Text('שבוע ${weekData['week']}, ${weekData['year']}'),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('מספר שיחות: ${weekData['sessions']}'),
                                Text('ניקוד התקדמות ממוצע: ${weekData['avg_progress_score']}'),
                                Text('זמן כולל: ${weekData['total_time_minutes']} דקות'),
                                if (weekData['avg_satisfaction'] != null)
                                  Text('רמת שביעות רצון: ${weekData['avg_satisfaction']}'),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                ),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בטעינת נתוני התקדמות: $e')),
      );
    }
  }

  void _showReportsArchive(BuildContext context) async {
    try {
      final reportData = await AnalyticsService.getSummaryReport();
      
      showDialog(
        context: context,
        builder: (context) => Dialog(
          child: Container(
            width: MediaQuery.of(context).size.width * 0.9,
            height: MediaQuery.of(context).size.height * 0.8,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'דוח סיכום',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    Row(
                      children: [
                        Tooltip(
                          message: 'ייצא נתונים מקיפים: סשנים, מטריקות, שגיאות, דירוגים וכל הנתונים הסטטיסטיים',
                          child: TextButton.icon(
                            onPressed: () async {
                              try {
                                // Get CSV data from backend
                                final csvData = await AnalyticsService.exportComprehensiveCSV();
                                
                                // Handle file saving for different platforms
                                final fileName = 'learnobot_comprehensive_${DateFormat('yyyy-MM-dd').format(DateTime.now())}.csv';
                                
                                // For web platform, use different approach
                                if (kIsWeb) {
                                  // Create blob with proper UTF-8 BOM for Hebrew text
                                  final bytes = utf8.encode('\uFEFF$csvData'); // Add BOM for proper Hebrew display
                                  final blob = html.Blob([bytes], 'text/csv;charset=utf-8');
                                  final url = html.Url.createObjectUrlFromBlob(blob);
                                  html.AnchorElement(href: url)
                                    ..setAttribute('download', fileName)
                                    ..click();
                                  html.Url.revokeObjectUrl(url);
                                  
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text('נתונים מקיפים יוצאו בהצלחה! הקובץ הורד כ-$fileName'),
                                      backgroundColor: Colors.green,
                                    ),
                                  );
                                } else {
                                  // For mobile/desktop, use file picker
                                  final String? outputFile = await FilePicker.platform.saveFile(
                                    dialogTitle: 'Save Comprehensive Analytics Data',
                                    fileName: fileName,
                                    type: FileType.custom,
                                    allowedExtensions: ['csv'],
                                  );

                                  if (outputFile != null) {
                                    final file = File(outputFile);
                                    await file.writeAsString(csvData);
                                    
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text('נתונים מקיפים יוצאו בהצלחה ל:\n$outputFile'),
                                        backgroundColor: Colors.green,
                                      ),
                                    );
                                  } else {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                        content: Text('יצוא בוטל - לא נבחר קובץ'),
                                        backgroundColor: Colors.orange,
                                      ),
                                    );
                                  }
                                }
                              } catch (e) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('שגיאה ביצוא הנתונים: $e'),
                                    backgroundColor: Colors.red,
                                  ),
                                );
                              }
                            },
                            icon: const Icon(Icons.analytics),
                            label: const Text('ייצא נתונים מקיפים'),
                          ),
                        ),
                        IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: const Icon(Icons.close),
                        ),
                      ],
                    ),
                  ],
                ),
                const Divider(),
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'תקופת הדוח',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                                Text('מ: ${DateTime.parse(reportData['period']['start_date']).toLocal().toString().substring(0, 10)}'),
                                Text('עד: ${DateTime.parse(reportData['period']['end_date']).toLocal().toString().substring(0, 10)}'),
                                Text('מספר ימים: ${reportData['period']['days']}'),
                              ],
                            ),
                          ),
                        ),
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'סיכום נתונים',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                                const SizedBox(height: 8),
                                Text('סך שיחות: ${reportData['summary']['total_sessions']}'),
                                Text('תלמידים ייחודיים: ${reportData['summary']['unique_students']}'),
                                Text('סך זמן (שעות): ${reportData['summary']['total_time_hours']}'),
                                Text('סך הודעות: ${reportData['summary']['total_messages']}'),
                                Text('קריאות למורה: ${reportData['summary']['teacher_calls']}'),
                                Text('משימות שהועלו: ${reportData['summary']['tasks_uploaded']}'),
                                Text('ניקוד התקדמות ממוצע: ${reportData['summary']['avg_progress_score']}'),
                                if (reportData['summary']['avg_satisfaction_rating'] != null)
                                  Text('רמת שביעות רצון ממוצעת: ${reportData['summary']['avg_satisfaction_rating']}'),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בטעינת הדוח: $e')),
      );
    }
  }
}
