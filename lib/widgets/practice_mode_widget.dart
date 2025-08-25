
// lib/widgets/practice_mode_widget.dart
import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class PracticeModeWidget extends StatelessWidget {
  final Function(String) onOptionSelected;
  
  const PracticeModeWidget({
    Key? key,
    required this.onOptionSelected,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Text(
          'איך אוכל לעזור לך?',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),
        
        // Options Grid
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          childAspectRatio: 1.2,
          mainAxisSpacing: 15,
          crossAxisSpacing: 15,
          padding: const EdgeInsets.symmetric(horizontal: 15),
          children: [
            _buildOptionCard(
              context,
              'הדגמה',
              Icons.play_circle_outline,
              'demonstrate',
              'הראה לי דוגמה קונקרטית כיצד לפתור את המשימה',
            ),
            _buildOptionCard(
              context,
              'הסבר',
              Icons.lightbulb_outline,
              'explain',
              'הסבר לי את המשימה בצורה ברורה ופשוטה',
            ),
            _buildOptionCard(
              context,
              'פירוק לשלבים',
              Icons.format_list_numbered,
              'breakdown',
              'חלק את המשימה לשלבים קטנים וברורים',
            ),
            _buildOptionCard(
              context,
              'שאלות הבהרה',
              Icons.help_outline,
              'clarify',
              'שאל אותי שאלות כדי להבין מה לא ברור לי',
            ),
          ],
        ),
      ],
    );
  }
  
  Widget _buildOptionCard(
    BuildContext context,
    String title,
    IconData icon,
    String option,
    String description,
  ) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
      ),
      child: InkWell(
        onTap: () => onOptionSelected(option),
        borderRadius: BorderRadius.circular(15),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 35,
                color: AppColors.primary,
              ),
              const SizedBox(height: 10),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 5),
              Expanded(
                child: Text(
                  description,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

