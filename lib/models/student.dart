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
      id: map['id']?.toString() ?? '',
      name: map['full_name'] ?? map['name'] ?? '',
      grade: map['grade'] ?? '',
      difficultyLevel: map['difficulty_level'] ?? map['difficultyLevel'] ?? 3,
      description: map['difficulties_description'] ?? map['description'] ?? '',
      profileImageUrl: map['profile_image_url'] ?? map['profileImageUrl'] ?? '',
    );
  }
}