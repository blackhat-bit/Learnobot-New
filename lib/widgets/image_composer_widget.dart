// lib/widgets/image_composer_widget.dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:typed_data';
import '../constants/app_colors.dart';

class ImageComposerWidget extends StatefulWidget {
  final Function(List<XFile>, String) onSend;
  final VoidCallback onCancel;
  final List<XFile> initialImages;

  const ImageComposerWidget({
    Key? key,
    required this.onSend,
    required this.onCancel,
    this.initialImages = const [],
  }) : super(key: key);

  @override
  State<ImageComposerWidget> createState() => _ImageComposerWidgetState();
}

class _ImageComposerWidgetState extends State<ImageComposerWidget> {
  final TextEditingController _textController = TextEditingController();
  List<XFile> _images = [];
  final Map<String, Uint8List> _imagePreviewCache = {};

  @override
  void initState() {
    super.initState();
    _images = List.from(widget.initialImages);
    _loadPreviews();
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _loadPreviews() async {
    if (_images.isEmpty) return;
    
    for (final image in _images) {
      if (!_imagePreviewCache.containsKey(image.path)) {
        try {
          final bytes = await image.readAsBytes();
          if (mounted) {
            setState(() {
              _imagePreviewCache[image.path] = bytes;
            });
          }
        } catch (e) {
          print('Error loading preview for ${image.path}: $e');
        }
      }
    }
  }

  Future<void> _addMoreImages() async {
    try {
      final ImagePicker picker = ImagePicker();
      final List<XFile> images = await picker.pickMultiImage();
      
      if (images.isNotEmpty) {
        setState(() {
          _images.addAll(images);
        });
        await _loadPreviews();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בהוספת תמונות: $e')),
      );
    }
  }

  Future<void> _takePhoto() async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? image = await picker.pickImage(source: ImageSource.camera);
      
      if (image != null) {
        setState(() {
          _images.add(image);
        });
        await _loadPreviews();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('שגיאה בצילום: $e')),
      );
    }
  }

  void _removeImage(int index) {
    setState(() {
      final imagePath = _images[index].path;
      _images.removeAt(index);
      _imagePreviewCache.remove(imagePath);
    });
  }

  void _handleSend() {
    if (_images.isEmpty && _textController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('אנא הוסף תמונה או כתוב הודעה')),
      );
      return;
    }
    
    widget.onSend(_images, _textController.text.trim());
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.1),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'העלאת תמונות',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: widget.onCancel,
                  icon: const Icon(Icons.close, color: AppColors.primary),
                  tooltip: 'ביטול',
                ),
              ],
            ),
          ),

          // Image previews
          if (_images.isNotEmpty)
            Container(
              height: 120,
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _images.length,
                itemBuilder: (context, index) {
                  final image = _images[index];
                  final imageBytes = _imagePreviewCache[image.path];
                  
                  return Container(
                    width: 100,
                    margin: const EdgeInsets.only(left: 8),
                    child: Stack(
                      children: [
                        // Image preview
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: imageBytes != null
                              ? Image.memory(
                                  imageBytes,
                                  width: 100,
                                  height: 100,
                                  fit: BoxFit.cover,
                                )
                              : Container(
                                  width: 100,
                                  height: 100,
                                  color: Colors.grey.shade300,
                                  child: const Center(
                                    child: CircularProgressIndicator(),
                                  ),
                                ),
                        ),
                        
                        // Remove button
                        Positioned(
                          top: 4,
                          left: 4,
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.red,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: InkWell(
                              onTap: () => _removeImage(index),
                              child: const Icon(
                                Icons.close,
                                size: 16,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                        
                        // Image number
                        Positioned(
                          bottom: 4,
                          left: 4,
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.black.withOpacity(0.6),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              '${index + 1}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),

          // Add images buttons
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _addMoreImages,
                    icon: const Icon(Icons.photo_library),
                    label: const Text('הוסף מהגלריה'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.primary,
                      side: const BorderSide(color: AppColors.primary),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _takePhoto,
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('צלם תמונה'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.primary,
                      side: const BorderSide(color: AppColors.primary),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // Text input
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _textController,
              maxLines: 3,
              textDirection: TextDirection.rtl,
              decoration: const InputDecoration(
                hintText: 'כתוב שאלה או הוסף הערה על התמונות...',
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Colors.white,
              ),
            ),
          ),

          // Send button
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _handleSend,
                icon: const Icon(Icons.send),
                label: Text(
                  _images.isEmpty 
                      ? 'שלח הודעה' 
                      : 'שלח ${_images.length} ${_images.length == 1 ? "תמונה" : "תמונות"}',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

