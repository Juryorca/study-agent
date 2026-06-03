const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const method = options?.method || "GET";
  const headers: Record<string, string> = {};
  // Only set Content-Type for requests with a body
  if (options?.body) {
    headers["Content-Type"] = "application/json";
  }
  if (options?.headers) {
    Object.assign(headers, options.headers);
  }
  const res = await fetch(url, { ...options, method, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// ─── Courses ───
export const api = {
  courses: {
    list: () => request<{ courses: import("@/types").Course[]; total: number }>("/api/courses"),
    get: (id: string) => request<import("@/types").Course>(`/api/courses/${id}`),
    create: (data: { name: string; category?: string; description?: string }) =>
      request<import("@/types").Course>("/api/courses", { method: "POST", body: JSON.stringify(data) }),
    delete: (id: string) => request<{ message: string }>(`/api/courses/${id}`, { method: "DELETE" }),
  },

  documents: {
    list: (courseId?: string) =>
      request<{ documents: import("@/types").Document[]; total: number }>(
        `/api/documents${courseId ? `?course_id=${courseId}` : ""}`
      ),
    upload: async (file: File, courseId: string) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("course_id", courseId);
      const res = await fetch(`${BASE_URL}/api/documents/upload`, { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload failed");
      }
      return res.json();
    },
    embed: (id: string) =>
      request<{ message: string; chunk_count: number }>(`/api/documents/${id}/reindex`, { method: "POST" }),
    delete: (id: string) =>
      request<{ message: string }>(`/api/documents/${id}`, { method: "DELETE" }),
  },

  knowledge: {
    list: (courseId?: string, importance?: string, mastery?: string, chapter?: string, search?: string) => {
      const params = new URLSearchParams();
      if (courseId) params.set("course_id", courseId);
      if (importance) params.set("importance", importance);
      if (mastery) params.set("mastery", mastery);
      if (chapter) params.set("chapter", chapter);
      if (search) params.set("search", search);
      return request<{ knowledge_points: import("@/types").KnowledgePoint[]; total: number }>(
        `/api/knowledge?${params}`
      );
    },
    extract: (courseId: string, documentId: string) =>
      request<{ knowledge_points: import("@/types").KnowledgePoint[]; total: number }>(
        `/api/knowledge/extract?course_id=${courseId}`,
        { method: "POST", body: JSON.stringify({ document_id: documentId }) }
      ),
    extractStream: (
      courseId: string,
      documentId: string,
      onProgress: (msg: string) => void
    ): Promise<{ knowledge_points: import("@/types").KnowledgePoint[]; total: number }> =>
      new Promise((resolve, reject) => {
        fetch(`${BASE_URL}/api/knowledge/extract?course_id=${courseId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ document_id: documentId }),
        })
          .then(async (res) => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const reader = res.body!.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || "";
              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  const data = JSON.parse(line.slice(6));
                  if (data.type === "progress") {
                    onProgress(data.message);
                  } else if (data.type === "done") {
                    resolve({ knowledge_points: data.knowledge_points, total: data.total });
                  }
                }
              }
            }
            reject(new Error("Stream ended without done event"));
          })
          .catch(reject);
      }),
    outlineCreate: (courseId: string, chapter: string) =>
      request<{ outline_id: string; status: string; message: string }>(
        `/api/knowledge/outline?course_id=${courseId}`,
        { method: "POST", body: JSON.stringify({ chapter }) }
      ),
    outlineList: (courseId: string) =>
      request<{ outlines: { id: string; chapter: string; content: string; status: string; error_message?: string; created_at: string }[] }>(
        `/api/knowledge/outline?course_id=${courseId}`
      ),
    outlineDelete: (outlineId: string) =>
      request<{ message: string }>(`/api/knowledge/outline/${outlineId}`, { method: "DELETE" }),
    updateMastery: (id: string, mastery: string) =>
      request<{ id: string; mastery: string }>(`/api/knowledge/${id}/mastery`, {
        method: "PATCH",
        body: JSON.stringify({ mastery }),
      }),
  },

  questions: {
    list: (courseId?: string, knowledgePoint?: string, difficulty?: string, questionType?: string) => {
      const params = new URLSearchParams();
      if (courseId) params.set("course_id", courseId);
      if (knowledgePoint) params.set("knowledge_point", knowledgePoint);
      if (difficulty) params.set("difficulty", difficulty);
      if (questionType) params.set("question_type", questionType);
      return request<{ questions: import("@/types").Question[]; total: number }>(`/api/questions?${params}`);
    },
    generate: (courseId: string, data: { knowledge_point?: string; question_type?: string; count?: number; difficulty?: string }) =>
      request<{ questions: import("@/types").Question[]; total: number }>(
        `/api/questions/generate?course_id=${courseId}`,
        { method: "POST", body: JSON.stringify(data) }
      ),
  },

  answers: {
    submit: (questionId: string, studentAnswer: string) =>
      request<import("@/types").AnswerResult>("/api/answers/submit?user_id=default", {
        method: "POST",
        body: JSON.stringify({ question_id: questionId, student_answer: studentAnswer }),
      }),
    submitBatch: (answers: { question_id: string; student_answer: string }[]) =>
      request<import("@/types").AnswerBatchResult>("/api/answers/submit-batch?user_id=default", {
        method: "POST",
        body: JSON.stringify({ answers }),
      }),
  },

  analysis: {
    weakness: (courseId: string) =>
      request<import("@/types").WeaknessReport>(`/api/analysis/weakness/${courseId}?user_id=default`, {
        method: "POST",
      }),
  },

  agent: {
    chatSync: (message: string, courseId?: string) =>
      request<{ response: string }>("/api/agent/chat/sync", {
        method: "POST",
        body: JSON.stringify({ message, course_id: courseId || "", user_id: "default" }),
      }),
    reset: () => request<{ message: string }>("/api/agent/reset?user_id=default", { method: "POST" }),
    sessions: {
      list: (courseId?: string) =>
        request<{ sessions: import("@/types").ChatSession[]; total: number }>(
          `/api/agent/sessions${courseId ? `?course_id=${courseId}` : ""}`
        ),
      create: (data: { course_id?: string; title?: string }) =>
        request<import("@/types").ChatSession>("/api/agent/sessions", {
          method: "POST", body: JSON.stringify(data),
        }),
      delete: (id: string) =>
        request<{ message: string }>(`/api/agent/sessions/${id}`, { method: "DELETE" }),
      messages: (id: string) =>
        request<{ messages: import("@/types").ChatMessage[]; total: number }>(
          `/api/agent/sessions/${id}/messages`
        ),
    },
  },

  exams: {
    generate: (courseId: string, data: import("@/types").ExamConfig & { title?: string }) =>
      request<import("@/types").ExamPaperDetail>(`/api/exams/generate?course_id=${courseId}`, {
        method: "POST", body: JSON.stringify({ config: data, title: data.title || "新试卷" }),
      }),
    list: (courseId: string, status?: string) => {
      const params = new URLSearchParams();
      if (courseId) params.set("course_id", courseId);
      if (status) params.set("status", status);
      return request<{ papers: import("@/types").ExamPaper[]; total: number }>(`/api/exams?${params}`);
    },
    get: (id: string) => request<import("@/types").ExamPaperDetail>(`/api/exams/${id}`),
    saveAnswer: (examId: string, questionId: string, studentAnswer: string) =>
      request<{ message: string }>(`/api/exams/${examId}/answer`, {
        method: "PUT", body: JSON.stringify({ question_id: questionId, student_answer: studentAnswer }),
      }),
    saveDraft: (examId: string) =>
      request<{ message: string }>(`/api/exams/${examId}/save`, { method: "POST" }),
    submit: (examId: string) =>
      request<import("@/types").ExamPaperDetail>(`/api/exams/${examId}/submit`, { method: "POST" }),
    delete: (examId: string) =>
      request<{ message: string }>(`/api/exams/${examId}`, { method: "DELETE" }),
  },
};
