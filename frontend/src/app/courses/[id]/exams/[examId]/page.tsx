"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { ExamQuestion, ExamPaper } from "@/types";

export default function ExamTakePage() {
  const { id, examId } = useParams<{ id: string; examId: string }>();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["exam", examId],
    queryFn: () => api.exams.get(examId),
  });
  const paper: ExamPaper | undefined = data?.paper;
  const questions: ExamQuestion[] = data?.questions ?? [];

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const saveTimer = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  // Init answers from loaded data
  useEffect(() => {
    const init: Record<string, string> = {};
    for (const q of questions) {
      if (q.student_answer) init[q.id] = q.student_answer;
    }
    setAnswers(init);
  }, [questions.length > 0 ? questions[0]?.id : null]); // sync once when questions load

  const answeredCount = Object.keys(answers).filter((k) => answers[k].trim()).length;
  const isGraded = paper?.status === "graded";

  const debouncedSave = useCallback((qid: string, value: string) => {
    if (saveTimer.current[qid]) clearTimeout(saveTimer.current[qid]);
    saveTimer.current[qid] = setTimeout(() => {
      api.exams.saveAnswer(examId, qid, value).catch(() => {});
    }, 2000);
  }, [examId]);

  const handleAnswerChange = (qid: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [qid]: value }));
    if (!isGraded) debouncedSave(qid, value);
  };

  const handleSaveDraft = async () => {
    setSaving(true);
    await api.exams.saveDraft(examId);
    queryClient.invalidateQueries({ queryKey: ["exam", examId] });
    setSaving(false);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    await api.exams.submit(examId);
    queryClient.invalidateQueries({ queryKey: ["exam", examId] });
    setSubmitting(false);
  };

  if (isLoading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mt-24" />;

  return (
    <div className="max-w-3xl mx-auto">
      <Link href={`/courses/${id}/exams`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回试卷列表
      </Link>

      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">{paper?.title || "试卷"}</h1>
          {isGraded && paper && (
            <p className="text-lg font-bold text-green-700 mt-1">
              得分：{paper.earned_score.toFixed(0)} / {paper.total_score.toFixed(0)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!isGraded && (
            <>
              <Button variant="outline" size="sm" onClick={handleSaveDraft} disabled={saving}>
                {saving && <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />}
                保存草稿
              </Button>
              <Button size="sm" onClick={handleSubmit} disabled={submitting}>
                {submitting && <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />}
                提交评分
              </Button>
            </>
          )}
        </div>
      </div>

      {!isGraded && (
        <div className="mb-4">
          <Progress value={questions.length ? (answeredCount / questions.length) * 100 : 0} className="h-2" />
          <p className="text-xs text-muted-foreground mt-1">答题进度：{answeredCount} / {questions.length}</p>
        </div>
      )}

      <div className="space-y-4">
        {questions.map((q, i) => (
          <Card key={q.id} className={isGraded ? (q.is_correct ? "border-green-200" : "border-red-200") : ""}>
            <CardContent className="py-4">
              <div className="flex items-start gap-2 mb-3">
                <span className="font-bold text-sm text-muted-foreground shrink-0">{i + 1}.</span>
                <div className="flex-1">
                  <p className="font-medium">{q.stem}</p>
                  <div className="flex gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">{q.question_type === "single_choice" ? "选择题" : q.question_type === "true_false" ? "判断题" : "简答题"}</Badge>
                    <Badge variant="outline" className="text-xs">{q.max_score} 分</Badge>
                    {isGraded && (
                      <>
                        <Badge className={q.is_correct ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>{q.score} 分</Badge>
                        {q.is_correct ? <CheckCircle className="w-4 h-4 text-green-600" /> : <XCircle className="w-4 h-4 text-red-500" />}
                      </>
                    )}
                  </div>
                </div>
              </div>

              {q.question_type === "single_choice" ? (
                <div className="space-y-1 ml-6">
                  {Object.entries(q.options).map(([key, val]) => {
                    const isSelected = answers[q.id] === key;
                    const isCorrect = q.student_answer === key && q.is_correct;
                    let optClass = "border rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors ";
                    if (isGraded) {
                      if (key === q.student_answer && !q.is_correct) optClass += "border-red-300 bg-red-50";
                      else if (isCorrect) optClass += "border-green-300 bg-green-50";
                      else optClass += "border-border";
                    } else {
                      optClass += isSelected ? "border-primary bg-primary/5" : "border-border hover:border-primary/50";
                    }
                    return (
                      <div
                        key={key}
                        className={optClass}
                        onClick={() => !isGraded && handleAnswerChange(q.id, key)}
                      >
                        <span className="font-medium mr-2">{key}.</span>{val}
                      </div>
                    );
                  })}
                </div>
              ) : q.question_type === "true_false" ? (
                <div className="space-y-1 ml-6">
                  {["正确", "错误"].map((label) => {
                    const key = label === "正确" ? "T" : "F";
                    const isSelected = answers[q.id] === key;
                    let optClass = "border rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors ";
                    if (isGraded) {
                      if (key === q.student_answer && !q.is_correct) optClass += "border-red-300 bg-red-50";
                      else if (isSelected && q.is_correct) optClass += "border-green-300 bg-green-50";
                      else optClass += "border-border";
                    } else {
                      optClass += isSelected ? "border-primary bg-primary/5" : "border-border hover:border-primary/50";
                    }
                    return (
                      <div
                        key={key}
                        className={optClass}
                        onClick={() => !isGraded && handleAnswerChange(q.id, key)}
                      >
                        {label}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="ml-6">
                  <Textarea
                    value={answers[q.id] || ""}
                    onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                    placeholder="请输入你的答案..."
                    className="min-h-[80px]"
                    disabled={isGraded}
                  />
                </div>
              )}

              {isGraded && q.feedback && (
                <div className="mt-3 ml-6 p-2 bg-muted/50 rounded text-sm">
                  <p className="text-muted-foreground">{q.feedback}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {questions.length === 0 && (
        <Card className="text-center py-12">
          <CardContent><p className="text-muted-foreground">试卷加载中...</p></CardContent>
        </Card>
      )}
    </div>
  );
}
