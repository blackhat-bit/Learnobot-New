// lib/services/speech_service.dart
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:speech_to_text/speech_recognition_result.dart';

// Import web speech service for web platform
import 'web_speech_service.dart' if (dart.library.io) 'web_speech_service_stub.dart';

class SpeechService extends ChangeNotifier {
  late FlutterTts _flutterTts;
  late SpeechToText _speechToText;
  WebSpeechService? _webSpeechService;
  
  bool _isTtsInitialized = false;
  bool _isSttInitialized = false;
  bool _isSpeaking = false;
  bool _isListening = false;
  String _lastWords = '';
  double _confidence = 0.0;
  String _lastError = '';

  // TTS State
  bool get isSpeaking => kIsWeb ? (_webSpeechService?.isSpeaking ?? false) : _isSpeaking;
  bool get isTtsInitialized => kIsWeb ? (_webSpeechService?.isInitialized ?? false) : _isTtsInitialized;
  String get lastError => kIsWeb ? (_webSpeechService?.lastError ?? '') : _lastError;
  bool get hasHebrewVoice => kIsWeb ? (_webSpeechService?.hasHebrewVoice ?? false) : true; // Assume mobile has Hebrew

  // STT State
  bool get isListening => _isListening;
  bool get isSttInitialized => _isSttInitialized;
  String get lastWords => _lastWords;
  double get confidence => _confidence;

  SpeechService() {
    if (kIsWeb) {
      // Initialize web-specific TTS service
      _webSpeechService = WebSpeechService();
      _webSpeechService!.addListener(() {
        notifyListeners(); // Forward notifications from web service
      });
    }
    _initializeTts();
    _initializeStt();
  }

  // Initialize Text-to-Speech
  Future<void> _initializeTts() async {
    // Skip flutter_tts initialization on web - use WebSpeechService instead
    if (kIsWeb) {
      _isTtsInitialized = true;
      notifyListeners();
      return;
    }
    
    try {
      _flutterTts = FlutterTts();

      // Get available languages first
      List<dynamic> languages = await _flutterTts.getLanguages ?? [];
      print('Available TTS languages: $languages');

      // Try multiple Hebrew language codes
      List<String> hebrewCodes = ["he-IL", "he", "iw-IL", "iw"];
      String? workingLanguage;
      
      for (String langCode in hebrewCodes) {
        try {
          int result = await _flutterTts.setLanguage(langCode);
          print('Trying language $langCode, result: $result');
          if (result == 1) {
            workingLanguage = langCode;
            break;
          }
        } catch (e) {
          print('Failed to set language $langCode: $e');
        }
      }

      if (workingLanguage == null) {
        print('Hebrew TTS not available, falling back to default language');
        // Try to set default language
        await _flutterTts.setLanguage("en-US");
        workingLanguage = "en-US";
      }

      print('Using TTS language: $workingLanguage');

      await _flutterTts.setSpeechRate(0.5); // Slower for learning disabilities
      await _flutterTts.setVolume(0.8);
      await _flutterTts.setPitch(1.0);

      // Set up TTS handlers
      _flutterTts.setStartHandler(() {
        print('TTS started speaking');
        _isSpeaking = true;
        notifyListeners();
      });

      _flutterTts.setCompletionHandler(() {
        print('TTS completed speaking');
        _isSpeaking = false;
        notifyListeners();
      });

      _flutterTts.setErrorHandler((msg) {
        print('TTS Error: $msg');
        _isSpeaking = false;
        notifyListeners();
      });

      // Test TTS with a simple Hebrew phrase
      print('Testing TTS with Hebrew text...');
      await _flutterTts.speak("שלום");

      _isTtsInitialized = true;
      print('TTS initialized successfully with language: $workingLanguage');
    } catch (e) {
      print('Failed to initialize TTS: $e');
      _isTtsInitialized = false;
    }
    notifyListeners();
  }

  // Initialize Speech-to-Text
  Future<void> _initializeStt() async {
    try {
      _speechToText = SpeechToText();
      bool available = await _speechToText.initialize(
        onError: (error) {
          print('STT Error: $error');
          _isListening = false;
          notifyListeners();
        },
        onStatus: (status) {
          print('STT Status: $status');
          if (status == 'done' || status == 'notListening') {
            _isListening = false;
            notifyListeners();
          }
        },
      );

      _isSttInitialized = available;
      print('STT initialized: $available');
    } catch (e) {
      print('Failed to initialize STT: $e');
      _isSttInitialized = false;
    }
    notifyListeners();
  }

