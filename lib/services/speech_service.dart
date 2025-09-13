// lib/services/speech_service.dart
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:speech_to_text/speech_recognition_result.dart';

class SpeechService extends ChangeNotifier {
  late FlutterTts _flutterTts;
  late SpeechToText _speechToText;
  
  bool _isTtsInitialized = false;
  bool _isSttInitialized = false;
  bool _isSpeaking = false;
  bool _isListening = false;
  String _lastWords = '';
  double _confidence = 0.0;

  // TTS State
  bool get isSpeaking => _isSpeaking;
  bool get isTtsInitialized => _isTtsInitialized;

  // STT State
  bool get isListening => _isListening;
  bool get isSttInitialized => _isSttInitialized;
  String get lastWords => _lastWords;
  double get confidence => _confidence;

  SpeechService() {
    _initializeTts();
    _initializeStt();
  }

  // Initialize Text-to-Speech
  Future<void> _initializeTts() async {
    try {
      _flutterTts = FlutterTts();

      // Configure TTS for Hebrew
      await _flutterTts.setLanguage("he-IL");
      await _flutterTts.setSpeechRate(0.5); // Slower for learning disabilities
      await _flutterTts.setVolume(0.8);
      await _flutterTts.setPitch(1.0);

      // Set up TTS handlers
      _flutterTts.setStartHandler(() {
        _isSpeaking = true;
        notifyListeners();
      });

      _flutterTts.setCompletionHandler(() {
        _isSpeaking = false;
        notifyListeners();
      });

      _flutterTts.setErrorHandler((msg) {
        print('TTS Error: $msg');
        _isSpeaking = false;
        notifyListeners();
      });

      _isTtsInitialized = true;
      print('TTS initialized successfully');
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
    if (!_isTtsInitialized) {
      await _initializeTts();
    }

    if (_isTtsInitialized && text.isNotEmpty) {
      try {
        // Stop any current speech
        await stop();
        
        // Start speaking
        await _flutterTts.speak(text);
      } catch (e) {
        print('Error speaking: $e');
        _isSpeaking = false;
        notifyListeners();
      }
    }
  }

  Future<void> stop() async {
    if (_isTtsInitialized) {
      await _flutterTts.stop();
      _isSpeaking = false;
      notifyListeners();
    }
  }

  Future<void> pause() async {
    if (_isTtsInitialized) {
      await _flutterTts.pause();
      _isSpeaking = false;
      notifyListeners();
    }
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
    _flutterTts.stop();
    _speechToText.stop();
    super.dispose();
  }
}