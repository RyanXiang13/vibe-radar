import React, { useState, useEffect, useRef, useMemo } from 'react';
import Map, { Marker, NavigationControl } from 'react-map-gl';
import { Coffee, Search, Zap, Plug, Volume2, Wifi, Moon, Sun, Clock, Users, ExternalLink, Armchair, X, Laptop, MessageCircle, Heart, Utensils } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Analytics } from '@vercel/analytics/react';
import { fetchCafes } from './api';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
// Grab the key from Vercel env variables
const GOOGLE_KEY = import.meta.env.VITE_GMAPS_KEY;

// --- CONFIG: COLOR SYSTEM ---
// --- CONFIG: COLOR SYSTEM & SORTING ---
const TAG_CONFIG = {
  quiet: {
    label: 'Quiet', icon: <Volume2 size={12} />,
    color: 'emerald', bg: 'bg-emerald-100', text: 'text-emerald-700', darkBg: 'dark:bg-emerald-900/40', darkText: 'dark:text-emerald-400', border: 'border-emerald-200 dark:border-emerald-800',
    levels: { 'Quiet': 3, 'Moderate': 2, 'Loud': 1 }, // Higher = Quieter (Better)
    map: { 'Quiet': 'Silent', 'Moderate': 'Moderate', 'Loud': 'Loud' }
  },
  power: {
    label: 'Plugs', icon: <Plug size={12} />,
    color: 'amber', bg: 'bg-amber-100', text: 'text-amber-700', darkBg: 'dark:bg-amber-900/40', darkText: 'dark:text-amber-400', border: 'border-amber-200 dark:border-amber-800',
    levels: { 'Many': 3, 'Scarce': 2, 'None': 1 }, // Higher = More Plugs
    map: { 'Many': 'Many', 'Scarce': 'Moderate', 'None': 'Little/None' }
  },
  late: {
    label: 'Late', icon: <Moon size={12} />,
    color: 'indigo', bg: 'bg-indigo-100', text: 'text-indigo-700', darkBg: 'dark:bg-indigo-900/40', darkText: 'dark:text-indigo-400', border: 'border-indigo-200 dark:border-indigo-800',
    levels: { true: 1, false: 0 },
    map: { true: 'Open Late' }
  },
  food: {
    label: 'Food', icon: <Utensils size={12} />,
    color: 'orange', bg: 'bg-orange-100', text: 'text-orange-700', darkBg: 'dark:bg-orange-900/40', darkText: 'dark:text-orange-400', border: 'border-orange-200 dark:border-orange-800',
    levels: { 'Full Meals': 3, 'Pastries': 2, 'Coffee Only': 1 }, // Proxy for "Great" -> "Moderate"
    map: { 'Full Meals': 'Great Food', 'Pastries': 'Good Food', 'Coffee Only': 'Mod. Food' }
  },
  wifi: {
    label: 'Wifi', icon: <Wifi size={12} />,
    color: 'blue', bg: 'bg-blue-100', text: 'text-blue-700', darkBg: 'dark:bg-blue-900/40', darkText: 'dark:text-blue-400', border: 'border-blue-200 dark:border-blue-800',
    levels: { 'Fast': 3, 'Spotty': 2, 'None': 1 },
    map: { 'Fast': 'Good Wifi', 'Spotty': 'Mod. Wifi', 'None': 'Poor Wifi' }
  },
  group: {
    label: 'Groups', icon: <Users size={12} />,
    color: 'purple', bg: 'bg-purple-100', text: 'text-purple-700', darkBg: 'dark:bg-purple-900/40', darkText: 'dark:text-purple-400', border: 'border-purple-200 dark:border-purple-800',
    levels: { 'Good for Groups': 3, 'Best for Pairs': 2, 'Solo Only': 1 }, // Higher = Bigger Groups
    map: { 'Good for Groups': '> 5 ppl', 'Best for Pairs': '3-4 ppl', 'Solo Only': '1-2 ppl' }
  },
};

