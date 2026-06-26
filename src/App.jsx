import Mapa from "./components/mapa";
import DataCard from "./components/daracard";
import { useState } from "react";
import datasets from "./data/datasets.json";

function App() {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [open, setOpen] = useState(false);

  return (
    <div className="h-screen w-screen flex flex-col md:flex-row bg-gray-950 text-white">
      {/* HEADER MOBILE */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900">
        <div>
          <p className="font-semibold text-lg">
            Landslide Open Datasets - Brazil
          </p>
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="px-3 py-1 bg-gray-800 rounded-lg text-sm"
        >
          {open ? "Fechar" : "Lista"}
        </button>
      </div>

      {/* SIDEBAR */}
      <aside
        className={`
          bg-gray-900 border-r border-gray-800 flex flex-col
          md:w-[22%] w-full
          ${open ? "block" : "hidden"} md:flex
        `}
      >
        {/* HEADER DESKTOP */}
        <div className="hidden md:block px-6 py-6 border-b border-gray-800">
          <p className="font-semibold text-3xl leading-snug">
            Landslide Open Datasets - Brazil
          </p>
        </div>

        {/* LISTA */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {[...datasets]
            .sort((a, b) => b.year - a.year)
            .map((item) => (
              <DataCard
                key={item.name}
                location={item.location}
                authors={item.authors}
                year={item.year}
                onClick={
                  item.coords
                    ? () => {
                        setSelectedLocation(item.coords);
                        setOpen(false); // fecha no mobile ao clicar
                      }
                    : undefined
                }
              />
            ))}
        </div>
      </aside>

      {/* MAPA */}
      <main className="flex-1 flex flex-col">
        <div className="hidden md:flex h-14 border-b border-gray-800 bg-gray-900 items-center px-4" />

        <div className="flex-1">
          <Mapa selectedLocation={selectedLocation} />
        </div>
      </main>
    </div>
  );
}

export default App;
