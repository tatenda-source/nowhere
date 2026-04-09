import * as SecureStore from 'expo-secure-store';
import { v4 as uuidv4 } from 'uuid';
import { Platform } from 'react-native';
import { logWarn } from './logger';

const IDENTITY_KEY = 'nowhere_anon_id';
const JWT_KEY = 'nowhere_jwt';
const ROTATION_INTERVAL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
import { API_URL } from './config';

interface IdentityData {
    id: string;
    created_at: number;
}

function isTokenExpired(token: string): boolean {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Expired if past exp with a 30-second buffer
        return payload.exp * 1000 < Date.now() - 30000;
    } catch {
        return true;
    }
}

export async function getOrCreateIdentity(): Promise<string> {
    let data: IdentityData | null = null;
    let raw: string | null = null;

    try {
        if (Platform.OS === 'web') {
            raw = localStorage.getItem(IDENTITY_KEY);
        } else {
            raw = await SecureStore.getItemAsync(IDENTITY_KEY);
        }

        if (raw) {
            try {
                data = JSON.parse(raw);
            } catch {
                // Legacy string format — migrate
                data = { id: raw, created_at: Date.now() };
                await saveIdentity(data);
            }
        }
    } catch (e) {
        logWarn('Failed to read identity', e);
    }

    // Check rotation
    const now = Date.now();
    if (data && (now - data.created_at > ROTATION_INTERVAL_MS)) {
        data = null; // Force regeneration
        await saveAccessToken(null);
    }

    if (!data) {
        data = { id: uuidv4(), created_at: now };
        await saveIdentity(data);
    }

    return data.id;
}

async function saveIdentity(data: IdentityData) {
    const str = JSON.stringify(data);
    try {
        if (Platform.OS === 'web') {
            localStorage.setItem(IDENTITY_KEY, str);
        } else {
            await SecureStore.setItemAsync(IDENTITY_KEY, str);
        }
    } catch (e) {
        logWarn('Failed to save identity', e);
    }
}

export async function getAccessToken(): Promise<string | null> {
    // 1. Check storage
    let token: string | null = null;
    try {
        if (Platform.OS === 'web') {
            token = sessionStorage.getItem(JWT_KEY);
        } else {
            token = await SecureStore.getItemAsync(JWT_KEY);
        }
    } catch (e) {
        logWarn('Failed to read JWT', e);
    }

    // Return cached token only if it's not expired
    if (token && !isTokenExpired(token)) return token;

    // Token missing or expired — clear and re-handshake
    if (token) {
        await saveAccessToken(null);
    }

    // 2. Handshake
    try {
        const anonId = await getOrCreateIdentity();
        const response = await fetch(`${API_URL}/auth/handshake`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ anon_id: anonId })
        });

        if (response.ok) {
            const json = await response.json();
            token = json.access_token;
            if (token) await saveAccessToken(token);
            return token;
        } else {
            logWarn('Handshake failed with status ' + response.status);
        }
    } catch (e) {
        logWarn('Handshake error', e);
    }

    return null;
}

async function saveAccessToken(token: string | null) {
    try {
        if (!token) {
            if (Platform.OS === 'web') sessionStorage.removeItem(JWT_KEY);
            else await SecureStore.deleteItemAsync(JWT_KEY);
            return;
        }

        if (Platform.OS === 'web') {
            sessionStorage.setItem(JWT_KEY, token);
        } else {
            await SecureStore.setItemAsync(JWT_KEY, token);
        }
    } catch (e) {
        logWarn('Failed to save JWT', e);
    }
}
