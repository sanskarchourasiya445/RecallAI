import React from "react";
import { MeetingWorkspace } from "@/components/features/meeting/MeetingWorkspace";

interface MeetingDetailPageProps {
  params: {
    sessionId: string;
  };
}

export default function MeetingDetailPage({ params }: MeetingDetailPageProps) {
  return <MeetingWorkspace sessionId={params.sessionId} />;
}
