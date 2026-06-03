"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { KnowledgePoint, Mastery } from "@/types";

const importanceLabels: Record<string, string> = { high: "重要", medium: "中等", low: "一般" };
const importanceColors: Record<string, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

interface Props {
  points: KnowledgePoint[];
  onMastery: (id: string, mastery: Mastery) => void;
  onClose: () => void;
}

export default function FlashcardView({ points, onMastery, onClose }: Props) {
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const current = points[idx];

  if (!current) {
    return (
      <Card className="text-center py-12">
        <CardContent>
          <p className="text-muted-foreground">暂无知识点</p>
          <Button variant="outline" className="mt-4" onClick={onClose}>返回列表</Button>
        </CardContent>
      </Card>
    );
  }

  const go = (delta: number) => {
    setFlipped(false);
    setIdx((idx + delta + points.length) % points.length);
  };

  const mark = (mastery: Mastery) => {
    onMastery(current.id, mastery);
    if (idx < points.length - 1) go(1);
  };

  return (
    <div className="space-y-4">
      {/* Progress */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <Button variant="ghost" size="sm" onClick={onClose}>← 返回列表</Button>
        <span>{idx + 1} / {points.length}</span>
        <Button variant="ghost" size="sm" onClick={() => setFlipped(false)}>
          <RotateCcw className="w-4 h-4 mr-1" /> 翻转
        </Button>
      </div>

      {/* Card */}
      <div
        className="min-h-[240px] cursor-pointer perspective-1000"
        onClick={() => setFlipped(!flipped)}
      >
        <Card className={`relative h-full transition-all duration-300 min-h-[240px] flex items-center justify-center ${
          flipped ? "bg-blue-50 border-blue-200" : "hover:shadow-md"
        }`}>
          <CardContent className="py-8 text-center">
            {flipped ? (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground leading-relaxed">{current.description}</p>
                {current.source && (
                  <p className="text-xs text-muted-foreground">来源: {current.source}</p>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <h3 className="text-xl font-bold">{current.name}</h3>
                <div className="flex items-center justify-center gap-2">
                  <Badge className={importanceColors[current.importance]}>
                    {importanceLabels[current.importance]}
                  </Badge>
                  <Badge variant="outline">
                    {current.mastery === "mastered" ? "已掌握" : current.mastery === "learning" ? "学习中" : "未学习"}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-4">点击翻转查看详情</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="outline" size="icon" onClick={() => go(-1)}>
          <ChevronLeft className="w-5 h-5" />
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" className="border-red-200 hover:bg-red-50 text-red-700"
            onClick={() => mark("unlearned")}>
            不熟
          </Button>
          <Button variant="outline" className="border-yellow-200 hover:bg-yellow-50 text-yellow-700"
            onClick={() => mark("learning")}>
            学习中
          </Button>
          <Button className="bg-green-600 hover:bg-green-700"
            onClick={() => mark("mastered")}>
            已掌握
          </Button>
        </div>
        <Button variant="outline" size="icon" onClick={() => go(1)}>
          <ChevronRight className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
}
