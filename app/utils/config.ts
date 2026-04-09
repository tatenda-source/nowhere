import Constants from 'expo-constants';
import { Platform } from 'react-native';

function resolveApiUrl(): string {
    // 1. Expo config (set via NOWHERE_API_URL env var or app.json extra)
    const configUrl = Constants.expoConfig?.extra?.apiUrl;
    if (configUrl && !configUrl.includes('${')) {
        return configUrl;
    }

    // 2. Platform-aware defaults for development
    if (__DEV__) {
        if (Platform.OS === 'android') {
            // Android emulator loopback to host machine
            return 'http://10.0.2.2:8000';
        }
        // iOS simulator / web — localhost works
        return 'http://localhost:8000';
    }

    // 3. Production fallback (should be set via config)
    return 'https://api.nowhere.app';
}

const _resolved = resolveApiUrl();

// @ts-ignore — __DEV__ is a React Native global
if (typeof __DEV__ !== 'undefined' && !__DEV__ && !_resolved.startsWith('https://')) {
    throw new Error('API_URL must use HTTPS in production builds');
}

export const API_URL = _resolved;
