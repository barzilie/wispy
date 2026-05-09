# React Component Structure

## Architecture
Each component follows a 3-file pattern:
- **`.jsx`** - Component structure (HTML/JSX)
- **`.logic.js`** - Logic, utility functions, helpers
- **`.css`** - Component-specific styles

## Component Tree

```
App (App.js)
├── Header (Header.jsx)
├── DeviceList (DeviceList.jsx)
│   └── DeviceCard (DeviceCard.jsx) [multiple]
├── DnsTable (DnsTable.jsx)
└── RecommendationsPanel (RecommendationsPanel.jsx)
```

## Components

### Header
**Path:** `components/Header/`
- Displays WiSpy logo and title
- Props: none
- Logic: `getStatusMessage()`, `formatTitle()`, `getConnectionStatus()`

### DeviceList
**Path:** `components/DeviceList/`
- Renders grid of connected devices
- Props: `devices` (array)
- Logic: `sortDevicesByLastSeen()`, `filterDevicesByOS()`, `getOSBreakdown()`

### DeviceCard
**Path:** `components/DeviceCard/`
- Single device card with MAC, IP, vendor, OS
- Props: `device` (object)
- Logic: `formatTimestamp()`, `getDeviceIcon()`

### DnsTable
**Path:** `components/DnsTable/`
- Scrollable table of DNS queries
- Props: `dnsQueries` (array)
- Logic: `formatTimestamp()`, `getDomainCategory()`

### RecommendationsPanel
**Path:** `components/RecommendationsPanel/`
- Button to trigger AI recommendations
- Shows loading state and results
- Props: `recommendations`, `loading`, `onGetRecommendations`

## Custom Hooks

### useWispyData
**Path:** `hooks/useWispyData.js`
- Fetches devices and DNS data from `/api/data`
- Auto-refreshes every 2 seconds
- Returns: `{ devices, dnsQueries, error }`

### useRecommendations
**Path:** `hooks/useRecommendations.js`
- Calls `/api/recommend` on demand
- Manages loading and error states
- Returns: `{ recommendations, loading, error, getRecommendations }`

## File Organization

```
src/
├── App.js              # Main app component
├── App.css             # Global styles
├── components/
│   ├── Header/
│   │   ├── Header.jsx
│   │   ├── Header.logic.js
│   │   └── Header.css
│   ├── DeviceList/
│   │   ├── DeviceList.jsx
│   │   ├── DeviceList.logic.js
│   │   └── DeviceList.css
│   ├── DeviceCard/
│   │   ├── DeviceCard.jsx
│   │   ├── DeviceCard.logic.js
│   │   └── DeviceCard.css
│   ├── DnsTable/
│   │   ├── DnsTable.jsx
│   │   ├── DnsTable.logic.js
│   │   └── DnsTable.css
│   └── RecommendationsPanel/
│       ├── RecommendationsPanel.jsx
│       ├── RecommendationsPanel.logic.js
│       └── RecommendationsPanel.css
└── hooks/
    ├── useWispyData.js
    └── useRecommendations.js
```

## Adding New Components

1. Create folder: `src/components/ComponentName/`
2. Create files:
   - `ComponentName.jsx` - JSX structure
   - `ComponentName.logic.js` - Logic/utilities
   - `ComponentName.css` - Styles
3. Import and use in parent component

**Note:** Logic files are named `.logic.js` to avoid conflicts with React component imports.
