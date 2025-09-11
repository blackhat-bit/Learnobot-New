class ApiConfig {
  // Backend base URL - update this to match your FastAPI server
  static const String baseUrl = 'http://localhost:8000';
  
  // API endpoints
  static const String authEndpoint = '$baseUrl/api/v1/auth';
  static const String chatEndpoint = '$baseUrl/api/v1/chat';
  static const String teacherEndpoint = '$baseUrl/api/v1/teacher';
  static const String studentEndpoint = '$baseUrl/api/v1/student';
  static const String analyticsEndpoint = '$baseUrl/api/v1/analytics';
  static const String llmEndpoint = '$baseUrl/api/v1/llm';
  
  // Request timeouts
  static const Duration defaultTimeout = Duration(seconds: 30);
  static const Duration uploadTimeout = Duration(minutes: 2);
  static const Duration llmTimeout = Duration(minutes: 5); // Extended timeout for slow LLM models
  
  // Headers
  static Map<String, String> getHeaders({String? token}) {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    
    return headers;
  }
}
