// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'constants/app_colors.dart';
import 'screens/splash_screen.dart';
import 'services/auth_service.dart';
import 'services/chat_service.dart';
import 'services/database_service.dart';
import 'utils/router.dart';
import 'firebase_options.dart';

// Global SharedPreferences instance
late SharedPreferences prefs;

void main() async {
  // Ensure Flutter is initialized
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  // Load SharedPreferences
  prefs = await SharedPreferences.getInstance();

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Run the app with error zone handling
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Core services
        Provider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => ChatService()),
        ChangeNotifierProvider(create: (_) => DatabaseService()),
      ],
      child: MaterialApp(
        title: 'LearnoBot',
        debugShowCheckedModeBanner: false,

        // Localization setup
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [
          Locale('he', 'IL'), // Hebrew
          Locale('en', 'US'), // English
        ],
        locale: const Locale('he', 'IL'), // Default to Hebrew

        // Theme configuration
        theme: _buildTheme(),

        // Use onGenerateRoute for named routes with parameters
        onGenerateRoute: AppRouter.generateRoute,

        // Ensure RTL for Hebrew
        builder: (context, child) {
          // Apply RTL text direction
          return Directionality(
            textDirection: TextDirection.rtl,
            child: MediaQuery(
              // Apply font scaling
              data: MediaQuery.of(context)
                  .copyWith(textScaler: const TextScaler.linear(1.0)),
              child: child!,
            ),
          );
        },

        // Start with splash screen
        home: const SplashScreen(),
      ),
    );
  }

  // Build the app theme
  ThemeData _buildTheme() {
    return ThemeData(
      // Colors
      primaryColor: AppColors.primary,
      scaffoldBackgroundColor: AppColors.background,

      // Color scheme
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        primary: AppColors.primary,
        secondary: AppColors.primaryLight,
        background: AppColors.background,
      ),

      // Fonts
      fontFamily: 'Heebo', // Hebrew-friendly font

      // Text themes
      textTheme: const TextTheme(
        displayLarge:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.bold),
        displayMedium:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.bold),
        displaySmall:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.bold),
        headlineLarge:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.bold),
        headlineMedium:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.bold),
        headlineSmall:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600),
        titleLarge:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600),
        titleMedium:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w600),
        titleSmall:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w500),
        bodyLarge: TextStyle(color: AppColors.textDark),
        bodyMedium: TextStyle(color: AppColors.textDark),
        bodySmall: TextStyle(color: AppColors.textLight),
        labelLarge:
            TextStyle(color: AppColors.textDark, fontWeight: FontWeight.w500),
        labelMedium: TextStyle(color: AppColors.textDark),
        labelSmall: TextStyle(color: AppColors.textLight),
      ),

      // AppBar theme
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.primary,
        elevation: 0,
        centerTitle: true,
        iconTheme: IconThemeData(color: Colors.white),
        titleTextStyle: TextStyle(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),

      // Elevated Button theme
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
          padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 25),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      // Outlined Button theme
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary,
          side: const BorderSide(color: AppColors.primary),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
          padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 25),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      // Text Button theme
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primary,
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),

      // Input decoration theme
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        filled: true,
        fillColor: Colors.white,
        hintStyle: TextStyle(color: Colors.grey.shade400),
        prefixIconColor: AppColors.primary,
        suffixIconColor: AppColors.primary,
      ),

      // Card theme
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(15),
        ),
        color: Colors.white,
      ),

      // Progress indicator theme
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: AppColors.primary,
        circularTrackColor: AppColors.primaryLight.withOpacity(0.2),
      ),

      // Chip theme
      chipTheme: ChipThemeData(
        backgroundColor: Colors.grey.shade200,
        selectedColor: AppColors.primary,
        labelStyle: TextStyle(color: Colors.grey.shade800),
        secondaryLabelStyle: const TextStyle(color: Colors.white),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(15),
        ),
      ),

      // Divider theme
      dividerTheme: DividerThemeData(
        color: Colors.grey.shade300,
        thickness: 1,
        space: 24,
      ),

      // Dialog theme
      dialogTheme: DialogTheme(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        elevation: 5,
        backgroundColor: Colors.white,
        titleTextStyle: const TextStyle(
          fontSize: 18,
          color: AppColors.textDark,
          fontWeight: FontWeight.bold,
        ),
        contentTextStyle: TextStyle(
          fontSize: 14,
          color: Colors.grey.shade700,
        ),
      ),

      // Bottom sheet theme
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: Colors.white,
        modalBackgroundColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        modalElevation: 5,
      ),

      // Icon theme
      iconTheme: IconThemeData(
        color: Colors.grey.shade700,
        size: 24,
      ),
      primaryIconTheme: const IconThemeData(
        color: Colors.white,
        size: 24,
      ),

      // Bottom navigation bar theme
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: Colors.grey.shade600,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
        showUnselectedLabels: true,
      ),

      // Slider theme
      sliderTheme: SliderThemeData(
        activeTrackColor: AppColors.primary,
        inactiveTrackColor: AppColors.primaryLight.withOpacity(0.2),
        thumbColor: AppColors.primary,
        overlayColor: AppColors.primary.withOpacity(0.1),
        valueIndicatorColor: AppColors.primary,
        valueIndicatorTextStyle: const TextStyle(color: Colors.white),
      ),

      // Switch theme
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return AppColors.primary;
          }
          return Colors.grey.shade400;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return AppColors.primary.withOpacity(0.5);
          }
          return Colors.grey.shade300;
        }),
      ),

      // Material 3 support
      useMaterial3: true,
    );
  }
}

// Add a widget to ensure app is using the latest fonts and styles
class AppInit extends StatelessWidget {
  final Widget child;

  const AppInit({
    Key? key,
    required this.child,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Preload any resources or trigger any initialization here
    return child;
  }
}

// Helper class to store app-wide settings
class AppSettings {
  static bool get isFirstRun => prefs.getBool('firstRun') ?? true;

  static setFirstRunComplete() {
    prefs.setBool('firstRun', false);
  }

  static String get language => prefs.getString('language') ?? 'he';

  static setLanguage(String languageCode) {
    prefs.setString('language', languageCode);
  }

  static bool get darkModeEnabled => prefs.getBool('darkMode') ?? false;

  static setDarkMode(bool enabled) {
    prefs.setBool('darkMode', enabled);
  }

  static int get notificationBadgeCount =>
      prefs.getInt('notificationCount') ?? 0;

  static setNotificationBadgeCount(int count) {
    prefs.setInt('notificationCount', count);
  }

  static void incrementNotificationCount() {
    final currentCount = notificationBadgeCount;
    setNotificationBadgeCount(currentCount + 1);
  }

  static void resetNotificationCount() {
    setNotificationBadgeCount(0);
  }
}
