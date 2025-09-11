enum MessageType {
  text,
  image,
  taskCapture,
  systemMessage,
}

enum SenderType {
  bot,
  student,
  teacher,
}

class ChatMessage {
  final String id;
  final String content;
  final DateTime timestamp;
  final SenderType sender;
  final MessageType type;
  final Map<String, dynamic>? metadata; // For additional data like feedback rating
  
  ChatMessage({
    required this.id,
    required this.content,
    required this.timestamp,
    required this.sender,
    this.type = MessageType.text,
    this.metadata,
  });
  
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'content': content,
      'timestamp': timestamp.millisecondsSinceEpoch,
      'sender': sender.toString(),
      'type': type.toString(),
      'metadata': metadata,
    };
  }
  
  factory ChatMessage.fromMap(Map<String, dynamic> map) {
    return ChatMessage(
      id: map['id'],
      content: map['content'],
      timestamp: DateTime.fromMillisecondsSinceEpoch(map['timestamp']),
      sender: SenderType.values.firstWhere(
        (e) => e.toString() == map['sender'],
        orElse: () => SenderType.bot,
      ),
      type: MessageType.values.firstWhere(
        (e) => e.toString() == map['type'],
        orElse: () => MessageType.text,
      ),
      metadata: map['metadata'],
    );
  }
}