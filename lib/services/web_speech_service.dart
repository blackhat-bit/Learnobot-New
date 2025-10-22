// lib/services/web_speech_service.dart
import 'dart:async';
import 'dart:html' as html;
import 'package:flutter/foundation.dart';

/// Web-specific TTS service using browser's native speechSynthesis API
/// This provides better Hebrew language support on Chrome/Edge browsers
class WebSpeechService extends ChangeNotifier {
  html.SpeechSynthesis? _speechSynthesis;
  html.SpeechSynthesisUtterance? _currentUtterance;
  List<html.SpeechSynthesisVoice> _availableVoices = [];
  html.SpeechSynthesisVoice? _selectedHebrewVoice;
  html.SpeechSynthesisVoice? _fallbackVoice;
  
  bool _isInitialized = false;
  bool _isSpeaking = false;
  String _lastError = '';

  // Getters
  bool get isInitialized => _isInitialized;
  bool get isSpeaking => _isSpeaking;
  String get lastError => _lastError;
  bool get hasHebrewVoice => _selectedHebrewVoice != null;

  WebSpeechService() {
    _initializeWebSpeech();
  }

  /// Initialize the Web Speech API
  Future<void> _initializeWebSpeech() async {
    try {
      // Check if speechSynthesis is available
      if (html.window.speechSynthesis == null) {
        _lastError = 'Speech synthesis not supported in this browser';
        print('❌ Web Speech API not available');
        return;
      }

      _speechSynthesis = html.window.speechSynthesis!;
      
      // Load available voices
      await _loadVoices();
      
      _isInitialized = true;
      print('✅ Web Speech API initialized successfully');
      print('📢 Available voices: ${_availableVoices.length}');
      print('🇮🇱 Hebrew voice available: ${_selectedHebrewVoice?.name ?? 'None'}');
      
    } catch (e) {
      _lastError = 'Failed to initialize Web Speech API: $e';
      print('❌ Web Speech API initialization failed: $e');
    }
    
    notifyListeners();
  }

  /// Load and categorize available voices
  Future<void> _loadVoices() async {
    try {
      // Get voices - may need to wait for them to load
      _availableVoices = _speechSynthesis!.getVoices();
      
      // If no voices loaded yet, wait for voiceschanged event
      if (_availableVoices.isEmpty) {
        await _waitForVoices();
      }

      _selectBestVoices();
      
    } catch (e) {
      print('Error loading voices: $e');
    }
  }

  /// Wait for voices to be loaded (some browsers load them asynchronously)
  Future<void> _waitForVoices() async {
    final completer = Completer<void>();
    
    // Try to get voices directly (fallback)
    Future.delayed(const Duration(milliseconds: 100), () {
      _availableVoices = _speechSynthesis!.getVoices();
      if (_availableVoices.isNotEmpty && !completer.isCompleted) {
        completer.complete();
      }
    });

    // Timeout after 2 seconds
    Future.delayed(const Duration(seconds: 2), () {
      if (!completer.isCompleted) {
        completer.complete();
      }
    });

    await completer.future;
  }

  /// Select the best Hebrew and fallback voices
  void _selectBestVoices() {
    // Hebrew language codes to look for
    const hebrewCodes = ['he', 'he-IL', 'iw', 'iw-IL'];
    
    // Find Hebrew voice
    for (final langCode in hebrewCodes) {
      try {
        _selectedHebrewVoice = _availableVoices.firstWhere(
          (voice) => voice.lang?.toLowerCase().startsWith(langCode.toLowerCase()) ?? false,
        );
        break;
      } catch (e) {
        // Continue to next language code
      }
    }

    // Find fallback English voice
    try {
      _fallbackVoice = _availableVoices.firstWhere(
        (voice) => voice.lang?.toLowerCase().startsWith('en') ?? false,
      );
    } catch (e) {
      // Use first available voice as fallback
      _fallbackVoice = _availableVoices.isNotEmpty ? _availableVoices.first : null;
    }

    print('🎯 Selected Hebrew voice: ${_selectedHebrewVoice?.name ?? 'None'} (${_selectedHebrewVoice?.lang ?? 'N/A'})');
    print('🔄 Fallback voice: ${_fallbackVoice?.name ?? 'None'} (${_fallbackVoice?.lang ?? 'N/A'})');
  }

