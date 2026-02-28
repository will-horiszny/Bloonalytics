
import { DatabaseInfo } from '../types';

const BASE_URL = 'https://b2.kozow.com';

// Fallback data based on user provided JSON
const FALLBACK_DATA = {
  "databases": {
    "s24+_matches": { "path": "/s24~2B_matches" },
    "s33+_matches": { "path": "/s33~2B_matches" },
    "s37+_matches": { "path": "/s37~2B_matches" },
    "season_38_matches": { "path": "/season_38_matches" },
    "season_39_matches": { "path": "/season_39_matches" }
  }
};

export async function fetchDatabases(): Promise<DatabaseInfo[]> {
  let dbSource: any;
  
  try {
    const response = await fetch(`${BASE_URL}/.json`);
    if (!response.ok) throw new Error();
    dbSource = await response.json();
  } catch (error) {
    console.warn("Failed to fetch databases, using local fallback data.");
    dbSource = FALLBACK_DATA;
  }
  
  const databases = dbSource.databases || {};
  const dbNames = Object.keys(databases).filter(name => name !== '_internal');
  
  return dbNames
    .map(name => {
      const rawPath = databases[name].path || `/${name.replace(/\+/g, '~2B')}`;
      const pathValue = rawPath.startsWith('/') ? rawPath.substring(1) : rawPath;
      
      return {
        name: pathValue,
        displayName: name.replace('_matches', '').replace(/\+/g, '+')
      };
    })
    .sort((a, b) => b.name.localeCompare(a.name));
}

export async function fetchMaps(season: string): Promise<string[]> {
  try {
    const response = await fetch(`${BASE_URL}/${season}/-/query.json?sql=SELECT%0D%0A++DISTINCT%28map%29+as+Map%0D%0AFROM%0D%0A++matches%0D%0AWHERE%0D%0A++map+NOT+IN+%28%0D%0A++++%27bloontonium_mines%27%2C%0D%0A++++%27docks%27%2C%0D%0A++++%27in_the_wall%27%2C%0D%0A++++%27island_base%27%2C%0D%0A++++%27thin_ice%27%0D%0A++%29`);
    if (!response.ok) throw new Error();
    const data = await response.json();
    
    if (data && data.rows) {
      return data.rows.map((row: any) => row.Map);
    }
    return [];
  } catch (error) {
    console.error(`Failed to fetch maps for season ${season}:`, error);
    return [];
  }
}
