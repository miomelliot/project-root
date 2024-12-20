import 'package:flutter/material.dart';
import 'package:flutter_application_1/config.dart';
import 'global_styles.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'main_screen_user.dart';
import 'main_screen_admin.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  bool _isLogin = true; // Флаг для переключения формы
  String _errorMessage = ''; // Сообщение об ошибке



  Future<void> _submit() async {
    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();

    if (username.isEmpty || password.isEmpty) {
      setState(() {
        _errorMessage = "Все поля должны быть заполнены!";
      });
      return;
    }

    try {
      final endpoint = _isLogin ? '${Config.baseUrl}/login' : '${Config.baseUrl}/register';

      final response = await http.post(
        Uri.parse(endpoint),
        headers: {"Content-Type": "application/json; charset=UTF-8"},
        body: utf8
            .encode(jsonEncode({"username": username, "password": password})),
      );

      final responseBody = utf8.decode(response.bodyBytes);

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(responseBody);

        if (_isLogin) {
          String role = data['role'];
          String token = data['access_token'];

          // Переход на соответствующий экран
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => role == 'admin'
                  ? MainScreenAdmin(token: token, role: role)
                  : MainScreenUser(token: token, role: role),
            ),
          );
        } else {
          _showSuccess("Регистрация успешна! Пожалуйста, войдите.");
          _toggleForm(); // Переключаемся на форму входа
        }
      } else {
        final errorData = jsonDecode(responseBody);
        setState(() {
          _errorMessage = errorData['detail'] ?? "Ошибка запроса!";
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Ошибка соединения с сервером.";
      });
      print("Error: $e");
    }
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message, style: TextStyle(color: Colors.white))),
    );
  }

  void _toggleForm() {
    setState(() {
      _isLogin = !_isLogin;
      _errorMessage = '';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Container(
          width: GlobalStyles.maxWidth,
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                _isLogin ? 'Вход' : 'Регистрация',
                style: GlobalStyles.titleTextStyle,
                textAlign: TextAlign.center,
              ),
              GlobalStyles.verticalSpaceMedium,
              TextField(
                controller: _usernameController,
                style: GlobalStyles.inputTextStyle,
                decoration: GlobalStyles.inputDecoration.copyWith(
                  hintText: 'Имя пользователя',
                ),
              ),
              GlobalStyles.verticalSpaceSmall,
              TextField(
                controller: _passwordController,
                style: GlobalStyles.inputTextStyle,
                decoration: GlobalStyles.inputDecoration.copyWith(
                  hintText: 'Пароль',
                ),
                obscureText: true,
              ),
              if (_errorMessage.isNotEmpty) ...[
                GlobalStyles.verticalSpaceSmall,
                Text(
                  _errorMessage,
                  style: const TextStyle(color: Colors.red),
                ),
              ],
              GlobalStyles.verticalSpaceMedium,
              ElevatedButton(
                style: GlobalStyles.elevatedButtonStyle,
                onPressed: _submit,
                child: Text(_isLogin ? 'Войти' : 'Зарегистрироваться'),
              ),
              TextButton(
                style: GlobalStyles.textButtonStyle,
                onPressed: _toggleForm,
                child: Text(
                  _isLogin ? 'У меня нет аккаунта' : 'У меня есть аккаунт',
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
