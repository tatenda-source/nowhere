import React from 'react';
import { View, Text, StyleSheet, Button } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import HomeScreen from './screens/HomeScreen';
import CreateScreen from './screens/CreateScreen';
import ChatScreen from './screens/ChatScreen';

export type RootStackParamList = {
    Home: undefined;
    Create: undefined;
    Chat: { intentId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

// --- Error Boundary ---
interface ErrorBoundaryState {
    hasError: boolean;
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorBoundaryState> {
    state: ErrorBoundaryState = { hasError: false };

    static getDerivedStateFromError(): ErrorBoundaryState {
        return { hasError: true };
    }

    componentDidCatch(error: Error) {
        // @ts-ignore
        if (typeof __DEV__ !== 'undefined' && __DEV__) {
            console.error('ErrorBoundary caught:', error);
        }
    }

    render() {
        if (this.state.hasError) {
            return (
                <View style={crashStyles.container}>
                    <Text style={crashStyles.title}>Something went wrong</Text>
                    <Text style={crashStyles.body}>The app ran into an unexpected error.</Text>
                    <Button title="Try Again" onPress={() => this.setState({ hasError: false })} />
                </View>
            );
        }
        return this.props.children;
    }
}

const crashStyles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
    title: { fontSize: 22, fontWeight: 'bold', marginBottom: 12 },
    body: { fontSize: 16, color: '#666', marginBottom: 24, textAlign: 'center' },
});

// --- App ---
export default function App() {
    return (
        <ErrorBoundary>
            <NavigationContainer>
                <Stack.Navigator
                    initialRouteName="Home"
                    screenOptions={{ headerShown: false }}
                >
                    <Stack.Screen name="Home" component={HomeScreen} />
                    <Stack.Screen
                        name="Create"
                        component={CreateScreen}
                        options={{ presentation: 'modal' }}
                    />
                    <Stack.Screen name="Chat" component={ChatScreen} />
                </Stack.Navigator>
                <StatusBar style="auto" />
            </NavigationContainer>
        </ErrorBoundary>
    );
}
