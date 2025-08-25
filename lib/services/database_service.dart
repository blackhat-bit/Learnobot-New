// lib/services/database_service.dart
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/student.dart';
import '../models/chat_message.dart';
import '../models/teacher.dart';

class DatabaseService extends ChangeNotifier {
  // Firestore instance
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  
  // Collection references
  final CollectionReference _usersCollection = FirebaseFirestore.instance.collection('users');
  final CollectionReference _studentsCollection = FirebaseFirestore.instance.collection('students');
  final CollectionReference _teachersCollection = FirebaseFirestore.instance.collection('teachers');
  final CollectionReference _chatsCollection = FirebaseFirestore.instance.collection('chats');
  
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
  
  // Add a new student
  Future<void> addStudent(Student student) async {
    try {
      // Try to add to Firestore first
      try {
        await _studentsCollection.doc(student.id).set(student.toMap());
      } catch (e) {
        debugPrint('Firestore add student error: $e');
      }
      
      // Always update local cache
      _students.add(student);
      notifyListeners();
    } catch (e) {
      throw Exception('Error adding student: $e');
    }
  }
  
  // Update a student
  Future<void> updateStudent(Student updatedStudent) async {
    try {
      // Try to update in Firestore first
      try {
        await _studentsCollection.doc(updatedStudent.id).update(updatedStudent.toMap());
      } catch (e) {
        debugPrint('Firestore update student error: $e');
      }
      
      // Always update local cache
      final index = _students.indexWhere((student) => student.id == updatedStudent.id);
      if (index != -1) {
        _students[index] = updatedStudent;
        notifyListeners();
      }
    } catch (e) {
      throw Exception('Error updating student: $e');
    }
  }
  
  // Delete a student
  Future<void> deleteStudent(String id) async {
    try {
      // Try to delete from Firestore first
      try {
        await _studentsCollection.doc(id).delete();
      } catch (e) {
        debugPrint('Firestore delete student error: $e');
      }
      
      // Always update local cache
      _students.removeWhere((student) => student.id == id);
      notifyListeners();
    } catch (e) {
      throw Exception('Error deleting student: $e');
    }
  }
  
  // TEACHER MANAGEMENT METHODS
  
  // Get teacher by ID
  Teacher? getTeacherById(String id) {
    try {
      return _teachers.firstWhere((teacher) => teacher.id == id);
    } catch (e) {
      return null;
    }
  }
  
  // Update a teacher
  Future<void> updateTeacher(Teacher updatedTeacher) async {
    try {
      // Try to update in Firestore first
      try {
        await _teachersCollection.doc(updatedTeacher.id).update(updatedTeacher.toMap());
      } catch (e) {
        debugPrint('Firestore update teacher error: $e');
      }
      
      // Always update local cache
      final index = _teachers.indexWhere((teacher) => teacher.id == updatedTeacher.id);
      if (index != -1) {
        _teachers[index] = updatedTeacher;
        notifyListeners();
      }
    } catch (e) {
      throw Exception('Error updating teacher: $e');
    }
  }
  
  // CHAT AND MESSAGE METHODS
  
  // Get chat history for a specific student
  List<ChatMessage> getChatHistory(String studentId) {
    return _chatHistory[studentId] ?? [];
  }
  
  // Add message to chat history
  Future<void> addChatMessage(String studentId, ChatMessage message) async {
    try {
      // Try to add to Firestore first
      try {
        await _chatsCollection
            .doc(studentId)
            .collection('messages')
            .doc(message.id)
            .set(message.toMap());
      } catch (e) {
        debugPrint('Firestore add message error: $e');
      }
      
      // Always update local cache
      if (!_chatHistory.containsKey(studentId)) {
        _chatHistory[studentId] = [];
      }
      
      _chatHistory[studentId]!.add(message);
      notifyListeners();
    } catch (e) {
      throw Exception('Error adding message: $e');
    }
  }
  
  // Clear chat history for a student
  Future<void> clearChatHistory(String studentId) async {
    try {
      // Try to delete from Firestore first
      try {
        final messageDocs = await _chatsCollection
            .doc(studentId)
            .collection('messages')
            .get();
            
        for (var doc in messageDocs.docs) {
          await doc.reference.delete();
        }
      } catch (e) {
        debugPrint('Firestore clear chat history error: $e');
      }
      
      // Always update local cache
      _chatHistory[studentId] = [];
      notifyListeners();
    } catch (e) {
      throw Exception('Error clearing chat history: $e');
    }
  }
  
  // ANALYTICS AND REPORTING
  
