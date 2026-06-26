import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import datasets from "../data/datasets.json";

import icon2x from "leaflet/dist/images/marker-icon-2x.png";
import icon from "leaflet/dist/images/marker-icon.png";
import shadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: icon2x,
  iconUrl: icon,
  shadowUrl: shadow,
});
const position = [-14.235, -51.9253];

// componente responsável pelo movimento do mapa
function FlyToLocation({ selectedLocation }) {
  const map = useMap();

  useEffect(() => {
    if (selectedLocation) {
      map.flyTo([selectedLocation.lat, selectedLocation.lng], 12, {
        duration: 1.5,
      });
    }
  }, [selectedLocation, map]);

  return null;
}

const Mapa = ({ selectedLocation }) => {
  return (
    <div className="relative h-screen w-full">
      <MapContainer
        center={position}
        zoom={5}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {datasets.map((data) => (
          <Marker key={data.name} position={data.coords}>
            <Popup className="custom-popup">
              <div className="flex flex-col gap-2 min-w-[200px]">
                <h3 className="text-3xl font-bold text-gray-800">
                  {data.name}
                </h3>

                <a
                  href={data.links.zenodo}
                  target="_blank"
                  rel="noreferrer"
                  className=" text-2xl text-blue-600 hover:text-blue-800 underline transition"
                >
                  🔗 Zenodo
                </a>

                <a
                  href={data.links.paper}
                  target="_blank"
                  rel="noreferrer"
                  className=" text-2xl text-green-600 hover:text-green-800 underline transition"
                >
                  📄 Paper
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
        <FlyToLocation selectedLocation={selectedLocation} />
      </MapContainer>
    </div>
  );
};

export default Mapa;