function App() {
  // --- STATE ---
  // Default: Downtown Toronto
  const DEFAULT_LOC = { lat: 43.6532, lng: -79.3832 };

  const [viewState, setViewState] = useState({ latitude: DEFAULT_LOC.lat, longitude: DEFAULT_LOC.lng, zoom: 13 });
  const [userLocation, setUserLocation] = useState({ latitude: DEFAULT_LOC.lat, longitude: DEFAULT_LOC.lng });
  const [cafes, setCafes] = useState([]);
  const [selectedCafe, setSelectedCafe] = useState(null);

  // --- GLOBAL THEME STATE ---
  const [isDarkMode, setIsDarkMode] = useState(false);

  const [activePurpose, setActivePurpose] = useState('all');
  const [activePreferences, setActivePreferences] = useState([]);

  const searchInputRef = useRef(null);
  const mapRef = useRef(null);

  // Load cafes based on the PIN location (User's "Home Base"), not just the camera center
  // Actually, typically we want to load based on where the user is looking, but for "Vibe Radar" 
  // usually it searches around the point of interest. 
  // Let's stick to loading around the USER LOCATION (the pin).
  const loadCafes = async (lat, lng) => { setCafes(await fetchCafes(lat, lng)); };
  useEffect(() => { loadCafes(userLocation.latitude, userLocation.longitude); }, []);

  // Force HTML class toggle for Tailwind Dark Mode
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // --- FIX START: ROBUST GOOGLE MAPS LOADER ---
  useEffect(() => {
    const initAutocomplete = () => {
      if (!searchInputRef.current || !window.google) return;

      const ac = new window.google.maps.places.Autocomplete(searchInputRef.current, {
        types: ['geocode'],
        fields: ['geometry']
      });

      ac.addListener('place_changed', () => {
        const place = ac.getPlace();
        if (!place.geometry) return;
        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();

        // Update BOTH the camera and the "You are Here" pin
        setViewState({ latitude: lat, longitude: lng, zoom: 14 });
        setUserLocation({ latitude: lat, longitude: lng });

        loadCafes(lat, lng);
        setSelectedCafe(null);
      });
    };

    if (!window.google) {
      // Create script tag ONLY if it's missing
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_KEY}&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = initAutocomplete; // Run our setup once loaded
      document.head.appendChild(script);
    } else {
      // If it's already there (e.g. from a previous navigation), just run setup
      initAutocomplete();
    }
  }, []);
  // --- FIX END ---

  const togglePreference = (id) => {
    if (activePreferences.includes(id)) {
      setActivePreferences(activePreferences.filter(p => p !== id));
    } else {
      setActivePreferences([...activePreferences, id]);
    }
  };

  const filtered = useMemo(() => {
    let result = cafes.filter(c => {
      if (!c.vibes) return false;
      // Purpose Logic
      if (activePurpose !== 'all') {
        const purposeMap = {
          'study': (v) => v.best_for?.includes('Study') || v.outlets_level === 'Many',
          'social': (v) => v.best_for?.includes('Social') || v.noise_level === 'Moderate',
          'group': (v) => v.best_for?.includes('Group Work') || v.group_suitability === 'Good for Groups',
          'date': (v) => v.best_for?.includes('Date') || v.comfort_level === 'Cozy'
        };
        if (purposeMap[activePurpose] && !purposeMap[activePurpose](c.vibes)) return false;
      }
      return true;
    });

    // --- SORTING LOGIC ---
    // If a preference is active, sort by it. If multiple, sort by the LAST selected one (primary sort).
    if (activePreferences.length > 0) {
      const primaryPref = activePreferences[activePreferences.length - 1]; // Sort by most recent click
      const config = TAG_CONFIG[primaryPref];

      if (config && config.levels) {
        result.sort((a, b) => {
          // Get Raw Values
          const valA = a.vibes?.[getVibeKey(primaryPref)];
          const valB = b.vibes?.[getVibeKey(primaryPref)];

          // Get Score (Default to 0)
          const scoreA = config.levels[valA] || 0;
          const scoreB = config.levels[valB] || 0;

          return scoreB - scoreA; // Descending (Best first)
        });
      }
    }

    return result;
  }, [cafes, activePurpose, activePreferences]);

  // Helper to map Pref ID to DB Column Key
  const getVibeKey = (id) => {
    if (id === 'quiet') return 'noise_level';
    if (id === 'power') return 'outlets_level';
    if (id === 'late') return 'is_late_night';
    if (id === 'food') return 'food_type';
    if (id === 'wifi') return 'wifi_quality';
    if (id === 'group') return 'group_suitability';
    return id;
  };

  const flyToCafe = (c) => { setSelectedCafe(c); mapRef.current?.flyTo({ center: [c.lng, c.lat], zoom: 16 }); };
  const getMapsUrl = (c) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(c.name + " " + c.address)}`;

  return (
    <div className={`${isDarkMode ? 'dark' : ''} flex h-screen w-screen font-sans overflow-hidden relative bg-slate-200 dark:bg-slate-950`}>

      {/* SIDEBAR */}
      <div className="w-full md:w-[400px] h-full flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shadow-xl z-20 flex-shrink-0 transition-colors duration-300">

        {/* HEADER */}
        <div className="flex-none px-5 py-5 bg-white dark:bg-slate-900 shadow-sm z-20 border-b border-slate-100 dark:border-slate-800 transition-colors">

          {/* LOGO AREA */}
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              <div className="bg-indigo-600 p-2 rounded-lg text-white shadow-md shadow-indigo-500/20">
                <Coffee size={20} strokeWidth={2.5} />
              </div>
              <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Vibe Radar</h1>
            </div>
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-yellow-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all border border-transparent dark:border-slate-700">
              {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </div>

          {/* Search */}
          <div className="relative group mb-5">
            <Search className="absolute left-3 top-3 text-slate-400 w-5 h-5" />
            <input ref={searchInputRef} placeholder="Find your spot..."
              className="w-full bg-slate-100 dark:bg-slate-800 rounded-xl py-3 pl-10 outline-none focus:ring-2 focus:ring-indigo-500 font-bold text-slate-700 dark:text-slate-200 placeholder:text-slate-400 transition-colors" />
          </div>

          {/* Purpose Filters (NOW WRAPPED/STACKED) */}
          <div className="mb-4">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">What are you doing?</h4>
            <div className="flex flex-wrap gap-2"> {/* CHANGED to flex-wrap */}
              {[
                { id: 'all', l: 'All', i: null },
                { id: 'study', l: 'Focus', i: <Laptop size={12} /> },
                { id: 'social', l: 'Chat', i: <MessageCircle size={12} /> },
                { id: 'group', l: 'Group', i: <Users size={12} /> },
                { id: 'date', l: 'Date', i: <Heart size={12} /> }
              ].map(p => (
                <button key={p.id} onClick={() => setActivePurpose(p.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap border
                        ${activePurpose === p.id
                      ? 'bg-slate-800 dark:bg-indigo-600 text-white border-slate-800 dark:border-indigo-600 shadow-md'
                      : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-100 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'}`}>
                  {p.i}{p.l}
                </button>
              ))}
            </div>
          </div>

          {/* Preference Filters (WRAPPED/STACKED) */}
          <div>
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Preferences</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(TAG_CONFIG).map(([key, config]) => {
                const isActive = activePreferences.includes(key);
                return (
                  <button key={key} onClick={() => togglePreference(key)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all border
                            ${isActive
                        ? `${config.bg} ${config.text} ${config.border} ring-1 ring-offset-1 dark:ring-offset-slate-900 ${config.darkBg} ${config.darkText}`
                        : 'bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'}`}>
                    {config.icon}{config.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* LIST */}
        <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950 p-4 space-y-3 transition-colors">
          {filtered.map(c => (
            <div key={c.id} onClick={() => flyToCafe(c)}
              className={`p-4 rounded-2xl border cursor-pointer hover:shadow-lg transition-all dark:hover:border-indigo-500
                ${selectedCafe?.id === c.id
                  ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-500 ring-1 ring-indigo-500'
                  : 'bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800'}`}>

              <div className="flex justify-between mb-1">
                <h3 className={`font-bold line-clamp-1 ${selectedCafe?.id === c.id ? 'text-indigo-700 dark:text-indigo-400' : 'text-slate-800 dark:text-slate-200'}`}>{c.name}</h3>
                <div className="flex items-center gap-1">
                  {c.distance_km && <span className="text-xs font-bold bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-400 px-2 py-1 rounded h-fit">{c.distance_km} km</span>}
                  {c.rating && <span className="text-xs font-bold bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-400 px-2 py-1 rounded h-fit">★ {c.rating}</span>}
                </div>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-2 leading-relaxed">{c.vibes?.summary}</p>
              {/* EXPANDED TAGS DISPLAY (Only Top Tier) */}
              <div className="flex flex-wrap gap-2 mt-2">
                {Object.entries(TAG_CONFIG).map(([key, config]) => {
                  const rawVal = c.vibes?.[getVibeKey(key)];
                  if (!rawVal) return null;

                  // Logic: Only show if it matches the "Best" level (3) or is boolean true
                  // This keeps the card clean. Full details are in the profile.
                  const isTopTier = (config.levels && config.levels[rawVal] === 3) || rawVal === true;

                  if (!isTopTier) return null;

                  let label = config.map?.[rawVal] || rawVal;
                  if (rawVal === true) label = config.map?.[true];

                  return (
                    <MiniTag key={key} config={config} label={label} />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* DETAIL PANEL */}
      <AnimatePresence>
        {selectedCafe && (
          <motion.div initial={{ x: -400, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: -400, opacity: 0 }}
            className="absolute left-0 md:left-[400px] top-0 h-full w-full md:w-[400px] bg-white dark:bg-slate-900 shadow-2xl z-30 border-l border-slate-200 dark:border-slate-800 overflow-y-auto transition-colors">

            <div className="sticky top-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur z-20 px-4 py-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
              <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">PROFILE</div>
              <button onClick={() => setSelectedCafe(null)} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-500"><X size={20} /></button>
            </div>

            <div className="p-6 pb-20">
              <h2 className="text-3xl font-black mb-1 text-slate-900 dark:text-white leading-tight">{selectedCafe.name}</h2>
              <div className="flex justify-between items-start mb-6">
                <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">{selectedCafe.address}</p>
                {selectedCafe.distance_km && (
                  <span className="shrink-0 text-xs font-bold bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-2 py-1 rounded-md">
                    {selectedCafe.distance_km} km away
                  </span>
                )}
              </div>

              {selectedCafe.vibes?.best_for && (
                <div className="flex flex-wrap gap-2 mb-6">
                  {selectedCafe.vibes.best_for.map(tag => (
                    <span key={tag} className="px-3 py-1 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold rounded-full shadow-md">{tag}</span>
                  ))}
                </div>
              )}

              <div className="mb-6 bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700">
                <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">Vibe Check</h4>
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed italic">"{selectedCafe.vibes?.summary}"</p>
              </div>

              {/* FULL PREFERENCES GRID */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                <Badge config={TAG_CONFIG.wifi} val={selectedCafe.vibes?.wifi_quality} />
                <Badge config={TAG_CONFIG.power} val={selectedCafe.vibes?.outlets_level} />
                <Badge config={TAG_CONFIG.quiet} val={selectedCafe.vibes?.noise_level} />
                <Badge config={TAG_CONFIG.food} val={selectedCafe.vibes?.food_type} />
                <Badge config={TAG_CONFIG.group} val={selectedCafe.vibes?.group_suitability === 'Good for Groups' ? "Good" : (selectedCafe.vibes?.group_suitability === 'Best for Pairs' ? "Pairs" : "Solo")} />
                <Badge config={TAG_CONFIG.late} val={selectedCafe.vibes?.is_late_night ? "Yes" : "No"} />
              </div>

              <div className="space-y-4 mb-8">
                <InfoRow icon={<Clock size={16} />} label="Time Limit?" val={selectedCafe.vibes?.time_limit_status === 'Strict' ? "⚠️ Strict Limits" : "✅ Chill / None"} />
                <InfoRow icon={<Armchair size={16} />} label="Seating Tip" val={`"${selectedCafe.vibes?.seating_tip || "Arrive early."}"`} />
                <InfoRow icon={<Users size={16} />} label="Crowd Vibe" val={`"${selectedCafe.vibes?.busyness_info || "Steady."}"`} />
              </div>

              <a href={getMapsUrl(selectedCafe)} target="_blank" rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 py-4 rounded-xl font-bold shadow-lg hover:bg-slate-800 dark:hover:bg-slate-200 transition-all">
                <ExternalLink size={18} /> Open in Google Maps
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* MAP */}
      <div className="flex-1 h-full relative z-10 bg-slate-200 dark:bg-slate-950 transition-colors">
        <Map ref={mapRef} {...viewState} onMove={e => setViewState(e.viewState)} style={{ width: '100%', height: '100%' }}
          mapStyle={isDarkMode ? "mapbox://styles/mapbox/dark-v11" : "mapbox://styles/mapbox/streets-v12"}
          mapboxAccessToken={MAPBOX_TOKEN}>
          <NavigationControl position="bottom-right" showCompass={false} />

          {/* USER LOCATION PIN (Now bound to userLocation, not viewState) */}
          <Marker latitude={userLocation.latitude} longitude={userLocation.longitude}>
            <div className="relative flex items-center justify-center w-8 h-8 group">
              <span className="absolute w-8 h-8 bg-blue-500 rounded-full opacity-30 animate-ping"></span>
              <div className="relative w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-xl z-20"></div>
              <div className="absolute -top-8 bg-slate-900 text-white text-[10px] font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-30">
                You are here
              </div>
            </div>
          </Marker>

          {filtered.map(c => (
            <Marker key={c.id} latitude={c.lat} longitude={c.lng} onClick={e => { e.originalEvent.stopPropagation(); flyToCafe(c) }}>
              <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center shadow-lg hover:scale-110 transition-transform cursor-pointer
                ${selectedCafe?.id === c.id
                  ? 'bg-indigo-600 border-white text-white scale-110'
                  : 'bg-white dark:bg-slate-800 border-indigo-100 dark:border-slate-600 text-indigo-600 dark:text-indigo-400'}`}>
                {c.vibes?.outlets_level === 'Many' ? <Plug size={14} /> : <Coffee size={14} />}
              </div>
            </Marker>
          ))}
        </Map>
      </div>
      <Analytics />
      <style>{`.scrollbar-hide::-webkit-scrollbar { display: none; }`}</style>
    </div>
  );
}

// Sub-Components
const MiniTag = ({ config, label }) => (
  <span className={`px-1.5 py-0.5 rounded flex gap-1 items-center text-[10px] font-bold ${config.bg} ${config.text} ${config.darkBg} ${config.darkText} border ${config.border}`}>
    {config.icon} {label || config.label}
  </span>
);

const Badge = ({ config, val }) => (
  <div className={`p-3 rounded-xl border flex flex-col items-center text-center ${config.bg} ${config.border} ${config.darkBg} transition-colors`}>
    <div className={`${config.text} ${config.darkText} mb-1`}>{config.icon}</div>
    <div className="text-[10px] font-bold uppercase text-slate-500 dark:text-slate-400">{config.label}</div>
    <div className="font-bold text-slate-800 dark:text-slate-200 text-sm line-clamp-1">{val || "-"}</div>
  </div>
);

const InfoRow = ({ icon, label, val }) => (
  <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700 transition-colors">
    <h4 className="font-bold text-sm mb-1 flex gap-2 items-center text-slate-700 dark:text-slate-300">{icon} {label}</h4>
    <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">{val}</p>
  </div>
);

export default App;
