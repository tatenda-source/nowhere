export default {
    app: {
        name: 'Nowhere',
    },
    home: {
        emptyState: "It's quiet here.",
        startSomething: 'Start something',
        joinCount: '{{count}} joined',
        join: 'Join',
        chat: 'Chat',
    },
    create: {
        title: 'New Intent',
        whatHappening: "What's happening?",
        placeholder: 'Coffee run? Frisbee?',
        emoji: 'Emoji',
        cancel: 'Cancel',
        create: 'Create',
        creating: 'Creating...',
        titleRequired: 'Please add a title',
        locationRequired: 'Location needed to create intent',
        error: 'Failed to create intent',
    },
    chat: {
        title: 'Chat',
        placeholder: 'Type a message...',
        send: 'Send',
        sendError: 'Could not send message',
    },
    errors: {
        networkError: 'Cannot reach server. Check your connection.',
        rateLimit: 'Too many requests. Try again soon.',
        serverError: 'Something went wrong on our end. Try again.',
        generic: 'Something went wrong.',
        fetchNearby: 'Could not fetch nearby events',
        joinFailed: 'Could not join intent',
        locationNeeded: 'We need your location to find the Nowhere.',
    },
};
