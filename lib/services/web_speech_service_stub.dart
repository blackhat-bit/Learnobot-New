// lib/services/web_speech_service_stub.dart
// Stub implementation for non-web platforms
import 'package:flutter/foundation.dart';

class WebSpeechService extends ChangeNotifier {
  bool get isInitialized => false;
  bool get isSpeaking => false;
  String get lastError => 'Web Speech API not available on this platform';
  bool get hasHebrewVoice => false;
  bool get isHebrewSupported => false;

  Future<void> speak(String text) async {
    // No-op on non-web platforms
  }

  Future<void> stop() async {
    // No-op on non-web platforms
  }

  Future<void> pause() async {
    // No-op on non-web platforms
  }

  Future<void> resume() async {
    // No-op on non-web platforms
  }

  List<Map<String, String>> getAvailableVoices() {
    return [];
  }
}
