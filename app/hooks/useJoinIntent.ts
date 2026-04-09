import { useCallback } from 'react';
import { Alert } from 'react-native';
import { api } from '../utils/api';
import { isValidUUID } from '../utils/validation';
import { logError } from '../utils/logger';

export function useJoinIntent() {
    const joinIntent = useCallback(async (id: string, onJoinSuccess?: () => void) => {
        if (!isValidUUID(id)) {
            Alert.alert("Error", "Invalid intent");
            return false;
        }
        try {
            const res = await api.post(`/intents/${id}/join`);
            if (res.data.joined) {
                Alert.alert("Joined!", "You are in.");
            } else {
                Alert.alert("Already joined", res.data.message || "You're already part of this.");
            }
            if (onJoinSuccess) {
                onJoinSuccess();
            }
            return true;
        } catch (e: any) {
            logError('Join intent failed', e);
            Alert.alert("Error", e.userMessage || "Could not join intent");
            return false;
        }
    }, []);

    return { joinIntent };
}
