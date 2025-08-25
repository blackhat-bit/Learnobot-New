// lib/widgets/chat_bubble.dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart' hide TextDirection;
import '../constants/app_colors.dart';
import '../models/chat_message.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  final bool showAvatar;
  
  const ChatBubble({
    Key? key,
    required this.message,
    this.showAvatar = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final bool isStudent = message.sender == SenderType.student;
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 15),
      child: Row(
        mainAxisAlignment: isStudent
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar for bot (non-student) messages
          if (!isStudent && showAvatar)
            const CircleAvatar(
              radius: 16,
              backgroundColor: AppColors.primary,
              child: Icon(
                Icons.smart_toy,
                color: Colors.white,
                size: 18,
              ),
            )
          else if (!isStudent)
            const SizedBox(width: 32),
            
          const SizedBox(width: 8),
          
          // Message content
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 15,
                vertical: 10,
              ),
              decoration: BoxDecoration(
                color: isStudent
                    ? AppColors.userBubble
                    : AppColors.botBubble,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(15),
                  topRight: const Radius.circular(15),
                  bottomLeft: Radius.circular(isStudent ? 15 : 0),
                  bottomRight: Radius.circular(isStudent ? 0 : 15),
                ),
              ),
              child: Column(
                crossAxisAlignment: isStudent
                    ? CrossAxisAlignment.end
                    : CrossAxisAlignment.start,
                children: [
                  // Message text with Directionality widget to handle RTL properly
                  Directionality(
                    textDirection: isStudent ? TextDirection.rtl : TextDirection.ltr,
                    child: Text(
                      message.content,
                      style: const TextStyle(
                        fontSize: 15,
                        height: 1.4,
                      ),
                      textAlign: isStudent ? TextAlign.right : TextAlign.left,
                    ),
                  ),
                  
                  const SizedBox(height: 5),
                  
                  // Timestamp
                  Text(
                    _formatTime(message.timestamp),
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.grey.shade600,
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(width: 8),
          
          // Avatar for student messages
          if (isStudent && showAvatar)
            CircleAvatar(
              radius: 16,
              backgroundColor: Colors.blue.shade100,
              child: const Icon(
                Icons.person,
                color: Colors.blueAccent,
                size: 18,
              ),
            )
          else if (isStudent)
            const SizedBox(width: 32),
        ],
      ),
    );
  }
  
  // Format timestamp to display time
  String _formatTime(DateTime time) {
    return DateFormat('HH:mm').format(time);
  }
}