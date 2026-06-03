"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Sparkles, FileText, Loader2, Search, MessageCircle, BookOpen, LayoutList } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import FlashcardView from "@/components/knowledge/flashcard";
import type { KnowledgePoint, Mastery } from "@/types";

const importanceColors: Record<string, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};
const importanceLabels: Record<string, string> = { high: "重要", medium: "中等", low: "一般" };
const masteryLabels: Record<Mastery, string> = { unlearned: "未学习", learning: "学习中", mastered: "已掌握" };
const masteryColors: Record<Mastery, string> = {
  unlearned: "bg-gray-100 text-gray-700",
  learning: "bg-yellow-100 text-yellow-700",
  mastered: "bg-green-100 text-green-800",
};

export default function KnowledgePage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  // ── Filters & view ──
  const [search, setSearch] = useState("");
  const [importanceFilter, setImportanceFilter] = useState("");
  const [masteryFilter, setMasteryFilter] = useState("");
  const [chapterFilter, setChapterFilter] = useState("");
  const [viewMode, setViewMode] = useState<"list" | "flashcard">("list");
  const [groupByChapter, setGroupByChapter] = useState(false);

  // ── Extract state ──
  const [extracting, setExtracting] = useState(false);
  const [extractProgress, setExtractProgress] = useState("");
  const handleExtract = async () => {
    setExtracting(true);
    setExtractProgress("正在准备...");
    try {
      await api.knowledge.extractStream(id, "", (msg) => setExtractProgress(msg));
      queryClient.invalidateQueries({ queryKey: ["knowledge", id] });
    } catch (err: any) {
      setExtractProgress(`提取失败: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  // ── Data ──
  const { data: kpData, isLoading } = useQuery({
    queryKey: ["knowledge", id, importanceFilter, masteryFilter, chapterFilter, search],
    queryFn: () => api.knowledge.list(id, importanceFilter || undefined, masteryFilter || undefined, chapterFilter || undefined, search || undefined),
  });
  const points: KnowledgePoint[] = kpData?.knowledge_points ?? [];

  // ── Chapter groups (derived from data) ──
  const chapters = useMemo(() => [...new Set(points.map((p) => p.chapter).filter(Boolean))], [points]);
  const groupedPoints = useMemo(() => {
    if (!groupByChapter) return null;
    const groups: Record<string, KnowledgePoint[]> = {};
    for (const p of points) {
      const ch = p.chapter || "未归类";
      (groups[ch] ??= []).push(p);
    }
    return groups;
  }, [points, groupByChapter]);

  // ── Stats ──
  const stats = useMemo(() => {
    const total = points.length;
    const mastered = points.filter((p) => p.mastery === "mastered").length;
    const learning = points.filter((p) => p.mastery === "learning").length;
    const unlearned = points.filter((p) => p.mastery === "unlearned").length;
    return { total, mastered, learning, unlearned, pct: total ? Math.round((mastered / total) * 100) : 0 };
  }, [points]);

  // ── Mastery update ──
  const handleMastery = async (kpId: string, mastery: Mastery) => {
    // Optimistic update
    queryClient.setQueryData(["knowledge", id, importanceFilter, masteryFilter, chapterFilter, search], (old: any) => {
      if (!old) return old;
      return {
        ...old,
        knowledge_points: old.knowledge_points.map((p: KnowledgePoint) =>
          p.id === kpId ? { ...p, mastery } : p
        ),
      };
    });
    try {
      await api.knowledge.updateMastery(kpId, mastery);
    } catch {
      queryClient.invalidateQueries({ queryKey: ["knowledge", id] });
    }
  };

  // ── Outline ──
  const [chapter, setChapter] = useState("");
  const [outlineLoading, setOutlineLoading] = useState(false);
  const { data: outlineData } = useQuery({
    queryKey: ["outlines", id],
    queryFn: () => api.knowledge.outlineList(id),
    refetchInterval: (query) => {
      const hasGenerating = query.state.data?.outlines?.some((o: any) => o.status === "generating");
      return hasGenerating ? 2000 : false;
    },
  });
  const outlines = outlineData?.outlines || [];
  const latestOutline = outlines[0];
  const isGenerating = latestOutline?.status === "generating";

  const handleGenerateOutline = async () => {
    setOutlineLoading(true);
    try {
      await api.knowledge.outlineCreate(id, chapter);
      queryClient.invalidateQueries({ queryKey: ["outlines", id] });
    } catch (err: any) {
      console.error(err);
    } finally {
      setOutlineLoading(false);
    }
  };

  const renderCard = (kp: KnowledgePoint) => (
    <Card key={kp.id} className="group">
      <CardContent className="py-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold truncate">{kp.name}</h3>
              <Badge className={importanceColors[kp.importance]}>{importanceLabels[kp.importance]}</Badge>
              <Badge className={masteryColors[kp.mastery as Mastery]}>{masteryLabels[kp.mastery as Mastery]}</Badge>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">{kp.description}</p>
            {kp.source && (
              <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                <FileText className="w-3 h-3" /> {kp.source}
              </p>
            )}
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
            <Link
              href={`/agent?course_id=${id}&prompt=${encodeURIComponent("请帮我讲解一下：" + kp.name)}`}
              className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
              title="AI 对话"
            >
              <MessageCircle className="w-3.5 h-3.5" />
            </Link>
            {(["unlearned", "learning", "mastered"] as Mastery[]).map((m) => (
              <button
                key={m}
                className={`px-2 py-0.5 text-[11px] rounded transition-colors ${
                  kp.mastery === m ? "bg-primary text-primary-foreground" : "hover:bg-muted text-muted-foreground"
                }`}
                onClick={() => handleMastery(kp.id, m)}
              >
                {masteryLabels[m]}
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (isLoading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mt-24" />;

  return (
    <div className="max-w-4xl mx-auto">
      <Link href={`/courses/${id}`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回课程
      </Link>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">知识点与复习提纲</h1>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" nativeButton={false} render={<Link href={`/agent?course_id=${id}`} />}>
            <MessageCircle className="w-4 h-4 mr-1" /> AI 对话
          </Button>
          <Button onClick={handleExtract} disabled={extracting} size="sm">
            {extracting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
            提取知识点
          </Button>
        </div>
      </div>

      {extractProgress && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700 flex items-center gap-2">
          {extracting && <Loader2 className="w-4 h-4 animate-spin" />}
          {extractProgress}
        </div>
      )}

      <Tabs defaultValue="knowledge">
        <TabsList className="mb-4">
          <TabsTrigger value="knowledge">知识点列表</TabsTrigger>
          <TabsTrigger value="outline">复习提纲</TabsTrigger>
        </TabsList>

        {/* ═══ 知识点 Tab ═══ */}
        <TabsContent value="knowledge" className="space-y-4">
          {/* Stats bar */}
          {points.length > 0 && (
            <Card>
              <CardContent className="py-3">
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">掌握进度</span>
                    <span className="font-bold text-green-700">{stats.mastered}</span>
                    <span className="text-muted-foreground">/ {stats.total}</span>
                  </div>
                  <Progress value={stats.pct} className="flex-1 h-2" />
                  <div className="flex gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />已掌握 {stats.mastered}</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400" />学习中 {stats.learning}</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-300" />未学习 {stats.unlearned}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Toolbar */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
              <Input
                className="pl-8"
                placeholder="搜索知识点..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="flex gap-1 bg-muted rounded-md p-0.5">
              {["", "high", "medium", "low"].map((v) => (
                <button
                  key={v}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                    importanceFilter === v ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
                  }`}
                  onClick={() => setImportanceFilter(v)}
                >
                  {v === "" ? "全部" : importanceLabels[v]}
                </button>
              ))}
            </div>

            <div className="flex gap-1 bg-muted rounded-md p-0.5">
              {["", "unlearned", "learning", "mastered"].map((v) => (
                <button
                  key={v}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                    masteryFilter === v ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
                  }`}
                  onClick={() => setMasteryFilter(v)}
                >
                  {v === "" ? "全部" : masteryLabels[v as Mastery]}
                </button>
              ))}
            </div>

            <div className="flex gap-1 bg-muted rounded-md p-0.5">
              <button
                className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                  viewMode === "list" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => setViewMode("list")}
              >
                <LayoutList className="w-3.5 h-3.5 inline mr-1" /> 列表
              </button>
              <button
                className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                  viewMode === "flashcard" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => setViewMode("flashcard")}
              >
                <BookOpen className="w-3.5 h-3.5 inline mr-1" /> 闪卡
              </button>
            </div>

            {chapters.length > 0 && (
              <button
                className={`px-2.5 py-1 text-xs rounded font-medium transition-colors border ${
                  groupByChapter ? "bg-primary text-primary-foreground border-primary" : "bg-muted border-border hover:bg-background"
                }`}
                onClick={() => setGroupByChapter(!groupByChapter)}
              >
                按章节分组
              </button>
            )}
          </div>

          {/* Chapter quick filter */}
          {chapters.length > 0 && (
            <div className="flex gap-1 bg-muted rounded-md p-0.5 flex-wrap">
              <button
                className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                  chapterFilter === "" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => setChapterFilter("")}
              >
                全部章节
              </button>
              {chapters.map((ch) => (
                <button
                  key={ch}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                    chapterFilter === ch ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
                  }`}
                  onClick={() => setChapterFilter(ch)}
                >
                  {ch}
                </button>
              ))}
            </div>
          )}

          {/* Content */}
          {points.length === 0 ? (
            <Card className="text-center py-12">
              <CardContent>
                <p className="text-muted-foreground">暂无知识点，请先上传课程资料并点击「提取知识点」</p>
              </CardContent>
            </Card>
          ) : viewMode === "flashcard" ? (
            <FlashcardView points={points} onMastery={handleMastery} onClose={() => setViewMode("list")} />
          ) : groupedPoints ? (
            <div className="space-y-6">
              {Object.entries(groupedPoints).map(([ch, kps]) => (
                <div key={ch}>
                  <h3 className="text-sm font-semibold text-muted-foreground mb-2 border-b pb-1">{ch}</h3>
                  <div className="space-y-2">
                    {kps.map(renderCard)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">{points.map(renderCard)}</div>
          )}
        </TabsContent>

        {/* ═══ 复习提纲 Tab ═══ */}
        <TabsContent value="outline">
          <Card>
            <CardHeader>
              <CardTitle>生成复习提纲</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3">
                <Input
                  value={chapter}
                  onChange={(e) => setChapter(e.target.value)}
                  placeholder="章节名称（如：第三章），留空则覆盖全部"
                />
                <Button onClick={handleGenerateOutline} disabled={outlineLoading || isGenerating}>
                  {(outlineLoading || isGenerating) && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  生成提纲
                </Button>
              </div>

              {isGenerating && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  AI 正在生成复习提纲，可以离开页面稍后回来查看...
                </div>
              )}

              {outlines.length > 0 && (
                <div className="space-y-4 mt-4">
                  {outlines.map((o: any) => (
                    <div key={o.id} className="border rounded-lg">
                      <div className="flex items-center justify-between px-4 py-2 bg-muted/30 rounded-t-lg">
                        <span className="text-sm font-medium">
                          {o.chapter || "全部内容"} &mdash; {new Date(o.created_at).toLocaleString("zh-CN")}
                        </span>
                        <div className="flex items-center gap-2">
                          {o.status === "completed" && <Badge className="bg-green-100 text-green-800">已完成</Badge>}
                          {o.status === "generating" && <Badge className="bg-yellow-100 text-yellow-800">生成中</Badge>}
                          {o.status === "failed" && <Badge className="bg-red-100 text-red-800">失败</Badge>}
                          <Button variant="ghost" size="sm" onClick={async () => {
                            await api.knowledge.outlineDelete(o.id);
                            queryClient.invalidateQueries({ queryKey: ["outlines", id] });
                          }}>删除</Button>
                        </div>
                      </div>
                      {(o.status === "completed" || (o.status === "generating" && o.content)) && (
                        <div className="prose prose-sm max-w-none p-4">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{o.content}</ReactMarkdown>
                          {o.status === "generating" && (
                            <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-0.5 align-text-bottom" />
                          )}
                        </div>
                      )}
                      {o.status === "failed" && (
                        <div className="p-4 text-sm text-red-600">生成失败: {o.error_message}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {!isGenerating && outlines.length === 0 && (
                <p className="text-sm text-muted-foreground py-4 text-center">暂无复习提纲，请点击「生成提纲」创建</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
