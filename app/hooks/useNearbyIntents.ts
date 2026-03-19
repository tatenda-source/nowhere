import { useState, useCallback } from 'react';
import { Alert } from 'react-native';
import { api } from '../utils/api';
import { Intent } from '../types/intent';
import { CoarseLocation } from '../utils/location';

export function useNearbyIntents() {
    const [nearby, setNearby] = useState<Intent[]>([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState<string | null>(null);

    const fetchIntents = useCallback(async (loc: CoarseLocation | null) => {
        setLoading(true);
        try {
            if (loc) {
                const res = await api.get('/intents/nearby', {
                    params: { lat: loc.latitude, lon: loc.longitude }
                });
                setNearby(res.data.intents);
                setMessage(res.data.message || null);
            } else {
                setMessage("We need your location to find the Nowhere.");
            }
        } catch (e: any) {
            console.error(e);
            // Keep stale data visible — don't clear nearby
            setMessage(e.userMessage || "Could not fetch nearby events");
        } finally {
            setLoading(false);
        }
    }, []);

    return { nearby, loading, message, fetchIntents };
}
