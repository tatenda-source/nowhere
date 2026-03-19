import { useCallback } from 'react';
import { Alert } from 'react-native';
import { api } from '../utils/api';

export function useJoinIntent() {
    const joinIntent = useCallback(async (id: string, onJoinSuccess?: () => void) => {
        try {
            await api.post(`/intents/${id}/join`);
            Alert.alert("Joined!", "You are in.");
            if (onJoinSuccess) {
                onJoinSuccess();
            }
            return true;
        } catch (e) {
            console.error(e);
            Alert.alert("Error", "Could not join intent");
            return false;
        }
    }, []);

    return { joinIntent };
}
