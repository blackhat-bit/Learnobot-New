// lib/widgets/notification_widget.dart
import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class NotificationWidget extends StatefulWidget {
  final VoidCallback? onViewAllPressed;
  final int maxNotifications;
  final bool showViewAll;
  
  const NotificationWidget({
    Key? key,
    this.onViewAllPressed,
    this.maxNotifications = 3,
    this.showViewAll = true,
  }) : super(key: key);

  @override
  State<NotificationWidget> createState() => _NotificationWidgetState();
}

class _NotificationWidgetState extends State<NotificationWidget> {
  // Sample notification data - in a real app, this would come from a service
  final List<Map<String, dynamic>> _notifications = [
    {
      'message': 'התלמיד חן לוי מבקש עזרה',
      'time': '8:05 אפר׳ 30',
      'icon': Icons.school,
      'isNew': true,
      'studentId': '1',
    },
    {
      'message': 'נוספו 3 תלמידים חדשים',
      'time': '10:15 אפר׳ 28',
      'icon': Icons.person_add,
      'isNew': false,
      'studentId': null,
    },
    {
      'message': 'התלמידה נילי נעים השלימה משימה',
      'time': '14:30 אפר׳ 27',
      'icon': Icons.task_alt,
      'isNew': false,
      'studentId': '4',
    },
    {
      'message': 'יום המורה שמח! 🎉',
      'time': '9:00 אפר׳ 25',
      'icon': Icons.celebration,
      'isNew': false,
      'studentId': null,
    },
  ];

  void _markAsRead(int index) {
    setState(() {
      _notifications[index]['isNew'] = false;
    });
  }

  void _dismissNotification(int index) {
    setState(() {
      _notifications.removeAt(index);
    });
  }

  void _handleNotificationTap(int index) {
    final notification = _notifications[index];
    
    // Mark as read
    _markAsRead(index);
    
    // Handle notification action based on type
    if (notification['studentId'] != null) {
      // Navigate to student profile or chat
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('פתיחת פרופיל של ${notification['message'].split(' ')[1]}'),
          duration: const Duration(seconds: 1),
        ),
      );
    } else if (notification['message'].contains('נוספו')) {
      // Navigate to student list
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('מעבר לרשימת תלמידים'),
          duration: Duration(seconds: 1),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final displayedNotifications = _notifications.take(widget.maxNotifications).toList();
    final hasMoreNotifications = _notifications.length > widget.maxNotifications;
    
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
                  'התראות',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                if (widget.showViewAll)
                  TextButton(
                    onPressed: widget.onViewAllPressed ?? () {
                      // Show all notifications in a dialog
                      _showAllNotificationsDialog(context);
                    },
                    child: const Text('לכל ההתראות'),
                  ),
              ],
            ),
            const Divider(),
            
            if (displayedNotifications.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 20),
                child: Center(
                  child: Text(
                    'אין התראות חדשות',
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 16,
                    ),
                  ),
                ),
              )
            else
              ...displayedNotifications.asMap().entries.map((entry) {
                final index = entry.key;
                final notification = entry.value;
                return _buildNotification(
                  notification['message'],
                  notification['time'],
                  notification['icon'],
                  notification['isNew'],
                  onTap: () => _handleNotificationTap(index),
                  onDismiss: () => _dismissNotification(index),
                );
              }).toList(),
              
            if (hasMoreNotifications && !widget.showViewAll)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Center(
                  child: TextButton.icon(
                    onPressed: widget.onViewAllPressed ?? () {
                      // Show all notifications in a dialog
                      _showAllNotificationsDialog(context);
                    },
                    icon: const Icon(Icons.arrow_downward, size: 16),
                    label: Text('עוד ${_notifications.length - widget.maxNotifications} התראות'),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildNotification(
    String message,
    String time,
    IconData icon,
    bool isNew, {
    VoidCallback? onTap,
    VoidCallback? onDismiss,
  }) {
    return Dismissible(
      key: Key(message + time),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        color: Colors.red,
        child: const Icon(
          Icons.delete,
          color: Colors.white,
        ),
      ),
      onDismissed: (_) => onDismiss?.call(),
      child: InkWell(
        onTap: onTap,
        child: Container(
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
              Stack(
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
                      icon,
                      color: isNew ? AppColors.primary : Colors.grey,
                      size: 20,
                    ),
                  ),
                  if (isNew)
                    Positioned(
                      right: 0,
                      top: 0,
                      child: Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: Colors.red,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                ],
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
              // Action indicator
              Icon(
                Icons.arrow_forward_ios,
                size: 14,
                color: Colors.grey.shade400,
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  void _showAllNotificationsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('כל ההתראות'),
            TextButton(
              onPressed: () {
                setState(() {
                  for (var notification in _notifications) {
                    notification['isNew'] = false;
                  }
                });
                Navigator.pop(context);
              },
              child: const Text('סמן הכל כנקרא'),
            ),
          ],
        ),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: _notifications.length,
            itemBuilder: (context, index) {
              final notification = _notifications[index];
              return _buildNotification(
                notification['message'],
                notification['time'],
                notification['icon'],
                notification['isNew'],
                onTap: () {
                  _markAsRead(index);
                  Navigator.pop(context);
                  _handleNotificationTap(index);
                },
                onDismiss: () {
                  _dismissNotification(index);
                  Navigator.pop(context);
                  _showAllNotificationsDialog(context);
                },
              );
            },
          ),
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
}