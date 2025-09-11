import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'auth_service_backend.dart';

class ChatServiceBackend {
  // Create a new chat session
  static Future<Map<String, dynamic>> createSession({
    required String mode, // 'practice' or 'test'
  }) async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.post(
        Uri.parse('${ApiConfig.chatEndpoint}/sessions'),
        headers: ApiConfig.getHeaders(token: token),
        body: json.encode({
          'mode': mode,
        }),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to create session');
      }
    } catch (e) {
      throw Exception('Failed to create session: $e');
    }
  }

  // Get user's chat sessions
  static Future<List<Map<String, dynamic>>> getSessions() async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('${ApiConfig.chatEndpoint}/sessions'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get sessions: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get sessions: $e');
    }
  }

  // Get messages for a session
  static Future<List<Map<String, dynamic>>> getMessages({
    required int sessionId,
  }) async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('${ApiConfig.chatEndpoint}/sessions/$sessionId/messages'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get messages: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get messages: $e');
    }
  }

  // Send a message
  static Future<Map<String, dynamic>> sendMessage({
    required int sessionId,
    required String content,
    String? assistanceType, // 'breakdown', 'example', 'explain'
    String? provider, // LLM provider to use
  }) async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final body = {
        'content': content,
      };
      if (assistanceType != null) {
        body['assistance_type'] = assistanceType;
      }
      if (provider != null) {
        body['provider'] = provider;
      }

      final response = await http.post(
        Uri.parse('${ApiConfig.chatEndpoint}/sessions/$sessionId/messages'),
        headers: ApiConfig.getHeaders(token: token),
        body: json.encode(body),
      ).timeout(ApiConfig.uploadTimeout); // Longer timeout for AI responses

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to send message');
      }
    } catch (e) {
      throw Exception('Failed to send message: $e');
    }
  }

  // Upload and process an image/task
  static Future<Map<String, dynamic>> uploadTask({
    required int sessionId,
    required List<int> imageBytes,
    required String fileName,
  }) async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig.chatEndpoint}/sessions/$sessionId/upload-task'),
      );

      request.headers.addAll(ApiConfig.getHeaders(token: token));
      request.files.add(http.MultipartFile.fromBytes(
        'file',
        imageBytes,
        filename: fileName,
      ));

      final streamedResponse = await request.send().timeout(ApiConfig.uploadTimeout);
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to upload task');
      }
    } catch (e) {
      throw Exception('Failed to upload task: $e');
    }
  }

  // Rate a message
  static Future<void> rateMessage({
    required int messageId,
    required int rating, // 1-5
  }) async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.put(
        Uri.parse('${ApiConfig.chatEndpoint}/messages/$messageId/rate'),
        headers: ApiConfig.getHeaders(token: token),
        body: json.encode({
          'message_id': messageId,
          'rating': rating,
        }),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to rate message');
      }
    } catch (e) {
      throw Exception('Failed to rate message: $e');
    }
  }

  // Call teacher for help
  static Future<void> callTeacher({
    required int sessionId,
  }) async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.post(
        Uri.parse('${ApiConfig.chatEndpoint}/call-teacher/$sessionId'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to call teacher');
      }
    } catch (e) {
      throw Exception('Failed to call teacher: $e');
    }
  }

  // End a session
  static Future<void> endSession({
    required int sessionId,
  }) async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.post(
        Uri.parse('${ApiConfig.chatEndpoint}/sessions/$sessionId/end'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to end session');
      }
    } catch (e) {
      throw Exception('Failed to end session: $e');
    }
  }

  // Get available AI models
  static Future<List<Map<String, dynamic>>> getAvailableModels() async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/v1/llm/models'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get available models: ${response.statusCode}');
      }
    } catch (e) {
      print('Failed to get available models: $e');
      // Return fallback models if API fails
      return [
        {
          'provider_type': 'ollama',
          'provider_name': 'Ollama (Local)',
          'models': [
            {
              'provider_key': 'ollama-llama3_1_8b',
              'model_name': 'llama3.1:8b',
              'display_name': 'llama3.1:8b',
              'active': true
            }
          ]
        }
      ];
    }
  }
}
