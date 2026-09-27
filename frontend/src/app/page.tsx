import React, { Suspense } from "react";
import { MeetingWorkspace } from "@/components/features/meeting/MeetingWorkspace";
import { DEMO_SESSION_ID } from "@/lib/hooks/useMeeting";

export default function HomePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#F6F8FC]" />}>
      <MeetingWorkspace sessionId={DEMO_SESSION_ID} />
    </Suspense>
  );
}
