import * as Location from 'expo-location';

export interface CoarseLocation {
    latitude: number;
    longitude: number;
}

export async function getCurrentLocation(): Promise<CoarseLocation | null> {
    try {
        // Timeout: if location takes more than 10s, give up
        const result = await Promise.race([
            _getLocation(),
            new Promise<null>((resolve) => setTimeout(() => resolve(null), 10000)),
        ]);
        return result;
    } catch {
        return null;
    }
}

async function _getLocation(): Promise<CoarseLocation | null> {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
        return null;
    }

    const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
    });

    // 3 decimal places ~ 110m precision
    const lat = parseFloat(location.coords.latitude.toFixed(3));
    const lon = parseFloat(location.coords.longitude.toFixed(3));

    return { latitude: lat, longitude: lon };
}
