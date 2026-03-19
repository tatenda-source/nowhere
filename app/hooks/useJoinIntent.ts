import { useCallback } from 'react';
import { Alert } from 'react-native';
import { api } from '../utils/api';

export function useJoinIntent() {
    const joinIntent = useCallback(async (id: string, onJoinSuccess?: () => void) => {
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
            console.error(e);
            Alert.alert("Error", e.userMessage || "Could not join intent");
            return false;
        }
    }, []);

    return { joinIntent };
}
