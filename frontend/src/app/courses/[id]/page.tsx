"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Upload, Brain, FileQuestion, BarChart3, FileText, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const subPages = [
  {
    href: "upload",
    icon: Upload,
    title: "资料上传",
    desc: "上传 PPT / PDF / 笔记，自动解析和索引",
    color: "text-blue-500",
  },
  {
    href: "knowledge",
    icon: Brain,
    title: "知识点与提纲",
    desc: "AI 提取知识点，生成复习提纲",
    color: "text-purple-500",
  },
  {
    href: "exams",
    icon: FileQuestion,
    title: "试卷考试",
    desc: "生成期末模拟卷，在线答题和评分",
    color: "text-green-500",
  },
  {
    href: "analysis",
    icon: BarChart3,
    title: "薄弱点分析",
    desc: "统计答题正确率，定位薄弱环节",
    color: "text-orange-500",
  },
];

export default function CourseDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: course, isLoading } = useQuery({
    queryKey: ["course", id],
    queryFn: () => api.courses.get(id),
  });

  const { data: docsData } = useQuery({
    queryKey: ["documents", id],
    queryFn: () => api.documents.list(id),
  });

  if (isLoading)
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  if (!course) return <div>课程不存在</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Link href="/courses" className="text-sm text-muted-foreground hover:text-foreground mb-2 inline-block">
          ← 返回课程列表
        </Link>
        <h1 className="text-2xl font-bold">{course.name}</h1>
        <div className="flex gap-2 mt-2">
          {course.category && <Badge variant="secondary">{course.category}</Badge>}
          <Badge variant="outline" className="flex items-center gap-1">
            <FileText className="w-3 h-3" />
            {docsData?.total || 0} 份资料
          </Badge>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {subPages.map((p) => (
          <Link key={p.href} href={`/courses/${id}/${p.href}`}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full group">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <p.icon className={`w-8 h-8 ${p.color}`} />
                  <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <CardTitle className="text-lg mt-2">{p.title}</CardTitle>
                <CardDescription>{p.desc}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
