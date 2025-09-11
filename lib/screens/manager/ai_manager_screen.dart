// lib/screens/manager/ai_manager_screen.dart
import 'package:flutter/material.dart';
import '../../services/llm_service.dart';
import '../../services/auth_service_backend.dart';

class AIManagerScreen extends StatefulWidget {
  const AIManagerScreen({super.key});

  @override
  _AIManagerScreenState createState() => _AIManagerScreenState();
}

class _AIManagerScreenState extends State<AIManagerScreen> {
  
  // State variables
  List<dynamic> _providers = [];
  String _activeProvider = '';
  final Map<String, dynamic> _prompts = {
    'practice': {
      'system': '''אתה LearnoBot, עוזר AI שנועד לעזור לתלמידים עם לקויות למידה להבין הוראות לימודיות.

התפקיד שלך:
1. לפרק הוראות מורכבות לצעדים פשוטים
2. לספק הסברים ברורים
3. לתת דוגמאות רלוונטיות
4. להיות סבלני ומעודד''',
      'temperature': 0.7,
      'maxTokens': 2048,
    },
    'test': {
      'system': '''אתה במצב מבחן. ספק עזרה מינימלית בלבד.
מקסימום 3 ניסיונות עזרה.''',
      'temperature': 0.5,
      'maxTokens': 1024,
    }
  };
  
  bool _isLoading = false;
  String _selectedMode = 'practice';
  final TextEditingController _systemPromptController = TextEditingController();
  final TextEditingController _testPromptController = TextEditingController();
  Map<String, dynamic>? _comparisonResults;

  @override
  void initState() {
    super.initState();
    _loadProviders();
    _systemPromptController.text = _prompts['practice']['system'];
  }

