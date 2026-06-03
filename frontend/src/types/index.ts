export interface Course {
  id: string;
  user_id: string;
  name: string;
  category: string;
  description: string;
  created_at: string;
}

export interface Document {
  id: string;
  course_id: string;
  filename: string;
  file_type: string;
  status: string;
  chunk_count: number;
  error_message: string;
  created_at: string;
}

export type Mastery = "unlearned" | "learning" | "mastered";

export interface KnowledgePoint {
  id: string;
  course_id: string;
  chapter: string;
  name: string;
  description: string;
  importance: "high" | "medium" | "low";
  mastery: Mastery;
  source: string;
  created_at: string;
}

export interface Question {
  id: string;
  course_id: string;
  knowledge_point_id: string;
  knowledge_point: string;
  question_type: "single_choice" | "short_answer" | "true_false";
  stem: string;
  options: Record<string, string>;
  answer: string;
  explanation: string;
  difficulty: "easy" | "medium" | "hard";
  source: string;
  created_at: string;
}

export interface AnswerResult {
  question_id: string;
  is_correct: boolean;
  score: number;
  max_score: number;
  correct_answer: string;
  explanation: string;
  feedback: string;
}

export interface AnswerBatchResult {
  results: AnswerResult[];
  total_score: number;
  max_total_score: number;
  correct_count: number;
  total_count: number;
}

export interface WeaknessPoint {
  knowledge_point: string;
  total_attempts: number;
  wrong_count: number;
  error_rate: number;
  suggestion: string;
}

export interface WeaknessReport {
  course_id: string;
  user_id: string;
  weak_points: WeaknessPoint[];
  report_text: string;
  study_plan: string;
}

export interface AgentChatEvent {
  type: "text" | "tool_call" | "tool_result" | "done" | "error";
  content?: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  tool_result?: string;
}

export interface PaginatedResponse<T> {
  [key: string]: T[] | number;
  total: number;
}

export interface ChatSession {
  id: string;
  course_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: string;
  content: string;
  tool_name: string;
  tool_args: unknown;
  created_at: string;
}

export type ExamStatus = "draft" | "in_progress" | "submitted" | "graded";

export interface ExamConfig {
  choice_count: number;
  short_answer_count: number;
  difficulty_distribution: Record<string, number>;
}

export interface ExamPaper {
  id: string;
  course_id: string;
  title: string;
  config: ExamConfig;
  status: ExamStatus;
  total_score: number;
  earned_score: number;
  created_at: string;
  updated_at: string;
}

export interface ExamQuestion {
  id: string;
  paper_id: string;
  question_id: string;
  question_type: "single_choice" | "short_answer" | "true_false";
  stem: string;
  options: Record<string, string>;
  max_score: number;
  order: number;
  student_answer: string;
  score: number;
  is_correct: boolean;
  feedback: string;
}

export interface ExamPaperDetail {
  paper: ExamPaper;
  questions: ExamQuestion[];
}
