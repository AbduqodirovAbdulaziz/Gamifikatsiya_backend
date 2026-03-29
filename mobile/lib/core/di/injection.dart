import 'package:get_it/get_it.dart';
import '../network/api_client.dart';
import '../../features/auth/data/repositories/auth_repository.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/gamification/data/repositories/gamification_repository.dart';
import '../../features/gamification/presentation/bloc/gamification_bloc.dart';

final getIt = GetIt.instance;

void setupDependencies() {
  getIt.registerLazySingleton<ApiClient>(() => ApiClient());

  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepository(getIt<ApiClient>()),
  );

  getIt.registerLazySingleton<GamificationRepository>(
    () => GamificationRepository(getIt<ApiClient>()),
  );

  getIt.registerFactory<AuthBloc>(
    () => AuthBloc(getIt<AuthRepository>()),
  );

  getIt.registerFactory<GamificationBloc>(
    () => GamificationBloc(getIt<GamificationRepository>()),
  );
}
