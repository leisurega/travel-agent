import React, { useState } from 'react';
import api from '../../services/api';

const WeatherTest: React.FC = () => {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testWeather = async () => {
    setLoading(true);
    try {
      const response = await api.getCurrentWeather('北京');
      console.log('API Response:', response);
      setResult(response);
    } catch (error) {
      console.error('Error:', error);
      setResult({ error: error instanceof Error ? error.message : String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h1>Weather API Test</h1>
      <button 
        onClick={testWeather} 
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        {loading ? 'Testing...' : 'Test Weather API'}
      </button>
      
      {result && (
        <div className="mt-4">
          <h2>Result:</h2>
          <pre className="bg-gray-100 p-4 rounded overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default WeatherTest;
