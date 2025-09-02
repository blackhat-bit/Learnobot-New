import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'api_config.dart';

class AuthServiceBackend {
  static const String _tokenKey = 'auth_token';
  static const String _userKey = 'current_user';

  // Login to backend
  static Future<Map<String, dynamic>> login({
    required String username,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.authEndpoint}/login'),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: {
          'username': username,
          'password': password,
        },
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Save token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_tokenKey, data['access_token']);
        
        // Get user info
        final userInfo = await getCurrentUser(token: data['access_token']);
        await prefs.setString(_userKey, json.encode(userInfo));
        
        return {
          'success': true,
          'token': data['access_token'],
          'user': userInfo,
        };
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Login failed');
      }
    } catch (e) {
      throw Exception('Login failed: $e');
    }
  }

  // Register new user
  static Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String username,
    required String fullName,
    required String role, // 'student', 'teacher', 'admin'
    String? grade,
    int? difficultyLevel,
    String? difficultiesDescription,
    String? school,
  }) async {
    try {
      final body = {
        'email': email,
        'password': password,
        'username': username,
        'full_name': fullName,
        'role': role,
      };

      // Add student-specific fields
      if (role == 'student') {
        body['grade'] = grade ?? '';
        body['difficulty_level'] = difficultyLevel ?? 3;
        body['difficulties_description'] = difficultiesDescription ?? '';
      }
      
      // Add teacher-specific fields
      if (role == 'teacher') {
        body['school'] = school ?? '';
      }

      final response = await http.post(
        Uri.parse('${ApiConfig.authEndpoint}/register'),
        headers: ApiConfig.getHeaders(),
        body: json.encode(body),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return {
          'success': true,
          'user': data,
        };
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      throw Exception('Registration failed: $e');
    }
  }

  // Get current user info
  static Future<Map<String, dynamic>> getCurrentUser({String? token}) async {
    try {
      String? authToken = token;
      if (authToken == null) {
        final prefs = await SharedPreferences.getInstance();
        authToken = prefs.getString(_tokenKey);
      }

      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.authEndpoint}/me'),
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get user info: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get user info: $e');
    }
  }

  // Check if user is logged in
  static Future<bool> isLoggedIn() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString(_tokenKey);
      
      if (token == null) return false;
      
      // Verify token is still valid
      await getCurrentUser(token: token);
      return true;
    } catch (e) {
      return false;
    }
  }

  // Get stored user data
  static Future<Map<String, dynamic>?> getStoredUser() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userJson = prefs.getString(_userKey);
      
      if (userJson != null) {
        return json.decode(userJson);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  // Get stored token
  static Future<String?> getStoredToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_tokenKey);
    } catch (e) {
      return null;
    }
  }

  // Logout
  static Future<void> logout() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_tokenKey);
      await prefs.remove(_userKey);
    } catch (e) {
      print('Error during logout: $e');
    }
  }

  // Update user profile
  static Future<Map<String, dynamic>> updateProfile({
    required Map<String, dynamic> updates,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.put(
        Uri.parse('${ApiConfig.authEndpoint}/profile'),
        headers: ApiConfig.getHeaders(token: authToken),
        body: json.encode(updates),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final updatedUser = json.decode(response.body);
        
        // Update stored user data
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_userKey, json.encode(updatedUser));
        
        return updatedUser;
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Profile update failed');
      }
    } catch (e) {
      throw Exception('Profile update failed: $e');
    }
  }
}
