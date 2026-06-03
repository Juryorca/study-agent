"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, FileText, Clock, CheckCircle, XCircle, Loader2, Trash2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Document } from "@/types";

const processingStatuses = new Set(["uploaded", "parsing", "embedding"]);

const statusConfig: Record<string, { icon: typeof CheckCircle; label: string; className: string }> = {
  uploaded: { icon: Clock, label: "等待处理", className: "bg-yellow-100 text-yellow-800" },
  parsing: { icon: RefreshCw, label: "解析中", className: "bg-blue-100 text-blue-800" },
  chunked: { icon: FileText, label: "待索引", className: "bg-orange-100 text-orange-800" },
  embedding: { icon: RefreshCw, label: "索引中", className: "bg-blue-100 text-blue-800" },
  completed: { icon: CheckCircle, label: "已完成", className: "bg-green-100 text-green-800" },
  failed: { icon: XCircle, label: "失败", className: "bg-red-100 text-red-800" },
};

export default function UploadPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");

  const { data: docsData, isLoading } = useQuery({
    queryKey: ["documents", id],
    queryFn: () => api.documents.list(id),
    refetchInterval: (query) => {
      // Auto-poll while any document is still processing
      const docs = query.state.data?.documents;
      if (!docs || docs.length === 0) return false;
      return docs.some((d: Document) => processingStatuses.has(d.status)) ? 2000 : false;
    },
  });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowed = [".pdf", ".pptx", ".txt", ".md"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowed.includes(ext)) {
      setUploadMsg(`不支持的文件类型: ${ext}，请上传 PDF/PPTX/TXT/MD 文件`);
      return;
    }

    setUploading(true);
    setUploadMsg("");
    try {
      const result = await api.documents.upload(file, id);
      setUploadMsg(result.message);
      queryClient.invalidateQueries({ queryKey: ["documents", id] });
    } catch (err: any) {
      setUploadMsg(`上传失败: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const embedMutation = useMutation({
    mutationFn: (docId: string) => api.documents.embed(docId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", id] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => api.documents.delete(docId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents", id] }),
  });

  const processingCount = useMemo(() => {
    if (!docsData?.documents) return 0;
    return docsData.documents.filter((d: Document) => processingStatuses.has(d.status)).length;
  }, [docsData]);

  if (isLoading) return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mt-24" />;

  return (
    <div className="max-w-3xl mx-auto">
      <Link href={`/courses/${id}`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回课程
      </Link>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">资料上传</h1>
        {processingCount > 0 && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <RefreshCw className="w-4 h-4 animate-spin" />
            正在处理 {processingCount} 个文件...
          </div>
        )}
      </div>

      <Card className="mb-6">
        <CardContent className="pt-6">
          <label className="flex flex-col items-center gap-4 p-8 border-2 border-dashed rounded-lg cursor-pointer hover:border-primary transition-colors">
            <Upload className="w-10 h-10 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {uploading ? "上传中..." : "点击选择文件（支持 PDF / PPTX / TXT / MD）"}
            </span>
            <input type="file" accept=".pdf,.pptx,.txt,.md" onChange={handleUpload} disabled={uploading} className="hidden" />
          </label>
          {uploadMsg && <p className={`mt-4 text-sm ${uploadMsg.includes("失败") ? "text-red-600" : "text-green-600"}`}>{uploadMsg}</p>}
        </CardContent>
      </Card>

      <h2 className="font-semibold mb-4">已上传资料 ({docsData?.total || 0})</h2>
      <div className="space-y-3">
        {docsData?.documents?.map((doc: Document) => {
          const cfg = statusConfig[doc.status] || statusConfig.uploaded;
          const Icon = cfg.icon;
          return (
            <Card key={doc.id}>
              <CardContent className="flex items-center justify-between py-4">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{doc.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(doc.created_at).toLocaleString("zh-CN")}
                      {doc.chunk_count > 0 && ` · ${doc.chunk_count} 个文本块`}
                    </p>
                    {doc.error_message && (
                      <p className={`text-xs mt-1 ${doc.status === "failed" ? "text-red-600" : "text-amber-600"}`}>
                        {doc.error_message}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={cfg.className}>
                    <Icon className={`w-3 h-3 mr-1 ${processingStatuses.has(doc.status) ? "animate-spin" : ""}`} />
                    {cfg.label}
                  </Badge>
                  {doc.status === "chunked" && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs"
                      disabled={embedMutation.isPending}
                      onClick={() => embedMutation.mutate(doc.id)}
                    >
                      {embedMutation.isPending && embedMutation.variables === doc.id ? (
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      ) : null}
                      索引
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    title="删除资料"
                    onClick={() => {
                      if (confirm(`确定删除「${doc.filename}」？`)) {
                        deleteMutation.mutate(doc.id);
                      }
                    }}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {(!docsData?.documents || docsData.documents.length === 0) && (
          <p className="text-center text-muted-foreground py-8">暂无上传资料</p>
        )}
      </div>
    </div>
  );
}
