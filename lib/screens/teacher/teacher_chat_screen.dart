// lib/screens/teacher/teacher_chat_screen.dart
import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../models/chat_message.dart';
import '../../models/student.dart';
import '../../widgets/chat_bubble.dart';
import 'package:provider/provider.dart';
import '../../services/database_service.dart';

class TeacherChatScreen extends StatefulWidget {
  final Student student;
  
  const TeacherChatScreen({
    Key? key,
    required this.student,
  }) : super(key: key);

  @override
  State<TeacherChatScreen> createState() => _TeacherChatScreenState();
}

class _TeacherChatScreenState extends State<TeacherChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  List<ChatMessage> _messages = [];
  bool _isTyping = false;
  bool _isSending = false;
  
  @override
  void initState() {
    super.initState();
    _loadChatHistory();
  }
  
  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
  
  void _loadChatHistory() {
    final databaseService = Provider.of<DatabaseService>(context, listen: false);
    setState(() {
      _messages = databaseService.getChatHistory(widget.student.id);
      
      // If no chat history exists, add a welcome message
      if (_messages.isEmpty) {
        _messages.add(
          ChatMessage(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            content: 'שלום, המורה ${widget.student.name}! אני כאן כדי לסייע לך בהבנת הוראות ומשימות. במה אוכל לעזור היום?',
            timestamp: DateTime.now(),
            sender: SenderType.bot,
          ),
        );
      }
    });
    
    // Scroll to bottom after messages are loaded
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
    });
  }
  
  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }
  
  void _sendMessage() async {
    if (_messageController.text.trim().isEmpty) return;
    
    final messageText = _messageController.text.trim();
    _messageController.clear();
    
    final newMessage = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: messageText,
      timestamp: DateTime.now(),
      sender: SenderType.teacher,
    );
    
    setState(() {
      _messages.add(newMessage);
      _isSending = true;
    });
    
    // Scroll to show the new message
    _scrollToBottom();
    
    // Save the message to the database
    final databaseService = Provider.of<DatabaseService>(context, listen: false);
    await databaseService.addChatMessage(widget.student.id, newMessage);
    
    // Simulate the student's response after a short delay
    await Future.delayed(const Duration(seconds: 1));
    
    setState(() {
      _isTyping = true;
    });
    
    // Scroll to show typing indicator
    _scrollToBottom();
    
    // Simulate typing delay
    await Future.delayed(const Duration(seconds: 2));
    
    // Generate a response
    final studentResponse = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: _generateStudentResponse(messageText),
      timestamp: DateTime.now(),
      sender: SenderType.student,
    );
    
    setState(() {
      _isTyping = false;
      _isSending = false;
      _messages.add(studentResponse);
    });
    
    // Save the student's response
    await databaseService.addChatMessage(widget.student.id, studentResponse);
    
    // Scroll to show the response
    _scrollToBottom();
  }
  
  String _generateStudentResponse(String teacherMessage) {
    // In a real app, this would be connected to the student's profile and AI analysis
    // For demo purposes, return simple responses
    
    if (teacherMessage.contains('?')) {
      return 'תודה על השאלה, המורה. אני מתקשה להבין את ההוראות בעמוד 34. האם תוכל/י להסביר לי מה בדיוק צריך לעשות בשאלה 3?';
    } else if (teacherMessage.toLowerCase().contains('להסביר') || 
               teacherMessage.toLowerCase().contains('הסבר')) {
      return 'תודה רבה על ההסבר! עכשיו אני מבין יותר טוב. אני אנסה לפתור את התרגיל שוב.';
    } else if (teacherMessage.toLowerCase().contains('שיעורי בית') || 
               teacherMessage.toLowerCase().contains('משימה') ||
               teacherMessage.toLowerCase().contains('תרגיל')) {
      return 'אני אעבוד על זה הערב. האם אוכל לשלוח לך את התשובות לבדיקה מחר?';
    } else {
      return 'תודה על ההודעה, המורה. אשמח לקבל עוד עזרה בהבנת ההוראות של המשימה הבאה.';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: Colors.white,
              child: Text(
                widget.student.name.substring(0, 1),
                style: const TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Text(widget.student.name),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              _showStudentInfoDialog(context);
            },
          ),
          IconButton(
            icon: const Icon(Icons.more_vert),
            onPressed: () {
              _showChatOptionsMenu(context);
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Display student's difficulty level
          Container(
            color: _getDifficultyColor(widget.student.difficultyLevel).withOpacity(0.2),
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  size: 16,
                  color: _getDifficultyColor(widget.student.difficultyLevel),
                ),
                const SizedBox(width: 8),
                Text(
                  'רמת קושי: ${widget.student.difficultyLevel}/5',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: _getDifficultyColor(widget.student.difficultyLevel),
                  ),
                ),
                const Spacer(),
                Text(
                  'כיתה: ${widget.student.grade}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          
          // Chat messages
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                image: const DecorationImage(
                  image: AssetImage('assets/images/chat_background.png'),
                  fit: BoxFit.cover,
                  opacity: 0.1,
                ),
              ),
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.all(16),
                itemCount: _messages.length + (_isTyping ? 1 : 0),
                itemBuilder: (context, index) {
                  // Show typing indicator if needed
                  if (index == _messages.length && _isTyping) {
                    return Align(
                      alignment: Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.only(top: 10, right: 50),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 10,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade300,
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(
                                  Colors.grey,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'מקליד...',
                              style: TextStyle(
                                color: Colors.grey.shade700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }
                  
                  // Regular message
                  final message = _messages[index];
                  
                  return ChatBubble(
                    message: message,
                    showAvatar: index == 0 || 
                      _messages[index - 1].sender != message.sender,
                  );
                },
              ),
            ),
          ),
          
          // Message input
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.2),
                  spreadRadius: 1,
                  blurRadius: 5,
                ),
              ],
            ),
            padding: const EdgeInsets.symmetric(
              horizontal: 8,
              vertical: 8,
            ),
            child: Row(
              children: [
                // Attachment button
                IconButton(
                  icon: const Icon(Icons.attach_file),
                  onPressed: () {
                    _showAttachmentOptions(context);
                  },
                  color: Colors.grey,
                ),
                
                // Text input
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    textDirection: TextDirection.rtl,
                    decoration: const InputDecoration(
                      hintText: 'הקלד הודעה...',
                      hintTextDirection: TextDirection.rtl,
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                    maxLines: null,
                    textInputAction: TextInputAction.send,
                  ),
                ),
                
                // Send button
                Container(
                  margin: const EdgeInsets.only(right: 4),
                  child: _isSending
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                          ),
                        )
                      : IconButton(
                          icon: const Icon(Icons.send),
                          onPressed: _sendMessage,
                          color: AppColors.primary,
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  void _showStudentInfoDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('פרטי תלמיד'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('שם: ${widget.student.name}', style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('כיתה: ${widget.student.grade}'),
            const SizedBox(height: 8),
            Text('רמת קושי: ${widget.student.difficultyLevel}/5'),
            const SizedBox(height: 12),
            const Text('תיאור קשיים:', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(widget.student.description),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
            },
            child: const Text('סגור'),
          ),
        ],
      ),
    );
  }
  
  void _showChatOptionsMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.delete),
            title: const Text('נקה היסטוריית שיחה'),
            onTap: () {
              Navigator.pop(context);
              _confirmClearHistory(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.save_alt),
            title: const Text('ייצא שיחה'),
            onTap: () {
              Navigator.pop(context);
              _showExportOptions(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.block),
            title: const Text('חסום הודעות'),
            onTap: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('תכונה זו עדיין לא זמינה'),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
  
  void _confirmClearHistory(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('נקה היסטוריית שיחה'),
        content: const Text('האם אתה בטוח שברצונך למחוק את כל היסטוריית השיחה עם תלמיד זה? פעולה זו אינה הפיכה.'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
            },
            child: const Text('ביטול'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              // Clear chat history
              final databaseService = Provider.of<DatabaseService>(context, listen: false);
              await databaseService.clearChatHistory(widget.student.id);
              
              setState(() {
                _messages = [];
                // Add a new welcome message
                _messages.add(
                  ChatMessage(
                    id: DateTime.now().millisecondsSinceEpoch.toString(),
                    content: 'שלום, ${widget.student.name}! היסטוריית השיחה נוקתה. במה אוכל לעזור היום?',
                    timestamp: DateTime.now(),
                    sender: SenderType.bot,
                  ),
                );
              });
              
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('היסטוריית השיחה נמחקה'),
                ),
              );
            },
            style: TextButton.styleFrom(
              foregroundColor: Colors.red,
            ),
            child: const Text('מחק'),
          ),
        ],
      ),
    );
  }
  
  void _showExportOptions(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('ייצא שיחה'),
        children: [
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('מייצא לPDF... בקרוב!'),
                ),
              );
            },
            child: const Text('ייצא לPDF'),
          ),
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('מייצא לTXT... בקרוב!'),
                ),
              );
            },
            child: const Text('ייצא לTXT'),
          ),
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('שיתוף עם מורים אחרים... בקרוב!'),
                ),
              );
            },
            child: const Text('שתף עם מורים אחרים'),
          ),
        ],
      ),
    );
  }
  
  void _showAttachmentOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.image),
            title: const Text('תמונה'),
            onTap: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('תכונה זו עדיין לא זמינה'),
                ),
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.insert_drive_file),
            title: const Text('מסמך'),
            onTap: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('תכונה זו עדיין לא זמינה'),
                ),
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.camera_alt),
            title: const Text('צילום משימה'),
            onTap: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('תכונה זו עדיין לא זמינה'),
                ),
              );
            },
          ),
        ],
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