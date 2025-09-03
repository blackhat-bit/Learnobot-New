// lib/services/notification_service.dart
import 'package:flutter/foundation.dart';

class NotificationService extends ChangeNotifier {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final List<Map<String, dynamic>> _notifications = [];
  
  // Get all notifications for the current teacher
  List<Map<String, dynamic>> get notifications => List.from(_notifications);
  
  // Get unread notification count
  int get unreadCount => _notifications.where((n) => !n['isRead']).length;
  
  // Load notifications - now returns empty list (no mock data)
  Future<List<Map<String, dynamic>>> getTeacherNotifications() async {
    // TODO: Replace with actual API call when notifications backend is ready
    // Example: 
    // final response = await http.get('/api/notifications/teacher/${teacherId}');
    // return response.data;
    
    await Future.delayed(const Duration(milliseconds: 500)); // Simulate network delay
    
    // Return empty list instead of mock data
    final realNotifications = <Map<String, dynamic>>[];
    
    _notifications.clear();
    _notifications.addAll(realNotifications);
    notifyListeners();
    
    return realNotifications;
  }
  
  // Mark all notifications as read
  Future<void> markAllAsRead() async {
    // TODO: Replace with actual API call
    // Example: await http.post('/api/notifications/mark-all-read');
    
    await Future.delayed(const Duration(milliseconds: 200)); // Simulate network delay
    
    for (var notification in _notifications) {
      notification['isRead'] = true;
    }
    
    notifyListeners();
  }
  
  // Mark specific notification as read
  Future<void> markAsRead(String notificationId) async {
    // TODO: Replace with actual API call
    // Example: await http.post('/api/notifications/$notificationId/read');
    
    await Future.delayed(const Duration(milliseconds: 200)); // Simulate network delay
    
    final notificationIndex = _notifications.indexWhere((n) => n['id'] == notificationId);
    if (notificationIndex != -1) {
      _notifications[notificationIndex]['isRead'] = true;
      notifyListeners();
    }
  }
  
  // Add new notification (for testing or real-time updates)
  void addNotification(Map<String, dynamic> notification) {
    _notifications.insert(0, notification); // Add to beginning
    notifyListeners();
  }
  
  // Create help request notification
  void createHelpRequestNotification({
    required String studentId,
    required String studentName,
  }) {
    final notification = {
      'id': DateTime.now().millisecondsSinceEpoch.toString(),
      'message': 'התלמיד $studentName מבקש עזרה',
      'time': _formatCurrentTime(),
      'timestamp': DateTime.now(),
      'isRead': false,
      'type': 'help_request',
      'studentId': studentId,
    };
    
    addNotification(notification);
  }
  
  // Create task completion notification
  void createTaskCompletionNotification({
    required String studentId,
    required String studentName,
    required String taskName,
  }) {
    final notification = {
      'id': DateTime.now().millisecondsSinceEpoch.toString(),
      'message': 'התלמיד $studentName השלים את המשימה: $taskName',
      'time': _formatCurrentTime(),
      'timestamp': DateTime.now(),
      'isRead': false,
      'type': 'task_completed',
      'studentId': studentId,
    };
    
    addNotification(notification);
  }
  
  // Helper method to format current time
  String _formatCurrentTime() {
    final now = DateTime.now();
    final months = [
      'ינו׳', 'פבר׳', 'מרץ', 'אפר׳', 'מאי', 'יונ׳',
      'יול׳', 'אוג׳', 'ספט׳', 'אוק׳', 'נוב׳', 'דצמ׳'
    ];
    
    return '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')} ${months[now.month - 1]} ${now.day}';
  }
  
  // Clear all notifications (for logout or reset)
  void clearAll() {
    _notifications.clear();
    notifyListeners();
  }
}
