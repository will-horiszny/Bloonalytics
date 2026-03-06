import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { DatabaseInfo, MapType, StatType } from './types';
import { BASE_URL, formatMapName } from './constants';
import { fetchDatabases, fetchMaps } from './services/datasetteService';

const ADVANCED_TOOLS = [
  {
    id: 'counter_loadouts',
    name: 'Counter Loadout Finder',
    description: 'Find the most effective strategies to defeat specific hero and tower combinations.',
    path: 'counter_loadouts',
    accent: 'from-amber-500 to-orange-600'
  },
  {
    id: 'win_loss_by_round',
    name: 'Survival Analysis',
    description: 'Identify the exact rounds where specific strategies tend to struggle or excel.',
    path: 'win_loss_by_round',
    accent: 'from-rose-500 to-red-600'
  },
  {
    id: 'winrate_by_round',
    name: 'Round-by-Round Meta',
    description: 'Statistical breakdown of win rates across different phases of the game.',
    path: 'winrate_by_round',
    accent: 'from-emerald-500 to-teal-600'
  }
];

const THEMATIC_MESSAGES = [
  "Analyzing Hall of Masters data...",
  "Consulting the Sun God...",
  "Calculating RBE values...",
  "Popping data bloons...",
  "Reviewing monkey strategies...",
  "Optimizing dart trajectories...",
  "Scouting the battlefield...",
  "Crunching win percentages..."
];

const App: React.FC = () => {
  const [databases, setDatabases] = useState<DatabaseInfo[]>([]);
  const [mapOptions, setMapOptions] = useState<MapType[]>(['ALL']);
  const [selectedSeason, setSelectedSeason] = useState<string>('');
  const [selectedMap, setSelectedMap] = useState<MapType>('ALL');
  const [selectedStat, setSelectedStat] = useState<StatType>('Hero Loadouts');
  const [loading, setLoading] = useState(true);
  const [isFetchingMaps, setIsFetchingMaps] = useState(false);
  const [isExploring, setIsExploring] = useState(false);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

// Reset loading state if browser back button is used (handles BFCache)
  useEffect(() => {
    const resetNavigationState = () => {
      // Use setTimeout to ensure this runs in the next event loop tick
      // This is crucial for Safari/iOS when restoring from BFCache
      setTimeout(() => {
        setIsExploring(false);
      }, 0);
    };

    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        resetNavigationState();
      } else {
        resetNavigationState();
      }
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        resetNavigationState();
      }
    };

    window.addEventListener('pageshow', handlePageShow);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('pageshow', handlePageShow);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Initial Data Fetch: Databases
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const dbs = await fetchDatabases();
      setDatabases(dbs);
      if (dbs.length > 0) {
        setSelectedSeason(dbs[0].name);
      }
      setLoading(false);
    };
    loadData();
  }, []);

