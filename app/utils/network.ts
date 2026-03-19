import { useState, useEffect, useRef } from 'react';
import { api } from './api';

export type NetworkStatus = 'online' | 'offline' | 'unknown';

export function useNetworkStatus(): NetworkStatus {
    const [status, setStatus] = useState<NetworkStatus>('unknown');
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        const check = async () => {
            try {
                await api.get('/health', { timeout: 5000 });
                setStatus('online');
            } catch {
                setStatus('offline');
            }
        };

        check();
        intervalRef.current = setInterval(check, 15000);

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, []);

    return status;
}
