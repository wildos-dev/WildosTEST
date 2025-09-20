import * as React from "react";


interface HeaderProps {
    start?: React.ReactNode;
    center?: React.ReactNode;
    end?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ start, center, end }) => (
    <header className="h-[2.75rem] sm:h-[3.5rem] border-b border-slate-700/50">
        <div className="flex flex-row justify-between justify-items-stretch items-center lg:grid grid-cols-3 p-1 px-3 sm:px-6 w-full h-full bg-slate-900/95 backdrop-blur-sm border-b border-slate-800/50">
            <div className="flex flex-row gap-2 sm:gap-3 justify-center-start justify-start items-center">
                {start}
            </div>
            <div className="justify-center justify-self-center hidden min-[480px]:block">
                {center}
            </div>
            <div className="flex flex-row gap-2 sm:gap-3 h-10 justify-end justify-self-end items-center">
                {end}
            </div>
        </div>
    </header>
);
