import React, { Suspense } from "react";
import { MeetingWorkspace } from "@/components/features/meeting/MeetingWorkspace";

interface MeetingDetailPageProps {
  params: {
    sessionId: string;
  };
}

export default function MeetingDetailPage({ params }: MeetingDetailPageProps) {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F6F8FC]" />}>
      <MeetingWorkspace sessionId={params.sessionId} />
    </Suspense>
  );
}
