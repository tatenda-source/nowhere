import React, { useEffect, useState, useRef, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, TextInput, Button, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { api } from '../utils/api';
import { API_URL } from '../utils/config';
import { getAccessToken } from '../utils/identity';
import { isValidUUID, sanitizeDisplay } from '../utils/validation';
import { logError } from '../utils/logger';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../App';

interface Message {
    id: string;
    user_id: string;
    content: string;
    created_at: string;
}

type Props = NativeStackScreenProps<RootStackParamList, 'Chat'>;

function buildWsUrl(intentId: string, token: string | null): string {
    const url = new URL(`/ws/intents/${encodeURIComponent(intentId)}/messages`, API_URL);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    if (token) {
        url.searchParams.set('token', token);
    }
    return url.toString();
}

export default function ChatScreen({ route, navigation }: Props) {
    const { intentId } = route.params;
    const [messages, setMessages] = useState<Message[]>([]);
    const [text, setText] = useState('');
    const [loading, setLoading] = useState(true);
    const [connected, setConnected] = useState(false);
    const [sending, setSending] = useState(false);

    const wsRef = useRef<WebSocket | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const flatListRef = useRef<FlatList>(null);

    // Validate intentId is a real UUID — reject malicious route params
    useEffect(() => {
        if (!isValidUUID(intentId)) {
            Alert.alert('Error', 'Invalid intent');
            navigation.goBack();
        }
    }, [intentId, navigation]);

    const fetchMessages = useCallback(async () => {
        if (!isValidUUID(intentId)) return;
        try {
            const res = await api.get(`/intents/${intentId}/messages`);
            setMessages(res.data);
        } catch (e) {
            logError('Failed to fetch messages', e);
        } finally {
            setLoading(false);
        }
    }, [intentId]);

    // WebSocket connection with polling fallback
    useEffect(() => {
        if (!isValidUUID(intentId)) return;

        // Initial fetch
        fetchMessages();

        let ws: WebSocket;

        // Async connect so we can await the token
        (async () => {
            const token = await getAccessToken();
            ws = new WebSocket(buildWsUrl(intentId, token));

            ws.onopen = () => {
                setConnected(true);
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                    intervalRef.current = null;
                }
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'new_message' && data.message) {
                        setMessages(prev => [...prev, data.message]);
                    }
                } catch {
                    // Ignore non-JSON (e.g. "pong")
                }
            };

            ws.onerror = () => {
                setConnected(false);
                if (!intervalRef.current) {
                    intervalRef.current = setInterval(fetchMessages, 3000);
                }
            };

            ws.onclose = () => {
                setConnected(false);
                if (!intervalRef.current) {
                    intervalRef.current = setInterval(fetchMessages, 3000);
                }
            };

            wsRef.current = ws;
        })();

        // Keepalive ping every 30s
        const pingInterval = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send('ping');
            }
        }, 30000);

        return () => {
            clearInterval(pingInterval);
            if (intervalRef.current) clearInterval(intervalRef.current);
            wsRef.current?.close();
        };
    }, [intentId, fetchMessages]);

    const handleSend = async () => {
        if (!text.trim() || sending) return;
        setSending(true);
        try {
            await api.post(`/intents/${intentId}/messages`, {
                user_id: "ignored_by_backend",
                content: text
            });
            setText('');
            if (!connected) {
                fetchMessages();
            }
        } catch (e) {
            logError('Failed to send message', e);
            Alert.alert("Error", "Could not send message");
        } finally {
            setSending(false);
        }
    };

    return (
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.container}>
            <View style={styles.headerRow}>
                <Button title="<" onPress={() => navigation.goBack()} accessibilityLabel="Go back" />
                <Text style={styles.header}>Chat</Text>
                <View style={[styles.statusDot, { backgroundColor: connected ? '#4CAF50' : '#FF9800' }]} accessibilityLabel={connected ? 'Connected' : 'Reconnecting'} />
            </View>

            <FlatList
                ref={flatListRef}
                data={messages}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => (
                    <View style={styles.bubble}>
                        <Text style={styles.content}>{sanitizeDisplay(item.content)}</Text>
                    </View>
                )}
                onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
            />

            <View style={styles.inputRow}>
                <TextInput
                    style={styles.input}
                    value={text}
                    onChangeText={setText}
                    placeholder="Type a message..."
                    accessibilityLabel="Message input"
                    accessibilityHint="Type your message and press send"
                />
                <Button title="Send" onPress={handleSend} disabled={sending} accessibilityLabel="Send message" />
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        paddingTop: 50,
        backgroundColor: '#fff',
    },
    headerRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 10,
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        paddingBottom: 10
    },
    header: {
        fontSize: 20,
        fontWeight: 'bold',
        marginLeft: 10,
        flex: 1,
    },
    statusDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginRight: 10,
    },
    bubble: {
        padding: 10,
        margin: 10,
        backgroundColor: '#e6f7ff',
        borderRadius: 10,
        alignSelf: 'flex-start',
        maxWidth: '80%'
    },
    content: {
        fontSize: 16
    },
    inputRow: {
        flexDirection: 'row',
        padding: 10,
        borderTopWidth: 1,
        borderTopColor: '#eee',
        alignItems: 'center'
    },
    input: {
        flex: 1,
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 20,
        paddingHorizontal: 15,
        paddingVertical: 10,
        marginRight: 10,
        fontSize: 16
    }
});
