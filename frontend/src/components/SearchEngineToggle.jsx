import React from 'react';

const SearchEngineToggle = ({ value, onChange }) => {
  const isGoogle = value === 'google';

  return (
    <div 
      className="relative flex items-center w-[120px] h-9 bg-[#080b12] border border-slate-700/60 rounded-full cursor-pointer p-1 shadow-inner select-none overflow-hidden group"
      onClick={() => onChange(isGoogle ? 'duckduckgo' : 'google')}
    >
      {/* Background active pill */}
      <div 
        className={`absolute w-[54px] h-7 rounded-full shadow-lg transition-all duration-400 ease-[cubic-bezier(0.34,1.56,0.64,1)] ${
          isGoogle 
            ? 'translate-x-[56px] bg-gradient-to-tr from-blue-600 to-cyan-400' 
            : 'translate-x-0 bg-gradient-to-tr from-amber-600 to-orange-400'
        }`}
      />
      
      {/* Icons container */}
      <div className="relative z-10 w-full flex justify-between px-[14px] pointer-events-none">
        
        {/* DuckDuckGo Icon */}
        <div className={`flex items-center justify-center transition-colors duration-300 font-black tracking-tighter text-[13px] ${!isGoogle ? 'text-white' : 'text-slate-500 group-hover:text-slate-400'}`}>
          DDG
        </div>
        
        {/* Google Icon */}
        <div className={`flex items-center justify-center transition-colors duration-300 font-black tracking-tight text-[14px] ${isGoogle ? 'text-white' : 'text-slate-500 group-hover:text-slate-400'}`}>
          G
        </div>

      </div>
    </div>
  );
};

export default SearchEngineToggle;
