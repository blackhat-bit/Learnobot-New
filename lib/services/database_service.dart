// lib/services/database_service.dart
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/student.dart';
import '../models/chat_message.dart';
import '../models/teacher.dart';

class DatabaseService extends ChangeNotifier {
  static const String _studentsKey = 'local_students';
  static const String _teachersKey = 'local_teachers';
  static const String _chatsKey = 'local_chats';
  
  // Mock data for development/demo
  final List<Student> _students = [
    Student(
      id: '1',
      name: 'חן לוי',
      grade: '3\'ג',
      difficultyLevel: 3,
      description: 'מתקשה בקריאת הוראות ארוכות ובפירוק משימות מורכבות',
      profileImageUrl: '',
    ),
    Student(
      id: '2',
      name: 'הילה שושני',
      grade: '1\'ה',
      difficultyLevel: 2,
      description: 'קשיי קשב וריכוז, צריכה הסברים קצרים וברורים',
      profileImageUrl: '',
    ),
    Student(
      id: '3',
      name: 'רון שני',
      grade: '2\'ב',
      difficultyLevel: 4,
      description: 'קשיים בהבנת הוראות מילוליות, מעדיף הוראות חזותיות',
      profileImageUrl: '',
    ),
    Student(
      id: '4',
      name: 'נילי נעים',
      grade: '1\'ו',
      difficultyLevel: 1,
      description: 'צריכה חיזוקים חיוביים תכופים לשמירה על מוטיבציה',
      profileImageUrl: '',
    ),
    Student(
      id: '5',
      name: 'נועם אופלי',
      grade: '5\'ג',
      difficultyLevel: 5,
      description: 'קשיים משמעותיים בהבנת הוראות, נדרשת עזרה צמודה',
      profileImageUrl: '',
    ),
  ];
  
  final List<Teacher> _teachers = [
    Teacher(
      id: 'teacher_1',
      name: 'המורה עדי',
      email: 'adi.teacher@example.com',
      school: 'בית ספר יסודי דוגמא',
    ),
  ];
  
  final Map<String, List<ChatMessage>> _chatHistory = {};
  
  // Constructor
  DatabaseService() {
    _initializeData();
  }
  
  // Initialize mock data for demo
  void _initializeData() {
    // Initialize chat history for each student
    for (var student in _students) {
      if (!_chatHistory.containsKey(student.id)) {
        _chatHistory[student.id] = [
          ChatMessage(
            id: '${student.id}_msg1',
            content: 'שלום, ${student.name}! אני כאן כדי לעזור לך בהבנת הוראות ומשימות. במה אוכל לסייע לך היום?',
            timestamp: DateTime.now().subtract(const Duration(days: 3, hours: 2)),
            sender: SenderType.bot,
          ),
        ];
      }
    }
  }
  
  // STUDENT MANAGEMENT METHODS
  
  // Get all students
  List<Student> getAllStudents() {
    return List.from(_students);
  }
  
  // Get student by ID
  Student? getStudentById(String id) {
    try {
      return _students.firstWhere((student) => student.id == id);
    } catch (e) {
      return null;
    }
  }
  
  // Add new student
  Future<void> addStudent(Student student) async {
    try {
      _students.add(student);
      await _saveStudentsToLocal();
      notifyListeners();
    } catch (e) {
      debugPrint('Error adding student: $e');
      rethrow;
    }
  }
  
