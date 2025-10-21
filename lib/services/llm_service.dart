import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'auth_service_backend.dart';

class LLMService {
  // Get all available providers with their status
  static Future<List<Map<String, dynamic>>> getProviders() async {
    try {
      // Get auth token for admin access
      final token = await AuthServiceBackend.getStoredToken();
      final headers = ApiConfig.getHeaders(token: token);
      
      final response = await http.get(
        Uri.parse('${ApiConfig.llmEndpoint}/providers/status'),
        headers: headers,
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to load providers: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading providers: $e');
      throw Exception('Failed to connect to backend: $e');
    }
  }

  // Get all available models grouped by provider
  static Future<List<Map<String, dynamic>>> getAvailableModels() async {
    try {
      final token = await AuthServiceBackend.getStoredToken();
      final headers = ApiConfig.getHeaders(token: token);
      
      final response = await http.get(
        Uri.parse('${ApiConfig.llmEndpoint}/models'),
        headers: headers,
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to load models: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading models: $e');
      throw Exception('Failed to connect to backend: $e');
    }
  }

  // Add API key for a provider
  static Future<Map<String, dynamic>> addApiKey({
    required String providerName,
    required String apiKey,
    String? token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.llmEndpoint}/providers/api-key'),
        headers: ApiConfig.getHeaders(token: token),
        body: json.encode({
          'provider_name': providerName,
          'api_key': apiKey,
        }),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to add API key');
      }
    } catch (e) {
      throw Exception('Failed to add API key: $e');
    }
  }

  // Remove API key for a provider
  static Future<void> removeApiKey({
    required String providerName,
    String? token,
  }) async {
    try {
      final response = await http.delete(
        Uri.parse('${ApiConfig.llmEndpoint}/providers/$providerName/api-key'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to remove API key');
      }
    } catch (e) {
      throw Exception('Failed to remove API key: $e');
    }
  }

  // Activate a provider
  static Future<void> activateProvider({
    required String providerName,
    String? token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.llmEndpoint}/providers/$providerName/activate'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to activate provider');
      }
    } catch (e) {
      throw Exception('Failed to activate provider: $e');
    }
  }

  // Toggle model activation/deactivation
  static Future<void> toggleModelActivation({
    required String providerKey,
    required bool isDeactivated,
    String? token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.llmEndpoint}/models/deactivate'),
        headers: ApiConfig.getHeaders(token: token),
        body: json.encode({
          'model_key': providerKey,
          'is_deactivated': isDeactivated,
        }),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to toggle model');
      }
    } catch (e) {
      throw Exception('Failed to toggle model: $e');
    }
  }

  // Get prompt configuration for a mode
  static Future<Map<String, dynamic>> getPromptConfig({
    required String mode,
    String? token,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.llmEndpoint}/prompts/$mode'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get prompt config: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get prompt config: $e');
    }
  }

  // Save prompt configuration
  static Future<void> savePromptConfig({
    required String mode,
    required String systemPrompt,
    required double temperature,
    required int maxTokens,
    String? token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.llmEndpoint}/prompts/$mode'),
        headers: ApiConfig.getHeaders(token: token),
        body: json.encode({
          'system': systemPrompt,
          'temperature': temperature,
          'maxTokens': maxTokens,
        }),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to save prompt config');
      }
    } catch (e) {
      throw Exception('Failed to save prompt config: $e');
    }
  }

  // Delete saved prompt configuration (reset to default)
  static Future<void> deletePromptConfig({
    required String mode,
    String? token,
  }) async {
    try {
      final response = await http.delete(
        Uri.parse('${ApiConfig.llmEndpoint}/prompts/$mode'),
        headers: ApiConfig.getHeaders(token: token),
      ).timeout(ApiConfig.defaultTimeout);

      if (response.statusCode != 200) {
        throw Exception('Failed to delete prompt config');
      }
    } catch (e) {
      throw Exception('Failed to delete prompt config: $e');
    }
  }

  // Compare providers with a test prompt
  static Future<Map<String, dynamic>> compareProviders({
    required String testPrompt,
    String? token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.llmEndpoint}/compare'),
        headers: ApiConfig.getHeaders(token: token),
        body: json.encode({
          'prompt': testPrompt,
          'providers': ['ollama', 'anthropic', 'openai', 'google', 'cohere'], // Compare all available providers
        }),
      ).timeout(ApiConfig.uploadTimeout); // Longer timeout for comparison

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to compare providers');
      }
    } catch (e) {
      throw Exception('Failed to compare providers: $e');
    }
  }

}
