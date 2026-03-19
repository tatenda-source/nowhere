import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { getCurrentLocation } from '../utils/location';
import { api } from '../utils/api';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Create'>;

export default function CreateScreen({ navigation }: Props) {
    const [title, setTitle] = useState('');
    const [emoji, setEmoji] = useState('📍');
    const [creating, setCreating] = useState(false);

    const handleCreate = async () => {
        if (!title.trim()) {
            Alert.alert("Needed", "Please add a title");
            return;
        }

        setCreating(true);
        try {
            const loc = await getCurrentLocation();
            if (!loc) {
                Alert.alert("Permission", "Location needed to create intent");
                setCreating(false);
                return;
            }

            await api.post('/intents/', {
                title: title,
                emoji: emoji,
                latitude: loc.latitude,
                longitude: loc.longitude
            });

            navigation.goBack();
        } catch (e) {
            console.error("Creation failed:", e);
            Alert.alert("Error", "Failed to create intent");
        } finally {
            setCreating(false);
        }
    };

    if (creating) {
        return (
            <View style={styles.center}>
                <ActivityIndicator size="large" />
                <Text>Creating...</Text>
            </View>
        )
    }

    return (
        <View style={styles.container}>
            <Text style={styles.header}>New Intent</Text>

            <Text style={styles.label}>What's happening?</Text>
            <TextInput
                style={styles.input}
                placeholder="Coffee run? Frisbee?"
                value={title}
                onChangeText={setTitle}
                maxLength={50}
            />

            <Text style={styles.label}>Emoji</Text>
            <TextInput
                style={styles.input}
                placeholder="📍"
                value={emoji}
                onChangeText={setEmoji}
                maxLength={2}
            />

            <View style={styles.buttons}>
                <Button title="Cancel" onPress={() => navigation.goBack()} color="#999" />
                <Button title="Create" onPress={handleCreate} />
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        paddingTop: 60,
        backgroundColor: '#fff',
        paddingHorizontal: 20
    },
    center: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center'
    },
    header: {
        fontSize: 28,
        fontWeight: 'bold',
        marginBottom: 30
    },
    label: {
        fontSize: 16,
        marginBottom: 8,
        fontWeight: '600'
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        padding: 12,
        borderRadius: 8,
        fontSize: 18,
        marginBottom: 20
    },
    buttons: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: 20
    }
});
