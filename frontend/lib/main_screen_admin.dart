import 'package:flutter/material.dart';
import 'package:flutter_application_1/config.dart';
import 'package:flutter_application_1/login_screen.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';


class MainScreenAdmin extends StatefulWidget {
  final String token;
  final String role;

  const MainScreenAdmin({required this.token, required this.role, Key? key})
      : super(key: key);

  @override
  State<MainScreenAdmin> createState() => _MainScreenAdminState();
}

class _MainScreenAdminState extends State<MainScreenAdmin>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  void _logout() {
  Navigator.of(context).pushReplacement(
    MaterialPageRoute(builder: (context) => LoginScreen()),
  );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Административная панель"),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 23.0),
            child: IconButton(
              icon: Icon(Icons.logout),
              onPressed: _logout,
              tooltip: "Выйти",
            ),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Каталог"),
            Tab(text: "Пользователи"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          CatalogTab(token: widget.token),
          UsersTab(token: widget.token),
        ],
      ),
    );
  }
}

class CatalogTab extends StatefulWidget {
  final String token;

  const CatalogTab({required this.token, Key? key}) : super(key: key);

  @override
  State<CatalogTab> createState() => _CatalogTabState();
}

class _CatalogTabState extends State<CatalogTab> {
  List<dynamic> _plants = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchPlants();
  }

  Future<void> _fetchPlants() async {
    final response = await http.get(
      Uri.parse('${Config.baseUrl}/plants'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );
    if (response.statusCode == 200) {
      setState(() {
        _plants = json.decode(response.body);
        _isLoading = false;
      });
    }
  }

  Future<void> _deletePlant(int plantId) async {
    final response = await http.delete(
      Uri.parse('${Config.baseUrl}/plants/$plantId'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );
    if (response.statusCode == 200) {
      setState(() => _plants.removeWhere((plant) => plant['id'] == plantId));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Растение удалено")),
      );
    }
  }

  Future<void> _deleteAllPlants() async {
    final response = await http.delete(
      Uri.parse('${Config.baseUrl}/plants'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );
    if (response.statusCode == 200) {
      setState(() => _plants.clear());
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Все растения удалены")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        ElevatedButton(
          onPressed: _deleteAllPlants,
          child: const Text("Удалить все растения"),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: _plants.length,
            itemBuilder: (context, index) {
              final plant = _plants[index];
              return ListTile(
                title: Text(plant['common_name'] ?? 'Неизвестно'),
                subtitle: Text(plant['scientific_name'] ?? ''),
                trailing: IconButton(
                  icon: const Icon(Icons.delete),
                  onPressed: () => _deletePlant(plant['id']),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class UsersTab extends StatefulWidget {
  final String token;

  const UsersTab({required this.token, Key? key}) : super(key: key);

  @override
  State<UsersTab> createState() => _UsersTabState();
}

class _UsersTabState extends State<UsersTab> {
  List<dynamic> _users = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchUsers();
  }

  Future<void> _fetchUsers() async {
    final response = await http.get(
      Uri.parse('${Config.baseUrl}/admin/users'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );
    if (response.statusCode == 200) {
      setState(() {
        _users = json.decode(response.body);
        _isLoading = false;
      });
    }
  }

  Future<void> _deleteUser(int userId) async {
    final response = await http.delete(
      Uri.parse('${Config.baseUrl}/admin/users/$userId'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );
    if (response.statusCode == 200) {
      setState(() => _users.removeWhere((user) => user['id'] == userId));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Пользователь удален")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return ListView.builder(
      itemCount: _users.length,
      itemBuilder: (context, index) {
        final user = _users[index];
        return ListTile(
          title: Text(user['username']),
          subtitle: Text("Роль: ${user['role']}"),
          trailing: IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () => _deleteUser(user['id']),
          ),
        );
      },
    );
  }
}
