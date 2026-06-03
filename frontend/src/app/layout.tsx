import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar } from "@/components/layout/sidebar";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Study Agent - 个性化课程复习智能体",
  description: "基于 RAG 与 Tool Calling 的个性化课程复习智能体",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex">
        <Providers>
          <Sidebar />
          <main className="flex-1 overflow-auto p-6 lg:p-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
