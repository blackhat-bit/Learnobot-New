// lib/services/chat_service.dart
import 'package:flutter/material.dart';
import '../models/chat_message.dart';
//import '../models/student.dart';
import 'database_service.dart';

class ChatService extends ChangeNotifier {
  final Map<String, List<ChatMessage>> _activeChats = {};
  final List<String> _pendingRequests = [];
  bool _isProcessing = false;
  bool _isRecording = false;

  // Getters
  Map<String, List<ChatMessage>> get activeChats => _activeChats;
  List<String> get pendingRequests => _pendingRequests;
  bool get isProcessing => _isProcessing;
  bool get isRecording => _isRecording;

  // Toggle recording state
  void toggleRecording() {
    _isRecording = !_isRecording;
    notifyListeners();
  }

  // Initialize chat for a student
  Future<void> initChat(String studentId, {DatabaseService? databaseService}) async {
    if (!_activeChats.containsKey(studentId)) {
      // If database service is provided, load chat history from database
      if (databaseService != null) {
        final messages = databaseService.getChatHistory(studentId);
        _activeChats[studentId] = List.from(messages);
      } else {
        _activeChats[studentId] = [];
        
        // Add a welcome message for new chats
        final welcomeMessage = ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: 'שלום! אני כאן כדי לעזור לך להבין את ההוראות. במה אוכל לסייע לך היום?',
          timestamp: DateTime.now(),
          sender: SenderType.bot,
        );
        _activeChats[studentId]!.add(welcomeMessage);
      }
      notifyListeners();
    }
  }

  // Send a message
  Future<void> sendMessage(String studentId, ChatMessage message, {DatabaseService? databaseService}) async {
    // Initialize chat if not already initialized
    if (!_activeChats.containsKey(studentId)) {
      await initChat(studentId, databaseService: databaseService);
    }

    // Add message to active chat
    _activeChats[studentId]!.add(message);
    
    // Save to database if provided
    if (databaseService != null) {
      await databaseService.addChatMessage(studentId, message);
    }
    
    notifyListeners();

    // If message is from a student, automatically generate a bot response
    if (message.sender == SenderType.student) {
      await generateBotResponse(studentId, message, databaseService: databaseService);
    }
  }

  // Generate bot response
  Future<void> generateBotResponse(String studentId, ChatMessage userMessage, {DatabaseService? databaseService}) async {
    _isProcessing = true;
    notifyListeners();

    // Simulate processing delay
    await Future.delayed(const Duration(seconds: 1));

    // Generate response based on user message
    final botResponse = _createBotResponse(studentId, userMessage.content);
    
    // Add bot response to chat
    _activeChats[studentId]!.add(botResponse);
    
    // Save to database if provided
    if (databaseService != null) {
      await databaseService.addChatMessage(studentId, botResponse);
    }

    _isProcessing = false;
    notifyListeners();
  }

  // Helper method to create a bot response based on message content
  ChatMessage _createBotResponse(String studentId, String userMessage) {
    String responseText;
    
    // Simple response logic based on keywords in Hebrew and English
    if (userMessage.contains('?') || 
        userMessage.toLowerCase().contains('עזרה') || 
        userMessage.toLowerCase().contains('help')) {
      responseText = 'אני אשמח לעזור לך. איזה חלק בהוראות אינך מבין?';
    } else if (userMessage.toLowerCase().contains('תודה') || 
              userMessage.toLowerCase().contains('thank')) {
      responseText = 'בשמחה! האם יש משהו נוסף שתרצה לשאול?';
    } else if (userMessage.toLowerCase().contains('פירוק') || 
              userMessage.toLowerCase().contains('שלבים')) {
      responseText = 'הנה פירוק המשימה לשלבים קטנים יותר:\n\n1. קרא את כל ההוראות פעם אחת\n2. סמן את המילים שאינך מבין\n3. זהה מה המטרה הסופית של המשימה\n4. התחל לעבוד צעד אחר צעד';
    } else if (userMessage.toLowerCase().contains('דוגמה') || 
               userMessage.toLowerCase().contains('הדגמה') ||
               userMessage.toLowerCase().contains('example')) {
      responseText = 'הנה דוגמה לפתרון משימה דומה: [כאן תופיע דוגמה מפורטת]';
    } else if (userMessage.toLowerCase().contains('לא מבין') || 
              userMessage.toLowerCase().contains('קשה לי')) {
      responseText = 'אני מבין שזה יכול להיות מאתגר. בוא ננסה להסתכל על זה בצורה אחרת. איזה חלק בדיוק קשה לך?';
    } else {
      // Default response
      responseText = 'הבנתי את השאלה שלך. בוא נפרק את המשימה ביחד לשלבים פשוטים יותר. האם תרצה שאעזור לך בפירוק המשימה, אתן לך דוגמה, או אסביר בצורה אחרת?';
    }

    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: responseText,
      timestamp: DateTime.now(),
      sender: SenderType.bot,
    );
  }

  // Process a specific assistance option (breakdown, demonstrate, explain)
  Future<void> processAssistanceOption(String studentId, String option, {DatabaseService? databaseService}) async {
    String userMessage;
    
    switch (option) {
      case 'breakdown':
        userMessage = 'אנא פרק את המשימה לשלבים';
        break;
      case 'demonstrate':
        userMessage = 'תן לי דוגמה בבקשה';
        break;
      case 'explain':
        userMessage = 'אנא הסבר את המשימה בצורה פשוטה יותר';
        break;
      case 'clarify':
        userMessage = 'יש לי שאלות לגבי המשימה';
        break;
      default:
        userMessage = 'אני צריך עזרה עם המשימה';
    }
    
    // Add user message
    final message = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: userMessage,
      timestamp: DateTime.now(),
      sender: SenderType.student,
    );
    
    await sendMessage(studentId, message, databaseService: databaseService);
  }

  // Request teacher assistance
  void requestTeacherAssistance(String studentId, String studentName) {
    if (!_pendingRequests.contains(studentId)) {
      _pendingRequests.add(studentId);
      notifyListeners();
    }
  }

  // Clear teacher assistance request
  void clearTeacherAssistanceRequest(String studentId) {
    _pendingRequests.remove(studentId);
    notifyListeners();
  }

  // Clear chat history
  Future<void> clearChatHistory(String studentId, {DatabaseService? databaseService}) async {
    if (_activeChats.containsKey(studentId)) {
      _activeChats[studentId]!.clear();
      
      // Clear from database if provided
      if (databaseService != null) {
        await databaseService.clearChatHistory(studentId);
      }
      
      notifyListeners();
    }
  }

  // Get chat messages for a specific student
  List<ChatMessage> getChatMessages(String studentId) {
    return _activeChats[studentId] ?? [];
  }

  // Submit feedback for a bot response
  void submitFeedback(String studentId, String messageId, int rating, {DatabaseService? databaseService}) {
    if (_activeChats.containsKey(studentId)) {
      final index = _activeChats[studentId]!.indexWhere((msg) => msg.id == messageId);
      
      if (index != -1) {
        final message = _activeChats[studentId]![index];
        final updatedMetadata = message.metadata ?? {};
        updatedMetadata['rating'] = rating;
        
        final updatedMessage = ChatMessage(
          id: message.id,
          content: message.content,
          timestamp: message.timestamp,
          sender: message.sender,
          type: message.type,
          metadata: updatedMetadata,
        );
        
        _activeChats[studentId]![index] = updatedMessage;
        
        // Update in database if provided
        if (databaseService != null) {
          databaseService.addChatMessage(studentId, updatedMessage);
        }
        
        notifyListeners();
      }
    }
  }
}