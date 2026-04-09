# Nowhere - Problem Statement & Solution

## The Problem

Modern social platforms have fundamentally broken how people discover spontaneous, local activity. Three core failures define this space:

### 1. The Permanence Trap
Every post, check-in, and story creates a permanent digital footprint. Users self-censor because content lives forever -- leading to performative behavior instead of authentic, in-the-moment sharing. People won't post "anyone want to grab coffee right now?" because it feels trivial against a curated feed.

### 2. The Social Graph Prison
Existing platforms route discovery through follower counts, algorithmic feeds, and social hierarchies. Finding out what's happening *near you right now* requires following the right accounts, being in the right group chats, or stumbling onto the right event listing hours in advance. The spontaneous "I wonder if anyone's at the park" question has no good digital answer.

### 3. The Engagement Treadmill
Platforms optimize for time-on-screen: infinite scroll, notifications, likes, metrics. None of this helps someone who simply wants to know: **is anything happening nearby that I could join?**

---

## The Solution

**Nowhere** is a real-time, location-scoped, ephemeral utility for spontaneous local gatherings.

### Core Design Principles

| Principle | Implementation |
|---|---|
| **Ephemeral by default** | Everything expires in 24 hours. No archives, no history, no permanence. |
| **Density over engagement** | Shows what's happening nearby *now*. No infinite scroll, no feed algorithm. |
| **No social graph** | Anonymous, device-scoped identity. No profiles, no followers, no likes. |
| **Honest empty states** | If nothing is happening, the app says so -- and encourages you to start something. |

### How It Works

**Intents** -- Users declare "I am here doing X" with an emoji and short title. This is the atomic unit of the app. Intents are geolocated, time-bound (24hr), and discoverable by anyone nearby.

**Joins** -- Other users respond with "I'm in." No DMs, no negotiations. A simple headcount that signals momentum.

**Messages** -- Lightweight, temporary coordination chat attached to an intent. Expires with the intent. Not a social messenger -- a walkie-talkie.

**Discovery** -- Nearby intents are ranked by a composite score: distance (closest first), freshness (newest first), and popularity (most joined first). No algorithmic curation, no promoted content.

### What Nowhere Is NOT

- Not a social network (no profiles, no followers)
- Not an event platform (no RSVPs, no planning ahead)
- Not a messaging app (chat is coordination-only, temporary)
- Not a review site (no ratings, no permanence)

### Target User

Someone standing in their neighborhood thinking: *"Is anything happening around here right now?"* -- and currently having no good way to find out without texting five group chats.

---

## Success Metrics

| Metric | Why It Matters |
|---|---|
| Intents created per km^2 per day | Measures real-world activity density |
| Join-to-view ratio | Measures intent quality and relevance |
| Time from app open to first action | Should be < 10 seconds -- utility, not engagement |
| Return visits without notifications | Organic pull, not push-driven retention |
