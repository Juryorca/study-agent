"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Lightbulb, Bot, Home } from "lucide-react";
import { cn } from "@/lib/utils";
import { SettingsDialog } from "./settings-dialog";

const navItems = [
  { href: "/", label: "首页", icon: Home },
  { href: "/courses", label: "课程管理", icon: BookOpen },
  { href: "/agent", label: "AI 对话", icon: Bot },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-muted/30 hidden lg:flex flex-col shrink-0">
      <div className="p-6 border-b">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <Lightbulb className="w-6 h-6 text-primary" />
          <span>Study Agent</span>
        </Link>
        <p className="text-xs text-muted-foreground mt-1">个性化课程复习智能体</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t flex items-center justify-between text-xs text-muted-foreground">
        <span>Study Agent v0.1</span>
        <SettingsDialog />
      </div>
    </aside>
  );
}
