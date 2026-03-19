import React from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Button } from 'react-native';
import { useIntents } from '../hooks/useIntents';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../App';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

export default function HomeScreen({ navigation }: Props) {
    const { nearby, loading, message, fetchData, joinIntent } = useIntents();

    if (loading && !nearby.length) {
        return (
            <View style={styles.center}>
                <ActivityIndicator size="large" />
            </View>
        )
    }

    if (!loading && nearby.length === 0) {
        return (
            <View style={styles.container}>
                <View style={styles.headerRow}>
                    <Text style={styles.header}>Nowhere</Text>
                </View>
                <View style={styles.center}>
                    <Text style={[styles.message, { fontSize: 20, textAlign: 'center' }]}>
                        {message || "It's quiet here."}
                    </Text>
                    <Button title="Start something" onPress={() => navigation.navigate('Create')} />
                </View>
            </View>
        )
    }

    return (
        <View style={styles.container}>
            <View style={styles.headerRow}>
                <Text style={styles.header}>Nowhere</Text>
                <Button title="+" onPress={() => navigation.navigate('Create')} />
            </View>
            {message && <Text style={styles.message}>{message}</Text>}

            <FlatList
                data={nearby}
                keyExtractor={(item) => item.id}
                refreshing={loading}
                onRefresh={fetchData}
                renderItem={({ item }) => (
                    <View style={styles.card}>
                        <Text style={styles.emoji}>{item.emoji}</Text>
                        <View style={styles.info}>
                            <Text style={styles.title}>{item.title}</Text>
                            <Text style={styles.meta}>{item.join_count} joined</Text>
                        </View>
                        <View style={styles.actions}>
                            <Button title="Join" onPress={() => joinIntent(item.id)} />
                            <Button title="Chat" color="#666" onPress={() => navigation.navigate('Chat', { intentId: item.id })} />
                        </View>
                    </View>
                )}
            />
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
        fontSize: 32,
        fontWeight: 'bold',
    },
    headerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20
    },
    message: {
        fontSize: 16,
        color: '#666',
        marginBottom: 20
    },
    card: {
        flexDirection: 'row',
        padding: 15,
        marginBottom: 10,
        backgroundColor: '#f8f8f8',
        borderRadius: 12,
        alignItems: 'center'
    },
    emoji: {
        fontSize: 30,
        marginRight: 15
    },
    info: {
        flex: 1
    },
    actions: {
        flexDirection: 'row',
        gap: 8,
    },
    title: {
        fontSize: 18,
        fontWeight: '600'
    },
    meta: {
        fontSize: 14,
        color: '#888',
        marginTop: 4
    }
});
