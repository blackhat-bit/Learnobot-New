// lib/widgets/chat_bubble.dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart' hide TextDirection;
import '../constants/app_colors.dart';
import '../models/chat_message.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  final bool showAvatar;
  final Function(String)? onSpeakPressed;
  final String? studentProfileImageUrl;
  
  const ChatBubble({
    Key? key,
    required this.message,
    this.showAvatar = true,
    this.onSpeakPressed,
    this.studentProfileImageUrl,
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
                  // Message text with proper RTL/LTR handling for mixed content
                  _buildMessageText(message.content, isStudent),
                  
                  const SizedBox(height: 5),
                  
                  // Bottom row with timestamp and speaker button (for bot only)
                  Row(
                    mainAxisAlignment: isStudent
                        ? MainAxisAlignment.end
                        : MainAxisAlignment.spaceBetween,
                    children: [
                      // Timestamp
                      Text(
                        _formatTime(message.timestamp),
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey.shade600,
                        ),
                      ),
                      
                      // Speaker button for bot messages only
                      if (!isStudent && onSpeakPressed != null)
                        IconButton(
                          icon: const Icon(
                            Icons.volume_up,
                            size: 16,
                            color: AppColors.primary,
                          ),
                          onPressed: () => onSpeakPressed!(message.content),
                          tooltip: 'הקרא בקול',
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(
                            minWidth: 24,
                            minHeight: 24,
                          ),
                        ),
                    ],
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
              backgroundImage: studentProfileImageUrl != null && studentProfileImageUrl!.isNotEmpty
                  ? NetworkImage(studentProfileImageUrl!)
                  : null,
              child: studentProfileImageUrl == null || studentProfileImageUrl!.isEmpty
                  ? const Icon(
                      Icons.person,
                      color: Colors.blueAccent,
                      size: 18,
                    )
                  : null,
            )
          else if (isStudent)
            const SizedBox(width: 32),
        ],
      ),
    );
  }
  
  // Build message text with proper RTL/LTR handling for mixed content
  Widget _buildMessageText(String content, bool isStudent) {
    // Detect if the message contains mathematical expressions or mixed content
    final bool hasMathOrNumbers = _containsMathOrNumbers(content);
    
    if (hasMathOrNumbers) {
      // For mixed content, we need special handling
      return _buildMixedContentText(content, isStudent);
    } else {
      // Regular text - use appropriate direction
      return Directionality(
        textDirection: isStudent ? TextDirection.rtl : TextDirection.ltr,
        child: Text(
          content,
          style: const TextStyle(
            fontSize: 15,
            height: 1.4,
          ),
          textAlign: isStudent ? TextAlign.right : TextAlign.left,
        ),
      );
    }
  }
  
  // Check if text contains mathematical expressions or numbers
  bool _containsMathOrNumbers(String text) {
    // Check for numbers, mathematical symbols, or English mathematical terms
    final mathPattern = RegExp(r'[\d+\-*/=()<>\[\]{}.,]|[a-zA-Z]{2,}');
    return mathPattern.hasMatch(text);
  }
  
  // Build text widget for mixed Hebrew-Math content
  Widget _buildMixedContentText(String content, bool isStudent) {
    // Split content into segments and handle each appropriately
    List<InlineSpan> spans = _parseContentToSpans(content);
    
    return RichText(
      textDirection: TextDirection.rtl, // Start with RTL for Hebrew
      textAlign: isStudent ? TextAlign.right : TextAlign.left,
      text: TextSpan(
        style: const TextStyle(
          fontSize: 15,
          height: 1.4,
          color: Colors.black,
        ),
        children: spans,
      ),
    );
  }
  
  // Parse content into spans with proper directionality
  List<InlineSpan> _parseContentToSpans(String content) {
    List<InlineSpan> spans = [];
    
    // Simple regex to match mathematical expressions or English words
    final RegExp mathRegex = RegExp(r'([0-9+\-*/=().<>\[\]{},:;]+|\b[a-zA-Z]+\b)');
    
    int lastEnd = 0;
    for (Match match in mathRegex.allMatches(content)) {
      // Add Hebrew text before the match
      if (match.start > lastEnd) {
        String hebrewText = content.substring(lastEnd, match.start);
        if (hebrewText.isNotEmpty) {
          spans.add(TextSpan(
            text: hebrewText,
            // Hebrew text - use RTL embedding
            style: const TextStyle(textBaseline: TextBaseline.alphabetic),
          ));
        }
      }
      
      // Add the mathematical/English part with LTR override
      String mathText = match.group(0)!;
      spans.add(TextSpan(
        text: '\u202D$mathText\u202C', // LTR override + pop directional formatting
        style: const TextStyle(
          fontFamily: 'monospace', // Better for numbers and math
          textBaseline: TextBaseline.alphabetic,
        ),
      ));
      
      lastEnd = match.end;
    }
    
    // Add any remaining Hebrew text
    if (lastEnd < content.length) {
      String remainingText = content.substring(lastEnd);
      if (remainingText.isNotEmpty) {
        spans.add(TextSpan(text: remainingText));
      }
    }
    
    // If no matches found, return the whole content as Hebrew
    if (spans.isEmpty) {
      spans.add(TextSpan(text: content));
    }
    
    return spans;
  }
  
  // Format timestamp to display time
  String _formatTime(DateTime time) {
    return DateFormat('HH:mm').format(time);
  }
}