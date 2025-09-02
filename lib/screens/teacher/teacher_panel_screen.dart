// lib/screens/teacher/teacher_panel_screen.dart
import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../models/student.dart';
import 'student_list_screen.dart';
import 'account_settings_screen.dart';
import '../../widgets/notification_widget.dart';
import '../../services/database_service.dart';
import '../../services/auth_service.dart';
import '../../services/auth_service_backend.dart';
import '../../services/analytics_service.dart';
import '../../services/notification_service.dart';
import '../auth/welcome_screen.dart';
import 'package:provider/provider.dart';

class TeacherPanelScreen extends StatefulWidget {
  const TeacherPanelScreen({Key? key}) : super(key: key);

  @override
  State<TeacherPanelScreen> createState() => _TeacherPanelScreenState();
}

class _TeacherPanelScreenState extends State<TeacherPanelScreen> {
  List<Student> _recentStudents = [];
  bool _isLoading = true;
  String _username = 'המורה';
  String? _userRole;
  
  // Local state

  @override
  void initState() {
    super.initState();
    _loadNotifications();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
      _loadUsername();
      _loadUserRole();
    });
  }
  
  // Load notifications using the service
  Future<void> _loadNotifications() async {
    final notificationService = Provider.of<NotificationService>(context, listen: false);
    await notificationService.getTeacherNotifications();
  }

  Future<void> _loadUsername() async {
    final authService = Provider.of<AuthService>(context, listen: false);
    final username = await authService.getCurrentUserName();
    if (username != null && mounted) {
      setState(() {
        _username = username;
      });
    }
  }

  Future<void> _loadUserRole() async {
    final authService = Provider.of<AuthService>(context, listen: false);
    final role = await authService.getCurrentUserRole();
    if (role != null && mounted) {
      setState(() {
        _userRole = role;
      });
    }
  }

  Future<void> _loadData() async {
    await Future.delayed(const Duration(milliseconds: 800));
    if (mounted) {
      try {
        // Load real students from backend
        final token = await AuthServiceBackend.getStoredToken();
        final studentsData = await AnalyticsService.getAllStudents(token: token);
        
        // Convert backend data to Student model format
        final allStudents = studentsData.map((studentData) {
          return Student(
            id: studentData['id'].toString(),
            name: studentData['full_name'] ?? 'Student ${studentData['id']}',
            grade: studentData['grade'] ?? 'N/A',
            difficultyLevel: studentData['difficulty_level'] ?? 3,
            description: studentData['difficulties_description'] ?? 'No description available',
            profileImageUrl: '',
          );
        }).toList();

        allStudents.sort((a, b) => b.grade.compareTo(a.grade));
        setState(() {
          _recentStudents = allStudents.take(3).toList();
          _isLoading = false;
        });
      } catch (e) {
        debugPrint('Error loading backend students: $e');
        setState(() {
          _recentStudents = [];
          _isLoading = false;
        });
      }
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
                    padding: const EdgeInsets.symmetric(
                        horizontal: 20, vertical: 15),
                    color: AppColors.primary,
                    child: Row(
                      children: [
                        GestureDetector(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) =>
                                    const AccountSettingsScreen(),
                              ),
                            );
                          },
                          child: const CircleAvatar(
                            backgroundColor: Colors.white,
                            radius: 25,
                            child: Icon(
                              Icons.person,
                              color: AppColors.primary,
                              size: 30,
                            ),
                          ),
                        ),
                        const SizedBox(width: 15),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                AppStrings.teacherPanel,
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              Text(
                                'שלום, $_username!',
                                style: const TextStyle(
                                  fontSize: 16,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                        // Notification icon with badge
                        Consumer<NotificationService>(
                          builder: (context, notificationService, child) {
                            final unreadCount = notificationService.unreadCount;
                            return Stack(
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.notifications,
                                      color: Colors.white, size: 28),
                                  onPressed: () {
                                    _showNotificationsDialog(context);
                                  },
                                ),
                                if (unreadCount > 0)
                                  Positioned(
                                    right: 8,
                                    top: 8,
                                    child: Container(
                                      padding: const EdgeInsets.all(4),
                                      decoration: const BoxDecoration(
                                        color: Colors.red,
                                        shape: BoxShape.circle,
                                      ),
                                      constraints: const BoxConstraints(
                                        minWidth: 16,
                                        minHeight: 16,
                                      ),
                                      child: Text(
                                        unreadCount.toString(),
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                        ),
                                        textAlign: TextAlign.center,
                                      ),
                                    ),
                                  ),
                              ],
                            );
                          },
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
                  // Dashboard summary
                  Container(
                    padding: const EdgeInsets.symmetric(
                        vertical: 15, horizontal: 20),
                    color: AppColors.primary.withOpacity(0.8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildSummaryItem('תלמידים', '5'),
                        _buildSummaryItem('שיחות היום', '12'),
                        _buildSummaryItem('קריאות לעזרה', '3'),
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
                            // Professional Menu List
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
                                          'פאנל ניהול',
                                          style: TextStyle(
                                            fontSize: 18,
                                            fontWeight: FontWeight.bold,
                                            color: AppColors.primary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  
                                  // Menu Items
                                  
                                  _buildProfessionalMenuItem(
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
                                    isFirst: true, // First item for teachers
                                  ),
                                  
                                  _buildProfessionalMenuItem(
                                    icon: Icons.archive_outlined,
                                    title: 'ארכיון ותיעוד',
                                    subtitle: 'היסטוריית שיחות וניתוח נתונים',
                                    color: Colors.purple,
                                    onTap: () => _showArchiveOptions(context),
                                  ),
                                  
                                  _buildProfessionalMenuItem(
                                    icon: Icons.settings_outlined,
                                    title: 'הגדרות מערכת',
                                    subtitle: 'צליל, תצוגה והגדרות צ׳אטבוט',
                                    color: Colors.orange,
                                    onTap: () => _showSystemSettingsDialog(context),
                                  ),
                                  
                                  _buildProfessionalMenuItem(
                                    icon: Icons.person_outline,
                                    title: 'הגדרות חשבון',
                                    subtitle: 'עדכון פרטים ושינוי סיסמה',
                                    color: Colors.teal,
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
                            if (_recentStudents.isNotEmpty) ...[
                              const SizedBox(height: 20),
                              Align(
                                alignment: Alignment.centerRight,
                                child: Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text(
                                      'פעילות אחרונה',
                                      style: TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    TextButton(
                                      onPressed: () {
                                        Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                            builder: (context) =>
                                                const StudentListScreen(),
                                          ),
                                        );
                                      },
                                      child: const Text('לכל התלמידים'),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 10),
                              SizedBox(
                                height: 100,
                                child: ListView.builder(
                                  scrollDirection: Axis.horizontal,
                                  itemCount: _recentStudents.length,
                                  itemBuilder: (context, index) {
                                    final student = _recentStudents[index];
                                    return _buildRecentStudentCard(
                                        context, student);
                                  },
                                ),
                              ),
                              const SizedBox(height: 20),
                            ],
                            const NotificationWidget(),
                            const SizedBox(height: 20), // Add bottom padding
                          ],
                        ),
                      ),
                    ),
                  ),
                  // Bottom Navigation
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 20, vertical: 10),
                    color: AppColors.primary,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        IconButton(
                          icon:
                              const Icon(Icons.grid_view, color: Colors.white),
                          onPressed: () {},
                        ),
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(30),
                          ),
                          child: IconButton(
                            icon: const Icon(Icons.add,
                                color: AppColors.primary, size: 30),
                            onPressed: () {
                              _showAddStudentDialog(context);
                            },
                          ),
                        ),
                        IconButton(
                          icon:
                              const Icon(Icons.smart_toy, color: Colors.white),
                          onPressed: () {
                            _showBotTutorialDialog(context);
                          },
                        ),
                      ],
                    ),
                  ),
                ],
              ),
      ),
    );
  }


  // ============ Helper Widgets and Methods ==============

  Widget _buildSummaryItem(String label, String value) {
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



  Widget _buildRecentStudentCard(BuildContext context, Student student) {
    return GestureDetector(
      onTap: () {
        Navigator.pushNamed(
          context,
          '/student_profile',
          arguments: student,
        );
      },
      child: Container(
        width: 90,
        margin: const EdgeInsets.only(left: 10),
        child: Column(
          children: [
            CircleAvatar(
              radius: 30,
              backgroundColor: AppColors.primaryLight,
              child: Text(
                student.name.substring(0, 1),
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              student.name,
              textAlign: TextAlign.center,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              student.grade,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
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
              leading: const Icon(Icons.smart_toy),
              title: const Text('הגדרות צ׳אטבוט'),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
              onTap: () {
                Navigator.pop(context);
                _showBotSettingsDialog(context);
              },
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

  void _showBotSettingsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('הגדרות צ׳אטבוט'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const ListTile(
              leading: Icon(Icons.psychology),
              title: Text('רמת סיוע ברירת מחדל'),
              subtitle: Text('בינונית'),
            ),
            const Divider(),
            SwitchListTile(
              title: const Text('מצב בחינה'),
              subtitle: const Text('סיוע מוגבל למבחנים'),
              value: true,
              onChanged: (value) {},
              activeColor: AppColors.primary,
            ),
            const Divider(),
            SwitchListTile(
              title: const Text('כולל הסברים מפורטים'),
              value: true,
              onChanged: (value) {},
              activeColor: AppColors.primary,
            ),
            const Divider(),
            SwitchListTile(
              title: const Text('מאפשר ציור והדגמה'),
              value: true,
              onChanged: (value) {},
              activeColor: AppColors.primary,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ביטול'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('שמור'),
          ),
        ],
      ),
    );
  }

  void _showArchiveOptions(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('ארכיון'),
        children: [
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('תיעוד שיחות בקרוב!')),
              );
            },
            child: const ListTile(
              leading: Icon(Icons.chat),
              title: Text('תיעוד שיחות'),
            ),
          ),
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('התקדמות תלמידים בקרוב!')),
              );
            },
            child: const ListTile(
              leading: Icon(Icons.trending_up),
              title: Text('התקדמות תלמידים'),
            ),
          ),

          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('דוחות בקרוב!')),
              );
            },
            child: const ListTile(
              leading: Icon(Icons.description),
              title: Text('דוחות'),
            ),
          ),
          
          // Admin-only options (TODO: Add role checking)
          /* TODO: Uncomment when admin role checking is implemented
          if (userRole == 'admin') ...[
            SimpleDialogOption(
              onPressed: () {
                Navigator.pop(context);
                // TODO: Add AIManagerScreen navigation
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('הגדרות AI בקרוב!')),
                );
                /*
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => AIManagerScreen(),
                  ),
                );
                */
              },
              child: const ListTile(
                leading: Icon(Icons.settings_applications, color: Colors.blue),
                title: Text('הגדרות AI'),
                subtitle: Text('ניהול ספקי AI והוראות'),
              ),
            ),
            SimpleDialogOption(
              onPressed: () async {
                Navigator.pop(context);
                // Navigate to research analytics screen for data export
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ResearchAnalyticsScreen(),
                  ),
                );
              },
              child: const ListTile(
                leading: Icon(Icons.download, color: Colors.green),
                title: Text('ייצוא כל הנתונים'),
                subtitle: Text('הורדת נתוני מחקר כ-CSV'),
              ),
            ),
          ],
          */
        ],
      ),
    );
  }



  // Professional Menu Item Builder
  Widget _buildProfessionalMenuItem({
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

  void _showNotificationsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => Consumer<NotificationService>(
        builder: (context, notificationService, child) => AlertDialog(
          title: const Text('התראות'),
          content: SizedBox(
            width: double.maxFinite,
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: notificationService.notifications.length,
              itemBuilder: (context, index) {
                final notification = notificationService.notifications[index];
                return _buildNotificationItem(
                  notification['message'], 
                  notification['time'],
                  isNew: !notification['isRead'],
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () async {
                await notificationService.markAllAsRead();
                Navigator.pop(context);
              },
              child: const Text('סמן הכל כנקרא'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('סגור'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotificationItem(String message, String time,
      {bool isNew = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Colors.grey.shade300,
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isNew
                  ? AppColors.primary.withOpacity(0.2)
                  : Colors.grey.shade200,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              Icons.notifications,
              color: isNew ? AppColors.primary : Colors.grey,
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
                  style: TextStyle(
                    fontWeight: isNew ? FontWeight.bold : FontWeight.normal,
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
          if (isNew)
            Container(
              width: 8,
              height: 8,
              decoration: const BoxDecoration(
                color: AppColors.primary,
                shape: BoxShape.circle,
              ),
            ),
        ],
      ),
    );
  }

  void _showAddStudentDialog(BuildContext context) {
    final TextEditingController nameController = TextEditingController();
    final TextEditingController gradeController = TextEditingController();
    final TextEditingController descriptionController = TextEditingController();
    int selectedDifficulty = 3;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    AppStrings.createStudentProfile,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
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

                          final newStudent = Student(
                            id: DateTime.now()
                                .millisecondsSinceEpoch
                                .toString(),
                            name: nameController.text,
                            grade: gradeController.text,
                            difficultyLevel: selectedDifficulty,
                            description: descriptionController.text,
                          );

                          // Add student to database
                          final databaseService = DatabaseService();
                          await databaseService.addStudent(newStudent);

                          // Refresh recent students
                          _loadData();

                          Navigator.pop(context);

                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content:
                                  Text('התלמיד ${newStudent.name} נוסף בהצלחה'),
                              backgroundColor: Colors.green,
                            ),
                          );
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
      ),
    );
  }

  void _showBotTutorialDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        child: Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: AppColors.primaryLight.withOpacity(0.3),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.smart_toy,
                  size: 50,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'לרנובוט - מה הוא יכול לעשות?',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 15),
              _buildTutorialItem(
                icon: Icons.psychology,
                title: 'סיוע מותאם אישית',
                description:
                    'עזרה בהבנת הוראות והסבר משימות בהתאם לרמת הקושי של התלמיד',
              ),
              const SizedBox(height: 10),
              _buildTutorialItem(
                icon: Icons.format_list_numbered,
                title: 'פירוק משימות לשלבים',
                description: 'פירוק משימות מורכבות לשלבים פשוטים וברורים',
              ),
              const SizedBox(height: 10),
              _buildTutorialItem(
                icon: Icons.bar_chart,
                title: 'ניתוח נתונים',
                description: 'איסוף וניתוח מידע על הקשיים של התלמיד לאורך זמן',
              ),
              const SizedBox(height: 10),
              _buildTutorialItem(
                icon: Icons.notifications_active,
                title: 'התראות בזמן אמת',
                description: 'קבלת התראות כאשר תלמיד זקוק לעזרה',
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 45),
                ),
                child: const Text('הבנתי'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTutorialItem({
    required IconData icon,
    required String title,
    required String description,
  }) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.primaryLight.withOpacity(0.2),
            shape: BoxShape.circle,
          ),
          child: Icon(
            icon,
            color: AppColors.primary,
            size: 24,
          ),
        ),
        const SizedBox(width: 15),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                description,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
        ),
      ],
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
              final authService = Provider.of<AuthService>(context, listen: false);
              await authService.signOut();
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
}
