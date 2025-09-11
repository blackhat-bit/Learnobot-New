// lib/widgets/task_capture_widget.dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../constants/app_colors.dart';
import 'dart:io';

class TaskCaptureWidget extends StatefulWidget {
  final Function(File) onImageCaptured;
  
  const TaskCaptureWidget({
    Key? key,
    required this.onImageCaptured,
  }) : super(key: key);

  @override
  State<TaskCaptureWidget> createState() => _TaskCaptureWidgetState();
}

class _TaskCaptureWidgetState extends State<TaskCaptureWidget> {
  File? _imageFile;
  bool _isProcessing = false;
  
  Future<void> _captureImage() async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? image = await picker.pickImage(source: ImageSource.camera);
      
      if (image != null) {
        setState(() {
          _imageFile = File(image.path);
          _isProcessing = true;
        });
        
        // Simulate processing
        await Future.delayed(const Duration(seconds: 2));
        
        setState(() {
          _isProcessing = false;
        });
        
        // Send image back to parent
        widget.onImageCaptured(_imageFile!);
      }
    } catch (e) {
      setState(() {
        _isProcessing = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('שגיאה בצילום המשימה: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (_imageFile == null) ...[
          // Camera capture interface
          Container(
            width: double.infinity,
            height: 300,
            decoration: BoxDecoration(
              color: Colors.grey.shade200,
              borderRadius: BorderRadius.circular(15),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.camera_alt,
                  size: 60,
                  color: AppColors.primary,
                ),
                const SizedBox(height: 20),
                const Text(
                  'צלם את המשימה',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'וודא שהטקסט ברור וקריא',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 30),
                ElevatedButton.icon(
                  onPressed: _captureImage,
                  icon: const Icon(Icons.camera),
                  label: const Text('צילום משימה'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ] else ...[
          // Image preview
          Container(
            width: double.infinity,
            height: 300,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(15),
              image: DecorationImage(
                image: FileImage(_imageFile!),
                fit: BoxFit.cover,
              ),
            ),
          ),
          const SizedBox(height: 20),
          
          // Status indicator
          if (_isProcessing)
            const Column(
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 10),
                Text('מעבד את המשימה...'),
              ],
            )
          else
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: _captureImage,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('צלם שוב'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.grey.shade700,
                  ),
                ),
                const SizedBox(width: 15),
                ElevatedButton.icon(
                  onPressed: () {
                    widget.onImageCaptured(_imageFile!);
                  },
                  icon: const Icon(Icons.check),
                  label: const Text('המשך'),
                ),
              ],
            ),
        ],
      ],
    );
  }
}
