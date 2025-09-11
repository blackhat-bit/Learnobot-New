import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../services/auth_service_backend.dart';
import 'login_screen.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({Key? key}) : super(key: key);

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  // Student-specific fields
  final _gradeController = TextEditingController();
  String? _selectedTeacherUsername;
  
  // Teacher-specific fields
  final _schoolController = TextEditingController();
  
  bool _isTeacher = true; // Default to teacher registration
  bool _isLoading = false;
  List<Map<String, dynamic>> _availableTeachers = [];

  @override
  void initState() {
    super.initState();
    _loadAvailableTeachers();
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _fullNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _gradeController.dispose();
    _schoolController.dispose();
    super.dispose();
  }

  Future<void> _loadAvailableTeachers() async {
    try {
      final teachers = await AuthServiceBackend.getAvailableTeachers();
      setState(() {
        _availableTeachers = teachers;
      });
    } catch (e) {
      print('Error loading teachers: $e');
      // Continue without teachers - user can still register
    }
  }

  Future<void> _register() async {
    if (_formKey.currentState!.validate()) {
      if (_passwordController.text != _confirmPasswordController.text) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('הסיסמאות אינן תואמות'),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }

      setState(() {
        _isLoading = true;
      });

      try {
        // Use backend registration service
        final result = await AuthServiceBackend.register(
          email: _emailController.text.trim(),
          password: _passwordController.text,
          username: _usernameController.text.trim(),
          fullName: _fullNameController.text.trim(),
          role: _isTeacher ? 'teacher' : 'student',
          // Student-specific fields
          grade: _isTeacher ? null : _gradeController.text.trim(),
          difficultyLevel: _isTeacher ? null : 3, // Default difficulty level, will be set by teacher later
          difficultiesDescription: _isTeacher ? null : '', // Empty - will be set by teacher later
          teacherUsername: _isTeacher ? null : _selectedTeacherUsername,
          // Teacher-specific fields
          school: _isTeacher ? _schoolController.text.trim() : null,
        );

        if (!mounted) return;

        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('ההרשמה הושלמה בהצלחה! ניתן להתחבר כעת'),
              backgroundColor: Colors.green,
            ),
          );

          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => const LoginScreen(),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('שגיאה בהרשמה'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } catch (e) {
        if (!mounted) return;

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('שגיאת הרשמה: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(AppStrings.registerButtonText),
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Card(
            elevation: 5,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Logo or Icon
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(
                        Icons.app_registration,
                        size: 50,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 20),

                    const Text(
                      'יצירת חשבון חדש',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 20),

                    // User type selector
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () {
                              setState(() {
                                _isTeacher = true;
                              });
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _isTeacher
                                  ? AppColors.primary
                                  : Colors.grey.shade300,
                              foregroundColor:
                                  _isTeacher ? Colors.white : Colors.black,
                            ),
                            child: const Text(AppStrings.teacherLogin),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () {
                              setState(() {
                                _isTeacher = false;
                              });
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: !_isTeacher
                                  ? AppColors.primary
                                  : Colors.grey.shade300,
                              foregroundColor:
                                  !_isTeacher ? Colors.white : Colors.black,
                            ),
                            child: const Text(AppStrings.studentLogin),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Username Field
                    TextFormField(
                      controller: _usernameController,
                      decoration: const InputDecoration(
                        labelText: AppStrings.enterUsername,
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.person),
                      ),
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'אנא הכנס שם משתמש';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 15),

                    // Full Name Field (REQUIRED)
                    TextFormField(
                      controller: _fullNameController,
                      decoration: const InputDecoration(
                        labelText: 'שם מלא',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.account_circle),
                      ),
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'אנא הכנס שם מלא';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 15),

                    // Email Field
                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'דואר אלקטרוני',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.email),
                      ),
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'אנא הכנס דואר אלקטרוני';
                        }
                        if (!value.contains('@')) {
                          return 'אנא הכנס כתובת דואר אלקטרוני תקינה';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 15),

                    // Password Field
                    TextFormField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: AppStrings.enterPassword,
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.lock),
                      ),
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'אנא הכנס סיסמה';
                        }
                        if (value.length < 6) {
                          return 'הסיסמה חייבת להכיל לפחות 6 תווים';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 15),

                    // Confirm Password Field
                    TextFormField(
                      controller: _confirmPasswordController,
                      obscureText: true,
                      decoration: const InputDecoration(
                        labelText: 'אימות סיסמה',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.lock_outline),
                      ),
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'אנא אמת את הסיסמה';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 25),

                    // Role-specific fields
                    if (!_isTeacher) ...[
                      // Student-specific fields
                      TextFormField(
                        controller: _gradeController,
                        decoration: const InputDecoration(
                          labelText: 'כיתה',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.school),
                        ),
                        textAlign: TextAlign.right,
                        textDirection: TextDirection.rtl,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'אנא הכנס כיתה';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 15),
                      
                      // Teacher Selection Dropdown
                      DropdownButtonFormField<String>(
                        value: _selectedTeacherUsername,
                        decoration: const InputDecoration(
                          labelText: 'בחר מורה',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.person_outline),
                        ),
                        hint: const Text('בחר מורה (אופציונלי)'),
                        items: _availableTeachers.map((teacher) {
                          return DropdownMenuItem<String>(
                            value: teacher['username'],
                            child: Text(
                              '${teacher['full_name']} (${teacher['username']})',
                              textDirection: TextDirection.rtl,
                            ),
                          );
                        }).toList(),
                        onChanged: (String? newValue) {
                          setState(() {
                            _selectedTeacherUsername = newValue;
                          });
                        },
                        validator: (value) {
                          // Teacher selection is optional for students
                          return null;
                        },
                      ),
                      const SizedBox(height: 15),
                    ],
                    
                    if (_isTeacher) ...[
                      // Teacher-specific fields
                      TextFormField(
                        controller: _schoolController,
                        decoration: const InputDecoration(
                          labelText: 'בית ספר',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.location_city),
                        ),
                        textAlign: TextAlign.right,
                        textDirection: TextDirection.rtl,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'אנא הכנס שם בית ספר';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 15),
                    ],

                    // Register Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _register,
                        child: _isLoading
                            ? const CircularProgressIndicator(
                                color: Colors.white)
                            : const Text(
                                AppStrings.registerButtonText,
                                style: TextStyle(fontSize: 16),
                              ),
                      ),
                    ),
                    const SizedBox(height: 15),

                    // Login Link
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text('כבר יש לך חשבון?'),
                        TextButton(
                          onPressed: () {
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const LoginScreen(),
                              ),
                            );
                          },
                          child: const Text(AppStrings.loginButtonText),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
