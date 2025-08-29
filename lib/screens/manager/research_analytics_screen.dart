// lib/screens/manager/research_analytics_screen.dart
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../services/analytics_service.dart';
import '../../services/auth_service_backend.dart';

class ResearchAnalyticsScreen extends StatefulWidget {
  @override
  _ResearchAnalyticsScreenState createState() => _ResearchAnalyticsScreenState();
}

class _ResearchAnalyticsScreenState extends State<ResearchAnalyticsScreen> {
  
  // State variables
  List<dynamic> _students = [];
  String? _selectedStudentId;
  int _timeRange = 30; // days
  Map<String, dynamic>? _analytics;

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadStudents();
  }

  Future<void> _loadStudents() async {
    try {
      // For now, use mock data since we don't have a students endpoint yet
      setState(() {
        _students = [
          {'id': 1, 'full_name': 'חן לוי', 'grade': '3ג'},
          {'id': 2, 'full_name': 'הילה שושני', 'grade': '1ה'},
          {'id': 3, 'full_name': 'רון שני', 'grade': '2ב'},
          {'id': 4, 'full_name': 'נילי נעים', 'grade': '1ו'},
          {'id': 5, 'full_name': 'נועם אופלי', 'grade': '5ג'},
        ];
      });
    } catch (e) {
      _showError('Failed to load students');
    }
  }

  Future<void> _loadStudentAnalytics(String studentId) async {
    setState(() => _isLoading = true);
    
    try {
      final token = await AuthServiceBackend.getStoredToken();
      final analytics = await AnalyticsService.getStudentAnalytics(
        studentId: int.parse(studentId),
        token: token,
      );
      
      setState(() {
        _analytics = analytics;
      });
    } catch (e) {
      print('Error loading analytics for student $studentId: $e');
      // Use mock analytics data for students not in database
      setState(() {
        _analytics = {
          'summary': {
            'total_sessions': 0,
            'total_time_minutes': 0,
            'total_messages': 0,
            'average_session_duration_minutes': 0,
            'average_messages_per_session': 0,
          },
          'engagement_metrics': {
            'average_satisfaction': null,
            'teacher_calls': 0,
            'tasks_uploaded': 0,
            'error_rate': 0.0,
          },
          'assistance_usage': {
            'breakdown': 0,
            'example': 0,
            'explain': 0,
          },
          'progress_trend': [],
        };
      });
      _showError('Student not found in database - showing empty data');
    } finally {
      setState(() => _isLoading = false);
    }
  }



  Future<void> _exportData() async {
    try {
      // TODO: Implement actual file download with backend integration
      // final token = await _authService.getToken();
      // Implement file download logic here
      _showSuccess('Data export started');
    } catch (e) {
      _showError('Failed to export data');
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.green),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Research Analytics'),
        backgroundColor: Colors.purple,
        actions: [
          IconButton(
            icon: Icon(Icons.download),
            onPressed: _exportData,
            tooltip: 'Export Data',
          ),
        ],
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Student and Time Range Selector
                  _buildSelectors(),
                  SizedBox(height: 20),
                  
                  // Overview Cards
                  if (_analytics != null) ...[
                    _buildOverviewCards(),
                    SizedBox(height: 20),
                    
                    // Progress Chart
                    _buildProgressChart(),
                    SizedBox(height: 20),
                    
                    // Assistance Usage
                    _buildAssistanceAnalysis(),
                    SizedBox(height: 20),
                    
                    // Engagement Metrics
                    _buildEngagementMetrics(),
                    SizedBox(height: 20),
                    
                    // Research Insights
                    _buildResearchInsights(),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildSelectors() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Select Student & Time Range',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _selectedStudentId,
                    decoration: InputDecoration(
                      labelText: 'Student',
                      border: OutlineInputBorder(),
                    ),
                    items: _students.map((student) {
                      return DropdownMenuItem(
                        value: student['id'].toString(),
                        child: Text('${student['full_name']} - Grade ${student['grade']}'),
                      );
                    }).toList(),
                    onChanged: (value) {
                      setState(() {
                        _selectedStudentId = value;
                      });
                      if (value != null) {
                        _loadStudentAnalytics(value);
                      }
                    },
                  ),
                ),
                SizedBox(width: 16),
                Container(
                  width: 120,
                  child: DropdownButtonFormField<int>(
                    value: _timeRange,
                    decoration: InputDecoration(
                      labelText: 'Days',
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      DropdownMenuItem(value: 7, child: Text('7 days')),
                      DropdownMenuItem(value: 30, child: Text('30 days')),
                      DropdownMenuItem(value: 90, child: Text('90 days')),
                    ],
                    onChanged: (value) {
                      setState(() {
                        _timeRange = value!;
                      });
                      if (_selectedStudentId != null) {
                        _loadStudentAnalytics(_selectedStudentId!);
                      }
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOverviewCards() {
    if (_analytics == null) {
      return const Center(child: Text('אין נתונים זמינים'));
    }
    
    final summary = _analytics!['summary'] ?? {};
    final engagement = _analytics!['engagement_metrics'] ?? {};
    
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: NeverScrollableScrollPhysics(),
      childAspectRatio: 1.5,
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      children: [
        _buildMetricCard(
          'Total Sessions',
          (summary['total_sessions'] ?? 0).toString(),
          'Avg ${summary['average_session_duration_minutes'] ?? 0} min',
          Icons.calendar_today,
          Colors.blue,
        ),
        _buildMetricCard(
          'Total Time',
          '${summary['total_time_minutes'] ?? 0} min',
          '${((summary['total_time_minutes'] ?? 0) / 60).toStringAsFixed(1)} hours',
          Icons.access_time,
          Colors.green,
        ),
        _buildMetricCard(
          'Messages',
          (summary['total_messages'] ?? 0).toString(),
          'Avg ${summary['average_messages_per_session'] ?? 0}/session',
          Icons.message,
          Colors.orange,
        ),
        _buildMetricCard(
          'Satisfaction',
          engagement['average_satisfaction'] != null
              ? '${engagement['average_satisfaction'].toStringAsFixed(1)}/5'
              : 'N/A',
          'Student rating',
          Icons.sentiment_satisfied,
          Colors.purple,
        ),
      ],
    );
  }

  Widget _buildMetricCard(String title, String value, String subtitle, IconData icon, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                  ),
                ),
                Icon(icon, color: color, size: 20),
              ],
            ),
            Text(
              value,
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            Text(
              subtitle,
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressChart() {
    if (_analytics == null) {
      return const Card(child: Padding(padding: EdgeInsets.all(16), child: Center(child: Text('אין נתוני התקדמות'))));
    }
    final progressTrend = (_analytics!['progress_trend'] as List?) ?? [];
    
    if (progressTrend.isEmpty) {
      return Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Center(child: Text('No progress data available')),
        ),
      );
    }
    
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Learning Progress Over Time',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            Container(
              height: 200,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(show: true),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          if (value.toInt() >= 0 && value.toInt() < progressTrend.length) {
                            final date = progressTrend[value.toInt()]['date'];
                            return Text(
                              DateFormat('MM/dd').format(DateTime.parse(date)),
                              style: TextStyle(fontSize: 10),
                            );
                          }
                          return Text('');
                        },
                      ),
                    ),
                  ),
                  borderData: FlBorderData(show: true),
                  lineBarsData: [
                    LineChartBarData(
                      spots: progressTrend.asMap().entries.map((entry) {
                        return FlSpot(
                          entry.key.toDouble(),
                          (entry.value['average_progress'] ?? 0).toDouble(),
                        );
                      }).toList(),
                      isCurved: true,
                      color: Colors.purple,
                      barWidth: 3,
                      dotData: FlDotData(show: true),
                    ),
                  ],
                  minY: 0,
                  maxY: 100,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAssistanceAnalysis() {
    if (_analytics == null) {
      return const Card(child: Padding(padding: EdgeInsets.all(16), child: Center(child: Text('אין נתוני עזרה'))));
    }
    final assistance = _analytics!['assistance_usage'] ?? {};
    final total = (assistance['breakdown'] ?? 0) + (assistance['example'] ?? 0) + (assistance['explain'] ?? 0);
    
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Assistance Type Usage',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Column(
                    children: [
                      _buildAssistanceBar('פירוק', assistance['breakdown'] ?? 0, total, Colors.blue),
                      SizedBox(height: 8),
                      _buildAssistanceBar('דוגמה', assistance['example'] ?? 0, total, Colors.green),
                      SizedBox(height: 8),
                      _buildAssistanceBar('הסבר', assistance['explain'] ?? 0, total, Colors.orange),
                    ],
                  ),
                ),
                SizedBox(width: 16),
                Container(
                  width: 150,
                  height: 150,
                  child: PieChart(
                    PieChartData(
                      sections: [
                        PieChartSectionData(
                          value: (assistance['breakdown'] ?? 0).toDouble(),
                          title: 'פירוק\n${total > 0 ? ((assistance['breakdown'] ?? 0) / total * 100).toInt() : 0}%',
                          color: Colors.blue,
                          radius: 60,
                        ),
                        PieChartSectionData(
                          value: (assistance['example'] ?? 0).toDouble(),
                          title: 'דוגמה\n${total > 0 ? ((assistance['example'] ?? 0) / total * 100).toInt() : 0}%',
                          color: Colors.green,
                          radius: 60,
                        ),
                        PieChartSectionData(
                          value: (assistance['explain'] ?? 0).toDouble(),
                          title: 'הסבר\n${total > 0 ? ((assistance['explain'] ?? 0) / total * 100).toInt() : 0}%',
                          color: Colors.orange,
                          radius: 60,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAssistanceBar(String label, int value, int total, Color color) {
    final percentage = total > 0 ? value / total : 0.0;
    
    return Row(
      children: [
        SizedBox(
          width: 60,
          child: Text(label, style: TextStyle(fontSize: 14)),
        ),
        Expanded(
          child: LinearProgressIndicator(
            value: percentage,
            backgroundColor: Colors.grey[300],
            color: color,
            minHeight: 20,
          ),
        ),
        SizedBox(width: 8),
        Text('$value', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildEngagementMetrics() {
    if (_analytics == null) {
      return const Card(child: Padding(padding: EdgeInsets.all(16), child: Center(child: Text('אין נתוני מעורבות'))));
    }
    final engagement = _analytics!['engagement_metrics'] ?? {};
    
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Engagement Metrics',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            ListTile(
              leading: Icon(Icons.school, color: Colors.red),
              title: Text('Teacher Calls'),
              trailing: Text(
                (engagement['teacher_calls'] ?? 0).toString(),
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
            ListTile(
              leading: Icon(Icons.photo_camera, color: Colors.blue),
              title: Text('Tasks Uploaded'),
              trailing: Text(
                (engagement['tasks_uploaded'] ?? 0).toString(),
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
            ListTile(
              leading: Icon(Icons.error_outline, color: Colors.orange),
              title: Text('Error Rate'),
              trailing: Text(
                '${(engagement['error_rate'] ?? 0.0).toStringAsFixed(2)} per session',
                style: TextStyle(fontSize: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResearchInsights() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Research Insights',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            _buildInsight(
              'Learning Progress',
              _calculateProgressTrend(),
              _getProgressIcon(),
              _getProgressColor(),
            ),
            SizedBox(height: 12),
            _buildInsight(
              'Engagement Level',
              _getEngagementInsight(),
              Icons.favorite,
              Colors.blue,
            ),
            SizedBox(height: 12),
            _buildInsight(
              'Independence',
              _getIndependenceInsight(),
              Icons.trending_up,
              Colors.green,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInsight(String title, String insight, IconData icon, Color color) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: color, size: 24),
        SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              Text(
                insight,
                style: TextStyle(fontSize: 14, color: Colors.grey[700]),
              ),
            ],
          ),
        ),
      ],
    );
  }

  String _calculateProgressTrend() {
    if (_analytics == null) return 'אין נתוני התקדמות';
    final trend = (_analytics!['progress_trend'] as List?) ?? [];
    if (trend.isEmpty) return 'אין נתוני מגמה זמינים';
    
    final first = trend.first['average_progress'] ?? 0;
    final last = trend.last['average_progress'] ?? 0;
    final change = last - first;
    
    if (change > 5) return 'Significant improvement observed';
    if (change > 0) return 'Slight improvement observed';
    if (change < -5) return 'Decline in performance - intervention may be needed';
    return 'Performance is stable';
  }

  IconData _getProgressIcon() {
    if (_analytics == null) return Icons.help_outline;
    final trend = (_analytics!['progress_trend'] as List?) ?? [];
    if (trend.isEmpty) return Icons.help_outline;
    
    final first = trend.first['average_progress'] ?? 0;
    final last = trend.last['average_progress'] ?? 0;
    
    if (last > first) return Icons.trending_up;
    if (last < first) return Icons.trending_down;
    return Icons.trending_flat;
  }

  Color _getProgressColor() {
    final icon = _getProgressIcon();
    if (icon == Icons.trending_up) return Colors.green;
    if (icon == Icons.trending_down) return Colors.red;
    return Colors.orange;
  }

  String _getEngagementInsight() {
    if (_analytics == null) return 'אין נתונים';
    final messages = _analytics!['summary']?['average_messages_per_session'] ?? 0;
    if (messages > 20) return 'High engagement - very active in sessions';
    if (messages > 10) return 'Good engagement - actively participating';
    return 'Low engagement - consider intervention';
  }

  String _getIndependenceInsight() {
    if (_analytics == null) return 'אין נתונים';
    final assistance = _analytics!['assistance_usage'] ?? {};
    final total = (assistance['breakdown'] ?? 0) + (assistance['example'] ?? 0) + (assistance['explain'] ?? 0);
    final messages = _analytics!['summary']?['total_messages'] ?? 1;
    final ratio = total / messages;
    
    if (ratio < 0.2) return 'High independence - minimal assistance needed';
    if (ratio < 0.4) return 'Moderate independence - occasional help needed';
    return 'Low independence - requires frequent assistance';
  }
}
