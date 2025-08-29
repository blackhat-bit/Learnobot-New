// lib/screens/manager/manager_dashboard_screen.dart
import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../services/analytics_service.dart';
import '../../services/auth_service_backend.dart';
import 'ai_manager_screen.dart';
import 'research_analytics_screen.dart';
import '../auth/welcome_screen.dart';
import '../teacher/student_list_screen.dart';
import '../teacher/account_settings_screen.dart';

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
      // Use mock data for now
      setState(() {
        _dashboardData = {
          'total_sessions': 12,
          'total_students': 5,
          'total_interactions': 3,
          'recent_activities': [
            {'message': 'התלמיד חן לוי מבקש עזרה', 'time': '8:05 אפר׳ 30'},
            {'message': 'נוספו 3 תלמידים חדשים', 'time': '10:15 אפר׳ 28'},
            {'message': 'התלמידה נילי נעים השלימה משימה', 'time': '14:30 אפר׳ 27'},
          ],
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
}
