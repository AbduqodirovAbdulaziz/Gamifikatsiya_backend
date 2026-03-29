import 'package:flutter_test/flutter_test.dart';
import 'package:edugame/main.dart';

void main() {
  testWidgets('App renders splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const EduGameApp());
    await tester.pump();

    expect(find.text('EduGame'), findsOneWidget);
  });
}
