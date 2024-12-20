import 'package:flutter/material.dart';
import 'package:flutter_application_1/config.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import 'global_styles.dart';

class PlantDetailScreen extends StatefulWidget {
  final dynamic plant;

  const PlantDetailScreen({super.key, required this.plant});

  @override
  _PlantDetailScreenState createState() => _PlantDetailScreenState();
}

class _PlantDetailScreenState extends State<PlantDetailScreen> {
  final Map<String, TextEditingController> _controllers = {};

  @override
  void initState() {
    super.initState();
    _initializeControllers();
  }

  void _initializeControllers() {
    final fields = [
      'scientific_name',
      'family',
      'genus',
      'rank',
      'author',
      'bibliography',
      'year',
    ];
    for (var field in fields) {
      _controllers[field] =
          TextEditingController(text: widget.plant[field]?.toString());
    }
  }

  Future<void> _updatePlant() async {
    final url = Uri.parse("http://localhost:8000/plants/${widget.plant['id']}");
    final response = await http.put(
      url,
      headers: {"Content-Type": "application/json"},
      body: json.encode({
        for (var field in _controllers.keys)
          field: field == 'year'
              ? int.tryParse(_controllers[field]?.text ?? '0') ?? 0
              : _controllers[field]?.text ?? '',
      }),
    );

    if (response.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Данные растения успешно обновлены")),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Ошибка обновления данных")),
      );
    }
  }

  Widget _buildEditableField(String label, String field, TextStyle style) {
    return Row(
      children: [
        Expanded(
          child: Text(
            "$label: ${_controllers[field]?.text ?? 'Неизвестно'}",
            style: style,
          ),
        ),
        IconButton(
          icon: Icon(Icons.edit, color: Colors.blue),
          onPressed: () => _showEditDialog(label, field),
        ),
      ],
    );
  }

  void _showEditDialog(String label, String field) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Редактировать $label"),
        content: TextFormField(
          controller: _controllers[field],
          keyboardType:
              field == 'year' ? TextInputType.number : TextInputType.text,
          decoration: InputDecoration(
            labelText: label,
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text("Отмена"),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {});
              Navigator.pop(context);
            },
            child: Text("Сохранить"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.plant['common_name'] ?? "Детали растения"),
        actions: [
          IconButton(
            icon: Icon(Icons.save),
            onPressed: _updatePlant,
            tooltip: "Сохранить",
            padding: const EdgeInsets.only(right: 25.0),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Изображение растения
              Center(
                child: Container(
                  width: MediaQuery.of(context).size.width,
                  height: 200,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12.0),
                    color: Colors.grey[300],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12.0),
                    child: Image.network(
                      "${Config.baseUrl}/${widget.plant['image_url'] ?? ''}",
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Icon(Icons.image, size: 80),
                    ),
                  ),
                ),
              ),
              SizedBox(height: 20.0),

              // Поля с кнопкой редактирования
              _buildEditableField("Научное имя", "scientific_name",
                  GlobalStyles.titleTextStyle),
              SizedBox(height: 10.0),
              _buildEditableField(
                  "Семейство", "family", GlobalStyles.subtitleTextStyle),
              SizedBox(height: 10.0),
              _buildEditableField("Род", "genus", GlobalStyles.bodyTextStyle),
              SizedBox(height: 10.0),
              _buildEditableField("Ранг", "rank", GlobalStyles.bodyTextStyle),
              SizedBox(height: 10.0),
              _buildEditableField(
                  "Автор", "author", GlobalStyles.bodyTextStyle),
              SizedBox(height: 10.0),
              _buildEditableField(
                  "Библиография", "bibliography", GlobalStyles.bodyTextStyle),
              SizedBox(height: 10.0),
              _buildEditableField("Год", "year", GlobalStyles.bodyTextStyle),
            ],
          ),
        ),
      ),
    );
  }
}
