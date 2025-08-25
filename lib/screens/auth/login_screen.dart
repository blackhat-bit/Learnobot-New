import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../services/auth_service.dart';
import '../teacher/teacher_panel_screen.dart';
import '../student/student_home_screen.dart';
import 'package:provider/provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => LoginScreenState();
}

class LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isTeacher = true; // Default to teacher login
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        final authService = Provider.of<AuthService>(context, listen: false);
        final username = await authService.loginAndCheckRole(
          email: _emailController.text.trim(),
          password: _passwordController.text,
          role: _isTeacher ? 'Teacher' : 'Student',
        );

        if (username != null) {
          // Navigate to the appropriate screen based on user type
          if (_isTeacher) {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(
                builder: (context) => const TeacherPanelScreen(),
              ),
            );
          } else {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(
                builder: (context) => const StudentHomeScreen(),
              ),
            );
          }
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('שם משתמש או סיסמה שגויים'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } catch (e) {
        // Handle login errors - show user-friendly message instead of Firebase error
        String errorMessage = 'שם משתמש או סיסמה שגויים';
        
        // Check for specific Firebase errors and provide appropriate messages
        if (e.toString().contains('user-not-found') || e.toString().contains('wrong-password')) {
          errorMessage = 'שם משתמש או סיסמה שגויים';
        } else if (e.toString().contains('too-many-requests')) {
          errorMessage = 'יותר מדי ניסיונות התחברות. נסה שוב מאוחר יותר';
        } else if (e.toString().contains('network-request-failed')) {
          errorMessage = 'בעיית חיבור לאינטרנט. בדוק את החיבור שלך';
        } else if (e.toString().contains('invalid-email')) {
          errorMessage = 'כתובת אימייל לא תקינה';
        }
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
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
        title: const Text('כניסה'),
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
                        Icons.school,
                        size: 50,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // User type selector
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Teacher Button
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
                        // Student Button
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

                    // Email Field
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(
                        labelText: 'אימייל',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.email),
                      ),
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'אנא הכנס אימייל';
                        }
                        if (!value.contains('@')) {
                          return 'אימייל לא תקין';
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
                          return 'הסיסמה חייבת להיות לפחות 6 תווים';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 25),

                    // Login Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _login,
                        child: _isLoading
                            ? const CircularProgressIndicator(
                                color: Colors.white)
                            : const Text(
                                AppStrings.loginButtonText,
                                style: TextStyle(fontSize: 16),
                              ),
                      ),
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
