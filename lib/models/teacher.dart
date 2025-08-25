// lib/models/teacher.dart
class Teacher {
  final String id;
  final String name;
  final String email;
  final String school;
  final String? profileImageUrl;
  
  Teacher({
    required this.id,
    required this.name,
    required this.email,
    required this.school,
    this.profileImageUrl,
  });
  
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'school': school,
      'profileImageUrl': profileImageUrl,
    };
  }
  
  factory Teacher.fromMap(Map<String, dynamic> map) {
    return Teacher(
      id: map['id'],
      name: map['name'],
      email: map['email'],
      school: map['school'],
      profileImageUrl: map['profileImageUrl'],
    );
  }
}