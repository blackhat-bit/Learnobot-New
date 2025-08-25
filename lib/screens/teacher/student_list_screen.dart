// lib/screens/teacher/student_list_screen.dart
import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../models/student.dart';
import 'student_profile_screen.dart';

class StudentListScreen extends StatefulWidget {
  const StudentListScreen({Key? key}) : super(key: key);

  @override
  State<StudentListScreen> createState() => _StudentListScreenState();
}

class _StudentListScreenState extends State<StudentListScreen> {
  final TextEditingController _searchController = TextEditingController();
  List<Student> _students = [];
  List<Student> _filteredStudents = [];
  
  @override
  void initState() {
    super.initState();
    _loadStudents();
  }
  
  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
  
  void _loadStudents() {
    // Mock student data - in a real app, this would come from a database
    _students = [
      Student(
        id: '1',
        name: 'חן לוי',
        grade: '3\'ג',
        difficultyLevel: 3,
        description: 'מתקשה בקריאת הוראות ארוכות ובפירוק משימות מורכבות',
        profileImageUrl: '',
      ),
      Student(
        id: '2',
        name: 'הילה שושני',
        grade: '1\'ה',
        difficultyLevel: 2,
        description: 'קשיי קשב וריכוז, צריכה הסברים קצרים וברורים',
        profileImageUrl: '',
      ),
      Student(
        id: '3',
        name: 'רון שני',
        grade: '2\'ב',
        difficultyLevel: 4,
        description: 'קשיים בהבנת הוראות מילוליות, מעדיף הוראות חזותיות',
        profileImageUrl: '',
      ),
      Student(
        id: '4',
        name: 'נילי נעים',
        grade: '1\'ו',
        difficultyLevel: 1,
        description: 'צריכה חיזוקים חיוביים תכופים לשמירה על מוטיבציה',
        profileImageUrl: '',
      ),
      Student(
        id: '5',
        name: 'נועם אופלי',
        grade: '5\'ג',
        difficultyLevel: 5,
        description: 'קשיים משמעותיים בהבנת הוראות, נדרשת עזרה צמודה',
        profileImageUrl: '',
      ),
    ];
    
    // Sort by grade
    _students.sort((a, b) => a.grade.compareTo(b.grade));
    
    // Initialize filtered list
    _filteredStudents = List.from(_students);
  }
  