  /// Speak the given text using Web Speech API
  Future<void> speak(String text) async {
    if (!_isInitialized) {
      _lastError = 'Web Speech API not initialized';
      print('❌ Cannot speak: Web Speech API not initialized');
      return;
    }

    if (text.trim().isEmpty) {
      print('⚠️ Empty text provided to speak');
      return;
    }

    try {
      // Stop any current speech
      await stop();

      // Create utterance
      _currentUtterance = html.SpeechSynthesisUtterance(text);
      
      // Configure utterance
      _currentUtterance!.rate = 0.8; // Slightly slower for learning disabilities
      _currentUtterance!.pitch = 1.0;
      _currentUtterance!.volume = 0.8;

      // Select voice based on text content
      final voice = _detectTextLanguage(text) == 'hebrew' 
          ? (_selectedHebrewVoice ?? _fallbackVoice)
          : _fallbackVoice;
      
      if (voice != null) {
        _currentUtterance!.voice = voice;
        print('🗣️ Using voice: ${voice.name} (${voice.lang}) for text: "${text.substring(0, text.length > 50 ? 50 : text.length)}..."');
      }

      // Set up event listeners
      _currentUtterance!.onStart.listen((_) {
        _isSpeaking = true;
        print('🎵 TTS started speaking');
        notifyListeners();
      });

      _currentUtterance!.onEnd.listen((_) {
        _isSpeaking = false;
        print('✅ TTS completed speaking');
        notifyListeners();
      });

      _currentUtterance!.onError.listen((event) {
        _isSpeaking = false;
        _lastError = 'TTS error occurred';
        print('❌ TTS error occurred');
        notifyListeners();
      });

      // Start speaking
      _speechSynthesis!.speak(_currentUtterance!);
      
    } catch (e) {
      _isSpeaking = false;
      _lastError = 'Failed to speak: $e';
      print('❌ Web TTS speak error: $e');
      notifyListeners();
    }
  }

  /// Stop current speech
  Future<void> stop() async {
    if (_speechSynthesis != null && _isSpeaking) {
      _speechSynthesis!.cancel();
      _isSpeaking = false;
      notifyListeners();
    }
  }

  /// Pause current speech
  Future<void> pause() async {
    if (_speechSynthesis != null && _isSpeaking) {
      _speechSynthesis!.pause();
      _isSpeaking = false;
      notifyListeners();
    }
  }

  /// Resume paused speech
  Future<void> resume() async {
    if (_speechSynthesis != null) {
      _speechSynthesis!.resume();
      _isSpeaking = true;
      notifyListeners();
    }
  }

  /// Simple language detection for Hebrew text
  String _detectTextLanguage(String text) {
    // Hebrew Unicode range: \u0590-\u05FF
    final hebrewRegex = RegExp(r'[\u0590-\u05FF]');
    final hebrewMatches = hebrewRegex.allMatches(text).length;
    final totalChars = text.replaceAll(RegExp(r'\s'), '').length;
    
    // If more than 30% of non-space characters are Hebrew, consider it Hebrew
    if (totalChars > 0 && (hebrewMatches / totalChars) > 0.3) {
      return 'hebrew';
    }
    
    return 'other';
  }

  /// Get list of available voices for debugging
  List<Map<String, String>> getAvailableVoices() {
    return _availableVoices.map((voice) => {
      'name': voice.name ?? 'Unknown',
      'lang': voice.lang ?? 'Unknown',
      'localService': voice.localService?.toString() ?? 'false',
    }).toList();
  }

  /// Check if Hebrew TTS is supported
  bool get isHebrewSupported => _selectedHebrewVoice != null;

  @override
  void dispose() {
    stop();
    super.dispose();
  }
}
