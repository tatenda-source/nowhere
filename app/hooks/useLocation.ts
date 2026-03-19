import { useState, useCallback } from 'react';
import { getCurrentLocation, CoarseLocation } from '../utils/location';

export function useLocation() {
    const [location, setLocation] = useState<CoarseLocation | null>(null);

    const fetchLocation = useCallback(async () => {
        const loc = await getCurrentLocation();
        setLocation(loc);
        return loc;
    }, []);

    return { location, fetchLocation };
}
