"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Loader2, AlertTriangle, CheckCircle, Lightbulb } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { WeaknessPoint } from "@/types";

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<{ weak_points: WeaknessPoint[]; report_text: string; study_plan: string } | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await api.analysis.weakness(id);
      setReport(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <Link href={`/courses/${id}`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回课程
      </Link>
      <h1 className="text-2xl font-bold mb-6">薄弱点分析</h1>

      {!report && (
        <Card className="text-center py-12">
          <CardContent>
            <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">分析你的答题记录，定位薄弱知识点</p>
            <Button onClick={handleAnalyze} disabled={loading} size="lg">
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              开始分析
            </Button>
          </CardContent>
        </Card>
      )}

      {report && report.weak_points.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-4" />
            <p className="text-lg font-medium">{report.report_text || "目前答题正确率良好，继续保持！"}</p>
          </CardContent>
        </Card>
      )}

      {report && report.weak_points.length > 0 && (
        <div className="space-y-6">
          <div className="grid gap-4">
            {report.weak_points.map((wp: WeaknessPoint) => (
              <Card key={wp.knowledge_point}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-orange-500" />
                      {wp.knowledge_point}
                    </CardTitle>
                    <span className="text-sm font-bold text-red-600">
                      {(wp.error_rate * 100).toFixed(1)}% 错误率
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>答题 {wp.total_attempts} 次 · 错误 {wp.wrong_count} 次</span>
                      <span>正确率 {((1 - wp.error_rate) * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={(1 - wp.error_rate) * 100} className="h-2" />
                    <div className="flex items-start gap-2 text-sm bg-orange-50 p-3 rounded-lg">
                      <Lightbulb className="w-4 h-4 text-orange-500 shrink-0 mt-0.5" />
                      <span>{wp.suggestion}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {report.study_plan && (
            <Card>
              <CardHeader>
                <CardTitle>个性化学习计划</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.study_plan}</ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
