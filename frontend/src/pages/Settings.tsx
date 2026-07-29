import { useState, useEffect } from "react";
import { api } from "../api/client";

const PROVIDERS = [
  { value: "bailian", label: "阿里云百炼 (DashScope)" },
  { value: "deepseek", label: "DeepSeek" },
  { value: "openai", label: "OpenAI" },
];

interface SettingsData {
  provider: string;
  bailian_api_key: string;
  bailian_base_url: string;
  bailian_model: string;
  deepseek_api_key: string;
  deepseek_base_url: string;
  deepseek_model: string;
  openai_api_key: string;
  openai_base_url: string;
  openai_model: string;
}

const DEFAULT_MODELS: Record<string, string> = {
  bailian: "qwen3.5-turbo",
  deepseek: "deepseek-chat",
  openai: "gpt-4o-mini",
};

const DEFAULT_URLS: Record<string, string> = {
  bailian: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  deepseek: "https://api.deepseek.com",
  openai: "https://api.openai.com/v1",
};

import { CardSkeleton } from "../components/Skeleton";

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get<any>("/settings").then(data => {
      setSettings(data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const update = (key: string, value: string) => {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  };

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    setSaved(false);
    try {
      await api.put("/settings", settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // error surfaced by api client
    } finally {
      setSaving(false);
    }
  };

  const switchProvider = (provider: string) => {
    if (!settings) return;
    const updated = { ...settings, provider };
    // Auto-fill defaults for the new provider
    const key = provider + "_model";
    if (!(updated as any)[key]) {
      (updated as any)[key] = DEFAULT_MODELS[provider] || "";
    }
    const urlKey = provider + "_base_url";
    if (!(updated as any)[urlKey]) {
      (updated as any)[urlKey] = DEFAULT_URLS[provider] || "";
    }
    setSettings(updated);
  };

  if (loading) return <CardSkeleton count={1} />;
  if (!settings) return <div className="text-center py-12 text-slate-400">无法加载配置</div>;

  const provider = settings.provider;
  const apiKeyField = provider + "_api_key";
  const baseUrlField = provider + "_base_url";
  const modelField = provider + "_model";

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold text-slate-800 mb-6">AI 模型配置</h2>

      <div className="bg-white rounded-xl p-6 shadow-sm space-y-6">
        {/* Provider selection */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">AI 服务商</label>
          <div className="flex flex-wrap gap-2">
            {PROVIDERS.map(p => (
              <button key={p.value} onClick={() => switchProvider(p.value)}
                className={provider === p.value
                    ? "px-4 py-2 text-sm rounded-lg transition-colors bg-blue-600 text-white"
                    : "px-4 py-2 text-sm rounded-lg transition-colors bg-slate-100 text-slate-600 hover:bg-slate-200"
                }>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">API Key</label>
          <input type="password" value={(settings as any)[apiKeyField] || ""}
            onChange={e => update(apiKeyField, e.target.value)}
            placeholder={"请输入 " + PROVIDERS.find(p => p.value === provider)?.label + " API Key"}
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
          />
          <p className="text-xs text-slate-400 mt-1">已在 .env 中配置时会自动填充</p>
        </div>

        {/* Base URL */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">API 地址</label>
          <input type="text" value={(settings as any)[baseUrlField] || ""}
            onChange={e => update(baseUrlField, e.target.value)}
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
          />
        </div>

        {/* Model */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">模型名称</label>
          <input type="text" value={(settings as any)[modelField] || ""}
            onChange={e => update(modelField, e.target.value)}
            placeholder={DEFAULT_MODELS[provider] || ""}
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
          />
          <p className="text-xs text-slate-400 mt-1">
            百炼推荐: qwen3.5-turbo / qwen3.5-plus / qwen3.5-flash &middot; DeepSeek: deepseek-chat &middot; OpenAI: gpt-4o-mini
          </p>
        </div>

        <button onClick={handleSave} disabled={saving}
          className={saved
            ? "w-full py-2.5 text-white font-medium rounded-lg transition-colors bg-green-600"
            : "w-full py-2.5 text-white font-medium rounded-lg transition-colors bg-blue-600 hover:bg-blue-700"
          }>
          {saving ? "保存中..." : saved ? "已保存" : "保存配置"}
        </button>
      </div>

      <div className="mt-6 bg-white rounded-xl p-6 shadow-sm">
        <h3 className="font-semibold text-slate-800 mb-3">设置说明</h3>
        <ul className="text-sm text-slate-500 space-y-2">
          <li>&bull; 配置保存在 <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">user_settings.json</code> 文件中</li>
          <li>&bull; 切换服务商后，需填写对应的 API Key</li>
          <li>&bull; 面试和简历分析时会使用当前选中的服务商</li>
          <li>&bull; 也可以在 .env 文件中配置默认值</li>
        </ul>
      </div>
    </div>
  );
}