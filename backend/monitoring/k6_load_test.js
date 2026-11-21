import http from 'k6/http';
import { check, sleep } from 'k6';

// k6 Load & Drift Traffic Simulation Configuration
export const options = {
  stages: [
    { duration: '15s', target: 10 }, // Ramp up to 10 virtual users
    { duration: '30s', target: 20 }, // Maintain 20 users hitting inference
    { duration: '10s', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<50'], // 95% of requests must complete under 50ms
    http_req_failed: ['rate<0.01'],  // Error rate under 1%
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
  // Simulate continuous incoming terrain survey readings (with occasional altitude spikes to trigger drift)
  const isDriftBatch = Math.random() < 0.25; // 25% chance of simulated elevation drift

  const payload = JSON.stringify({
    Elevation: isDriftBatch ? 3600.0 + Math.random() * 200 : 2600.0 + Math.random() * 300,
    Aspect: Math.floor(Math.random() * 360),
    Slope: Math.floor(Math.random() * 30),
    Horizontal_Distance_To_Hydrology: Math.floor(Math.random() * 300),
    Vertical_Distance_To_Hydrology: Math.floor(Math.random() * 50),
    Horizontal_Distance_To_Roadways: Math.floor(Math.random() * 2000),
    Horizontal_Distance_To_Fire_Points: Math.floor(Math.random() * 3000),
    Hillshade_9am: 200 + Math.floor(Math.random() * 40),
    Hillshade_Noon: 220 + Math.floor(Math.random() * 25),
    Hillshade_3pm: 140 + Math.floor(Math.random() * 30),
    Wilderness_Area: Math.floor(Math.random() * 4) + 1,
    Soil_Type: Math.floor(Math.random() * 40) + 1,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(`${BASE_URL}/predict`, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has cover_type_id': (r) => JSON.parse(r.body).cover_type_id !== undefined,
    'latency under 20ms': (r) => r.timings.duration < 20,
  });

  sleep(0.1);
}
