"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function NewExamPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [choiceCount, setChoiceCount] = useState(20);
  const [saCount, setSaCount] = useState(5);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const result = await api.exams.generate(id, {
        title: title || "新试卷",
        choice_count: choiceCount,
        short_answer_count: saCount,
        difficulty_distribution: { easy: 0.3, medium: 0.5, hard: 0.2 },
      });
      router.push(`/courses/${id}/exams/${result.paper.id}`);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <Link href={`/courses/${id}/exams`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回试卷列表
      </Link>

      <Card>
        <CardHeader>
          <CardTitle>生成新试卷</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">试卷名称</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="如：期末模拟卷" className="mt-1" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">选择题数量</label>
              <Input type="number" min={0} max={50} value={choiceCount} onChange={(e) => setChoiceCount(+e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">简答题数量</label>
              <Input type="number" min={0} max={20} value={saCount} onChange={(e) => setSaCount(+e.target.value)} className="mt-1" />
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            难度分布：简单 30% / 中等 50% / 困难 20%。可从题库抽取已有题目，不足时自动生成。
          </p>

          <Button onClick={handleGenerate} disabled={loading || (choiceCount === 0 && saCount === 0)} className="w-full">
            {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            生成试卷
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
