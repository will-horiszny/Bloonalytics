
export interface DatabaseInfo {
  name: string;
  displayName: string;
}

export type MapType = string;

export type StatType = 
  | 'Maps'
  | 'Heroes'
  | 'Towers'
  | 'Loadouts'
  | 'Hero Loadouts';
