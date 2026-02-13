"use client";

import { useState } from "react";
import { useMutation } from "convex/react";
import { api } from "../../../convex/_generated/api";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Pause, Play } from "lucide-react";

interface PauseButtonProps {
  isPaused: boolean;
  remainingMinutes?: number;
}

export function PauseButton({ isPaused, remainingMinutes }: PauseButtonProps) {
  const pause = useMutation(api.system.pause);
  const resume = useMutation(api.system.resume);

  const handlePause = async (minutes: number) => {
    await pause({ durationMinutes: minutes });
  };

  const handleResume = async () => {
    await resume();
  };

  if (isPaused) {
    return (
      <Button variant="warning" size="sm" onClick={handleResume}>
        <Play className="h-4 w-4 mr-2" />
        Resume ({remainingMinutes}m)
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Pause className="h-4 w-4 mr-2" />
          Pause
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handlePause(5)}>
          Pause for 5 minutes
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handlePause(15)}>
          Pause for 15 minutes
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handlePause(30)}>
          Pause for 30 minutes
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handlePause(60)}>
          Pause for 1 hour
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
