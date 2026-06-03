"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Plus, Trash2, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ExamPaper } from "@/types";

const statusLabels: Record<string, string> = {
  draft: "草稿", in_progress: "进行中", submitted: "已提交", graded: "已批改",
};
const statusColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700", in_progress: "bg-yellow-100 text-yellow-700",
  submitted: "bg-blue-100 text-blue-700", graded: "bg-green-100 text-green-800",
};

export default function ExamsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"" | "graded">("");
  const [deleting, setDeleting] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["exams", id, tab],
    queryFn: () => api.exams.list(id, tab || undefined),
  });
  const papers: ExamPaper[] = data?.papers ?? [];

  const handleDelete = async (examId: string) => {
    setDeleting(examId);
    await api.exams.delete(examId);
    queryClient.invalidateQueries({ queryKey: ["exams", id] });
    setDeleting("");
  };

  if (isLoading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mt-24" />;

  return (
    <div className="max-w-4xl mx-auto">
      <Link href={`/courses/${id}`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回课程
      </Link>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">试卷考试</h1>
        <Button size="sm" render={<Link href={`/courses/${id}/exams/new`} />} nativeButton={false}>
          <Plus className="w-4 h-4 mr-1" /> 新建试卷
        </Button>
      </div>

      <div className="flex gap-1 bg-muted rounded-md p-0.5 mb-4 w-fit">
        {(["", "graded"] as const).map((v) => (
          <button
            key={v}
            className={`px-3 py-1 text-sm rounded font-medium transition-colors ${
              tab === v ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setTab(v)}
          >
            {v === "" ? "全部" : "已批改"}
          </button>
        ))}
      </div>

      {papers.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <p className="text-muted-foreground">暂无试卷</p>
            <Button className="mt-4" size="sm" render={<Link href={`/courses/${id}/exams/new`} />} nativeButton={false}>
              生成第一份试卷
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {papers.map((p) => (
            <Link key={p.id} href={`/courses/${id}/exams/${p.id}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer group">
                <CardContent className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{p.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(p.created_at).toLocaleString("zh-CN")}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {p.status === "graded" && (
                      <span className="text-sm font-bold text-green-700">
                        {p.earned_score.toFixed(0)} / {p.total_score.toFixed(0)}
                      </span>
                    )}
                    <Badge className={statusColors[p.status]}>{statusLabels[p.status]}</Badge>
                    <button
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-muted rounded"
                      onClick={(e) => { e.preventDefault(); handleDelete(p.id); }}
                    >
                      {deleting === p.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5 text-muted-foreground hover:text-red-500" />
                      )}
                    </button>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
