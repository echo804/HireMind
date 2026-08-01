#!/bin/bash
cd /mnt/d/codexproject/codexproject/HireMind/frontend/src

# InterviewList (py-8)
sed -i 's|<div className="text-center py-8 text-slate-400">加载中...</div>|<TableSkeleton rows={4} />|g' pages/InterviewList.tsx

# CardSkeleton pages
for f in pages/ResumeList.tsx pages/KnowledgeBase.tsx; do
  sed -i 's|<div className="text-center py-12 text-slate-400">加载中...</div>|<CardSkeleton count={3} />|g' "$f"
done

# DetailSkeleton pages
for f in pages/ResumeDetail.tsx pages/KnowledgeBaseDetail.tsx pages/InterviewReport.tsx; do
  sed -i 's|<div className="text-center py-12 text-slate-400">加载中...</div>|<DetailSkeleton />|g' "$f"
done

# Special counts
sed -i 's|<div className="text-center py-12 text-slate-400">加载中...</div>|<CardSkeleton count={1} />|g' pages/Settings.tsx
sed -i 's|<div className="text-center py-12 text-slate-400">加载中...</div>|<CardSkeleton count={4} />|g' pages/Home.tsx
sed -i 's|<div className="text-center py-12 text-slate-400">加载中...</div>|<TableSkeleton rows={4} />|g' pages/Schedule.tsx

echo "done"
