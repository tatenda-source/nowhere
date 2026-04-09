/**
 * Safe logging utility.
 * In production, only logs the context string — never the error object,
 * which may contain auth headers, tokens, or request URLs via Axios.
 */
export function logError(context: string, _e?: unknown) {
    // @ts-ignore — __DEV__ is a React Native global
    if (typeof __DEV__ !== 'undefined' && __DEV__) {
        console.error(context, _e);
        return;
    }
    console.error(context);
}

export function logWarn(context: string, _e?: unknown) {
    // @ts-ignore
    if (typeof __DEV__ !== 'undefined' && __DEV__) {
        console.warn(context, _e);
        return;
    }
    // Silence warnings in production
}
