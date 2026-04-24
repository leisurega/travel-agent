import React, { useState } from 'react';
import api from '../../services/api';

interface WeatherData {
  location: {
    name?: string;
    country?: string;
    latitude: number;
    longitude: number;
  };
  current?: {
    temperature: number;
    weathercode: number;
    time: string;
  };
  daily?: {
    time: string[];
    temperature_2m_max: number[];
    temperature_2m_min: number[];
    precipitation_sum: number[];
    weathercode: number[];
  };
}

const WeatherPage: React.FC = () => {
  const [city, setCity] = useState('');
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(false);
  const [currentWeather, setCurrentWeather] = useState<WeatherData | null>(null);
  const [forecast, setForecast] = useState<WeatherData | null>(null);
  const [error, setError] = useState<string>('');

  const getCurrentWeather = async () => {
    if (!city.trim()) {
      setError('请输入城市名称');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await api.getCurrentWeather(city);
      setCurrentWeather(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || '获取当前天气失败');
    } finally {
      setLoading(false);
    }
  };

  const getForecast = async () => {
    if (!city.trim()) {
      setError('请输入城市名称');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await api.getWeatherForecast(city, days);
      setForecast(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || '获取天气预报失败');
    } finally {
      setLoading(false);
    }
  };

  const getWeatherCodeDescription = (code: number): string => {
    const weatherCodes: { [key: number]: string } = {
      0: '晴朗',
      1: '大部分晴朗',
      2: '部分多云',
      3: '阴天',
      45: '雾',
      48: '霜雾',
      51: '小雨',
      53: '中雨',
      55: '大雨',
      61: '小雨',
      63: '中雨',
      65: '大雨',
      71: '小雪',
      73: '中雪',
      75: '大雪',
      77: '雪粒',
      80: '阵雨',
      81: '中阵雨',
      82: '强阵雨',
      85: '阵雪',
      86: '强阵雪',
      95: '雷暴',
      96: '雷暴伴小雨',
      99: '强雷暴'
    };
    return weatherCodes[code] || '未知';
  };

  const formatTemperature = (temp: number): string => {
    return `${Math.round(temp)}°C`;
  };

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">🌤️ 天气查询</h1>
        <p className="text-gray-600">查询当前天气和未来几天的天气预报</p>
      </div>

      {/* 查询表单 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">城市名称</label>
            <input
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="例如：杭州、北京、上海"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">预报天数</label>
            <input
              type="number"
              min="1"
              max="16"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
            />
          </div>
          <div className="flex items-end space-x-2">
            <button
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              onClick={getCurrentWeather}
              disabled={loading}
            >
              {loading ? '查询中...' : '当前天气'}
            </button>
            <button
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
              onClick={getForecast}
              disabled={loading}
            >
              {loading ? '查询中...' : '天气预报'}
            </button>
          </div>
        </div>
      </div>

      {/* 错误信息 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400">⚠️</span>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* 当前天气 */}
      {currentWeather && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">当前天气</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">
                {currentWeather.location.name}, {currentWeather.location.country}
              </h3>
              <p className="text-sm text-gray-500">
                坐标: {currentWeather.location.latitude.toFixed(4)}, {currentWeather.location.longitude.toFixed(4)}
              </p>
            </div>
            {currentWeather.current && (
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600 mb-2">
                  {formatTemperature(currentWeather.current.temperature)}
                </div>
                <div className="text-lg text-gray-600">
                  {getWeatherCodeDescription(currentWeather.current.weathercode)}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {new Date(currentWeather.current.time).toLocaleString('zh-CN')}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 天气预报 */}
      {forecast && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            {days}天天气预报 - {forecast.location.name}, {forecast.location.country}
          </h2>
          {forecast.daily && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {forecast.daily.time.map((date, index) => (
                <div key={date} className="bg-gray-50 rounded-lg p-4 text-center">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    {new Date(date).toLocaleDateString('zh-CN', { 
                      month: 'short', 
                      day: 'numeric',
                      weekday: 'short'
                    })}
                  </div>
                  <div className="text-2xl font-bold text-blue-600 mb-1">
                    {formatTemperature(forecast.daily!.temperature_2m_max[index])}
                  </div>
                  <div className="text-sm text-gray-500 mb-1">
                    {formatTemperature(forecast.daily!.temperature_2m_min[index])}
                  </div>
                  <div className="text-sm text-gray-600 mb-1">
                    {getWeatherCodeDescription(forecast.daily!.weathercode[index])}
                  </div>
                  {forecast.daily!.precipitation_sum[index] > 0 && (
                    <div className="text-xs text-blue-500">
                      💧 {forecast.daily!.precipitation_sum[index]}mm
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 数据源信息 */}
      {(currentWeather || forecast) && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">
            <span className="font-medium">数据源:</span> 
            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
              MCP Weather Service
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default WeatherPage;
