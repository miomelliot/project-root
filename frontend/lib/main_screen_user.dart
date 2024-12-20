import 'package:flutter/material.dart';
import 'package:flutter_application_1/config.dart';
import 'global_styles.dart';
import 'login_screen.dart';
import 'plant_detail_screen.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class MainScreenUser extends StatefulWidget {
  final String token;
  final String role;

  const MainScreenUser({required this.token, required this.role, Key? key})
      : super(key: key);

  @override
  _MainScreenState createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreenUser> {
  List<dynamic> _plants = [];
  List<dynamic> _favorites = [];
  List<dynamic> _filteredPlants = [];
  Set<int> _favoritePlantIds = {}; // Для отслеживания избранного
  int _offset = 0;
  bool _isLoading = false;
  bool _isFavoritesTab = false;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchPlants();
    _fetchFavorites();
    _searchController.addListener(_onSearchChanged);
  }

  void _onSearchChanged() {
    setState(() {
      _filteredPlants = _plants.where((plant) {
        final commonName = plant['common_name'];
        if (commonName == null) return false; // Пропускаем null значения
        return commonName
            .toLowerCase()
            .contains(_searchController.text.toLowerCase());
      }).toList();
    });
  }

  Future<void> _fetchPlants() async {
    if (_isLoading) return;
    setState(() => _isLoading = true);

    final response = await http.get(
      Uri.parse('${Config.baseUrl}/plants?offset=$_offset&limit=5'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );

    if (response.statusCode == 200) {
      final List<dynamic> newPlants = jsonDecode(response.body);

      if (newPlants.isEmpty) {
        // Если из БД не пришли новые данные, используем API random_plants
        await _fetchRandomPlants();
      } else {
        setState(() {
          // Добавляем только уникальные растения
          for (var plant in newPlants) {
            if (!_plants
                .any((existingPlant) => existingPlant['id'] == plant['id'])) {
              _plants.add(plant);
            }
          }
          _filteredPlants = List.from(_plants);
          _offset += 5;
        });
      }
    } else {
      _showError("Ошибка загрузки растений.");
    }
    setState(() => _isLoading = false);
  }

  Future<void> _fetchRandomPlants() async {
    final response = await http.get(
      Uri.parse('${Config.baseUrl}/random_plants'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);
      final List<dynamic> randomPlants = data['plants'];

      if (randomPlants.isNotEmpty) {
        setState(() {
          // Добавляем растения и увеличиваем смещение
          for (var plant in randomPlants) {
            if (!_plants
                .any((existingPlant) => existingPlant['id'] == plant['id'])) {
              _plants.add(plant);
            }
          }
          _filteredPlants = List.from(_plants);
          _offset += 5;
        });
      } else {
        _showError("Случайные растения не найдены.");
      }
    } else {
      _showError("Ошибка загрузки случайных растений.");
    }
  }

  Future<void> _fetchFavorites() async {
    final response = await http.get(
      Uri.parse('${Config.baseUrl}/favorites'),
      headers: {"Authorization": "Bearer ${widget.token}"},
    );

    if (response.statusCode == 200) {
      final List<dynamic> favorites = jsonDecode(response.body);
      setState(() {
        _favorites = favorites;
        _favoritePlantIds = favorites.map<int>((e) => e['id']).toSet();
      });
    }
  }

  void _toggleTab(bool isFavorites) {
    setState(() {
      _isFavoritesTab = isFavorites;
      _filteredPlants = isFavorites ? _favorites : _plants;
    });
  }

  Future<void> _toggleFavorite(int plantId) async {
    final bool isFavorite = _favoritePlantIds.contains(plantId);
    final endpoint = '${Config.baseUrl}/favorites/$plantId';

    final response = isFavorite
        ? await http.delete(Uri.parse(endpoint),
            headers: {"Authorization": "Bearer ${widget.token}"})
        : await http.post(Uri.parse(endpoint),
            headers: {"Authorization": "Bearer ${widget.token}"});

    if (response.statusCode == 200 || response.statusCode == 201) {
      setState(() {
        if (isFavorite) {
          _favoritePlantIds.remove(plantId);
        } else {
          _favoritePlantIds.add(plantId);
        }
      });
      _fetchFavorites();
    } else {
      _showError("Ошибка изменения избранного");
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  void _logout() {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (context) => LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final items = _isFavoritesTab ? _favorites : _filteredPlants;

    return Scaffold(
      appBar: AppBar(
        title: Text(_isFavoritesTab ? "Избранное" : "Каталог"),
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
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                ElevatedButton(
                  onPressed: () => _toggleTab(false),
                  style: GlobalStyles.elevatedButtonStyle,
                  child: Text("Каталог"),
                ),
                ElevatedButton(
                  onPressed: () => _toggleTab(true),
                  style: GlobalStyles.elevatedButtonStyle,
                  child: Text("Избранное"),
                ),
              ],
            ),
          ),
          if (!_isFavoritesTab)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: TextField(
                controller: _searchController,
                decoration: GlobalStyles.inputDecoration.copyWith(
                  hintText: "Поиск по названию",
                  prefixIcon: Icon(Icons.search),
                ),
              ),
            ),
          Expanded(
            child: ListView.builder(
              itemCount: items.length + (_isFavoritesTab ? 0 : 1),
              itemBuilder: (context, index) {
                if (!_isFavoritesTab && index == items.length) {
                  return _buildLoadMoreButton();
                }

                final plant = items[index];
                final plantId = plant['id'];
                final isFavorite = _favoritePlantIds.contains(plantId);

                return ListTile(
                  leading: Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8.0),
                      color: Colors.grey[300], // Цвет фона при загрузке
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8.0),
                      child: Image.network(
                        "${Config.baseUrl}/${plant['image_url'] ?? ''}", // Здесь добавляем полный путь
                        fit: BoxFit.cover,
                        loadingBuilder: (context, child, loadingProgress) {
                          if (loadingProgress == null) return child;
                          return Center(
                            child: CircularProgressIndicator(
                              strokeWidth: 2.0,
                              value: loadingProgress.expectedTotalBytes != null
                                  ? loadingProgress.cumulativeBytesLoaded /
                                      (loadingProgress.expectedTotalBytes ?? 1)
                                  : null,
                            ),
                          );
                        },
                        errorBuilder: (context, error, stackTrace) {
                          return Center(
                            child: Icon(
                              Icons.image_not_supported,
                              color: Colors.grey,
                              size: 30,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  title: Text(plant['common_name'] ?? 'Неизвестно'),
                  subtitle: Text(plant['scientific_name'] ?? ''),
                  trailing: IconButton(
                    icon: Icon(
                      Icons.favorite,
                      color: isFavorite ? Colors.red : Colors.grey,
                    ),
                    onPressed: () => _toggleFavorite(plantId),
                  ),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => PlantDetailScreen(plant: plant),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadMoreButton() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Center(
        child: ElevatedButton(
          style: GlobalStyles.elevatedButtonStyle,
          onPressed: _fetchPlants,
          child: _isLoading ? CircularProgressIndicator() : Text("Ещё"),
        ),
      ),
    );
  }
}
