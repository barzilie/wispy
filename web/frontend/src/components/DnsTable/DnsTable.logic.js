// DnsTable logic and utility functions

export const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleTimeString();
};

export const filterRecentQueries = (queries, limit = 50) => {
  return queries.slice(0, limit);
};

export const getDomainCategory = (domain) => {
  const categories = {
    'social': ['facebook', 'instagram', 'twitter', 'snapchat', 'tiktok'],
    'streaming': ['youtube', 'netflix', 'spotify', 'twitch'],
    'work': ['slack', 'zoom', 'microsoft', 'google', 'notion'],
    'gaming': ['steam', 'discord', 'epic'],
  };

  for (const [category, keywords] of Object.entries(categories)) {
    if (keywords.some(keyword => domain.toLowerCase().includes(keyword))) {
      return category;
    }
  }
  return 'other';
};
