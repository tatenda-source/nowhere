import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';
import { api } from '../utils/api';
import { getCurrentLocation, CoarseLocation } from '../utils/location';

import { Intent } from '../types/intent';
import { useLocation } from './useLocation';
import { useNearbyIntents } from './useNearbyIntents';
import { useJoinIntent } from './useJoinIntent';

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

    return {
        nearby,
        loading,
        location,
        message,
        fetchData,
        joinIntent
    };
}
