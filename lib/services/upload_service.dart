import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'auth_service_backend.dart';

class UploadService {
  /// Upload profile picture for current user
  static Future<Map<String, dynamic>> uploadProfilePicture({
    required dynamic imageFile, // Can be File or XFile
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig.baseUrl}/api/v1/upload/profile-picture'),
      );

      // Add authorization header
      request.headers['Authorization'] = 'Bearer $authToken';
      
      // Handle both File and XFile
      List<int> bytes;
      String filename;
      
      if (imageFile is File) {
        // For File objects (web/desktop)
        bytes = await imageFile.readAsBytes();
        filename = imageFile.path.split('/').last;
      } else {
        // For XFile objects (mobile)
        bytes = await imageFile.readAsBytes();
        filename = imageFile.name;
      }
      
      // Add file using bytes
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: filename,
        ),
      );

      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to upload profile picture');
      }
    } catch (e) {
      throw Exception('Failed to upload profile picture: $e');
    }
  }

  /// Delete current user's profile picture
  static Future<void> deleteProfilePicture({
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.delete(
        Uri.parse('${ApiConfig.baseUrl}/api/v1/upload/profile-picture'),
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to delete profile picture');
      }
    } catch (e) {
      throw Exception('Failed to delete profile picture: $e');
    }
  }

  /// Get current user's profile picture info
  static Future<Map<String, dynamic>> getProfilePictureInfo({
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/v1/upload/profile-picture'),
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to get profile picture info');
      }
    } catch (e) {
      throw Exception('Failed to get profile picture info: $e');
    }
  }

  /// Upload profile picture for a specific student (Teacher/Admin only)
  static Future<Map<String, dynamic>> uploadStudentProfilePicture({
    required dynamic imageFile, // Can be File or XFile
    required int studentId,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig.baseUrl}/api/v1/upload/student-profile-picture/$studentId'),
      );

      // Add authorization header
      request.headers['Authorization'] = 'Bearer $authToken';
      
      // Handle both File and XFile
      List<int> bytes;
      String filename;
      
      if (imageFile is File) {
        // For File objects (web/desktop)
        bytes = await imageFile.readAsBytes();
        filename = imageFile.path.split('/').last;
      } else {
        // For XFile objects (mobile)
        bytes = await imageFile.readAsBytes();
        filename = imageFile.name;
      }
      
      // Add file using bytes
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: filename,
        ),
      );

      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to upload student profile picture');
      }
    } catch (e) {
      throw Exception('Failed to upload student profile picture: $e');
    }
  }

  /// Delete profile picture for a specific student (Teacher/Admin only)
  static Future<void> deleteStudentProfilePicture({
    required int studentId,
    String? token,
  }) async {
    try {
      String? authToken = token ?? await AuthServiceBackend.getStoredToken();
      
      if (authToken == null) {
        throw Exception('No authentication token found');
      }

      final response = await http.delete(
        Uri.parse('${ApiConfig.baseUrl}/api/v1/upload/student-profile-picture/$studentId'),
        headers: ApiConfig.getHeaders(token: authToken),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to delete student profile picture');
      }
    } catch (e) {
      throw Exception('Failed to delete student profile picture: $e');
    }
  }

  /// Get full image URL from relative path
  static String getImageUrl(String? relativePath) {
    if (relativePath == null || relativePath.isEmpty) {
      return '';
    }
    return '${ApiConfig.baseUrl}$relativePath';
  }
}