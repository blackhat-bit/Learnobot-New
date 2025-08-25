// lib/screens/student/student_chat_screen.dart
import 'package:flutter/material.dart';
import 'dart:io';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../models/chat_message.dart';
import '../../widgets/chat_bubble.dart';
import 'package:image_picker/image_picker.dart';
import '../../services/local_llm_service.dart';

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
  final _llm = LocalLlmService();
  bool _isBotTyping = false;

  // Track the latest user question/task (for assist buttons)
  String? _lastTaskText;

  // Track last satisfaction for adaptive logic
  int? _lastSatisfaction;

  @override
  void initState() {
    super.initState();
    _currentMode = widget.initialMode;
    _addBotMessage('היי! איך אני יכול לעזור לך היום?');
  }

  @override
  void dispose() {
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
    // Adapt next response based on last satisfaction
    String contextInstruction = '';
    if (_lastSatisfaction != null) {
      if (_lastSatisfaction! <= 2) {
        contextInstruction =
            'The previous answer was not helpful (user rated it low). Please try a different approach, use simpler or more engaging language.';
      } else if (_lastSatisfaction! >= 5) {
        contextInstruction =
            'The previous answer was rated highly. Continue responding in the same style as before.';
      }
      _lastSatisfaction = null; // Use only once!
    }
    final adaptedQuestion = contextInstruction.isNotEmpty
        ? '$contextInstruction\n$userMessage'
        : userMessage;

    setState(() {
      _isBotTyping = true;
      _messages.add(ChatMessage(
        id: 'typing',
        content: '...',
        timestamp: DateTime.now(),
        sender: SenderType.bot,
        type: MessageType.systemMessage,
      ));
    });
    _scrollToBottom();

    try {
      final reply = await _llm.ask(
        question: adaptedQuestion,
        examMode: _currentMode == 'test',
      );

      setState(() {
        _messages.removeWhere((m) => m.id == 'typing');
        _addBotMessage(reply);
        _isBotTyping = false;
      });
    } catch (e) {
      setState(() {
        _messages.removeWhere((m) => m.id == 'typing');
        _addBotMessage('⚠️ שגיאה: $e');
        _isBotTyping = false;
      });
    }
  }

  Future<void> _captureTask() async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? image = await picker.pickImage(source: ImageSource.camera);

      if (image != null) {
        setState(() {
          _capturedImage = File(image.path);
        });

        _addUserMessage(
          'תמונת משימה',
          type: MessageType.taskCapture,
        );

        Future.delayed(const Duration(seconds: 1), () {
          _addBotMessage('אני מעבד את המשימה שצילמת...');
          Future.delayed(const Duration(seconds: 2), () {
            // Simulate extracting text from the image (replace with real OCR later)
            const extractedText =
                'כתוב חיבור בנושא "לאהוב את הטבע שמסביבנו" בהיקף של 30-40 שורות. לאחר מכן ענה על שאלות הבנה הקשורות לנושא.';
            _lastTaskText = extractedText;
            _addBotMessage('זיהיתי את המשימה הבאה: \n\n$extractedText');
            Future.delayed(const Duration(seconds: 1), () {
              setState(() {
                _showAssistanceOptions = true;
              });
            });
          });
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בצילום המשימה: $e')),
      );
    }
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
    String prompt;
    switch (type) {
      case 'breakdown':
        prompt =
            'Break down the following task into step-by-step instructions in simple language: ${_lastTaskText!}';
        break;
      case 'demonstrate':
        prompt =
            'Give a concrete worked example that shows how to solve: ${_lastTaskText!}';
        break;
      case 'explain':
        prompt =
            'Explain the following task in simple words so that a student can understand: ${_lastTaskText!}';
        break;
      default:
        prompt = _lastTaskText!;
    }
    _addUserMessage(prompt);
    _processBotResponse(prompt);
  }
  // === END ASSISTANCE BUTTONS HANDLER ===

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('שיחה עם לרנובוט'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Column(
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
                      message.content == 'typing') {
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
                          child: const SizedBox(
                            width: 50,
                            child: Center(
                              child: Text('...'),
                            ),
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
                          ),
                          if (_capturedImage != null) ...[
                            const SizedBox(height: 5),
                            Container(
                              margin: const EdgeInsets.only(left: 50),
                              height: 150,
                              width: 200,
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
                    () => _handleAssistButton('demonstrate'),
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
                  icon: const Icon(
                    Icons.mic,
                    color: Colors.white,
                  ),
                  onPressed: () {
                    // Do nothing or implement voice later
                  },
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
}
