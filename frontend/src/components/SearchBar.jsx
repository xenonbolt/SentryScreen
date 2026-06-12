import React from 'react';
import { Search, Loader2 } from 'lucide-react';

export default function SearchBar({ onSearch, isSearching }) {
  const [query, setQuery] = React.useState('Nexum Capital Partners');
  const [useLiveWeb, setUseLiveWeb] = React.useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isSearching) {
      onSearch(query.trim(), useLiveWeb);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-2xl mx-auto">
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none text-slate-400 group-focus-within:text-indigo-400 transition-colors">
          <Search size={20} />
        </div>
        <input
          type="text"
          className="input pl-11 pr-32 py-4 text-lg shadow-xl shadow-slate-900/50"
          placeholder="Enter company or person name (e.g., Viktor Dragan)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isSearching}
        />
        <div className="absolute inset-y-0 right-2 flex items-center">
          <button
            type="submit"
            disabled={!query.trim() || isSearching}
            className="btn-primary py-2 px-6"
          >
            {isSearching ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              'Screen Entity'
            )}
          </button>
        </div>
      </div>
      </div>
      <div className="mt-3 flex items-center justify-center gap-2 text-sm text-slate-400">
        <label className="flex items-center gap-2 cursor-pointer hover:text-slate-300 transition-colors">
          <input 
            type="checkbox" 
            className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-indigo-500 focus:ring-indigo-500/50"
            checked={useLiveWeb}
            onChange={(e) => setUseLiveWeb(e.target.checked)}
            disabled={isSearching}
          />
          Enable Live Web Scraping (Real-time Search)
        </label>
      </div>
    </form>
  );
}
