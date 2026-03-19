import en from './en';

export type TranslationKeys = typeof en;

// Current locale — extend with dynamic locale detection via expo-localization
const translations: Record<string, TranslationKeys> = {
    en,
};

let currentLocale = 'en';

export function setLocale(locale: string) {
    if (translations[locale]) {
        currentLocale = locale;
    }
}

export function t(path: string, params?: Record<string, string | number>): string {
    const keys = path.split('.');
    let value: any = translations[currentLocale];

    for (const key of keys) {
        if (value && typeof value === 'object' && key in value) {
            value = value[key];
        } else {
            return path; // fallback to key path
        }
    }

    if (typeof value !== 'string') return path;

    // Simple interpolation: {{key}} -> value
    if (params) {
        return value.replace(/\{\{(\w+)\}\}/g, (_, k) =>
            params[k] !== undefined ? String(params[k]) : `{{${k}}}`
        );
    }

    return value;
}