  // Get student statistics
  Map<String, dynamic> getStudentStatistics(String studentId) {
    final chatMessages = _chatHistory[studentId] ?? [];
    final totalMessages = chatMessages.length;
    final studentMessages = chatMessages.where((msg) => 
        msg.sender == SenderType.student).length;
    final botMessages = chatMessages.where((msg) => 
        msg.sender == SenderType.bot).length;
    
    // Calculate average response time (in seconds)
    double avgResponseTime = 0;
    if (chatMessages.length > 2) {
      int totalResponseTime = 0;
      int responseCount = 0;
      
      for (int i = 1; i < chatMessages.length; i++) {
        if (chatMessages[i].sender == SenderType.bot && 
            chatMessages[i-1].sender == SenderType.student) {
          final diff = chatMessages[i].timestamp.difference(
              chatMessages[i-1].timestamp).inSeconds;
          totalResponseTime += diff;
          responseCount++;
        }
      }
      
      if (responseCount > 0) {
        avgResponseTime = totalResponseTime / responseCount;
      }
    }
    
    // Get feedback ratings
    final ratings = chatMessages
        .where((msg) => msg.metadata != null && msg.metadata!.containsKey('rating'))
        .map((msg) => msg.metadata!['rating'] as int)
        .toList();
    
    final avgRating = ratings.isNotEmpty 
        ? ratings.reduce((a, b) => a + b) / ratings.length 
        : 0;
    
    // Most common support type
    final supportTypes = chatMessages
        .where((msg) => msg.metadata != null && msg.metadata!.containsKey('supportType'))
        .map((msg) => msg.metadata!['supportType'] as String)
        .toList();
    
    Map<String, int> supportTypeCounts = {};
    for (var type in supportTypes) {
      supportTypeCounts[type] = (supportTypeCounts[type] ?? 0) + 1;
    }
    
    String? mostCommonSupportType;
    int maxCount = 0;
    supportTypeCounts.forEach((type, count) {
      if (count > maxCount) {
        maxCount = count;
        mostCommonSupportType = type;
      }
    });
    
    return {
      'conversationCount': totalMessages,
      'studentMessageCount': studentMessages,
      'botMessageCount': botMessages,
      'averageResponseTime': avgResponseTime,
      'averageRating': avgRating,
      'commonSupportType': mostCommonSupportType ?? 'פירוק לשלבים',
      'feedbackCount': ratings.length,
    };
  }
  
  // Get overall system statistics
  Map<String, dynamic> getSystemStatistics() {
    final totalStudents = _students.length;
  // Get total messages
  int totalMessages = 0;
  for (var messages in _chatHistory.values) {
    totalMessages += messages.length;
  }

    
  int totalDifficultyLevel = 0;
  for (var student in _students) {
    totalDifficultyLevel += student.difficultyLevel;
  }
  final double avgDifficulty = totalStudents > 0 
    ? totalDifficultyLevel / totalStudents : 0.0;

    // Distribution by grade
    Map<String, int> gradeDistribution = {};
    for (var student in _students) {
      gradeDistribution[student.grade] = (gradeDistribution[student.grade] ?? 0) + 1;
    }
    
    return {
      'totalStudents': totalStudents,
      'totalMessages': totalMessages,
      'averageDifficultyLevel': avgDifficulty,
      'gradeDistribution': gradeDistribution,
      'lastUpdateTimestamp': DateTime.now().millisecondsSinceEpoch,
    };
  }
  
  // FIRESTORE SYNC METHODS
  
  // Fetch all students from Firestore
  Future<void> fetchStudentsFromFirestore() async {
    try {
      final snapshot = await _studentsCollection.get();
      final List<Student> fetchedStudents = [];
      
      for (var doc in snapshot.docs) {
        final data = doc.data() as Map<String, dynamic>;
        fetchedStudents.add(Student.fromMap(data));
      }
      
      // Update local cache
      _students.clear();
      _students.addAll(fetchedStudents);
      notifyListeners();
    } catch (e) {
      debugPrint('Error fetching students from Firestore: $e');
      // Continue with mock data
    }
  }
  
  // Fetch chat history for a student from Firestore
  Future<void> fetchChatHistoryFromFirestore(String studentId) async {
    try {
      final snapshot = await _chatsCollection
          .doc(studentId)
          .collection('messages')
          .orderBy('timestamp')
          .get();
      
      final List<ChatMessage> fetchedMessages = [];
      
      for (var doc in snapshot.docs) {
        final data = doc.data();
        fetchedMessages.add(ChatMessage.fromMap(data));
      }
      
      // Update local cache
      _chatHistory[studentId] = fetchedMessages;
      notifyListeners();
    } catch (e) {
      debugPrint('Error fetching chat history from Firestore: $e');
      // Continue with mock data
    }
  }
  
  // Sync all local data to Firestore
  Future<void> syncAllDataToFirestore() async {
    try {
      // Sync students
      for (var student in _students) {
        await _studentsCollection.doc(student.id).set(student.toMap());
      }
      
      // Sync chat history
      _chatHistory.forEach((studentId, messages) async {
        for (var message in messages) {
          await _chatsCollection
              .doc(studentId)
              .collection('messages')
              .doc(message.id)
              .set(message.toMap());
        }
      });
      
      debugPrint('All data synced to Firestore successfully');
    } catch (e) {
      debugPrint('Error syncing data to Firestore: $e');
    }
  }
}