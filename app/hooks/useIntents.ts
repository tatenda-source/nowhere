import { useEffect, useCallback } from 'react';

import { Intent } from '../types/intent';
import { useLocation } from './useLocation';
import { useNearbyIntents } from './useNearbyIntents';
import { useJoinIntent } from './useJoinIntent';

/**
 * Hook to manage nearby intents, location fetching, and intent joining.
 * Refactored using Single Responsibility Principle (SRP).
 */
export function useIntents() {
    const { location, fetchLocation } = useLocation();
    const { nearby, loading, message, fetchIntents } = useNearbyIntents();
    const { joinIntent: doJoinIntent } = useJoinIntent();

    const fetchData = useCallback(async () => {
        const loc = await fetchLocation();
        await fetchIntents(loc);
    }, [fetchLocation, fetchIntents]);

    const joinIntent = useCallback(async (id: string) => {
        return await doJoinIntent(id, fetchData);
    }, [doJoinIntent, fetchData]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Return aggregated state and actions
    return { nearby, loading, location, message, fetchData, joinIntent };
}
