import React from "react";
import { MeetingWorkspace } from "@/components/features/meeting/MeetingWorkspace";
import { DEMO_SESSION_ID } from "@/lib/hooks/useMeeting";

export default function HomePage() {
  return <MeetingWorkspace sessionId={DEMO_SESSION_ID} />;
}
