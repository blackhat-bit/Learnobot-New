// lib/screens/student/student_home_screen.dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../services/auth_service_backend.dart';
import '../../services/upload_service.dart';
import '../auth/welcome_screen.dart';
import 'student_chat_screen.dart';

class StudentHomeScreen extends StatefulWidget {
  const StudentHomeScreen({Key? key}) : super(key: key);

  @override
  State<StudentHomeScreen> createState() => _StudentHomeScreenState();
}

class _StudentHomeScreenState extends State<StudentHomeScreen> {
  String _username = 'תלמיד';
  String? _profileImageUrl;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadUsername();
    _loadProfilePicture();
  }

  Future<void> _loadUsername() async {
    try {
      final user = await AuthServiceBackend.getStoredUser();
      if (mounted && user != null) {
        setState(() {
          _username = user['full_name'] ?? user['username'] ?? 'תלמיד';
        });
      }
    } catch (e) {
      print('Error loading username: $e');
    }
  }

  Future<void> _loadProfilePicture() async {
    try {
      final profileInfo = await UploadService.getProfilePictureInfo();
      if (mounted && profileInfo['image_url'] != null) {
        setState(() {
          _profileImageUrl = UploadService.getImageUrl(profileInfo['image_url']);
        });
      }
    } catch (e) {
      print('Error loading profile picture: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
              color: AppColors.primary,
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => _showProfileOptions(context),
                    child: CircleAvatar(
                      backgroundColor: Colors.white,
                      radius: 25,
                      backgroundImage: _profileImageUrl != null 
                          ? NetworkImage(_profileImageUrl!)
                          : null,
                      child: _profileImageUrl == null
                          ? const Icon(
                              Icons.person,
                              color: AppColors.primary,
                              size: 30,
                            )
                          : null,
                    ),
                  ),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'מסך ראשי',
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        Text(
                          'שלום, $_username! מה ברצונך לשאול?',
                          style: const TextStyle(
                            fontSize: 16,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Logout button
                  IconButton(
                    onPressed: _showLogoutDialog,
                    icon: const Icon(
                      Icons.logout,
                      color: Colors.white,
                    ),
                    tooltip: 'התנתק',
                  ),
                ],
              ),
            ),

            // Main Content
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Colors.white, AppColors.background],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // LearnoBot Logo or Image
                      Container(
                        width: 160,
                        height: 160,
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.white, AppColors.primary.withOpacity(0.1)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(80),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.primary.withOpacity(0.2),
                              blurRadius: 20,
                              spreadRadius: 5,
                              offset: const Offset(0, 8),
                            ),
                          ],
                        ),
                        child: const Center(
                          child: Icon(
                            Icons.smart_toy,
                            size: 85,
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                      const SizedBox(height: 50),

                      // Buttons Row
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                        // Profile Update Button
                        ElevatedButton.icon(
                          onPressed: () {
                            _showUpdateProfileDialog(context);
                          },
                          icon: const Icon(Icons.edit),
                          label: const Text('עדכון פרטים'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 12,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),

                        // Start Conversation Button
                        ElevatedButton.icon(
                          onPressed: () {
                            _showModeSelectionDialog(context);
                          },
                          icon: const Icon(Icons.chat_bubble_outline),
                          label: const Text('התחל שיחה'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 12,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                      ],
                    ),
                    ],
                  ),
                ),
              ),
            ),

            // Bottom Encouragement Message
            Container(
              padding: const EdgeInsets.all(20),
              margin: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppColors.primary.withOpacity(0.1), AppColors.primary.withOpacity(0.05)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.primary.withOpacity(0.2), width: 1),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.1),
                    blurRadius: 10,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Column(
                children: [
                  const Icon(
                    Icons.star,
                    color: Colors.amber,
                    size: 28,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'כל נסיון מקדם אותך להצלחה, מאמין בך!',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showProfileOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.edit),
              title: const Text('עדכון פרטים'),
              onTap: () {
                Navigator.pop(context);
                _showUpdateProfileDialog(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('החלף תמונת פרופיל'),
              onTap: () {
                Navigator.pop(context);
                _showProfilePictureOptions(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.cancel),
              title: const Text('ביטול'),
              onTap: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
    );
  }

  void _showProfilePictureOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('צלם תמונה'),
              onTap: () {
                Navigator.pop(context);
                _pickImageFromCamera();
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('בחר מהגלריה'),
              onTap: () {
                Navigator.pop(context);
                _pickImageFromGallery();
              },
            ),
            if (_profileImageUrl != null)
              ListTile(
                leading: const Icon(Icons.delete, color: Colors.red),
                title: const Text('הסר תמונה', style: TextStyle(color: Colors.red)),
                onTap: () {
                  Navigator.pop(context);
                  _removeProfilePicture();
                },
              ),
            ListTile(
              leading: const Icon(Icons.cancel),
              title: const Text('ביטול'),
              onTap: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
    );
  }

  void _showUpdateProfileDialog(BuildContext context) {
    final TextEditingController nameController = TextEditingController();
    final TextEditingController emailController = TextEditingController();
    
    // Load current user data
    _loadCurrentUserData(nameController, emailController);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('עדכון פרטים אישיים'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                textDirection: TextDirection.rtl,
                decoration: const InputDecoration(
                  labelText: 'שם מלא',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.person),
                ),
              ),
              const SizedBox(height: 15),
              TextField(
                controller: emailController,
                textDirection: TextDirection.ltr,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'דואר אלקטרוני',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.email),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ביטול'),
          ),
          ElevatedButton(
            onPressed: () {
              _updateProfile(context, nameController.text, emailController.text);
            },
            child: const Text('שמור'),
          ),
        ],
      ),
    );
  }

  Future<void> _loadCurrentUserData(
      TextEditingController nameController, 
      TextEditingController emailController) async {
    try {
      final user = await AuthServiceBackend.getStoredUser();
      if (user != null) {
        nameController.text = user['full_name'] ?? '';
        emailController.text = user['email'] ?? '';
      }
    } catch (e) {
      print('Error loading user data: $e');
    }
  }

  void _updateProfile(BuildContext context, String name, String email) {
    if (name.isEmpty || email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('נא למלא את כל השדות'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    if (!email.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('נא להזין כתובת דואר אלקטרוני תקינה'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // TODO: Implement actual profile update API call
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('הפרטים עודכנו בהצלחה!'),
        backgroundColor: Colors.green,
      ),
    );
    
    // Reload username to reflect changes
    _loadUsername();
  }

  Future<void> _pickImageFromCamera() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 800,
        maxHeight: 800,
        imageQuality: 85,
      );
      
      if (image != null) {
        await _uploadProfilePicture(File(image.path));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('שגיאה בצילום התמונה: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _pickImageFromGallery() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 800,
        maxHeight: 800,
        imageQuality: 85,
      );
      
      if (image != null) {
        await _uploadProfilePicture(File(image.path));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('שגיאה בבחירת התמונה: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _uploadProfilePicture(File imageFile) async {
    try {
      // Show loading indicator
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => const Center(
          child: CircularProgressIndicator(),
        ),
      );

      final result = await UploadService.uploadProfilePicture(
        imageFile: imageFile,
      );

      // Close loading indicator
      Navigator.pop(context);

      if (result['image_url'] != null) {
        setState(() {
          _profileImageUrl = UploadService.getImageUrl(result['image_url']);
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('תמונת הפרופיל עודכנה בהצלחה!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      // Close loading indicator if still open
      Navigator.pop(context);
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('שגיאה בעדכון תמונת הפרופיל: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _removeProfilePicture() async {
    try {
      // Show confirmation dialog
      final bool? confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('הסרת תמונת פרופיל'),
          content: const Text('האם אתה בטוח שברצונך להסיר את תמונת הפרופיל?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('ביטול'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('הסר', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      );

      if (confirmed == true) {
        await UploadService.deleteProfilePicture();
        
        setState(() {
          _profileImageUrl = null;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('תמונת הפרופיל הוסרה בהצלחה'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('שגיאה בהסרת תמונת הפרופיל: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('התנתקות'),
        content: const Text('האם אתה בטוח שברצונך להתנתק?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ביטול'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await AuthServiceBackend.logout();
              // Navigate back to welcome screen
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const WelcomeScreen()),
                (route) => false,
              );
            },
            child: const Text(
              'התנתק',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }

  void _showModeSelectionDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'בחר מצב שיחה',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),

              // Practice Mode Button
              _buildModeButton(
                context,
                title: AppStrings.practiceMode,
                icon: Icons.school,
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const StudentChatScreen(
                        initialMode: 'practice',
                      ),
                    ),
                  );
                },
              ),

              const SizedBox(height: 15),

              // Test Mode Button (locked)
              _buildModeButton(
                context,
                title: AppStrings.testMode,
                icon: Icons.quiz,
                onTap: () {
                  // Just show dialog, do NOT navigate to chat
                  showDialog(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: const Text('מצב מבחן'),
                      content:
                          const Text('מצב מבחן בפיתוח כעת ויהיה זמין בקרוב.'),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('סגור'),
                        ),
                      ],
                    ),
                  );
                },
                isLocked: true,
              ),

              const SizedBox(height: 20),

              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: const Text('ביטול'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModeButton(
    BuildContext context, {
    required String title,
    required IconData icon,
    required VoidCallback onTap,
    bool isLocked = false,
  }) {
    return Material(
      color: isLocked
          ? Colors.grey.shade200
          : AppColors.primaryLight.withOpacity(0.2),
      borderRadius: BorderRadius.circular(15),
      child: InkWell(
        onTap: isLocked ? null : onTap,
        borderRadius: BorderRadius.circular(15),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 20),
          child: Row(
            children: [
              Icon(
                icon,
                color: isLocked ? Colors.grey : AppColors.primary,
                size: 28,
              ),
              const SizedBox(width: 15),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: isLocked ? Colors.grey : AppColors.textDark,
                  ),
                ),
              ),
              if (isLocked)
                const Icon(
                  Icons.lock,
                  color: Colors.grey,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
