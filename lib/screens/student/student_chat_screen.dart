// lib/screens/student/student_chat_screen.dart
import 'package:flutter/material.dart';
import 'dart:io';
import 'dart:math' as math;
import 'dart:async';
import 'package:provider/provider.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../models/chat_message.dart';
import '../../widgets/chat_bubble.dart';
import 'package:image_picker/image_picker.dart';
import '../../services/chat_service_backend.dart';
import '../../services/speech_service.dart';
import '../../services/upload_service.dart';

class StudentChatScreen extends StatefulWidget {
  final String initialMode;

  const StudentChatScreen({
    Key? key,
    this.initialMode = 'practice',
  }) : super(key: key);

  @override
  State<StudentChatScreen> createState() => _StudentChatScreenState();
}

class _StudentChatScreenState extends State<StudentChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  String _currentMode = 'practice';
  File? _capturedImage;
  bool _showAssistanceOptions = false;
  int? _currentSessionId;
  bool _isBotTyping = false;

  // Track the latest user question/task (for assist buttons)
  String? _lastTaskText;

  // Track last satisfaction for adaptive logic
  int? _lastSatisfaction;

  // Model selection
  List<Map<String, dynamic>> _availableModels = [];
  String? _selectedModel;
  bool _showModelSelector = false;

  // Typing indicator messages
  late List<String> _typingMessages;
  int _currentTypingMessageIndex = 0;
  int _typingAnimationKey = 0;
  Timer? _typingMessageTimer;

  // Speech functionality
  bool _isListening = false;

  // Profile picture
  String? _profileImageUrl;

  @override
  void initState() {
    super.initState();
    _currentMode = widget.initialMode;
    _typingMessages = [
      'מעבד את השאלה...',  // First: Processing the question
      'חושב...',           // Then: Thinking
    ];
    _loadAvailableModels();
    _loadProfilePicture();
    _createSession();
  }

  String _getSelectedModelDisplayName() {
    if (_selectedModel == null) return 'Default';
    
    for (final providerGroup in _availableModels) {
      final models = providerGroup['models'] as List<dynamic>? ?? [];
      for (final model in models) {
        if (model['provider_key'] == _selectedModel) {
          return model['model_name'] ?? model['display_name'] ?? 'Unknown';
        }
      }
    }
    return 'Unknown';
  }
  
  Future<void> _loadAvailableModels() async {
    try {
      final models = await ChatServiceBackend.getAvailableModels();
      setState(() {
        _availableModels = models;
        // Set default selected model to the first active one
        for (final providerGroup in models) {
          final modelsList = providerGroup['models'] as List<dynamic>? ?? [];
          for (final model in modelsList) {
            if (model['active'] == true) {
              _selectedModel = model['provider_key'];
              break;
            }
          }
          if (_selectedModel != null) break;
        }
      });
    } catch (e) {
      print('Failed to load available models: $e');
    }
  }

  Future<void> _loadProfilePicture() async {
    try {
      final profileInfo = await UploadService.getProfilePictureInfo();
      if (mounted && profileInfo['image_url'] != null) {
        setState(() {
          _profileImageUrl = UploadService.getImageUrl(profileInfo['image_url']);
        });
      }
    } catch (e) {
      print('Error loading profile picture: $e');
    }
  }
  
  Future<void> _createSession() async {
    try {
      final session = await ChatServiceBackend.createSession(mode: _currentMode);
      setState(() {
        _currentSessionId = session['id'];
      });
      _addBotMessage('היי! איך אני יכול לעזור לך היום?');
    } catch (e) {
      _addBotMessage('שגיאה בחיבור לשרת: $e');
    }
  }

  @override
  void dispose() {
    // Cancel any ongoing requests
    if (_currentSessionId != null) {
      ChatServiceBackend.cancelRequest(_currentSessionId!);
    }
    // Cancel typing message timer
    _typingMessageTimer?.cancel();
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _addBotMessage(String content, {Map<String, dynamic>? metadata}) {
    setState(() {
      _messages.add(
        ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: content,
          timestamp: DateTime.now(),
          sender: SenderType.bot,
          metadata: metadata,
        ),
      );
    });
    _scrollToBottom();
  }

  void _addUserMessage(String content, {MessageType type = MessageType.text}) {
    setState(() {
      _messages.add(
        ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: content,
          timestamp: DateTime.now(),
          sender: SenderType.student,
          type: type,
        ),
      );
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage() {
    if (_messageController.text.trim().isNotEmpty && !_isBotTyping) {
      final message = _messageController.text.trim();
      _lastTaskText = message; // Track the latest user question
      _addUserMessage(message);
      _messageController.clear();
      _processBotResponse(message);
    }
  }

  Future<void> _processBotResponse(String userMessage) async {
    if (_currentSessionId == null) {
      _addBotMessage('⚠️ שגיאה: אין חיבור לשרת');
      return;
    }

    setState(() {
      _isBotTyping = true;
      _currentTypingMessageIndex = 0; // Start with "מעבד את השאלה..."
      _messages.add(ChatMessage(
        id: 'typing',
        content: '...',
        timestamp: DateTime.now(),
        sender: SenderType.bot,
        type: MessageType.systemMessage,
      ));
    });
    _scrollToBottom();

    // Start timer to switch to "חושב..." after 3 seconds
    _typingMessageTimer?.cancel();
    _typingMessageTimer = Timer(const Duration(seconds: 3), () {
      if (mounted && _isBotTyping) {
        setState(() {
          _currentTypingMessageIndex = 1; // Switch to "חושב..."
        });
      }
    });

    try {
      final response = await ChatServiceBackend.sendMessage(
        sessionId: _currentSessionId!,
        content: userMessage,
        provider: _selectedModel,
      );

      if (mounted) {
        _typingMessageTimer?.cancel(); // Cancel timer when response arrives
        setState(() {
          _messages.removeWhere((m) => m.id == 'typing');
          _addBotMessage(response['content'] ?? 'תשובה לא זמינה');
          _isBotTyping = false;
        });
      }
    } catch (e) {
      if (mounted) {
        _typingMessageTimer?.cancel(); // Cancel timer on error
        setState(() {
          _messages.removeWhere((m) => m.id == 'typing');
          if (e.toString().contains('Request was cancelled')) {
            // Don't show error message for cancelled requests
            _isBotTyping = false;
          } else {
            _addBotMessage('⚠️ שגיאה: $e');
            _isBotTyping = false;
          }
        });
      }
    }
  }

  Future<void> _captureTask() async {
    try {
      // Show options to user: camera or gallery
      final result = await showDialog<String>(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: const Text('העלאת משימה'),
            content: const Text('איך תרצה להעלות את המשימה?'),
            actions: [
              TextButton.icon(
                icon: const Icon(Icons.camera_alt),
                label: const Text('צלם תמונה'),
                onPressed: () => Navigator.of(context).pop('camera'),
              ),
              TextButton.icon(
                icon: const Icon(Icons.photo_library),
                label: const Text('בחר מהגלריה'),
                onPressed: () => Navigator.of(context).pop('gallery'),
              ),
              TextButton(
                child: const Text('בטל'),
                onPressed: () => Navigator.of(context).pop(null),
              ),
            ],
          );
        },
      );

      if (result == null) return;

      final ImagePicker picker = ImagePicker();
      final ImageSource source = result == 'camera' ? ImageSource.camera : ImageSource.gallery;
      final XFile? image = await picker.pickImage(source: source);

      if (image != null) {
        setState(() {
          _capturedImage = File(image.path);
        });

        print('Image captured: ${image.path}');

        _addUserMessage(
          'תמונת משימה',
          type: MessageType.taskCapture,
        );

        _addBotMessage('אני מעבד את המשימה שצילמת...');

        try {
          // Read image bytes
          final imageBytes = await image.readAsBytes();
          print('Image size: ${imageBytes.length} bytes, filename: ${image.name}');
          
          // Upload and process with OCR
          final result = await ChatServiceBackend.uploadTask(
            sessionId: _currentSessionId!,
            imageBytes: imageBytes,
            fileName: image.name,
          );
          
          print('Upload result: $result');
          
          final extractedText = result['extracted_text'] ?? '';
          final response = result['ai_response'] ?? '';
          final message = result['message'] ?? '';
          
          // Check if OCR was successful
          if (extractedText.isNotEmpty && 
              !extractedText.contains('לא הצלחתי') && 
              !extractedText.contains('שגיאה')) {
            _lastTaskText = extractedText;
            _addBotMessage('זיהיתי את המשימה הבאה: \n\n$extractedText');
            
            // If there's a mediation response, show it too
            if (response.isNotEmpty) {
              Future.delayed(const Duration(seconds: 1), () {
                _addBotMessage(response);
              });
            }
            
            Future.delayed(const Duration(seconds: 1), () {
              setState(() {
                _showAssistanceOptions = true;
              });
            });
          } else {
            // OCR failed or returned error message
            String errorMessage = message.isNotEmpty ? message : extractedText;
            if (errorMessage.isEmpty) {
              errorMessage = 'מצטער, לא הצלחתי לזהות טקסט בתמונה. אנא נסה שוב עם תמונה ברורה יותר.';
            }
            _addBotMessage(errorMessage);
          }
        } catch (e) {
          print('Upload task error: $e');
          String errorMessage = 'מצטער, נתקלתי בבעיה בעיבוד התמונה. אנא נסה שוב.';
          
          // Provide more specific error messages
          if (e.toString().contains('TimeoutException')) {
            errorMessage = 'העיבוד לוקח יותר מדי זמן. אנא נסה תמונה קטנה יותר או כתב את השאלה ידנית.';
          } else if (e.toString().contains('Connection')) {
            errorMessage = 'בעיית חיבור לשרת. אנא בדוק את החיבור לאינטרנט ונסה שוב.';
          } else if (e.toString().contains('400')) {
            errorMessage = 'התמונה לא תקינה. אנא נסה תמונה אחרת (JPG, PNG).';
          } else if (e.toString().contains('413')) {
            errorMessage = 'התמונה גדולה מדי. אנא נסה תמונה קטנה יותר (מתחת ל-5MB).';
          }
          
          _addBotMessage(errorMessage);
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בצילום המשימה: $e')),
      );
    }
  }

  // === SPEECH FUNCTIONALITY ===
  Future<void> _handleVoiceInput() async {
    final speechService = Provider.of<SpeechService>(context, listen: false);
    
    if (!speechService.isSttInitialized) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('מערכת הקול אינה מופעלת על המכשיר שלך')),
      );
      return;
    }

    if (_isListening) {
      // Stop listening
      await speechService.stopListening();
      setState(() {
        _isListening = false;
      });
    } else {
      // Start listening
      setState(() {
        _isListening = true;
      });
      
      try {
        await speechService.startListening(
          onResult: (String result) {
            setState(() {
              _isListening = false;
            });
            
            if (result.isNotEmpty) {
              _messageController.text = result;
              _sendMessage(); // Automatically send the message
            }
          },
          onPartialResult: (String partial) {
            // Update text field with partial results
            if (partial.isNotEmpty) {
              _messageController.text = partial;
            }
          },
        );
      } catch (e) {
        setState(() {
          _isListening = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('שגיאה בהקלטה: $e')),
        );
      }
    }
  }

  Future<void> _speakText(String text) async {
    final speechService = Provider.of<SpeechService>(context, listen: false);
    
    if (!speechService.isTtsInitialized) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('מערכת הקריאה אינה זמינה על המכשיר שלך')),
      );
      return;
    }

    await speechService.speak(text);
  }

  // === SATISFACTION BAR LOGIC ===
  Widget _buildSatisfactionBar(ChatMessage message, int msgIdx) {
    return Padding(
      padding: const EdgeInsets.only(top: 4.0, bottom: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(5, (i) {
          final starValue = i + 1;
          return IconButton(
            icon: const Icon(
              Icons.star,
              color: Colors.amber,
              size: 28,
            ),
            onPressed: () => _setSatisfaction(msgIdx, starValue),
          );
        }),
      ),
    );
  }

  void _setSatisfaction(int botMsgIndex, int value) {
    setState(() {
      final msg = _messages[botMsgIndex];
      final newMetadata = Map<String, dynamic>.from(msg.metadata ?? {});
      newMetadata['satisfaction'] = value;
      _messages[botMsgIndex] = ChatMessage(
        id: msg.id,
        content: msg.content,
        timestamp: msg.timestamp,
        sender: msg.sender,
        type: msg.type,
        metadata: newMetadata,
      );
      _lastSatisfaction = value;
    });
  }
  // === END SATISFACTION BAR LOGIC ===

  // === MODEL SELECTOR ===
  Widget _buildModelSelector() {
    if (_availableModels.isEmpty) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            spreadRadius: 1,
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'בחר מודל AI',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primary,
                ),
              ),
              IconButton(
                onPressed: () => setState(() => _showModelSelector = false),
                icon: const Icon(Icons.close, color: AppColors.primary),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ..._availableModels.map((providerGroup) {
            final providerName = providerGroup['provider_name'] as String;
            final models = providerGroup['models'] as List<dynamic>;
            
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    providerName,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppColors.primary,
                    ),
                  ),
                ),
                ...models.map((model) {
                  final providerKey = model['provider_key'] as String;
                  final displayName = model['display_name'] as String;
                  final isSelected = _selectedModel == providerKey;
                  
                  return ListTile(
                    dense: true,
                    leading: Radio<String>(
                      value: providerKey,
                      groupValue: _selectedModel,
                      onChanged: (value) {
                        setState(() {
                          _selectedModel = value;
                          _showModelSelector = false;
                        });
                      },
                      activeColor: AppColors.primary,
                    ),
                    title: Text(
                      displayName,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                        color: isSelected ? AppColors.primary : Colors.black87,
                      ),
                    ),
                    onTap: () {
                      setState(() {
                        _selectedModel = providerKey;
                        _showModelSelector = false;
                      });
                    },
                  );
                }).toList(),
                const SizedBox(height: 8),
              ],
            );
          }).toList(),
        ],
      ),
    );
  }

  // === MODE SELECTOR BAR ===
  Widget _buildModeSelector() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      color: Colors.white,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Practice Mode Button
          GestureDetector(
            onTap: () {
              if (_currentMode != 'practice') {
                setState(() {
                  _currentMode = 'practice';
                });
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
              decoration: BoxDecoration(
                color: _currentMode == 'practice'
                    ? AppColors.primary
                    : Colors.grey.shade300,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: _currentMode == 'practice'
                      ? AppColors.primary
                      : Colors.grey.shade400,
                  width: 2,
                ),
              ),
              child: Text(
                'מצב תרגול',
                style: TextStyle(
                  color: _currentMode == 'practice'
                      ? Colors.white
                      : Colors.black54,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // Test Mode Button (Locked)
          GestureDetector(
            onTap: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('מצב מבחן'),
                  content: const Text('מצב מבחן בפיתוח כעת ויהיה זמין בקרוב.'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('סגור'),
                    ),
                  ],
                ),
              );
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.grey.shade200,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: Colors.grey.shade400, width: 2),
              ),
              child: const Row(
                children: [
                  Icon(Icons.lock, size: 18, color: Colors.grey),
                  SizedBox(width: 4),
                  Text(
                    'מצב מבחן',
                    style: TextStyle(
                      color: Colors.grey,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
  // === END MODE SELECTOR ===

  // === ASSISTANCE BUTTONS HANDLER ===
  void _handleAssistButton(String type) {
    if (_lastTaskText == null || _lastTaskText!.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('אנא כתוב שאלה או העלה משימה לפני השימוש בעזרה')),
      );
      return;
    }
    
    // Create the instruction prompt for the AI but don't show it in chat
    String instructionPrompt;
    switch (type) {
      case 'breakdown':
        instructionPrompt = 'Break down the following task into step-by-step instructions in simple language: ${_lastTaskText!}';
        break;
      case 'example':
        instructionPrompt = 'Give a concrete worked example that shows how to solve: ${_lastTaskText!}';
        break;
      case 'explain':
        instructionPrompt = 'Explain the following task in simple words so that a student can understand: ${_lastTaskText!}';
        break;
      default:
        instructionPrompt = _lastTaskText!;
    }
    
    // Send the instruction prompt to AI but don't add it as a visible message
    _processAssistanceRequest(instructionPrompt, type);
  }
  
  Future<void> _processAssistanceRequest(String instructionPrompt, String assistanceType) async {
    if (_currentSessionId == null) {
      _addBotMessage('⚠️ שגיאה: אין חיבור לשרת');
      return;
    }

    setState(() {
      _isBotTyping = true;
      _currentTypingMessageIndex = 0; // Start with "מעבד את השאלה..."
      _messages.add(ChatMessage(
        id: 'typing',
        content: '...',
        timestamp: DateTime.now(),
        sender: SenderType.bot,
        type: MessageType.systemMessage,
      ));
    });
    _scrollToBottom();

    // Start timer to switch to "חושב..." after 3 seconds
    _typingMessageTimer?.cancel();
    _typingMessageTimer = Timer(const Duration(seconds: 3), () {
      if (mounted && _isBotTyping) {
        setState(() {
          _currentTypingMessageIndex = 1; // Switch to "חושב..."
        });
      }
    });

    try {
      final response = await ChatServiceBackend.sendMessage(
        sessionId: _currentSessionId!,
        content: instructionPrompt, // Send the full instruction prompt to AI
        assistanceType: assistanceType, // Also specify the assistance type
        provider: _selectedModel,
      );

      _typingMessageTimer?.cancel(); // Cancel timer when response arrives
      setState(() {
        _messages.removeWhere((m) => m.id == 'typing');
        _addBotMessage(response['content'] ?? 'תשובה לא זמינה');
        _isBotTyping = false;
      });
    } catch (e) {
      _typingMessageTimer?.cancel(); // Cancel timer on error
      setState(() {
        _messages.removeWhere((m) => m.id == 'typing');
        _addBotMessage('⚠️ שגיאה: $e');
        _isBotTyping = false;
      });
    }
  }
  // === END ASSISTANCE BUTTONS HANDLER ===

  @override
  Widget build(BuildContext context) {
    return PopScope(
      onPopInvoked: (didPop) {
        if (didPop && _currentSessionId != null) {
          ChatServiceBackend.cancelRequest(_currentSessionId!);
        }
      },
      child: Scaffold(
      appBar: AppBar(
        title: const Text('שיחה עם לרנובוט'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              setState(() {
                _showModelSelector = !_showModelSelector;
              });
            },
            tooltip: 'בחר מודל AI',
          ),
          if (_selectedModel != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    _getSelectedModelDisplayName(),
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: AppColors.primary,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
      body: Stack(
        children: [
          Column(
            children: [
              _buildModeSelector(),
              Container(
            height: 80,
            width: double.infinity,
            color: AppColors.skyBackground,
            child: Stack(
              children: [
                Positioned(
                  left: 20,
                  top: 10,
                  child: _buildCloud(70),
                ),
                Positioned(
                  right: 40,
                  top: 5,
                  child: _buildCloud(90),
                ),
                Positioned(
                  left: 130,
                  top: 30,
                  child: _buildCloud(60),
                ),
                Center(
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 20, vertical: 5),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.8),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      _currentMode == 'practice'
                          ? AppStrings.practiceMode
                          : AppStrings.testMode,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    AppColors.skyBackground,
                    AppColors.background,
                  ],
                ),
              ),
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.all(15),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final message = _messages[index];

                  // Typing indicator
                  if (message.type == MessageType.systemMessage &&
                      message.content == '...') {
                    return Align(
                      alignment: Alignment.centerRight,
                      child: Padding(
                        padding: const EdgeInsets.only(right: 15, bottom: 15),
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.botBubble,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              SizedBox(
                                width: 80,
                                height: 20,
                                child: _buildAnimatedTypingIndicator(),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _typingMessages[_currentTypingMessageIndex % _typingMessages.length],
                                style: TextStyle(
                                  fontSize: 12,
                                  color: AppColors.primary.withOpacity(0.8),
                                  fontWeight: FontWeight.w500,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }

                  // Task capture (with image)
                  if (message.type == MessageType.taskCapture) {
                    return Align(
                      alignment: Alignment.centerLeft,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ChatBubble(
                            message: message,
                            showAvatar: index == 0 ||
                                _messages[index - 1].sender != message.sender,
                            onSpeakPressed: _speakText,
                            studentProfileImageUrl: _profileImageUrl,
                          ),
                          if (_capturedImage != null) ...[
                            const SizedBox(height: 5),
                            Container(
                              margin: const EdgeInsets.only(left: 50),
                              height: 100,
                              width: 150,
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: AppColors.primary),
                                image: DecorationImage(
                                  image: FileImage(_capturedImage!),
                                  fit: BoxFit.cover,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    );
                  }

                  // Default: chat bubble + satisfaction logic
                  return Column(
                    crossAxisAlignment: message.sender == SenderType.bot
                        ? CrossAxisAlignment.start
                        : CrossAxisAlignment.end,
                    children: [
                      ChatBubble(
                        message: message,
                        showAvatar: index == 0 ||
                            _messages[index - 1].sender != message.sender,
                        onSpeakPressed: _speakText,
                        studentProfileImageUrl: _profileImageUrl,
                      ),
                      if (message.sender == SenderType.bot &&
                          (message.metadata == null ||
                              !message.metadata!.containsKey('satisfaction')))
                        _buildSatisfactionBar(message, index),
                      if (message.sender == SenderType.bot &&
                          (message.metadata?['satisfaction'] != null))
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Text('דירוג: ', style: TextStyle(fontSize: 14)),
                            ...List.generate(
                              5,
                              (i) => Icon(
                                Icons.star,
                                color: i <
                                        (message.metadata!['satisfaction']
                                            as int)
                                    ? Colors.amber
                                    : Colors.grey[400],
                                size: 20,
                              ),
                            ),
                          ],
                        ),
                    ],
                  );
                },
              ),
            ),
          ),
          if ((_lastTaskText != null && _lastTaskText!.trim().isNotEmpty) &&
              _currentMode == 'practice')
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              color: Colors.white,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildAssistanceButton(
                    'פירוק לשלבים',
                    Icons.format_list_numbered,
                    () => _handleAssistButton('breakdown'),
                  ),
                  _buildAssistanceButton(
                    'הדגמה',
                    Icons.play_circle_outline,
                    () => _handleAssistButton('example'),
                  ),
                  _buildAssistanceButton(
                    'הסבר',
                    Icons.lightbulb_outline,
                    () => _handleAssistButton('explain'),
                  ),
                ],
              ),
            ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            color: Colors.white,
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.keyboard_arrow_left),
                  onPressed: () {},
                  color: AppColors.primary,
                ),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 15),
                    decoration: BoxDecoration(
                      color: AppColors.background,
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: TextField(
                      controller: _messageController,
                      textDirection: TextDirection.rtl,
                      decoration: const InputDecoration(
                        hintText: AppStrings.enterQuestion,
                        hintTextDirection: TextDirection.rtl,
                        border: InputBorder.none,
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _isBotTyping ? null : _sendMessage,
                  color: AppColors.primary,
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 5),
            color: AppColors.primary,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: Icon(
                    _isListening ? Icons.mic_off : Icons.mic,
                    color: _isListening ? Colors.red : Colors.white,
                  ),
                  onPressed: _handleVoiceInput,
                  tooltip: _isListening ? 'עצור הקלטה' : 'הקלט קול',
                ),
                IconButton(
                  icon: const Icon(
                    Icons.camera_alt,
                    color: Colors.white,
                  ),
                  onPressed: _captureTask,
                ),
                IconButton(
                  icon: const Icon(
                    Icons.school,
                    color: Colors.white,
                  ),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('הודעה נשלחה למורה'),
                        duration: Duration(seconds: 2),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
            ],
          ),
          // Model selector overlay
          if (_showModelSelector)
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: Center(
                  child: _buildModelSelector(),
                ),
              ),
            ),
        ],
      ),
      ), // PopScope child
    );
  }

  Widget _buildCloud(double size) {
    return Container(
      width: size,
      height: size * 0.6,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.7),
        borderRadius: BorderRadius.circular(size / 2),
      ),
    );
  }

  Widget _buildAssistanceButton(
      String label, IconData icon, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.primaryLight.withOpacity(0.2),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: AppColors.primary,
              size: 20,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.primary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnimatedTypingIndicator() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        for (int i = 0; i < 3; i++)
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 3),
            child: TweenAnimationBuilder<double>(
              key: ValueKey('typing_${_typingAnimationKey}_$i'),
              duration: const Duration(milliseconds: 600),
              tween: Tween(begin: 0.0, end: 1.0),
              builder: (context, value, child) {
                // Create a wave that moves left to right, then right to left
                final wavePosition = math.sin(value * 2 * math.pi);
                final dotPosition = (i / 2.0) - 1.0; // -1, -0.5, 0 for dots 0,1,2
                final distance = (wavePosition - dotPosition).abs();
                
                // Closer to wave = more active (bigger and more opaque)
                final activity = math.max(0.0, 1.0 - distance * 2.0);
                final scale = 0.6 + 0.4 * activity;
                final opacity = 0.3 + 0.7 * activity;
                
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 100),
                  child: Transform.scale(
                    scale: scale,
                    child: Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(opacity),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                );
              },
              onEnd: () {
                // Continuously restart animation while typing (dots only, not text)
                if (_isBotTyping && mounted) {
                  Future.delayed(const Duration(milliseconds: 100), () {
                    if (_isBotTyping && mounted) {
                      setState(() {
                        _typingAnimationKey++;
                        // Don't cycle through messages - timer handles that
                      });
                    }
                  });
                }
              },
            ),
          ),
      ],
    );
  }
}
