import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'auth_service_backend.dart';

class AnalyticsService {
  // Get student analytics
  static Future<Map<String, dynamic>> getStudentAnalytics({
    required int studentId,
    String? token,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.analyticsEndpoint}/student/$studentId'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get student analytics: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get student analytics: $e');
    }
  }

  // Get session analytics
  static Future<List<Map<String, dynamic>>> getSessionAnalytics({
    required String startDate,
    required String endDate,
    String? token,
  }) async {
    try {
      final uri = Uri.parse('${ApiConfig.analyticsEndpoint}/sessions/export')
          .replace(queryParameters: {
        'start_date': startDate,
        'end_date': endDate,
      });

      final response = await http.get(
        uri,
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get session analytics: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get session analytics: $e');
    }
  }

  // Get teacher summary
  static Future<Map<String, dynamic>> getTeacherSummary({
    required int teacherId,
    String? token,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.analyticsEndpoint}/teacher/$teacherId/summary'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get teacher summary: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get teacher summary: $e');
    }
  }

  // Get research patterns (Admin only)
  static Future<Map<String, dynamic>> getResearchPatterns({
    String? token,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.analyticsEndpoint}/research/patterns'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get research patterns: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get research patterns: $e');
    }
  }

  // Export analytics data as CSV
  static Future<String> exportAnalytics({
    required String startDate,
    required String endDate,
    String? token,
  }) async {
    try {
      final uri = Uri.parse('${ApiConfig.analyticsEndpoint}/export/csv')
          .replace(queryParameters: {
        'start_date': startDate,
        'end_date': endDate,
      });

      final response = await http.get(
        uri,
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.uploadTimeout);

      if (response.statusCode == 200) {
        return response.body; // CSV content
      } else {
        throw Exception('Failed to export analytics: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to export analytics: $e');
    }
  }

  // Export student data as CSV for Excel analysis
  static Future<String> exportStudentsCSV({
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.analyticsEndpoint}/export/students/csv'),
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.uploadTimeout);

      if (response.statusCode == 200) {
        return response.body; // CSV content
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to export students data');
      }
    } catch (e) {
      throw Exception('Failed to export students data: $e');
    }
  }

  // Get all students for analytics
  static Future<List<Map<String, dynamic>>> getAllStudents({
    String? token,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.analyticsEndpoint}/students'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get students: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get students: $e');
    }
  }

  // Get dashboard summary for teacher/manager
  static Future<Map<String, dynamic>> getDashboardSummary({
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      // Get current user info to get teacher_id
      final userInfo = await AuthServiceBackend.getCurrentUser(token: authToken);
      
      // For admin/manager, use teacher_id = 0 or 1 (backend will handle showing all students)
      // For teachers, get their actual teacher_profile id
      int teacherId = 0;
      
      if (userInfo['role'] == 'teacher' || userInfo['role'] == 'TEACHER') {
        teacherId = userInfo['teacher_profile']?['id'] ?? 0;
        if (teacherId == 0) {
          throw Exception('No teacher profile found for teacher user');
        }
      } else if (userInfo['role'] == 'admin' || userInfo['role'] == 'ADMIN') {
        // For admin, we need to pass ANY teacher_id (backend checks role and ignores it for admins)
        // Use 1 as a dummy value since backend will show all students for admin
        teacherId = 1;
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.analyticsEndpoint}/summary/teacher/$teacherId'),
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data;
      } else {
        throw Exception('Failed to get dashboard summary: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get dashboard summary: $e');
    }
  }

  // Update student profile
  static Future<Map<String, dynamic>> updateStudentProfile({
    required int studentId,
    required Map<String, dynamic> updates,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.put(
        Uri.parse('${ApiConfig.analyticsEndpoint}/students/$studentId'),
        headers: ApiConfig.getHeaders(token: authToken),
        body: json.encode(updates),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to update student');
      }
    } catch (e) {
      throw Exception('Failed to update student: $e');
    }
  }

  // Archive methods
  
  // Get conversation history for archive
  static Future<List<Map<String, dynamic>>> getConversationArchive({
    int? studentId,
    int days = 30,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      Map<String, String> queryParams = {'days': days.toString()};
      if (studentId != null) {
        queryParams['student_id'] = studentId.toString();
      }

      final uri = Uri.parse('${ApiConfig.analyticsEndpoint}/archive/conversations')
          .replace(queryParameters: queryParams);

      final response = await http.get(
        uri,
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to get conversation archive');
      }
    } catch (e) {
      throw Exception('Failed to get conversation archive: $e');
    }
  }

  // Get detailed student progress for archive
  static Future<Map<String, dynamic>> getStudentProgressArchive({
    required int studentId,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.analyticsEndpoint}/archive/student-progress/$studentId'),
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to get student progress archive');
      }
    } catch (e) {
      throw Exception('Failed to get student progress archive: $e');
    }
  }

  // Get summary report for archive
  static Future<Map<String, dynamic>> getSummaryReport({
    DateTime? startDate,
    DateTime? endDate,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      Map<String, String> queryParams = {};
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String();
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String();
      }

      final uri = Uri.parse('${ApiConfig.analyticsEndpoint}/archive/reports/summary')
          .replace(queryParameters: queryParams.isNotEmpty ? queryParams : null);

      final response = await http.get(
        uri,
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to get summary report');
      }
    } catch (e) {
      throw Exception('Failed to get summary report: $e');
    }
  }

  // Export comprehensive analytics data as CSV
  static Future<String> exportComprehensiveCSV({
    DateTime? startDate,
    DateTime? endDate,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      Map<String, String> queryParams = {};
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String();
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String();
      }

      final uri = Uri.parse('${ApiConfig.analyticsEndpoint}/export/comprehensive-csv')
          .replace(queryParameters: queryParams.isNotEmpty ? queryParams : null);

      final response = await http.get(
        uri,
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.uploadTimeout);

      if (response.statusCode == 200) {
        return response.body; // CSV content
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to export comprehensive CSV');
      }
    } catch (e) {
      throw Exception('Failed to export comprehensive CSV: $e');
    }
  }
}
