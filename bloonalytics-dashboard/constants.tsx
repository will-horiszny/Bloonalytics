import { MapType } from './types';

export const BASE_URL = 'https://b2.kozow.com';

export const MAP_DISPLAY_NAMES: Record<string, string> = {
  'lava_canyon': 'Magma Mixup',
  'skull_party': 'Street Party',
  'ALL': 'ALL'
};

const MAP_EMOJIS: Record<string, string> = {
  banana_depot: '🍌',
  basalt_columns: '🪨',
  bloonstone_quarry: '💎',
  bot_factory: '🤖',
  building_site: '🏗️',
  castle_ruins: '🏰',
  cobra_command: '🐍',
  dino_graveyard: '🦖',
  garden: '🌻',
  glade: '🌲',
  inflection: '🔀',
  koru: '🌀',
  lava_canyon: '🌋',
  mayan: '🛕',
  neo_highway: '🚗',
  oasis: '🏝️',
  offtide: '🌊',
  pirate_cove: '💀',
  ports: '⚓',
  precious_space: '🚀',
  salmon_ladder: '🐟',
  sands_of_time: '⏳',
  skull_party: '🎉',
  splashdown: '💦',
  star: '⭐',
  sun_palace: '☀️',
  times_up: '⏰',
  up_on_the_roof: '🏠',
};

export function formatMapName(map: string): string {
  if (map === 'ALL') return 'ALL';

  // 1. Determine if it is reversed
  const isReversed = map.endsWith('_reversed');
  const baseMap = isReversed ? map.replace('_reversed', '') : map;

  // 2. Get the Textual Name (check hardcoded first, then format)
  let displayName = MAP_DISPLAY_NAMES[baseMap] || baseMap
    .split('_')
    .map((word, index) => {
      if (index !== 0 && (word === 'on' || word === 'of' || word === 'the')) return word;
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');

  // 3. Get the Emoji
  const emoji = MAP_EMOJIS[baseMap] || '';

  // 4. Combine: "Name Emoji⏪"
  // Note: We trim in case an emoji is missing to avoid double spaces
  return `${displayName} ${emoji}${isReversed ? '⏪' : ''}`.trim();
}