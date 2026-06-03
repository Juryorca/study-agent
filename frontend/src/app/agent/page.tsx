"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, User, Loader2, Wrench, Send, Trash2, Plus, MessageSquare, BookOpen, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { AgentChatEvent, ChatSession, ChatMessage, Course } from "@/types";

interface Message {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  toolName?: string;
  toolArgs?: Record<string, unknown>;
}

let _msgId = 0;
function nextId() { return `msg_${++_msgId}`; }

function AgentChatContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const urlCourseId = searchParams.get("course_id") || "";
  const prompt = searchParams.get("prompt") || "";
  const queryClient = useQueryClient();

  // Stabilize courseId: once set, never clear during session (prevents flash to picker)
  const courseIdRef = useRef(urlCourseId);
  if (urlCourseId) courseIdRef.current = urlCourseId;
  const courseId = courseIdRef.current;

  // ── Session state ──
  const [activeSessionId, setActiveSessionId] = useState(searchParams.get("session_id") || "");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(prompt);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<AbortController | null>(null);

  // ── Courses list (for picker when no courseId) ──
  const { data: coursesData } = useQuery({
    queryKey: ["courses"],
    queryFn: () => api.courses.list(),
    enabled: !courseId,
  });
  const courses: Course[] = coursesData?.courses ?? [];

  // ── Select course → set in URL ──
  const handleSelectCourse = (cid: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("course_id", cid);
    router.push(`/agent?${params.toString()}`);
  };

  // ── Sessions list ──
  const { data: sessionData } = useQuery({
    queryKey: ["sessions", courseId],
    queryFn: () => api.agent.sessions.list(courseId || undefined),
    enabled: !!courseId,
  });
  const sessions: ChatSession[] = sessionData?.sessions ?? [];

  // ── Load history when switching sessions
  // Use a ref to skip loading when a session was just auto-created (messages aren't saved yet)
  const skipHistoryRef = useRef(false);

  useEffect(() => {
    if (!activeSessionId || skipHistoryRef.current) {
      // Reset flag after one skip — next switch will load normally
      skipHistoryRef.current = false;
      return;
    }
    api.agent.sessions.messages(activeSessionId).then((data) => {
      setMessages(data.messages.map((m: ChatMessage) => ({
        id: m.id,
        role: m.role as Message["role"],
        content: m.content,
        toolName: m.tool_name || undefined,
        toolArgs: (m.tool_args as Record<string, unknown>) || undefined,
      })));
    }).catch(() => {});
  }, [activeSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  // ── Send ──
  const handleSend = useCallback(async () => {
    if (!input.trim() || loading) return;
    const content = input.trim();
    setInput("");
    setLoading(true);

    const userMsg: Message = { id: nextId(), role: "user", content };
    const assistantId = nextId();
    const assistantMsg: Message = { id: assistantId, role: "assistant", content: "" };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    // Create session if needed
    let sid = activeSessionId;
    if (!sid && courseId) {
      const s = await api.agent.sessions.create({ course_id: courseId });
      sid = s.id;
      skipHistoryRef.current = true; // skip history load — messages not saved yet
      setActiveSessionId(sid);
      queryClient.invalidateQueries({ queryKey: ["sessions", courseId] });
      // Update URL with new session_id
      const params = new URLSearchParams(searchParams.toString());
      params.set("course_id", courseId);
      params.set("session_id", sid);
      router.replace(`/agent?${params.toString()}`);
    }

    const controller = new AbortController();
    streamRef.current = controller;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/agent/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content, course_id: courseId, session_id: sid, user_id: "default" }),
          signal: controller.signal,
        }
      );

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader");
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          const data = line.startsWith("data: ") ? line.slice(6) : null;
          if (!data) continue;
          try {
            const event: AgentChatEvent = JSON.parse(data);
            setMessages((prev) => {
              const idx = prev.findIndex((m) => m.id === assistantId);
              if (idx === -1) return prev;
              const before = prev.slice(0, idx);
              const after = prev.slice(idx + 1);
              const cur = { ...prev[idx] };
              if (event.type === "text") {
                cur.content = event.content || "";
                return [...before, cur, ...after];
              }
              if (event.type === "tool_call") {
                const toolMsg: Message = { id: nextId(), role: "tool", content: `调用 ${event.tool_name}`, toolName: event.tool_name, toolArgs: event.tool_args };
                return [...before, toolMsg, cur, ...after];
              }
              if (event.type === "tool_result") {
                return prev.map((m) => m.role === "tool" && m.toolName === event.tool_name ? { ...m, content: `${event.tool_name} 完成` } : m);
              }
              return prev;
            });
          } catch { /* ignore */ }
        }
      }
      // Refresh session list (title may have updated)
      queryClient.invalidateQueries({ queryKey: ["sessions", courseId] });
    } catch (err: any) {
      if (err.name !== "AbortError") console.error("Chat error:", err);
    } finally {
      setLoading(false);
      streamRef.current = null;
    }
  }, [input, loading, activeSessionId, courseId]);

  // ── Session actions ──
  const handleNewSession = async () => {
    if (!courseId) return;
    const s = await api.agent.sessions.create({ course_id: courseId });
    queryClient.invalidateQueries({ queryKey: ["sessions", courseId] });
    switchToSession(s.id);
  };

  const switchToSession = (sid: string) => {
    if (activeSessionId === sid) return; // already active — no-op
    streamRef.current?.abort();
    setActiveSessionId(sid);
    setMessages([]);
    setLoading(false);
    // Use history.replaceState to update URL without triggering React re-render
    const params = new URLSearchParams(searchParams.toString());
    params.set("course_id", courseId);
    params.set("session_id", sid);
    router.replace(`/agent?${params.toString()}`);
  };

  const handleDeleteSession = async (sid: string) => {
    await api.agent.sessions.delete(sid);
    queryClient.invalidateQueries({ queryKey: ["sessions", courseId] });
    if (activeSessionId === sid) {
      setActiveSessionId("");
      setMessages([]);
      const params = new URLSearchParams(searchParams.toString());
      params.set("course_id", courseId);
      params.delete("session_id");
      router.replace(`/agent?${params.toString()}`);
    }
  };

  // ── Suggested actions ──
  const suggestedActions = [
    { label: "帮我复习一下这门课", msg: "帮我复习一下这门课的主要内容" },
    { label: "我哪里学得不好？", msg: "帮我分析一下我哪些知识点掌握得不好" },
    { label: "出几道题给我做", msg: "给我出5道选择题" },
    { label: "制定学习计划", msg: "根据我的答题情况，制定一个学习计划" },
  ];

  // ── Course Picker (no course selected yet) ──
  if (!courseId) {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <div className="text-center mb-8">
          <Bot className="w-16 h-16 mx-auto mb-4 text-primary" />
          <h1 className="text-2xl font-bold mb-2">AI 学习助手</h1>
          <p className="text-muted-foreground">选择一个课程，开始对话</p>
        </div>
        <div className="space-y-3">
          {courses.map((course) => (
            <Card
              key={course.id}
              className="hover:shadow-md transition-shadow cursor-pointer group"
              onClick={() => handleSelectCourse(course.id)}
            >
              <CardContent className="flex items-center justify-between py-4">
                <div className="flex items-center gap-3">
                  <BookOpen className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{course.name}</p>
                    {course.category && (
                      <p className="text-xs text-muted-foreground">{course.category}</p>
                    )}
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </CardContent>
            </Card>
          ))}
          {courses.length === 0 && (
            <Card className="text-center py-12">
              <CardContent>
                <p className="text-muted-foreground mb-4">还没有课程，请先创建课程</p>
                <Button onClick={() => router.push("/courses")}>前往课程管理</Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    );
  }

  // ── Chat interface (course selected) ──
  return (
    <div className="flex h-[calc(100vh-4rem)] -mx-[calc((100vw-100%)/2)] w-screen max-w-screen-xl mx-auto">
      {/* ── Sidebar ── */}
      {courseId && (
        <aside className="w-56 shrink-0 border-r flex flex-col">
          <div className="p-3 flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">对话历史</span>
            <Button variant="ghost" size="xs" onClick={handleNewSession} title="新建对话">
              <Plus className="w-3.5 h-3.5" />
            </Button>
          </div>
          <div className="flex-1 overflow-auto">
            {sessions.map((s) => (
              <div
                key={s.id}
                className={`group flex items-center px-3 py-2 cursor-pointer text-sm border-l-2 transition-colors ${
                  activeSessionId === s.id
                    ? "border-primary bg-muted/50 text-foreground"
                    : "border-transparent hover:bg-muted/30 text-muted-foreground"
                }`}
                onClick={() => switchToSession(s.id)}
              >
                <MessageSquare className="w-3.5 h-3.5 mr-2 shrink-0 opacity-50" />
                <span className="truncate flex-1">{s.title}</span>
                <button
                  className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-muted rounded shrink-0"
                  onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.id); }}
                >
                  <Trash2 className="w-3 h-3 text-muted-foreground hover:text-red-500" />
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <p className="px-3 py-4 text-xs text-muted-foreground text-center">暂无对话，发送消息自动创建</p>
            )}
          </div>
        </aside>
      )}

      {/* ── Chat area ── */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between p-4 border-b">
          <h1 className="text-lg font-bold flex items-center gap-2">
            <Bot className="w-5 h-5" /> AI 学习助手
          </h1>
        </div>

        <Card className="flex-1 flex flex-col overflow-hidden border-0 rounded-none">
          <CardContent className="flex-1 overflow-auto p-4" ref={scrollRef}>
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                <Bot className="w-16 h-16 mb-4" />
                <p className="text-lg font-medium mb-2">你好，我是你的学习助手</p>
                <p className="mb-6">我可以帮你检索课程资料、生成复习提纲、出题练习、分析薄弱点</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {suggestedActions.map((action) => (
                    <Button key={action.label} variant="outline" size="sm" onClick={() => setInput(action.msg)}>
                      {action.label}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {messages.map((msg) => (
                  <div key={msg.id}>
                    {msg.role === "tool" ? (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground py-1">
                        <Wrench className="w-3 h-3" />
                        <span>{msg.content}</span>
                        {msg.toolName && <Badge variant="outline" className="text-xs">{msg.toolName}</Badge>}
                      </div>
                    ) : (
                      <div className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-primary" : "bg-muted"}`}>
                          {msg.role === "user" ? <User className="w-3.5 h-3.5 text-primary-foreground" /> : <Bot className="w-3.5 h-3.5" />}
                        </div>
                        <div className={`rounded-lg px-3 py-2 max-w-[80%] text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                          {msg.content ? (
                            msg.role === "assistant" ? (
                              <div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown></div>
                            ) : (
                              <div className="whitespace-pre-wrap">{msg.content}</div>
                            )
                          ) : (
                            <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>

          <div className="p-4 border-t">
            <div className="flex gap-3">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入你的问题，例如：帮我复习数据库第三章..."
                className="min-h-[60px] resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
                }}
              />
              <Button onClick={handleSend} disabled={loading || !input.trim()} className="shrink-0">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">按 Enter 发送，Shift+Enter 换行</p>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function AgentChatPage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mt-24" />}>
      <AgentChatContent />
    </Suspense>
  );
}