  // Update student
  Future<void> updateStudent(Student updatedStudent) async {
    try {
      final index = _students.indexWhere((s) => s.id == updatedStudent.id);
      if (index != -1) {
        _students[index] = updatedStudent;
        await _saveStudentsToLocal();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Error updating student: $e');
      rethrow;
    }
  }
  
  // Delete student
  Future<void> deleteStudent(String id) async {
    try {
      _students.removeWhere((student) => student.id == id);
      _chatHistory.remove(id);
      await _saveStudentsToLocal();
      await _saveChatsToLocal();
      notifyListeners();
    } catch (e) {
      debugPrint('Error deleting student: $e');
      rethrow;
    }
  }
  
  // TEACHER MANAGEMENT METHODS
  
  // Get all teachers
  List<Teacher> getAllTeachers() {
    return List.from(_teachers);
  }
  
  // Update teacher
  Future<void> updateTeacher(Teacher updatedTeacher) async {
    try {
      final index = _teachers.indexWhere((t) => t.id == updatedTeacher.id);
      if (index != -1) {
        _teachers[index] = updatedTeacher;
        await _saveTeachersToLocal();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Error updating teacher: $e');
      rethrow;
    }
  }
  
  // CHAT MANAGEMENT METHODS
  
  // Add message to chat
  Future<void> addMessageToChat(String studentId, ChatMessage message) async {
    try {
      if (!_chatHistory.containsKey(studentId)) {
        _chatHistory[studentId] = [];
      }
      _chatHistory[studentId]!.add(message);
      await _saveChatsToLocal();
      notifyListeners();
    } catch (e) {
      debugPrint('Error adding message to chat: $e');
      rethrow;
    }
  }
  
  // Get chat history for student
  Future<List<ChatMessage>> getChatHistory(String studentId) async {
    try {
      return _chatHistory[studentId] ?? [];
    } catch (e) {
      debugPrint('Error getting chat history: $e');
      return [];
    }
  }
  
  // Clear chat history for student
  Future<void> clearChatHistory(String studentId) async {
    try {
      _chatHistory[studentId] = [];
      await _saveChatsToLocal();
      notifyListeners();
    } catch (e) {
      debugPrint('Error clearing chat history: $e');
      rethrow;
    }
  }
  
  // Get recent chats for all students
  List<Map<String, dynamic>> getRecentChats() {
    List<Map<String, dynamic>> recentChats = [];
    
    for (var student in _students) {
      final messages = _chatHistory[student.id] ?? [];
      if (messages.isNotEmpty) {
        final lastMessage = messages.last;
        recentChats.add({
          'student': student,
          'lastMessage': lastMessage,
          'messageCount': messages.length,
        });
      }
    }
    
    // Sort by timestamp (most recent first)
    recentChats.sort((a, b) => 
      b['lastMessage'].timestamp.compareTo(a['lastMessage'].timestamp));
    
    return recentChats;
  }
  
  // STATISTICS METHODS
  
  // Get total number of students
  int getTotalStudentsCount() {
    return _students.length;
  }
  
  // Get total number of messages
  int getTotalMessagesCount() {
    int totalMessages = 0;
    for (var messages in _chatHistory.values) {
      totalMessages += messages.length;
    }
    return totalMessages;
  }
  
  // Get average difficulty level
  double getAverageDifficultyLevel() {
    if (_students.isEmpty) return 0.0;
    
    int totalDifficulty = 0;
    for (var student in _students) {
      totalDifficulty += student.difficultyLevel;
    }
    
    return totalDifficulty / _students.length;
  }
  
  // Get students by difficulty level
  List<Student> getStudentsByDifficultyLevel(int level) {
    return _students.where((student) => student.difficultyLevel == level).toList();
  }
  
  // Get students with recent activity (within last 7 days)
  List<Student> getStudentsWithRecentActivity() {
    final sevenDaysAgo = DateTime.now().subtract(const Duration(days: 7));
    List<Student> activeStudents = [];
    
    for (var student in _students) {
      final messages = _chatHistory[student.id] ?? [];
      if (messages.any((message) => message.timestamp.isAfter(sevenDaysAgo))) {
        activeStudents.add(student);
      }
    }
    
    return activeStudents;
  }
  
  // DATA PERSISTENCE METHODS
  
  Future<void> _saveStudentsToLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final studentsJson = _students.map((s) => s.toMap()).toList();
      await prefs.setString(_studentsKey, json.encode(studentsJson));
    } catch (e) {
      debugPrint('Error saving students to local storage: $e');
    }
  }
  
  Future<void> _saveTeachersToLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final teachersJson = _teachers.map((t) => t.toMap()).toList();
      await prefs.setString(_teachersKey, json.encode(teachersJson));
    } catch (e) {
      debugPrint('Error saving teachers to local storage: $e');
    }
  }
  
  Future<void> _saveChatsToLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final chatsJson = <String, dynamic>{};
      _chatHistory.forEach((studentId, messages) {
        chatsJson[studentId] = messages.map((m) => m.toMap()).toList();
      });
      await prefs.setString(_chatsKey, json.encode(chatsJson));
    } catch (e) {
      debugPrint('Error saving chats to local storage: $e');
    }
  }
  
  Future<void> loadDataFromLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      
      // Load students
      final studentsJson = prefs.getString(_studentsKey);
      if (studentsJson != null) {
        final studentsList = json.decode(studentsJson) as List;
        _students.clear();
        _students.addAll(studentsList.map((s) => Student.fromMap(s)));
      }
      
      // Load teachers
      final teachersJson = prefs.getString(_teachersKey);
      if (teachersJson != null) {
        final teachersList = json.decode(teachersJson) as List;
        _teachers.clear();
        _teachers.addAll(teachersList.map((t) => Teacher.fromMap(t)));
      }
      
      // Load chats
      final chatsJson = prefs.getString(_chatsKey);
      if (chatsJson != null) {
        final chatsMap = json.decode(chatsJson) as Map<String, dynamic>;
        _chatHistory.clear();
        chatsMap.forEach((studentId, messagesList) {
          _chatHistory[studentId] = (messagesList as List)
              .map((m) => ChatMessage.fromMap(m))
              .toList();
        });
      }
      
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading data from local storage: $e');
    }
  }
  
  // BACKUP METHODS
  
  Future<void> exportData() async {
    try {
      await _saveStudentsToLocal();
      await _saveTeachersToLocal();
      await _saveChatsToLocal();
    } catch (e) {
      debugPrint('Error exporting data: $e');
      rethrow;
    }
  }
}
