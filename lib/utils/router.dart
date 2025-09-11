// lib/utils/router.dart
import 'package:flutter/material.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/registration_screen.dart';
import '../screens/auth/welcome_screen.dart';
import '../screens/teacher/teacher_panel_screen.dart';
import '../screens/teacher/student_list_screen.dart';
import '../screens/teacher/student_profile_screen.dart';
import '../screens/teacher/teacher_chat_screen.dart';
import '../screens/teacher/account_settings_screen.dart';
import '../screens/student/student_home_screen.dart';
import '../screens/student/student_chat_screen.dart';
import '../models/student.dart';

class AppRouter {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    // Extract route arguments if available
    final args = settings.arguments;

    switch (settings.name) {
      // Auth routes
      case '/':
        return MaterialPageRoute(builder: (_) => const WelcomeScreen());
      case '/login':
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      case '/register':
        return MaterialPageRoute(builder: (_) => const RegistrationScreen());
      
      // Teacher routes
      case '/teacher_panel':
        return MaterialPageRoute(builder: (_) => const TeacherPanelScreen());
      case '/student_list':
        return MaterialPageRoute(builder: (_) => const StudentListScreen());
      case '/account_settings':
        return MaterialPageRoute(builder: (_) => const AccountSettingsScreen());
      case '/student_profile':
        if (args is Student) {
          return MaterialPageRoute(
            builder: (_) => StudentProfileScreen(student: args),
          );
        }
        return _errorRoute();
      case '/teacher_chat':
        if (args is Student) {
          return MaterialPageRoute(
            builder: (_) => TeacherChatScreen(student: args),
          );
        }
        return _errorRoute();
      
      // Student routes
      case '/student_home':
        return MaterialPageRoute(builder: (_) => const StudentHomeScreen());
      case '/student_chat':
        if (args is String) {
          return MaterialPageRoute(
            builder: (_) => StudentChatScreen(initialMode: args),
          );
        }
        return MaterialPageRoute(
          builder: (_) => const StudentChatScreen(),
        );
      
      // Default - Error route
      default:
        return _errorRoute();
    }
  }

  static Route<dynamic> _errorRoute() {
    return MaterialPageRoute(builder: (_) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('שגיאה'),
        ),
        body: const Center(
          child: Text('דף לא נמצא'),
        ),
      );
    });
  }
}