// Fetch Maps when Season changes
  useEffect(() => {
    if (!selectedSeason) return;

	const loadMaps = async () => {
	setIsFetchingMaps(true);
	try {
		const fetchedMaps = await fetchMaps(selectedSeason);
	
		// Sort maps based on what the user actually sees (the display name)
		const sortedMaps = [...fetchedMaps].sort((a, b) => {
		const labelA = formatMapName(a);
		const labelB = formatMapName(b);
		return labelA.localeCompare(labelB);
		});
	
		const options = ['ALL', ...sortedMaps];
		
		setMapOptions(options);
		
		if (!options.includes(selectedMap)) {
		setSelectedMap('ALL');
		}
	} catch (error) {
		console.error("Failed to fetch maps", error);
	} finally {
		setIsFetchingMaps(false);
	}
	};

    loadMaps();
    // Removed selectedMap from dependencies to prevent unnecessary refetching
  }, [selectedSeason]);

  // Cycle thematic messages when loading
  useEffect(() => {
    if (isExploring) {
      const interval = setInterval(() => {
        setCurrentMessageIndex((prev) => (prev + 1) % THEMATIC_MESSAGES.length);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [isExploring]);

  // Define Stat Options based on Map
  const statOptions: StatType[] = useMemo(() => {
    const base: StatType[] = ['Heroes', 'Towers', 'Loadouts', 'Hero Loadouts'];
    if (selectedMap === 'ALL') {
      return ['Maps', ...base];
    }
    return base;
  }, [selectedMap]);

  // Ensure selectedStat is valid when map changes
  useEffect(() => {
    if (!statOptions.includes(selectedStat)) {
      setSelectedStat('Hero Loadouts');
    }
  }, [selectedMap, statOptions, selectedStat]);

  const generateUrl = useCallback(() => {
    if (!selectedSeason) return '#';
    
    const mapSlug = selectedMap.toLowerCase();
    const statSlug = selectedStat.toLowerCase().replace(' ', '_');
    
    return `${BASE_URL}/${selectedSeason}/${mapSlug}_${statSlug}`;
  }, [selectedSeason, selectedMap, selectedStat]);

  const handleNavigate = (url: string, e: React.MouseEvent) => {
    e.preventDefault();
    setIsExploring(true);
    // Short delay to allow the animation to be seen before browser navigation starts
    setTimeout(() => {
      window.location.href = url;
    }, 800);
  };

  const isS25Plus = selectedSeason === 's25~2B_matches' || selectedSeason.includes('s25');

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-white p-4 text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mb-6 shadow-[0_0_15px_rgba(59,130,246,0.5)]"></div>
        <h2 className="text-2xl font-bold tracking-tight mb-2">Preparing Bloonalytics</h2>
        <p className="text-slate-400 animate-pulse">Fetching latest match data...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-blue-500/30">
      <link rel="icon" type="image/webp" href="/static/favicon.webp" />
	  
	      {/* NEW BACKGROUND CONTAINER */}
    <div 
      className="fixed inset-0 z-0 opacity-60" 
      style={{ 
        backgroundImage: 'url(/static/bg.png)', 
        backgroundSize: 'cover', 
        backgroundPosition: 'center' 
      }} 
    />
      
      {/* Loading Overlay */}
      {isExploring && (
        <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-slate-950/90 backdrop-blur-xl animate-in fade-in duration-300">
          <div className="relative mb-8">
            <div className="w-24 h-24 rounded-full border-4 border-blue-500/10 border-t-blue-500 animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-12 h-12 bg-blue-600/40 rounded-full animate-pulse blur-xl"></div>
              <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
            </div>
          </div>
          <h2 className="text-3xl font-black italic uppercase tracking-tighter text-white mb-2">
            Launching Analytics
          </h2>
          <p className="text-blue-400 font-mono text-sm uppercase tracking-widest animate-pulse h-6">
            {THEMATIC_MESSAGES[currentMessageIndex]}
          </p>
        </div>
      )}

      {/* Hero Section */}
      <div className="relative w-full h-[300px] md:h-[400px] overflow-hidden flex items-center justify-center">
        
        <div className="relative z-10 text-center px-4 max-w-4xl">
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white mb-4 drop-shadow-[0_10px_20px_rgba(0,0,0,0.8)] uppercase italic">
            Bloonalytics
          </h1>
          <div className="h-1.5 w-32 bg-blue-600 mx-auto mb-6 rounded-full shadow-[0_0_20px_rgba(37,99,235,1)]"></div>
          <p className="text-lg md:text-2xl text-blue-100/90 font-medium drop-shadow-md max-w-2xl mx-auto leading-relaxed">
            The ultimate data companion for <span className="text-blue-400 font-bold">Bloons TD Battles 2</span> competitive play.
          </p>
        </div>
      </div>

      {/* Selector Card */}
      <main className="flex-grow flex flex-col items-center -mt-16 md:-mt-20 px-4 z-20 pb-20">
        <div className="w-full max-w-5xl bg-slate-900/95 backdrop-blur-2xl border border-slate-800 rounded-[2.5rem] shadow-[0_35px_60px_-15px_rgba(0,0,0,0.5)] p-8 md:p-12 mb-12">
          <div className="flex items-center justify-center space-x-3 mb-10">
            <div className="h-px bg-slate-800 flex-grow"></div>
            <h2 className="text-sm font-black uppercase tracking-[0.3em] text-slate-500">Configure View</h2>
            <div className="h-px bg-slate-800 flex-grow"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            {/* Season Selector */}
            <div className="flex flex-col space-y-3 group">
              <label htmlFor="season" className="text-xs font-bold text-blue-400/80 uppercase tracking-widest flex items-center">
                <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                Season
              </label>
              <div className="relative">
                <select
                  id="season"
                  value={selectedSeason}
                  onChange={(e) => setSelectedSeason(e.target.value)}
                  className="w-full bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-blue-500/50 rounded-2xl px-5 py-4 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none transition-all cursor-pointer shadow-inner"
                >
                  {databases.map((db) => (
                    <option key={db.name} value={db.name} className="bg-slate-900">
                      {db.displayName}
                    </option>
                  ))}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </div>
              </div>
            </div>

            {/* Map Selector */}
            <div className="flex flex-col space-y-3 group">
              <label htmlFor="map" className="text-xs font-bold text-indigo-400/80 uppercase tracking-widest flex items-center">
                <span className={`w-2 h-2 rounded-full mr-2 ${isFetchingMaps ? 'bg-slate-500 animate-pulse' : 'bg-indigo-500'}`}></span>
                Map
              </label>
              <div className="relative">
                <select
                  id="map"
                  value={selectedMap}
                  disabled={isFetchingMaps}
                  onChange={(e) => setSelectedMap(e.target.value as MapType)}
                  className={`w-full bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-indigo-500/50 rounded-2xl px-5 py-4 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500/50 appearance-none transition-all cursor-pointer shadow-inner ${isFetchingMaps ? 'opacity-50 cursor-wait' : ''}`}
                >
                  {mapOptions.map((map) => (
                    <option key={map} value={map} className="bg-slate-900">
                      {formatMapName(map)}
                    </option>
                  ))}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                  {isFetchingMaps ? (
                    <div className="w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  )}
                </div>
              </div>
            </div>

            {/* Stats Type Selector */}
            <div className="flex flex-col space-y-3 group">
              <label htmlFor="stats" className="text-xs font-bold text-purple-400/80 uppercase tracking-widest flex items-center">
                <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                Stats Category
              </label>
              <div className="relative">
                <select
                  id="stats"
                  value={selectedStat}
                  onChange={(e) => setSelectedStat(e.target.value as StatType)}
                  className="w-full bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-purple-500/50 rounded-2xl px-5 py-4 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-purple-500/50 appearance-none transition-all cursor-pointer shadow-inner"
                >
                  {statOptions.map((stat) => (
                    <option key={stat} value={stat} className="bg-slate-900">
                      {stat}
                    </option>
                  ))}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </div>
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex flex-col items-center space-y-8">
            <a
              href={generateUrl()}
              onClick={(e) => handleNavigate(generateUrl(), e)}
              className="group relative overflow-hidden px-20 py-5 bg-gradient-to-br from-blue-600 via-blue-500 to-indigo-600 text-white font-black text-2xl rounded-3xl shadow-[0_20px_40px_-15px_rgba(37,99,235,0.6)] hover:shadow-[0_25px_50px_-12px_rgba(37,99,235,0.8)] transition-all duration-500 transform hover:-translate-y-1.5 active:scale-95 flex items-center decoration-none"
            >
              <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.2)_50%,transparent_75%)] bg-[length:250%_250%] animate-[shimmer_3s_infinite] pointer-events-none"></div>
              Explore Database
              <div className="ml-3 p-1 bg-white/20 rounded-lg group-hover:bg-white/30 transition-colors">
                <svg className="w-6 h-6 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </div>
            </a>
            
            <div className="bg-slate-950/50 border border-slate-800/50 rounded-2xl px-6 py-3 flex items-center space-x-3">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <p className="text-slate-400 text-sm font-mono tracking-tight">
                Current: <span className="text-blue-400/80 ml-1">{generateUrl().replace(BASE_URL, '')}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Advanced Tools Section - Conditional for s24+ */}
        {isS25Plus && (
          <div className="w-full max-w-6xl mb-20 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex items-center mb-8 px-4">
              <div className="p-2 bg-amber-500/20 rounded-lg mr-4">
                <svg className="w-6 h-6 text-amber-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
              </div>
              <h2 className="text-3xl font-black text-white italic uppercase tracking-tight">Advanced Analytics <span className="text-amber-500 font-mono text-sm ml-2 px-2 py-1 bg-amber-500/10 rounded border border-amber-500/30">PREMIUM</span></h2>
              <div className="h-px bg-slate-800 flex-grow ml-8"></div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {ADVANCED_TOOLS.map((tool) => {
                const toolUrl = `${BASE_URL}/s25~2B_matches/${tool.path}`;
                return (
                  <a
                    key={tool.id}
                    href={toolUrl}
                    onClick={(e) => handleNavigate(toolUrl, e)}
                    className="group relative block p-8 bg-slate-900/60 border border-slate-800 rounded-3xl hover:bg-slate-800/40 hover:border-amber-500/30 transition-all duration-300"
                  >
                    <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${tool.accent} opacity-10 blur-2xl group-hover:opacity-20 transition-opacity`} ></div>
                    <h3 className="text-xl font-bold text-white mb-3 group-hover:text-amber-400 transition-colors">{tool.name}</h3>
                    <p className="text-slate-400 text-sm leading-relaxed mb-6">{tool.description}</p>
                    <div className="flex items-center text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-white transition-colors">
                      Launch Tool
                      <svg className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                    </div>
                  </a>
                );
              })}
            </div>
          </div>
        )}

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl">
          <FeatureCard 
            title="Meta Tracking" 
            description="Identify dominant hero & tower combinations before they become mainstream with data updated hourly."
            icon={<div className="p-3 bg-blue-500/10 rounded-xl"><svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg></div>}
          />
          <FeatureCard 
            title="Map Synergy" 
            description="Every map has its secrets. Filter from 700K+ matches to find the specific winning strategy for each battlefield."
            icon={<div className="p-3 bg-indigo-500/10 rounded-xl"><svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg></div>}
          />
          <FeatureCard 
            title="Advanced Analytics" 
            description="Powered by SQLite and Datasette, explore the raw data of the Hall of Masters with high-performance querying."
            icon={<div className="p-3 bg-purple-500/10 rounded-xl"><svg className="w-8 h-8 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg></div>}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-900 bg-slate-950/80 backdrop-blur-md text-slate-500 text-center">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between">
          <p className="text-sm font-medium mb-4 md:mb-0">© {new Date().getFullYear()} <span className="text-white font-bold tracking-tight">BLOONALYTICS</span></p>
          <div className="flex space-x-8 text-xs font-bold uppercase tracking-widest">
            <a href="https://datasette.io" className="hover:text-blue-400 transition-colors">Datasette</a>
            <a href="https://ninjakiwi.com" className="hover:text-blue-400 transition-colors">Ninja Kiwi</a>
          </div>
        </div>
      </footer>
      
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
};

const FeatureCard: React.FC<{ title: string; description: string; icon: React.ReactNode }> = ({ title, description, icon }) => (
  <div className="group bg-slate-900/40 p-10 rounded-[2rem] border border-slate-800/60 hover:border-slate-700/80 hover:bg-slate-900/60 transition-all duration-300 flex flex-col items-center text-center">
    <div className="mb-6 transform group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300">{icon}</div>
    <h3 className="text-xl font-black text-white mb-4 tracking-tight uppercase italic">{title}</h3>
    <p className="text-slate-400 leading-relaxed font-medium">{description}</p>
  </div>
);

export default App;
