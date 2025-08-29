// lib/screens/manager/ai_manager_screen.dart
import 'package:flutter/material.dart';
import 'dart:convert';
import '../../services/llm_service.dart';
import '../../services/auth_service_backend.dart';

class AIManagerScreen extends StatefulWidget {
  @override
  _AIManagerScreenState createState() => _AIManagerScreenState();
}

class _AIManagerScreenState extends State<AIManagerScreen> {
  
  // State variables
  List<dynamic> _providers = [];
  String _activeProvider = '';
  Map<String, dynamic> _prompts = {
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
  TextEditingController _systemPromptController = TextEditingController();
  TextEditingController _testPromptController = TextEditingController();
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
      final token = await _authService.getToken();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/llm/providers/$providerName/activate'),
        headers: {'Authorization': 'Bearer $token'},
      );
      
      if (response.statusCode == 200) {
        setState(() => _activeProvider = providerName);
        _showSuccess('Switched to $providerName');
        await _loadProviders();
      }
    } catch (e) {
      _showError('Failed to switch provider');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _savePrompt() async {
    setState(() => _isLoading = true);
    
    try {
      final token = await _authService.getToken();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/llm/prompts/$_selectedMode'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'system': _systemPromptController.text,
          'temperature': _prompts[_selectedMode]['temperature'],
          'maxTokens': _prompts[_selectedMode]['maxTokens'],
        }),
      );
      
      if (response.statusCode == 200) {
        _showSuccess('Prompt saved successfully');
      }
    } catch (e) {
      _showError('Failed to save prompt');
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
      final token = await _authService.getToken();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/llm/compare'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'prompt': _testPromptController.text,
          'providers': _providers.map((p) => p['name']).toList(),
        }),
      );
      
      if (response.statusCode == 200) {
        setState(() {
          _comparisonResults = jsonDecode(response.body);
        });
        _showSuccess('Comparison completed');
      }
    } catch (e) {
      _showError('Failed to compare providers');
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
        title: Text('AI Configuration Manager'),
        backgroundColor: Colors.purple,
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : DefaultTabController(
              length: 3,
              child: Column(
                children: [
                  Container(
                    color: Colors.purple[50],
                    child: TabBar(
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
      padding: EdgeInsets.all(16),
      children: [
        Text(
          'Available AI Providers',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        SizedBox(height: 16),
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
            title: Text(provider['info']['provider']),
            subtitle: Text(provider['info']['model']),
            trailing: provider['name'] == _activeProvider
                ? Chip(
                    label: Text('Active'),
                    backgroundColor: Colors.green[100],
                  )
                : ElevatedButton(
                    onPressed: () => _switchProvider(provider['name']),
                    child: Text('Activate'),
                  ),
          ),
        )).toList(),
      ],
    );
  }

  Widget _buildPromptsTab() {
    return ListView(
      padding: EdgeInsets.all(16),
      children: [
        Text(
          'Configure AI Behavior',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        SizedBox(height: 16),
        
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
                child: Text('Practice Mode'),
              ),
            ),
            SizedBox(width: 8),
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
                child: Text('Test Mode'),
              ),
            ),
          ],
        ),
        SizedBox(height: 16),
        
        // System prompt editor
        Text('System Prompt (Hebrew):', style: TextStyle(fontWeight: FontWeight.bold)),
        SizedBox(height: 8),
        TextField(
          controller: _systemPromptController,
          maxLines: 10,
          textDirection: TextDirection.rtl,
          decoration: InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'הכנס הוראות למערכת...',
          ),
          onChanged: (value) {
            _prompts[_selectedMode]['system'] = value;
          },
        ),
        SizedBox(height: 16),
        
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
        Text(
          '0 = Precise answers | 1 = Creative answers',
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
        SizedBox(height: 16),
        
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
        SizedBox(height: 24),
        
        ElevatedButton(
          onPressed: _savePrompt,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.purple,
            padding: EdgeInsets.symmetric(vertical: 16),
          ),
          child: Row(
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
      padding: EdgeInsets.all(16),
      children: [
        Text(
          'Test & Compare Providers',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        SizedBox(height: 16),
        
        TextField(
          controller: _testPromptController,
          maxLines: 3,
          textDirection: TextDirection.rtl,
          decoration: InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'הכנס שאלה לבדיקה...',
            labelText: 'Test Prompt',
          ),
        ),
        SizedBox(height: 16),
        
        ElevatedButton(
          onPressed: _compareProviders,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.purple,
            padding: EdgeInsets.symmetric(vertical: 16),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.compare_arrows),
              SizedBox(width: 8),
              Text('Compare All Providers'),
            ],
          ),
        ),
        
        if (_comparisonResults != null) ...[
          SizedBox(height: 24),
          Text(
            'Comparison Results:',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 16),
          ..._comparisonResults!.entries.map((entry) => Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        entry.key,
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      if (entry.value['success'])
                        Chip(
                          label: Text('${entry.value['response_time'].toStringAsFixed(2)}s'),
                          backgroundColor: Colors.blue[100],
                        ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      entry.value['response'] ?? 'Error: ${entry.value['error']}',
                      style: TextStyle(fontSize: 14),
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
