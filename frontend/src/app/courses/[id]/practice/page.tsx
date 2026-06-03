"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles, CheckCircle, XCircle, Loader2, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { Question, AnswerResult } from "@/types";

export default function PracticePage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [results, setResults] = useState<AnswerResult[] | null>(null);
  const [showExplanation, setShowExplanation] = useState<Record<string, boolean>>({});

  const { data: questionsData, isLoading } = useQuery({
    queryKey: ["questions", id],
    queryFn: () => api.questions.list(id),
  });

  const generateMutation = useMutation({
    mutationFn: (data: { knowledge_point?: string; question_type?: string; count?: number; difficulty?: string }) =>
      api.questions.generate(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["questions", id] }),
  });

  const submitMutation = useMutation({
    mutationFn: () => {
      const answersList = Object.entries(answers).map(([question_id, student_answer]) => ({
        question_id,
        student_answer,
      }));
      return api.answers.submitBatch(answersList);
    },
    onSuccess: (data) => {
      setResults(data.results);
    },
  });

  const questions = questionsData?.questions || [];
  const answeredCount = Object.keys(answers).filter((k) => answers[k].trim()).length;

  if (isLoading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mt-24" />;

  if (questions.length === 0) {
    return (
      <div className="max-w-3xl mx-auto">
        <Link href={`/courses/${id}`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
          ← 返回课程
        </Link>
        <h1 className="text-2xl font-bold mb-6">题目练习</h1>
        <Card className="text-center py-12">
          <CardContent>
            <p className="text-muted-foreground mb-4">还没有题目，请先生成练习题</p>
            <Button onClick={() => generateMutation.mutate({ count: 5, difficulty: "medium" })} disabled={generateMutation.isPending}>
              {generateMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              <Sparkles className="w-4 h-4 mr-2" />生成 5 道选择题
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <Link href={`/courses/${id}`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回课程
      </Link>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">题目练习</h1>
        <Button onClick={() => generateMutation.mutate({ count: 5 })} disabled={generateMutation.isPending} variant="outline">
          <Sparkles className="w-4 h-4 mr-2" />生成更多
        </Button>
      </div>

      {!results && (
        <div className="mb-4">
          <Progress value={(answeredCount / questions.length) * 100} className="h-2" />
          <p className="text-xs text-muted-foreground mt-1">
            已答 {answeredCount}/{questions.length} 题
          </p>
        </div>
      )}

      {results && (
        <Card className="mb-4 bg-primary/5">
          <CardContent className="py-4">
            <p className="font-semibold">
              得分: {results.reduce((s, r) => s + r.score, 0)} / {results.reduce((s, r) => s + r.max_score, 0)}
              {" · "}
              正确率: {((results.filter((r) => r.is_correct).length / results.length) * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {questions.map((q: Question, idx: number) => {
          const result = results?.find((r) => r.question_id === q.id);
          return (
            <Card key={q.id} className={result ? (result.is_correct ? "border-green-300" : "border-red-300") : ""}>
              <CardHeader>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-muted-foreground">第 {idx + 1} 题</span>
                  <Badge variant="secondary">{q.question_type === "single_choice" ? "单选题" : "简答题"}</Badge>
                  <Badge variant="outline">{q.difficulty}</Badge>
                  {q.knowledge_point && <Badge variant="outline">{q.knowledge_point}</Badge>}
                </div>
                <CardTitle className="text-base font-medium">{q.stem}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {q.question_type === "single_choice" && q.options && (
                  <div className="space-y-2">
                    {Object.entries(q.options).map(([key, value]) => {
                      const isSelected = answers[q.id] === key;
                      const isCorrectAnswer = result && key === result.correct_answer;
                      const isWrongSelected = result && isSelected && !result.is_correct;

                      let optionClass = "border rounded-lg p-3 cursor-pointer transition-colors hover:bg-accent";
                      if (isSelected && !result) optionClass += " bg-primary/10 border-primary";
                      if (isCorrectAnswer && result) optionClass += " bg-green-50 border-green-400";
                      if (isWrongSelected) optionClass += " bg-red-50 border-red-400";

                      return (
                        <div
                          key={key}
                          className={optionClass}
                          onClick={() => {
                            if (!result) setAnswers((prev) => ({ ...prev, [q.id]: key }));
                          }}
                        >
                          <span className="font-semibold mr-2">{key}.</span>
                          {value as string}
                          {isCorrectAnswer && result && <CheckCircle className="w-4 h-4 inline ml-2 text-green-600" />}
                          {isWrongSelected && <XCircle className="w-4 h-4 inline ml-2 text-red-600" />}
                        </div>
                      );
                    })}
                  </div>
                )}

                {q.question_type === "short_answer" && (
                  <textarea
                    className="w-full border rounded-lg p-3 min-h-[100px] text-sm"
                    placeholder="请输入你的答案..."
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                    disabled={!!result}
                  />
                )}

                {result && (
                  <div className="mt-3">
                    <button
                      className="text-sm text-primary flex items-center gap-1"
                      onClick={() => setShowExplanation((prev) => ({ ...prev, [q.id]: !prev[q.id] }))}
                    >
                      <ChevronDown className={`w-3 h-3 transition-transform ${showExplanation[q.id] ? "rotate-180" : ""}`} />
                      {showExplanation[q.id] ? "收起解析" : "查看解析"}
                    </button>
                    {showExplanation[q.id] && (
                      <div className="mt-2 p-3 bg-muted/30 rounded-lg text-sm">
                        <p className="font-medium">正确答案: {result.correct_answer}</p>
                        <p className="mt-1">{result.explanation}</p>
                        <p className="mt-1 text-muted-foreground">{result.feedback}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {questions.length > 0 && !results && (
        <div className="mt-6 flex justify-center">
          <Button
            size="lg"
            onClick={() => submitMutation.mutate()}
            disabled={answeredCount < questions.length || submitMutation.isPending}
          >
            {submitMutation.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : null}
            提交所有答案
          </Button>
        </div>
      )}

      {results && (
        <div className="mt-6 flex justify-center gap-3">
          <Button variant="outline" onClick={() => generateMutation.mutate({ count: 5 })}>
            再来一组
          </Button>
          <Link href={`/courses/${id}/analysis`}>
            <Button>查看薄弱点分析</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
