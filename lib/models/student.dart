class Student {
  final String id;
  final String name;
  final String grade;
  final int difficultyLevel; // From 1 to 5, how difficult it is for the student to understand instructions
  final String description;
  final String profileImageUrl;
  
  Student({
    required this.id,
    required this.name,
    required this.grade,
    required this.difficultyLevel,
    this.description = '',
    this.profileImageUrl = '',
  });
  
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'grade': grade,
      'difficultyLevel': difficultyLevel,
      'description': description,
      'profileImageUrl': profileImageUrl,
    };
  }
  
  factory Student.fromMap(Map<String, dynamic> map) {
    return Student(
      id: map['id'],
      name: map['name'],
      grade: map['grade'],
      difficultyLevel: map['difficultyLevel'],
      description: map['description'] ?? '',
      profileImageUrl: map['profileImageUrl'] ?? '',
    );
  }
}