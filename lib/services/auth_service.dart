// lib/services/auth_service.dart

import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class AuthService {
  static const String _usersKey = 'local_users';
  static const String _currentUserKey = 'current_user';
  
  // Initialize with test users
  Future<void> _initializeTestUsers() async {
    final prefs = await SharedPreferences.getInstance();
    final usersJson = prefs.getString(_usersKey);
    
    // Only create test users if no users exist
    if (usersJson == null || usersJson == '[]') {
      final testUsers = [
        {
          'uid': 'teacher_test_1',
          'email': 'teacher@test.com',
          'password': '123456',
          'username': 'מורה דוגמא',
          'role': 'Teacher',
        },
        {
          'uid': 'student_test_1', 
          'email': 'student@test.com',
          'password': '123456',
          'username': 'תלמיד דוגמא',
          'role': 'Student',
        },
        {
          'uid': 'admin_test_1',
          'email': 'admin@test.com',
          'password': '123456',
          'username': 'מנהל פרויקט',
          'role': 'Admin',
        },
      ];
      
      await prefs.setString(_usersKey, json.encode(testUsers));
    }
  }

  // Registration: Creates user locally and saves data
  Future<Map<String, dynamic>?> registerWithEmail({
    required String email,
    required String password,
    required String username,
    required String role, // 'Teacher' or 'Student'
  }) async {
    final prefs = await SharedPreferences.getInstance();
    
    // Get existing users
    final usersJson = prefs.getString(_usersKey) ?? '[]';
    final List<dynamic> users = json.decode(usersJson);
    
    // Check if user already exists
    if (users.any((user) => user['email'] == email)) {
      throw Exception('User already exists');
    }
    
    // Create new user
    final newUser = {
      'uid': DateTime.now().millisecondsSinceEpoch.toString(),
      'email': email,
      'password': password, // In production, this should be hashed
      'username': username,
      'role': role,
    };
    
    users.add(newUser);
    await prefs.setString(_usersKey, json.encode(users));
    
    return newUser;
  }

  // Login with Email/Password
  Future<Map<String, dynamic>?> loginWithEmail({
    required String email,
    required String password,
  }) async {
    // Initialize test users if needed
    await _initializeTestUsers();
    
    final prefs = await SharedPreferences.getInstance();
    final usersJson = prefs.getString(_usersKey) ?? '[]';
    final List<dynamic> users = json.decode(usersJson);
    
    final user = users.firstWhere(
      (user) => user['email'] == email && user['password'] == password,
      orElse: () => null,
    );
    
    if (user != null) {
      await prefs.setString(_currentUserKey, json.encode(user));
      return user;
    }
    
    throw Exception('Invalid credentials');
  }

  // Login and check role (returns username if correct, null if wrong role)
  Future<String?> loginAndCheckRole({
    required String email,
    required String password,
    required String role, // 'Teacher' or 'Student'
  }) async {
    try {
      final user = await loginWithEmail(email: email, password: password);
      if (user != null && user['role'] == role) {
        return user['username'] as String;
      }
      await signOut();
      return null;
    } catch (e) {
      return null;
    }
  }

  // Get current user's role
  Future<String?> getCurrentUserRole() async {
    final userData = await getCurrentUserData();
    return userData?['role'] as String?;
  }

  // Universal login method that returns user role
  Future<Map<String, dynamic>?> loginWithAutoRole({
    required String email,
    required String password,
  }) async {
    try {
      final user = await loginWithEmail(email: email, password: password);
      if (user != null) {
        return {
          'username': user['username'],
          'role': user['role'],
          'email': user['email'],
          'uid': user['uid'],
        };
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  // Get current user's data
  Future<Map<String, dynamic>?> getCurrentUserData() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString(_currentUserKey);
    if (userJson != null) {
      return json.decode(userJson);
    }
    return null;
  }

  // Get current user's username
  Future<String?> getCurrentUserName() async {
    final userData = await getCurrentUserData();
    return userData?['username'] as String?;
  }

  // Sign out
  Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_currentUserKey);
  }
}