  Future<void> _loadProviders() async {
    setState(() => _isLoading = true);
    
    try {
      final providers = await LLMService.getProviders();
      setState(() {
        _providers = providers;
        _activeProvider = providers.firstWhere(
          (p) => p['is_active'] == true,
          orElse: () => providers.isNotEmpty ? providers[0] : {}
        )['name'] ?? '';
      });
    } catch (e) {
      _showError('Failed to load providers: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _switchProvider(String providerName) async {
    setState(() => _isLoading = true);
    
    try {
      final token = await AuthServiceBackend.getStoredToken();
      await LLMService.activateProvider(
        providerName: providerName,
        token: token,
      );
      
      setState(() => _activeProvider = providerName);
      _showSuccess('Switched to $providerName');
      await _loadProviders();
    } catch (e) {
      _showError('Failed to switch provider: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _savePrompt() async {
    setState(() => _isLoading = true);
    
    try {
      final token = await AuthServiceBackend.getStoredToken();
      await LLMService.savePromptConfig(
        mode: _selectedMode,
        systemPrompt: _systemPromptController.text,
        temperature: _prompts[_selectedMode]['temperature'].toDouble(),
        maxTokens: _prompts[_selectedMode]['maxTokens'].toInt(),
        token: token,
      );
      
      _showSuccess('Prompt saved successfully');
    } catch (e) {
      _showError('Failed to save prompt: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _compareProviders() async {
    if (_testPromptController.text.isEmpty) {
      _showError('Please enter a test prompt');
      return;
    }
    
    setState(() => _isLoading = true);
    
    try {
      final token = await AuthServiceBackend.getStoredToken();
      final results = await LLMService.compareProviders(
        testPrompt: _testPromptController.text,
        token: token,
      );
      
      setState(() {
        _comparisonResults = results;
      });
      _showSuccess('Comparison completed');
    } catch (e) {
      _showError('Failed to compare providers: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Configuration Manager'),
        backgroundColor: Colors.purple,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : DefaultTabController(
              length: 3,
              child: Column(
                children: [
                  Container(
                    color: Colors.purple[50],
                    child: const TabBar(
                      labelColor: Colors.purple,
                      unselectedLabelColor: Colors.grey,
                      tabs: [
                        Tab(text: 'Providers'),
                        Tab(text: 'Prompts'),
                        Tab(text: 'Testing'),
                      ],
                    ),
                  ),
                  Expanded(
                    child: TabBarView(
                      children: [
                        _buildProvidersTab(),
                        _buildPromptsTab(),
                        _buildTestingTab(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildProvidersTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Available AI Providers',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        ..._providers.map((provider) => Card(
          child: ListTile(
            leading: Icon(
              provider['info']['type'] == 'local' 
                ? Icons.computer 
                : Icons.cloud,
              color: provider['name'] == _activeProvider 
                ? Colors.green 
                : Colors.grey,
            ),
            title: Text(provider['info']?['provider'] ?? provider['name'] ?? 'Unknown'),
            subtitle: Text(provider['info']?['model'] ?? 'No model specified'),
            trailing: (provider['name'] ?? '') == _activeProvider
                ? Chip(
                    label: const Text('Active'),
                    backgroundColor: Colors.green[100],
                  )
                : ElevatedButton(
                    onPressed: () => _switchProvider(provider['name'] ?? ''),
                    child: const Text('Activate'),
                  ),
          ),
        )).toList(),
      ],
    );
  }

  Widget _buildPromptsTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Configure AI Behavior',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        
        // Mode selector
        Row(
          children: [
            Expanded(
              child: ElevatedButton(
                onPressed: () {
                  setState(() {
                    _selectedMode = 'practice';
                    _systemPromptController.text = _prompts['practice']['system'];
                  });
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: _selectedMode == 'practice' 
                    ? Colors.purple 
                    : Colors.grey[300],
                ),
                child: const Text('Practice Mode'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: ElevatedButton(
                onPressed: () {
                  setState(() {
                    _selectedMode = 'test';
                    _systemPromptController.text = _prompts['test']['system'];
                  });
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: _selectedMode == 'test' 
                    ? Colors.purple 
                    : Colors.grey[300],
                ),
                child: const Text('Test Mode'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        
        // System prompt editor
        const Text('System Prompt (Hebrew):', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TextField(
          controller: _systemPromptController,
          maxLines: 10,
          textDirection: TextDirection.rtl,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'הכנס הוראות למערכת...',
          ),
          onChanged: (value) {
            _prompts[_selectedMode]['system'] = value;
          },
        ),
        const SizedBox(height: 16),
        
        // Temperature slider
        Text('Temperature (Creativity): ${_prompts[_selectedMode]['temperature']}'),
        Slider(
          value: _prompts[_selectedMode]['temperature'],
          min: 0,
          max: 1,
          divisions: 10,
          onChanged: (value) {
            setState(() {
              _prompts[_selectedMode]['temperature'] = value;
            });
          },
        ),
        const Text(
          '0 = Precise answers | 1 = Creative answers',
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
        const SizedBox(height: 16),
        
        // Max tokens slider
        Text('Max Tokens: ${_prompts[_selectedMode]['maxTokens']}'),
        Slider(
          value: _prompts[_selectedMode]['maxTokens'].toDouble(),
          min: 256,
          max: 4096,
          divisions: 15,
          onChanged: (value) {
            setState(() {
              _prompts[_selectedMode]['maxTokens'] = value.toInt();
            });
          },
        ),
        const SizedBox(height: 24),
        
        ElevatedButton(
          onPressed: _savePrompt,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.purple,
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.save),
              SizedBox(width: 8),
              Text('Save Configuration'),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTestingTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Test & Compare Providers',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        
        TextField(
          controller: _testPromptController,
          maxLines: 3,
          textDirection: TextDirection.rtl,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'הכנס שאלה לבדיקה...',
            labelText: 'Test Prompt',
          ),
        ),
        const SizedBox(height: 16),
        
        ElevatedButton(
          onPressed: _compareProviders,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.purple,
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.compare_arrows),
              SizedBox(width: 8),
              Text('Compare All Providers'),
            ],
          ),
        ),
        
        if (_comparisonResults != null) ...[
          const SizedBox(height: 24),
          const Text(
            'Comparison Results:',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          ..._comparisonResults!.entries.map((entry) => Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        entry.key,
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      if (entry.value['success'])
                        Chip(
                          label: Text('${entry.value['response_time'].toStringAsFixed(2)}s'),
                          backgroundColor: Colors.blue[100],
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      entry.value['response'] ?? 'Error: ${entry.value['error']}',
                      style: const TextStyle(fontSize: 14),
                      textDirection: TextDirection.rtl,
                    ),
                  ),
                ],
              ),
            ),
          )).toList(),
        ],
      ],
    );
  }
}
