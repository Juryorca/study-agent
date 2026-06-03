"use client";

import Link from "next/link";
import { BookOpen, Upload, Brain, FileQuestion, BarChart3, Bot, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  { icon: Upload, title: "资料上传", desc: "支持 PPTX / PDF / Markdown 文档上传与自动解析" },
  { icon: Brain, title: "知识点提取", desc: "AI 自动提取课程核心知识点，生成结构化知识体系" },
  { icon: BookOpen, title: "复习提纲", desc: "一键生成章节化复习提纲，标注重点与易错点" },
  { icon: FileQuestion, title: "智能出题", desc: "基于课程资料自动生成选择题与简答题" },
  { icon: BarChart3, title: "薄弱分析", desc: "根据答题记录统计正确率，定位薄弱知识点" },
  { icon: Bot, title: "AI 学习助手", desc: "支持自然语言对话，推荐个性化学习计划" },
];

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold tracking-tight mb-4">Study Agent</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          基于 RAG + Tool Calling 的个性化课程复习智能体，让 AI 帮你高效备考
        </p>
        <div className="flex gap-4 justify-center mt-8">
          <Link href="/courses">
            <Button size="lg">
              开始使用 <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
          <Link href="/agent">
            <Button variant="outline" size="lg">
              <Bot className="w-4 h-4 mr-2" />AI 对话
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mt-8">
        {features.map((f) => (
          <Card key={f.title}>
            <CardHeader>
              <f.icon className="w-8 h-8 text-primary mb-2" />
              <CardTitle className="text-lg">{f.title}</CardTitle>
              <CardDescription>{f.desc}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card className="mt-12">
        <CardHeader>
          <CardTitle>学习工作流</CardTitle>
          <CardDescription>完整的「上传 → 学习 → 练习 → 分析」闭环</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
            {["上传课程资料", "AI 提取知识点", "生成复习提纲", "自动出题练习", "薄弱点分析", "个性化学习建议"].map(
              (step, i) => (
                <span key={i} className="flex items-center gap-2">
                  <span className="px-3 py-1.5 rounded-full bg-primary/10 text-primary font-medium">{step}</span>
                  {i < 5 && <ArrowRight className="w-3 h-3 text-muted-foreground" />}
                </span>
              )
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
