import 'dart:convert';
import 'package:http/http.dart' as http;

/// Simple wrapper that talks to the local Ollama server on Windows.
class LocalLlmService {
  static const _url = 'http://13.60.179.69:8000/chat';

  Future<String> ask({
    required String question,
    required bool examMode,
  }) async {
    // For now, examMode can be handled in the backend later if needed.

    final res = await http.post(
      Uri.parse(_url),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'question': question,
        // You can add 'examMode': examMode if you update your backend for this
      }),
    );

    if (res.statusCode != 200) {
      throw Exception('LLM error ${res.statusCode}: ${res.body}');
    }
    // Note: 'reply', not 'message'
    return (jsonDecode(res.body)['reply'] as String).trim();
  }

  String _buildPrompt(String q, bool exam) => q;

//   String _buildPrompt(String q, bool exam) => exam
//       ? '''
// You are ExamHelperBot.
// - Do NOT reveal the full answer.
// - Break down what the question asks.
// - Give hints only.

// Question: $q
// '''
//       : '''
// You are TutorBot.
// 1. Explain clearly in simple words.
// 2. Break the reasoning into stages.
// 3. Provide a concrete worked example.

// Question: $q
// ''';
// }
}
