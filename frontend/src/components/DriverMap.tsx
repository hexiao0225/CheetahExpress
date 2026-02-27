import {
  APIProvider,
  Map,
  AdvancedMarker,
  Pin,
  useMap,
  useMapsLibrary,
} from "@vis.gl/react-google-maps";
import { useEffect, useState } from "react";

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

interface RouteSummary {
  etaMinutes: number;
  distanceKm: number;
}

function RouteOverlay({
  origin,
  pickup,
  dropoff,
  onSummary,
}: {
  origin: { lat: number; lng: number };
  pickup?: { lat: number; lng: number };
  dropoff?: { lat: number; lng: number };
  onSummary: (summary: RouteSummary | null) => void;
}) {
  const map = useMap();
  const routesLib = useMapsLibrary("routes");

  useEffect(() => {
    if (!map || !routesLib || (!pickup && !dropoff)) {
      onSummary(null);
      return;
    }

    const service = new routesLib.DirectionsService();
    const renderer = new routesLib.DirectionsRenderer({
      map,
      suppressMarkers: true,
      polylineOptions: {
        strokeColor: "#2563eb",
        strokeOpacity: 0.9,
        strokeWeight: 6,
      },
    });

    const destination = dropoff || pickup;
    const waypoints =
      pickup && dropoff ? [{ location: pickup, stopover: true }] : undefined;

    if (!destination) {
      renderer.setMap(null);
      onSummary(null);
      return;
    }

    service.route(
      {
        origin,
        destination,
        waypoints,
        travelMode: routesLib.TravelMode.DRIVING,
      },
      (result: any, status: any) => {
        if (status !== "OK" || !result?.routes?.[0]) {
          onSummary(null);
          return;
        }

        renderer.setDirections(result);
        const route = result.routes[0];
        if (route.bounds) {
          map.fitBounds(route.bounds, 80);
        }

        const totals = route.legs?.reduce(
          (acc: { duration: number; distance: number }, leg: any) => {
            return {
              duration: acc.duration + (leg.duration?.value || 0),
              distance: acc.distance + (leg.distance?.value || 0),
            };
          },
          { duration: 0, distance: 0 },
        );

        if (!totals) {
          onSummary(null);
          return;
        }

        onSummary({
          etaMinutes: totals.duration / 60,
          distanceKm: totals.distance / 1000,
        });
      },
    );

    return () => {
      renderer.setMap(null);
    };
  }, [map, routesLib, origin, pickup, dropoff, onSummary]);

  return null;
}

export default function DriverMap({
  driverLocation,
  pickupLocation,
  dropoffLocation,
}: DriverMapProps) {
  const [routeSummary, setRouteSummary] = useState<RouteSummary | null>(null);

  const center = {
    lat: driverLocation.latitude,
    lng: driverLocation.longitude,
  };

  const apiKey =
    (import.meta as any).env?.VITE_GOOGLE_MAPS_API_KEY ||
    "YOUR_GOOGLE_MAPS_API_KEY";

  return (
    <APIProvider apiKey={apiKey} libraries={["routes"]}>
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

          <RouteOverlay
            origin={center}
            pickup={
              pickupLocation
                ? {
                    lat: pickupLocation.latitude,
                    lng: pickupLocation.longitude,
                  }
                : undefined
            }
            dropoff={
              dropoffLocation
                ? {
                    lat: dropoffLocation.latitude,
                    lng: dropoffLocation.longitude,
                  }
                : undefined
            }
            onSummary={setRouteSummary}
          />
        </Map>
      </div>

      {routeSummary && (
        <div className="mt-3 p-3 rounded-lg bg-blue-50 border border-blue-200 flex flex-wrap gap-4 text-sm">
          <p className="text-blue-800">
            <span className="font-semibold">Estimated Time:</span>{" "}
            {routeSummary.etaMinutes.toFixed(0)} min
          </p>
          <p className="text-blue-800">
            <span className="font-semibold">Trip Route Distance:</span>{" "}
            {routeSummary.distanceKm.toFixed(2)} km
          </p>
        </div>
      )}

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
