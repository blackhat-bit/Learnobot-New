// lib/screens/teacher/account_settings_screen.dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';
import '../../services/auth_service_backend.dart';
import '../../services/upload_service.dart';

class AccountSettingsScreen extends StatefulWidget {
  const AccountSettingsScreen({Key? key}) : super(key: key);

  @override
  State<AccountSettingsScreen> createState() => _AccountSettingsScreenState();
}

class _AccountSettingsScreenState extends State<AccountSettingsScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  bool _isEditing = false;
  bool _isLoading = true;
  bool _notificationsEnabled = true;
  bool _darkModeEnabled = false;
  Map<String, dynamic>? _userData;
  String? _profileImageUrl;
  final ImagePicker _picker = ImagePicker();
  
  @override
  void initState() {
    super.initState();
    _loadUserData();
    _loadProfilePicture();
  }
  
  Future<void> _loadUserData() async {
    setState(() => _isLoading = true);
    
    try {
      final user = await AuthServiceBackend.getStoredUser();
      if (user != null && mounted) {
        setState(() {
          _userData = user;
          _nameController.text = user['full_name'] ?? user['username'] ?? '';
          _emailController.text = user['email'] ?? '';
        });
      }
    } catch (e) {
      print('Error loading user data: $e');
    } finally {
      setState(() => _isLoading = false);
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
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(AppStrings.accountSettings),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(_isEditing ? Icons.close : Icons.edit),
            onPressed: () {
              setState(() {
                if (_isEditing) {
                  // Cancel editing - restore original values
                  _nameController.text = _userData?['full_name'] ?? _userData?['username'] ?? '';
                  _emailController.text = _userData?['email'] ?? '';
                }
                _isEditing = !_isEditing;
              });
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Profile Picture Section
              Center(
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 50,
                      backgroundColor: AppColors.primary,
                      backgroundImage: _profileImageUrl != null 
                          ? NetworkImage(_profileImageUrl!)
                          : null,
                      child: _profileImageUrl == null
                          ? const Icon(
                              Icons.person,
                              size: 60,
                              color: Colors.white,
                            )
                          : null,
                    ),
                    if (_isEditing) ...[
                      const SizedBox(height: 10),
                      TextButton.icon(
                        onPressed: () => _showProfilePictureOptions(),
                        icon: const Icon(Icons.camera_alt),
                        label: const Text('החלף תמונה'),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 30),
              
              // Personal Info Section
              const Text(
                'פרטים אישיים',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 15),
              
              // Name Field
              TextFormField(
                controller: _nameController,
                textDirection: TextDirection.rtl,
                readOnly: !_isEditing,
                decoration: InputDecoration(
                  labelText: 'שם מלא',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  prefixIcon: const Icon(Icons.person),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'נא להזין שם מלא';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 15),
              
              // Email Field
              TextFormField(
                controller: _emailController,
                textDirection: TextDirection.ltr,
                readOnly: !_isEditing,
                decoration: InputDecoration(
                  labelText: 'דואר אלקטרוני',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  prefixIcon: const Icon(Icons.email),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'נא להזין דואר אלקטרוני';
                  }
                  if (!value.contains('@')) {
                    return 'נא להזין כתובת דואר אלקטרוני תקינה';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 30),
              
              // Password Change Section
              if (_isEditing) ...[
                const Text(
                  'שינוי סיסמה',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 15),
                
                // Current Password Field
                TextFormField(
                  controller: _currentPasswordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'סיסמה נוכחית',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    prefixIcon: const Icon(Icons.lock),
                  ),
                  validator: (value) {
                    if (_newPasswordController.text.isNotEmpty && 
                        (value == null || value.isEmpty)) {
                      return 'נא להזין סיסמה נוכחית';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 15),
                
                // New Password Field
                TextFormField(
                  controller: _newPasswordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'סיסמה חדשה',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    prefixIcon: const Icon(Icons.lock_outline),
                  ),
                  validator: (value) {
                    if (value != null && value.isNotEmpty && value.length < 6) {
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
                  decoration: InputDecoration(
                    labelText: 'אימות סיסמה חדשה',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    prefixIcon: const Icon(Icons.lock_outline),
                  ),
                  validator: (value) {
                    if (_newPasswordController.text.isNotEmpty && 
                        value != _newPasswordController.text) {
                      return 'הסיסמאות אינן תואמות';
                    }
                    return null;
                  },
                ),
              ],
              const SizedBox(height: 30),
              
              // App Settings Section
              const Text(
                'הגדרות אפליקציה',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 15),
              
              // Notification Settings
              _buildSettingItem(
                'התראות',
                'קבלת התראות מתלמידים',
                Icons.notifications,
                _notificationsEnabled,
              ),
              
              // Dark Mode
              _buildSettingItem(
                'מצב כהה',
                'שינוי ערכת הצבעים של האפליקציה',
                Icons.dark_mode,
                _darkModeEnabled,
              ),
              
              // Language Settings
              _buildSettingItem(
                'שפה',
                'עברית',
                Icons.language,
                null,
                onTap: () {
                  // Show language selection dialog
                  _showLanguageDialog(context);
                },
              ),
              
              const SizedBox(height: 20),
              
              // Save Button (only when editing)
              if (_isEditing)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      if (_formKey.currentState!.validate()) {
                        // Save changes
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('הפרטים נשמרו בהצלחה'),
                            backgroundColor: AppColors.success,
                          ),
                        );
                        setState(() {
                          _isEditing = false;
                        });
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 15),
                    ),
                    child: const Text(
                      'שמור שינויים',
                      style: TextStyle(fontSize: 16),
                    ),
                  ),
                ),
              
              const SizedBox(height: 20),
              
              // Logout Button
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () {
                    // Show logout confirmation
                    _showLogoutDialog(context);
                  },
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 15),
                    side: const BorderSide(color: Colors.red),
                  ),
                  child: const Text(
                    'התנתק',
                    style: TextStyle(
                      color: Colors.red,
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildSettingItem(
    String title,
    String subtitle,
    IconData icon,
    bool? switchValue, {
    VoidCallback? onTap,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Row(
            children: [
              Icon(
                icon,
                color: AppColors.primary,
                size: 28,
              ),
              const SizedBox(width: 15),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.textLight,
                      ),
                    ),
                  ],
                ),
              ),
              if (switchValue != null)
                Switch(
                  value: switchValue,
                  onChanged: (value) {
                    setState(() {
                      if (title == 'התראות') {
                        _notificationsEnabled = value;
                      } else if (title == 'מצב כהה') {
                        _darkModeEnabled = value;
                      }
                    });
                  },
                  activeColor: AppColors.primary,
                )
              else
                const Icon(
                  Icons.arrow_forward_ios,
                  size: 16,
                  color: AppColors.textLight,
                ),
            ],
          ),
        ),
      ),
    );
  }
  
  void _showLanguageDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text(
          'בחר שפה',
          textAlign: TextAlign.center,
        ),
        children: [
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
            },
            child: const Text(
              'עברית',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
          ),
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              // Would change language in a real app
            },
            child: const Text(
              'English',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
          ),
          SimpleDialogOption(
            onPressed: () {
              Navigator.pop(context);
              // Would change language in a real app
            },
            child: const Text(
              'العربية',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
    );
  }
  
  void _showProfilePictureOptions() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('מצלמה'),
              onTap: () {
                Navigator.pop(context);
                _pickImageFromCamera();
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('גלריה'),
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
          ],
        ),
      ),
    );
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
      print('Error picking image from camera: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('שגיאה בפתיחת המצלמה'),
            backgroundColor: Colors.red,
          ),
        );
      }
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
      print('Error picking image from gallery: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('שגיאה בבחירת תמונה'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _uploadProfilePicture(File imageFile) async {
    setState(() => _isLoading = true);
    
    try {
      final result = await UploadService.uploadProfilePicture(
        imageFile: imageFile,
      );
      
      if (mounted) {
        setState(() {
          _profileImageUrl = UploadService.getImageUrl(result['image_url']);
          _isLoading = false;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('תמונת הפרופיל עודכנה בהצלחה'),
            backgroundColor: AppColors.success,
          ),
        );
      }
    } catch (e) {
      print('Error uploading profile picture: $e');
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('שגיאה בהעלאת תמונת הפרופיל'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _removeProfilePicture() async {
    setState(() => _isLoading = true);
    
    try {
      await UploadService.deleteProfilePicture();
      
      if (mounted) {
        setState(() {
          _profileImageUrl = null;
          _isLoading = false;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('תמונת הפרופיל הוסרה בהצלחה'),
            backgroundColor: AppColors.success,
          ),
        );
      }
    } catch (e) {
      print('Error removing profile picture: $e');
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('שגיאה בהסרת תמונת הפרופיל'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _showLogoutDialog(BuildContext context) {
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
            onPressed: () {
              Navigator.pop(context);
              // Navigate to login screen
              Navigator.of(context).popUntil((route) => route.isFirst);
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
}