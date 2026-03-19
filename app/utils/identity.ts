import * as SecureStore from 'expo-secure-store';
import { v4 as uuidv4 } from 'uuid';
import { Platform } from 'react-native';

const IDENTITY_KEY = 'nowhere_anon_id';
const JWT_KEY = 'nowhere_jwt';
const ROTATION_INTERVAL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
import { API_URL } from './config';

interface IdentityData {
    id: string;
    created_at: number;
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
                // Try parsing as JSON first
                data = JSON.parse(raw);
            } catch (e) {
                // Failed to parse, must be legacy string (Commit 1)
                // Migrate it
                data = { id: raw, created_at: Date.now() };
                await saveIdentity(data);
            }
        }
    } catch (e) {
        console.warn("Failed to read identity:", e);
    }

    // Check rotation
    const now = Date.now();
    if (data && (now - data.created_at > ROTATION_INTERVAL_MS)) {
        console.log("Identity expired, rotating...");
        data = null; // Force regeneration
        // Also clear JWT
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
        console.warn("Failed to save identity:", e);
    }
}

export async function getAccessToken(): Promise<string | null> {
    // 1. Check storage
    let token: string | null = null;
    try {
        if (Platform.OS === 'web') {
            token = localStorage.getItem(JWT_KEY);
        } else {
            token = await SecureStore.getItemAsync(JWT_KEY);
        }
    } catch (e) {
        console.warn("Failed to read JWT:", e);
    }

    if (token) return token;

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
            console.error("Handshake failed:", response.status);
        }
    } catch (e) {
        console.error("Handshake error:", e);
    }

    return null;
}

async function saveAccessToken(token: string | null) {
    try {
        if (!token) {
            if (Platform.OS === 'web') localStorage.removeItem(JWT_KEY);
            else await SecureStore.deleteItemAsync(JWT_KEY);
            return;
        }

        if (Platform.OS === 'web') {
            localStorage.setItem(JWT_KEY, token);
        } else {
            await SecureStore.setItemAsync(JWT_KEY, token);
        }
    } catch (e) {
        console.warn("Failed to save JWT:", e);
    }
}
