#!/bin/bash
cd /mnt/d/codexproject/codexproject/HireMind/frontend/src

# InterviewList already has import via the edit_file above
# ResumeList
sed -i '1s|^|import { CardSkeleton } from "../components/Skeleton";\n|' pages/ResumeList.tsx

# KnowledgeBase
sed -i '3s|^|import { CardSkeleton } from "../components/Skeleton";\n|' pages/KnowledgeBase.tsx

# ResumeDetail
sed -i '3s|^|import { DetailSkeleton } from "../components/Skeleton";\n|' pages/ResumeDetail.tsx

# KnowledgeBaseDetail
sed -i '3s|^|import { DetailSkeleton } from "../components/Skeleton";\n|' pages/KnowledgeBaseDetail.tsx

# InterviewReport
sed -i '4s|^|import { DetailSkeleton } from "../components/Skeleton";\n|' pages/InterviewReport.tsx

# Settings
sed -i '1s|^|import { CardSkeleton } from "../components/Skeleton";\n|' pages/Settings.tsx

# Home
sed -i '3s|^|import { CardSkeleton } from "../components/Skeleton";\n|' pages/Home.tsx

# Schedule
sed -i '1s|^|import { TableSkeleton } from "../components/Skeleton";\n|' pages/Schedule.tsx

echo "imports done"