  void _filterStudents(String query) {
    setState(() {
      if (query.isEmpty) {
        _filteredStudents = List.from(_students);
      } else {
        _filteredStudents = _students
            .where((student) => student.name.contains(query) || 
                               student.grade.contains(query))
            .toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(AppStrings.studentList),
        centerTitle: true,
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.all(15),
            child: TextField(
              controller: _searchController,
              textDirection: TextDirection.rtl,
              decoration: InputDecoration(
                hintText: 'חיפוש תלמיד',
                hintTextDirection: TextDirection.rtl,
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
                filled: true,
                fillColor: Colors.white,
              ),
              onChanged: _filterStudents,
            ),
          ),
          
          // Section Title
          Container(
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 5),
            alignment: Alignment.centerRight,
            child: const Text(
              'רשימת תלמידים',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark,
              ),
              textAlign: TextAlign.right,
            ),
          ),
          
          // Student List
          Expanded(
            child: _filteredStudents.isEmpty
                ? const Center(
                    child: Text(
                      'לא נמצאו תלמידים',
                      style: TextStyle(color: AppColors.textLight),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(10),
                    itemCount: _filteredStudents.length,
                    itemBuilder: (context, index) {
                      final student = _filteredStudents[index];
                      return _buildStudentCard(context, student);
                    },
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          _showAddStudentDialog(context);
        },
        backgroundColor: AppColors.primary,
        child: const Icon(Icons.add),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        color: AppColors.primary,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Back to Panel Button
            TextButton.icon(
              onPressed: () {
                Navigator.pop(context);
              },
              icon: const Icon(Icons.arrow_back, color: Colors.white),
              label: const Text(
                AppStrings.backToPanel,
                style: TextStyle(color: Colors.white),
              ),
            ),
            
            // Student Count
            Text(
              '${_filteredStudents.length} תלמידים',
              style: const TextStyle(color: Colors.white),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStudentCard(BuildContext context, Student student) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 5, vertical: 8),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
      ),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => StudentProfileScreen(student: student),
            ),
          );
        },
        borderRadius: BorderRadius.circular(15),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // Student Avatar
              CircleAvatar(
                radius: 25,
                backgroundColor: AppColors.primaryLight,
                child: Text(
                  student.name.substring(0, 1),
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 20,
                  ),
                ),
              ),
              const SizedBox(width: 15),
              
              // Student Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      student.name,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'כיתה: ${student.grade}',
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.textLight,
                      ),
                    ),
                  ],
                ),
              ),
              
              // Difficulty Level Indicator
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10, 
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: _getDifficultyColor(student.difficultyLevel),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  'רמת קושי: ${student.difficultyLevel}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Color _getDifficultyColor(int level) {
    switch (level) {
      case 1:
        return Colors.green;
      case 2:
        return Colors.lightGreen;
      case 3:
        return Colors.orange;
      case 4:
        return Colors.deepOrange;
      case 5:
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
  
  void _showAddStudentDialog(BuildContext context) {
    final TextEditingController nameController = TextEditingController();
    final TextEditingController gradeController = TextEditingController();
    final TextEditingController descriptionController = TextEditingController();
    int selectedDifficulty = 3;
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  AppStrings.createStudentProfile,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                
                // Name Field
                TextField(
                  controller: nameController,
                  textDirection: TextDirection.rtl,
                  decoration: const InputDecoration(
                    labelText: 'שם תלמיד',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 15, 
                      vertical: 10,
                    ),
                  ),
                ),
                const SizedBox(height: 15),
                
                // Grade Field
                TextField(
                  controller: gradeController,
                  textDirection: TextDirection.rtl,
                  decoration: const InputDecoration(
                    labelText: 'כיתה',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 15, 
                      vertical: 10,
                    ),
                  ),
                ),
                const SizedBox(height: 15),
                
                // Difficulty Level Selector
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'רמת קושי בהבנת הוראות:',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.right,
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: List.generate(
                        5,
                        (index) => InkWell(
                          onTap: () {
                            setState(() {
                              selectedDifficulty = index + 1;
                            });
                          },
                          borderRadius: BorderRadius.circular(4),
                          child: Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: selectedDifficulty == index + 1
                                  ? _getDifficultyColor(index + 1)
                                  : Colors.grey.shade200,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Center(
                              child: Text(
                                '${index + 1}',
                                style: TextStyle(
                                  color: selectedDifficulty == index + 1
                                      ? Colors.white
                                      : Colors.black,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 15),
                
                // Description Field
                TextField(
                  controller: descriptionController,
                  textDirection: TextDirection.rtl,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'תיאור קשיי התלמיד',
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 15, 
                      vertical: 10,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                
                // Action Buttons
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('ביטול'),
                    ),
                    ElevatedButton(
                      onPressed: () {
                        if (nameController.text.isEmpty || 
                            gradeController.text.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('נא להזין שם וכיתה'),
                            ),
                          );
                          return;
                        }
                        
                        final newStudent = Student(
                          id: DateTime.now().millisecondsSinceEpoch.toString(),
                          name: nameController.text,
                          grade: gradeController.text,
                          difficultyLevel: selectedDifficulty,
                          description: descriptionController.text,
                        );
                        
                        setState(() {
                          _students.add(newStudent);
                          _students.sort((a, b) => a.grade.compareTo(b.grade));
                          _filteredStudents = List.from(_students);
                        });
                        
                        Navigator.pop(context);
                      },
                      child: const Text('שמור'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}