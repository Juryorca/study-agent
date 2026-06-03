"use client";

import { useState, useEffect } from "react";
import { Settings, Loader2, CheckCircle, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function SettingsDialog() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showKey, setShowKey] = useState(false);

  const [form, setForm] = useState({
    llm_api_key: "",
    llm_base_url: "",
    llm_model: "",
  });
  const [keyConfigured, setKeyConfigured] = useState(false);

  // Load current settings
  useEffect(() => {
    if (!open) return;
    setLoading(true);
    fetch(`${API}/api/settings`)
      .then((r) => r.json())
      .then((data) => {
        setForm({
          llm_api_key: "",  // always empty for security — user must re-enter
          llm_base_url: data.llm_base_url || "",
          llm_model: data.llm_model || "",
        });
        setKeyConfigured(data.llm_api_key_configured || false);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [open]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const res = await fetch(`${API}/api/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("保存失败");
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        className={cn(
          "inline-flex items-center justify-center shrink-0 rounded-lg h-8 w-8",
          "text-muted-foreground hover:bg-accent hover:text-foreground",
          "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
        title="API 设置"
      >
        <Settings className="w-4 h-4" />
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-4 h-4" /> LLM API 设置
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : (
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">API Key</label>
              <div className="relative">
                <Input
                  type={showKey ? "text" : "password"}
                  value={form.llm_api_key}
                  onChange={(e) => setForm({ ...form, llm_api_key: e.target.value })}
                  placeholder={keyConfigured ? "已配置（重新输入以覆盖）" : "sk-..."}
                  className="pr-10 mt-1"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowKey(!showKey)}
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {keyConfigured ? (
                  <span className="text-green-600">API Key 已配置，留空将保持现有密钥不变</span>
                ) : (
                  "留空则使用 .env 中的配置"
                )}
              </p>
            </div>

            <div>
              <label className="text-sm font-medium">Base URL</label>
              <Input
                value={form.llm_base_url}
                onChange={(e) => setForm({ ...form, llm_base_url: e.target.value })}
                placeholder="https://api.openai.com/v1"
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">模型</label>
              <Input
                value={form.llm_model}
                onChange={(e) => setForm({ ...form, llm_model: e.target.value })}
                placeholder="gpt-4o-mini"
                className="mt-1"
              />
            </div>

            <Button onClick={handleSave} disabled={saving} className="w-full">
              {saving ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : saved ? (
                <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              ) : null}
              {saving ? "保存中..." : saved ? "已保存" : "保存设置"}
            </Button>

            <p className="text-xs text-muted-foreground">
              保存后会自动重置 LLM 客户端连接。设置持久化到后端文件。
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
