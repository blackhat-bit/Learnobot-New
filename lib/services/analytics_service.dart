import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';

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

  // Get dashboard summary for admin
  static Future<Map<String, dynamic>> getDashboardSummary({
    String? token,
  }) async {
    try {
      // This endpoint doesn't exist yet, but we can create it
      // For now, we'll aggregate from existing endpoints
      
      // Get research patterns as a proxy for dashboard data
      final patterns = await getResearchPatterns(token: token);
      
      // Return a dashboard-friendly format
      return {
        'total_sessions': 0, // Will be populated from patterns
        'total_students': 0,
        'total_interactions': 0,
        'recent_activities': [],
        'patterns': patterns,
      };
    } catch (e) {
      throw Exception('Failed to get dashboard summary: $e');
    }
  }
}
