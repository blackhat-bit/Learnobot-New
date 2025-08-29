import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../services/auth_service_backend.dart';
import '../teacher/teacher_panel_screen.dart';
import '../student/student_home_screen.dart';
import '../manager/ai_manager_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => LoginScreenState();
}

class LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
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
        // Use backend authentication
        final loginResult = await AuthServiceBackend.login(
          username: _emailController.text.trim(), // Can be username or email
          password: _passwordController.text,
        );

        if (loginResult['success'] == true) {
          final user = loginResult['user'];
          final userRole = user['role'] as String;
          
          // Navigate based on actual user role
          switch (userRole) {
            case 'student':
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => const StudentHomeScreen(),
                ),
              );
              break;
            case 'teacher':
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => const TeacherPanelScreen(),
                ),
              );
              break;
            case 'admin':
              // Admin goes to AI Manager screen
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => AIManagerScreen(),
                ),
              );
              break;
            default:
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('סוג משתמש לא מזוהה'),
                  backgroundColor: Colors.red,
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
        // Handle login errors - show user-friendly message
        String errorMessage = 'שם משתמש או סיסמה שגויים';
        
        // Check for specific local authentication errors
        if (e.toString().contains('User already exists')) {
          errorMessage = 'המשתמש כבר קיים';
        } else if (e.toString().contains('Invalid credentials')) {
          errorMessage = 'שם משתמש או סיסמה שגויים';
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

                    // Welcome text
                    const Text(
                      'ברוכים הבאים למערכת הלמידה',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 30),

                    // Email Field
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(
                        labelText: 'שם משתמש או אימייל',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.person),
                      ),
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'אנא הכנס שם משתמש או אימייל';
                        }
                        // Accept both username and email formats
                        // Remove email validation since usernames are allowed
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
