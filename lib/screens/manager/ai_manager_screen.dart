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
  List<dynamic> _availableModels = [];
  String _activeProvider = '';
  final Map<String, TextEditingController> _apiKeyControllers = {
    'openai': TextEditingController(),
    'anthropic': TextEditingController(),
    'google': TextEditingController(),
    'cohere': TextEditingController(),
  };
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
    _loadAvailableModels();
    _systemPromptController.text = _prompts['practice']['system'];
  }

  @override
  void dispose() {
    _systemPromptController.dispose();
    _testPromptController.dispose();
    _apiKeyControllers.values.forEach((controller) => controller.dispose());
    super.dispose();
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

  Future<void> _loadAvailableModels() async {
    try {
      final models = await LLMService.getAvailableModels();
      setState(() {
        _availableModels = models;
      });
    } catch (e) {
      _showError('Failed to load available models: $e');
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

  void _toggleModelActivation(String providerKey, bool isActive) {
    // TODO: Implement model activation/deactivation logic
    // This should call the backend API to toggle the model status
    setState(() {
      // For now, just show a message
      if (isActive) {
        _showSuccess('Model $providerKey activated');
      } else {
        _showSuccess('Model $providerKey deactivated');
      }
    });
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
              length: 4,
              child: Column(
                children: [
                  Container(
                    color: Colors.purple[50],
                    child: const TabBar(
                      labelColor: Colors.purple,
                      unselectedLabelColor: Colors.grey,
                      isScrollable: true,
                      tabs: [
                        Tab(text: 'Providers'),
                        Tab(text: 'Prompts'),
                        Tab(text: 'Testing'),
                        Tab(text: 'API Keys'),
                      ],
                    ),
                  ),
                  Expanded(
                    child: TabBarView(
                      children: [
                        _buildProvidersTab(),
                        _buildPromptsTab(),
                        _buildTestingTab(),
                        _buildApiKeyManagementTab(),
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
          'Available AI Models',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        if (_availableModels.isNotEmpty)
          ..._availableModels.map((providerGroup) {
            final providerName = providerGroup['provider_name'] as String? ?? 'Unknown';
            final providerType = providerGroup['provider_type'] as String? ?? 'unknown';
            final models = providerGroup['models'] as List<dynamic>? ?? [];
            
            return Card(
              margin: const EdgeInsets.only(bottom: 16),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          providerType == 'ollama' ? Icons.computer : Icons.cloud,
                          color: Colors.purple,
                          size: 24,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          providerName,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.purple,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    if (models.isEmpty)
                      const Text(
                        'No models available',
                        style: TextStyle(color: Colors.grey),
                      )
                    else
                      ...models.map((model) {
                        final providerKey = model['provider_key'] as String? ?? '';
                        final modelName = model['model_name'] as String? ?? 'Unknown';
                        final displayName = model['display_name'] as String? ?? modelName;
                        final isActive = model['active'] as bool? ?? false;
                        final isDeactivated = model['is_deactivated'] as bool? ?? false;
                        final isOllamaModel = providerType == 'ollama';
                        final isAvailable = isOllamaModel; // Ollama models are available if they exist
                        
                        return ListTile(
                          dense: true,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                          leading: Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: isDeactivated
                                  ? Colors.red
                                  : (isActive
                                      ? Colors.green
                                      : (isAvailable ? Colors.blue : Colors.grey)),
                              shape: BoxShape.circle,
                            ),
                          ),
                          title: Text(
                            displayName,
                            style: TextStyle(
                              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                              color: isDeactivated
                                  ? Colors.red[700]
                                  : (isActive
                                      ? Colors.green[700]
                                      : (isAvailable ? Colors.blue[700] : Colors.black87)),
                              decoration: isDeactivated ? TextDecoration.lineThrough : null,
                            ),
                          ),
                          subtitle: Text('Provider: $providerKey'),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              // Deactivation Toggle
                              Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Switch(
                                    value: !isDeactivated,
                                    onChanged: (value) => _toggleModelActivation(providerKey, !value),
                                    activeColor: Colors.green,
                                    inactiveThumbColor: Colors.red,
                                  ),
                                  Text(
                                    isDeactivated ? 'Deactivated' : 'Active',
                                    style: const TextStyle(fontSize: 10),
                                  ),
                                ],
                              ),
                              const SizedBox(width: 8),
                              
                              // Status chips and buttons
                              if (isDeactivated)
                                const Chip(
                                  label: Text('Disabled'),
                                  backgroundColor: Colors.red,
                                  labelStyle: TextStyle(color: Colors.white),
                                )
                              else if (isActive)
                                const Chip(
                                  label: Text('Active'),
                                  backgroundColor: Colors.green,
                                  labelStyle: TextStyle(color: Colors.white),
                                )
                              else if (isAvailable)
                                Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Chip(
                                      label: Text('Available'),
                                      backgroundColor: Colors.blue,
                                      labelStyle: TextStyle(color: Colors.white),
                                    ),
                                    const SizedBox(width: 8),
                                    ElevatedButton(
                                      onPressed: () => _switchProvider(providerKey),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.purple,
                                      ),
                                      child: const Text('Activate'),
                                    ),
                                  ],
                                )
                              else
                                ElevatedButton(
                                  onPressed: () => _switchProvider(providerKey),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.purple,
                                  ),
                                  child: const Text('Activate'),
                                ),
                            ],
                          ),
                        );
                      }).toList(),
                  ],
                ),
              ),
            );
          }).toList()
        else
          const Center(
            child: Text(
              'No models available. Please check your configuration.',
              style: TextStyle(color: Colors.grey),
            ),
          ),
        
        const SizedBox(height: 24),
        const Divider(),
        const SizedBox(height: 16),
        
        // Legacy provider status for debugging
        if (_providers.isNotEmpty) ...[
          const Text(
            'Provider Status (Debug)',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 8),
          ..._providers.map((provider) => Card(
            color: Colors.grey[100],
            child: ListTile(
              dense: true,
              leading: Icon(
                provider['type'] == 'local' 
                  ? Icons.computer 
                  : Icons.cloud,
                color: provider['is_active'] 
                  ? Colors.green 
                  : Colors.grey,
                size: 20,
              ),
              title: Text(
                provider['name'] ?? 'Unknown',
                style: const TextStyle(fontSize: 14),
              ),
              subtitle: Text(
                'Type: ${provider['type']}, Has Key: ${provider['has_api_key']}',
                style: const TextStyle(fontSize: 12),
              ),
              trailing: provider['is_active']
                  ? const Icon(Icons.check_circle, color: Colors.green, size: 16)
                  : const Icon(Icons.radio_button_unchecked, color: Colors.grey, size: 16),
            ),
          )).toList(),
        ],
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

  Future<void> _addApiKey(String providerName) async {
    final controller = _apiKeyControllers[providerName];
    if (controller == null || controller.text.isEmpty) {
      _showError('Please enter an API key');
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      final token = await AuthServiceBackend.getStoredToken();
      await LLMService.addApiKey(
        providerName: providerName,
        apiKey: controller.text.trim(),
        token: token,
      );
      
      controller.clear();
      _showSuccess('API key added for $providerName');
      await _loadProviders(); // Refresh provider status
    } catch (e) {
      _showError('Failed to add API key: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _removeApiKey(String providerName) async {
    setState(() => _isLoading = true);
    
    try {
      final token = await AuthServiceBackend.getStoredToken();
      await LLMService.removeApiKey(
        providerName: providerName,
        token: token,
      );
      
      _showSuccess('API key removed for $providerName');
      await _loadProviders(); // Refresh provider status
    } catch (e) {
      _showError('Failed to remove API key: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Widget _buildApiKeyManagementTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'API Key Management',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        const Text(
          'Manage API keys for cloud AI providers. Local models (Ollama) don\'t require API keys.',
          style: TextStyle(color: Colors.grey),
        ),
        const SizedBox(height: 24),
        
        // OpenAI
        _buildApiKeySection('openai', 'OpenAI', 'Enter your OpenAI API key (sk-...)'),
        const SizedBox(height: 16),
        
        // Anthropic
        _buildApiKeySection('anthropic', 'Anthropic', 'Enter your Anthropic API key (sk-ant-...)'),
        const SizedBox(height: 16),
        
        // Google
        _buildApiKeySection('google', 'Google', 'Enter your Google AI API key'),
        const SizedBox(height: 16),
        
        // Cohere
        _buildApiKeySection('cohere', 'Cohere', 'Enter your Cohere API key'),
      ],
    );
  }

  Widget _buildApiKeySection(String providerName, String displayName, String hintText) {
    final controller = _apiKeyControllers[providerName]!;
    final provider = _providers.firstWhere(
      (p) => p['name'] == providerName,
      orElse: () => {'has_api_key': false, 'is_available': false, 'is_active': false}
    );
    
    final hasKey = provider['has_api_key'] ?? false;
    final isAvailable = provider['is_available'] ?? false;
    final isActive = provider['is_active'] ?? false;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.cloud,
                  color: Colors.purple,
                  size: 24,
                ),
                const SizedBox(width: 8),
                Text(
                  displayName,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.purple,
                  ),
                ),
                const Spacer(),
                if (hasKey)
                  Row(
                    children: [
                      if (isActive)
                        const Chip(
                          label: Text('Active'),
                          backgroundColor: Colors.green,
                          labelStyle: TextStyle(color: Colors.white),
                        )
                      else if (isAvailable)
                        const Chip(
                          label: Text('Available'),
                          backgroundColor: Colors.blue,
                          labelStyle: TextStyle(color: Colors.white),
                        ),
                      const SizedBox(width: 8),
                      const Icon(
                        Icons.check_circle,
                        color: Colors.green,
                        size: 20,
                      ),
                    ],
                  )
                else
                  const Icon(
                    Icons.warning,
                    color: Colors.orange,
                    size: 20,
                  ),
              ],
            ),
            const SizedBox(height: 12),
            
            if (hasKey) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.green[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.green[200]!),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle, color: Colors.green),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'API key configured for $displayName',
                        style: const TextStyle(color: Colors.green),
                      ),
                    ),
                    TextButton.icon(
                      onPressed: () => _removeApiKey(providerName),
                      icon: const Icon(Icons.delete, color: Colors.red),
                      label: const Text('Remove', style: TextStyle(color: Colors.red)),
                    ),
                  ],
                ),
              ),
            ] else ...[
              TextField(
                controller: controller,
                decoration: InputDecoration(
                  border: const OutlineInputBorder(),
                  hintText: hintText,
                  prefixIcon: const Icon(Icons.vpn_key),
                ),
                obscureText: true,
                onSubmitted: (_) => _addApiKey(providerName),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _addApiKey(providerName),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.purple,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  icon: const Icon(Icons.add),
                  label: Text('Add $displayName API Key'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
