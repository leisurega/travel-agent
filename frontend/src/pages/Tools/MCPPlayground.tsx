import React, { useState } from 'react';
import api from '../../services/api';

const MCPPlayground: React.FC = () => {
  const [query, setQuery] = useState('');
  const [params, setParams] = useState<Record<string, any>>({});
  const [mode, setMode] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const submit = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await api.mcpIntentExecute({ query, params, mode: mode || undefined });
      setResult(res);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || '请求失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-3xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">MCP Playground</h1>
      <div className="space-y-2">
        <label className="block text-sm">Query</label>
        <input className="w-full border rounded px-3 py-2" value={query} onChange={e => setQuery(e.target.value)} placeholder="查询杭州未来3天的天气预报 或 规划一条从滨江到西湖的bike route骑行路线" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm">City</label>
          <input className="w-full border rounded px-3 py-2" onChange={e => setParams(p => ({ ...p, city: e.target.value || undefined }))} />
        </div>
        <div>
          <label className="block text-sm">Days</label>
          <input className="w-full border rounded px-3 py-2" type="number" onChange={e => setParams(p => ({ ...p, days: e.target.value ? Number(e.target.value) : undefined }))} />
        </div>
        <div>
          <label className="block text-sm">Origin</label>
          <input className="w-full border rounded px-3 py-2" onChange={e => setParams(p => ({ ...p, origin: e.target.value || undefined }))} />
        </div>
        <div>
          <label className="block text-sm">Destination</label>
          <input className="w-full border rounded px-3 py-2" onChange={e => setParams(p => ({ ...p, destination: e.target.value || undefined }))} />
        </div>
      </div>
      <div className="space-y-2">
        <label className="block text-sm">Mode (可选)</label>
        <select className="border rounded px-3 py-2" value={mode} onChange={e => setMode(e.target.value)}>
          <option value="">自动识别</option>
          <option value="weather_current">weather_current</option>
          <option value="weather_forecast">weather_forecast</option>
        </select>
      </div>
      <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={submit} disabled={loading}>
        {loading ? '执行中...' : '执行'}
      </button>
      {error && <div className="text-red-600">{error}</div>}
      {result && (
        <pre className="bg-gray-100 p-3 rounded overflow-auto text-sm">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
};

export default MCPPlayground;


