// lib/screens/teacher/account_settings_screen.dart
import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../constants/app_strings.dart';

class AccountSettingsScreen extends StatefulWidget {
  const AccountSettingsScreen({Key? key}) : super(key: key);

  @override
  State<AccountSettingsScreen> createState() => _AccountSettingsScreenState();
}

class _AccountSettingsScreenState extends State<AccountSettingsScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController(text: 'המורה עדי');
  final _emailController = TextEditingController(text: 'adi.teacher@example.com');
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  bool _isEditing = false;
  
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
                  // Cancel editing
                  _nameController.text = 'המורה עדי';
                  _emailController.text = 'adi.teacher@example.com';
                }
                _isEditing = !_isEditing;
              });
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
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
                    const CircleAvatar(
                      radius: 50,
                      backgroundColor: AppColors.primary,
                      child: Icon(
                        Icons.person,
                        size: 60,
                        color: Colors.white,
                      ),
                    ),
                    if (_isEditing) ...[
                      const SizedBox(height: 10),
                      TextButton.icon(
                        onPressed: () {
                          // Implement profile picture change
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('שינוי תמונת פרופיל בפיתוח'),
                            ),
                          );
                        },
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
                true,
              ),
              
              // Dark Mode
              _buildSettingItem(
                'מצב כהה',
                'שינוי ערכת הצבעים של האפליקציה',
                Icons.dark_mode,
                false,
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
                    // Only allow changing when in edit mode
                    if (_isEditing) {
                      setState(() {
                        // This is just UI representation, would be connected to
                        // app state in a real app
                      });
                    }
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