import {
  APIProvider,
  Map,
  AdvancedMarker,
  Pin,
} from "@vis.gl/react-google-maps";

interface DriverMapProps {
  driverLocation: {
    latitude: number;
    longitude: number;
    name: string;
    address: string;
  };
  pickupLocation?: {
    latitude: number;
    longitude: number;
    address: string;
  };
  dropoffLocation?: {
    latitude: number;
    longitude: number;
    address: string;
  };
}

export default function DriverMap({
  driverLocation,
  pickupLocation,
  dropoffLocation,
}: DriverMapProps) {
  const center = {
    lat: driverLocation.latitude,
    lng: driverLocation.longitude,
  };

  const apiKey =
    (import.meta as any).env?.VITE_GOOGLE_MAPS_API_KEY ||
    "YOUR_GOOGLE_MAPS_API_KEY";

  return (
    <APIProvider apiKey={apiKey}>
      <div className="w-full h-[400px] rounded-lg overflow-hidden border border-gray-200">
        <Map
          defaultCenter={center}
          defaultZoom={14}
          mapId="driver-tracking-map"
          gestureHandling="greedy"
        >
          {/* Driver Location - Blue Pin */}
          <AdvancedMarker position={center}>
            <Pin
              background="#2563eb"
              borderColor="#1e40af"
              glyphColor="#ffffff"
            />
          </AdvancedMarker>

          {/* Pickup Location - Green Pin */}
          {pickupLocation && (
            <AdvancedMarker
              position={{
                lat: pickupLocation.latitude,
                lng: pickupLocation.longitude,
              }}
            >
              <Pin
                background="#10b981"
                borderColor="#059669"
                glyphColor="#ffffff"
              />
            </AdvancedMarker>
          )}

          {/* Dropoff Location - Red Pin */}
          {dropoffLocation && (
            <AdvancedMarker
              position={{
                lat: dropoffLocation.latitude,
                lng: dropoffLocation.longitude,
              }}
            >
              <Pin
                background="#ef4444"
                borderColor="#dc2626"
                glyphColor="#ffffff"
              />
            </AdvancedMarker>
          )}
        </Map>
      </div>

      {/* Legend */}
      <div className="mt-4 flex gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-600"></div>
          <span className="text-gray-700">Driver: {driverLocation.name}</span>
        </div>
        {pickupLocation && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-600"></div>
            <span className="text-gray-700">Pickup</span>
          </div>
        )}
        {dropoffLocation && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-600"></div>
            <span className="text-gray-700">Dropoff</span>
          </div>
        )}
      </div>
    </APIProvider>
  );
}
