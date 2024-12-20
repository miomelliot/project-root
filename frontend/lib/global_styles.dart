import 'package:flutter/material.dart';

class GlobalStyles {
  // Стиль заголовка
  static const TextStyle titleTextStyle = TextStyle(
    fontSize: 24.0,
    fontWeight: FontWeight.bold,
    color: Colors.black,
  );

  // Стиль подзаголовка
  static const TextStyle subtitleTextStyle = TextStyle(
    fontSize: 18.0,
    fontWeight: FontWeight.w500,
    color: Colors.black87,
  );

  // Стиль основного текста
  static const TextStyle bodyTextStyle = TextStyle(
    fontSize: 16.0,
    fontWeight: FontWeight.normal,
    color: Colors.black54,
  );

  // Стиль текста для ввода
  static const TextStyle inputTextStyle = TextStyle(
    fontSize: 16.0,
    color: Colors.black87,
  );

  // Стиль для кнопок
  static final ButtonStyle elevatedButtonStyle = ElevatedButton.styleFrom(
    padding: EdgeInsets.symmetric(vertical: 12.0, horizontal: 24.0),
    textStyle: const TextStyle(fontSize: 16.0, fontWeight: FontWeight.w600),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(10.0),
    ),
  );

  static final ButtonStyle textButtonStyle = TextButton.styleFrom(
    textStyle: const TextStyle(fontSize: 14.0, color: Colors.blue),
  );

  // Декорация для ввода текста
  static final InputDecoration inputDecoration = InputDecoration(
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10.0),
    ),
    contentPadding: EdgeInsets.symmetric(vertical: 15.0, horizontal: 20.0),
  );

  // Ограничение ширины контейнера
  static const double maxWidth = 400.0;

  // Промежутки
  static const SizedBox verticalSpaceMedium = SizedBox(height: 20.0);
  static const SizedBox verticalSpaceSmall = SizedBox(height: 10.0);
  static const EdgeInsets verticalSpaceSmallTop = EdgeInsets.only(top: 16.0);
  
}
