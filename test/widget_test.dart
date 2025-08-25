// // test/widget_test.dart
// //import 'package:flutter/material.dart';
// import 'package:flutter_test/flutter_test.dart';
// import 'package:learnobot/main.dart';
// import 'package:learnobot/screens/auth/welcome_screen.dart';

// void main() {
//   testWidgets('Counter increments smoke test', (WidgetTester tester) async {
//     // Build our app and trigger a frame.
//     await tester.pumpWidget(const MyApp(firebaseInitialized: false));

//     // Verify the welcome screen is shown as the starting point
//     expect(find.byType(WelcomeScreen), findsOneWidget);
    
//     // We can't test counter functionality directly since our app has changed
//     // Instead, let's verify basic UI elements from the welcome screen
//     expect(find.text('LearnoBot'), findsOneWidget);
    
//     // Additional tests specific to the welcome screen can be added here
//   });
// }

// // If you want to test the counter functionality, create a separate test file
// // with a simple counter widget for testing:

// // Example separate test file for counter functionality:
// /*
// // test/counter_test.dart
// import 'package:flutter/material.dart';
// import 'package:flutter_test/flutter_test.dart';

// class CounterWidget extends StatefulWidget {
//   const CounterWidget({Key? key}) : super(key: key);

//   @override
//   State<CounterWidget> createState() => _CounterWidgetState();
// }

// class _CounterWidgetState extends State<CounterWidget> {
//   int _counter = 0;

//   void _incrementCounter() {
//     setState(() {
//       _counter++;
//     });
//   }

//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(
//       home: Scaffold(
//         body: Center(
//           child: Column(
//             mainAxisAlignment: MainAxisAlignment.center,
//             children: <Widget>[
//               const Text('You have pushed the button this many times:'),
//               Text(
//                 '$_counter',
//                 style: Theme.of(context).textTheme.headlineMedium,
//               ),
//             ],
//           ),
//         ),
//         floatingActionButton: FloatingActionButton(
//           onPressed: _incrementCounter,
//           tooltip: 'Increment',
//           child: const Icon(Icons.add),
//         ),
//       ),
//     );
//   }
// }

// void main() {
//   testWidgets('Counter increments smoke test', (WidgetTester tester) async {
//     // Build our counter widget and trigger a frame
//     await tester.pumpWidget(const CounterWidget());

//     // Verify that our counter starts at 0
//     expect(find.text('0'), findsOneWidget);
//     expect(find.text('1'), findsNothing);

//     // Tap the '+' icon and trigger a frame
//     await tester.tap(find.byIcon(Icons.add));
//     await tester.pump();

//     // Verify that our counter has incremented
//     expect(find.text('0'), findsNothing);
//     expect(find.text('1'), findsOneWidget);
//   });
// }
// */