  // Text-to-Speech Functions
  Future<void> speak(String text) async {
    print('Speak requested for text: "$text"');
    
    if (!isTtsInitialized) {
      print('TTS not initialized, initializing...');
      await _initializeTts();
    }

    if (!isTtsInitialized) {
      print('TTS initialization failed, cannot speak');
      _lastError = 'TTS initialization failed';
      notifyListeners();
      return;
    }

    if (text.isEmpty) {
      print('Empty text provided, nothing to speak');
      return;
    }

    try {
      // Stop any current speech
      await stop();
      
      print('Starting TTS for: "$text"');
      
      if (kIsWeb) {
        // Use Web Speech API for better Hebrew support on browsers
        await _webSpeechService!.speak(text);
      } else {
        // Use flutter_tts on mobile platforms
        int result = await _flutterTts.speak(text);
        print('TTS speak result: $result');
      }
    } catch (e) {
      print('Error speaking: $e');
      _lastError = 'Error speaking: $e';
      if (!kIsWeb) {
        _isSpeaking = false;
      }
      notifyListeners();
    }
  }

  Future<void> stop() async {
    if (kIsWeb) {
      await _webSpeechService?.stop();
    } else if (_isTtsInitialized) {
      await _flutterTts.stop();
      _isSpeaking = false;
    }
    notifyListeners();
  }

  Future<void> pause() async {
    if (kIsWeb) {
      await _webSpeechService?.pause();
    } else if (_isTtsInitialized) {
      await _flutterTts.pause();
      _isSpeaking = false;
    }
    notifyListeners();
  }

  // Speech-to-Text Functions
  Future<void> startListening({
    Function(String)? onResult,
    Function(String)? onPartialResult,
  }) async {
    if (!_isSttInitialized) {
      await _initializeStt();
    }

    if (_isSttInitialized && !_isListening) {
      try {
        // Stop any current TTS
        await stop();

        _isListening = true;
        notifyListeners();

        await _speechToText.listen(
          onResult: (SpeechRecognitionResult result) {
            _lastWords = result.recognizedWords;
            _confidence = result.confidence;
            
            if (result.finalResult) {
              _isListening = false;
              onResult?.call(_lastWords);
            } else {
              onPartialResult?.call(_lastWords);
            }
            notifyListeners();
          },
          localeId: 'he-IL', // Hebrew locale
          listenFor: const Duration(seconds: 30), // Listen for up to 30 seconds
          pauseFor: const Duration(seconds: 3), // Pause after 3 seconds of silence
          listenOptions: SpeechListenOptions(
            partialResults: true,
            cancelOnError: true,
          ),
        );
      } catch (e) {
        print('Error starting listening: $e');
        _isListening = false;
        notifyListeners();
      }
    }
  }

  Future<void> stopListening() async {
    if (_isSttInitialized && _isListening) {
      await _speechToText.stop();
      _isListening = false;
      notifyListeners();
    }
  }

  // Utility Functions
  Future<List<String>> getAvailableLanguages() async {
    if (!_isTtsInitialized) return [];
    
    try {
      final languages = await _flutterTts.getLanguages;
      return List<String>.from(languages);
    } catch (e) {
      print('Error getting languages: $e');
      return [];
    }
  }

  Future<bool> isLanguageAvailable(String language) async {
    final languages = await getAvailableLanguages();
    return languages.contains(language);
  }

  // Check if Hebrew is supported
  Future<bool> get isHebrewSupported async {
    return await isLanguageAvailable('he-IL') || await isLanguageAvailable('he');
  }

  // Settings
  Future<void> setSpeechRate(double rate) async {
    if (_isTtsInitialized) {
      await _flutterTts.setSpeechRate(rate);
    }
  }

  Future<void> setVolume(double volume) async {
    if (_isTtsInitialized) {
      await _flutterTts.setVolume(volume);
    }
  }

  Future<void> setPitch(double pitch) async {
    if (_isTtsInitialized) {
      await _flutterTts.setPitch(pitch);
    }
  }

  @override
  void dispose() {
    if (kIsWeb) {
      _webSpeechService?.dispose();
    } else {
      _flutterTts.stop();
    }
    _speechToText.stop();
    super.dispose();
  }
}