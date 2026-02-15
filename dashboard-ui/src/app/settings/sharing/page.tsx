"use client";

import { useState } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Link as LinkIcon, Copy, Trash2, Plus, Check } from "lucide-react";

export default function SharingSettingsPage() {
  const shareLinks = useQuery(api.sharing.list);
  const createLink = useMutation(api.sharing.create);
  const revokeLink = useMutation(api.sharing.revoke);
  const removeLink = useMutation(api.sharing.remove);

  const [isCreating, setIsCreating] = useState(false);
  const [newLinkName, setNewLinkName] = useState("");
  const [newLinkPermissions, setNewLinkPermissions] = useState<"view" | "view+pause">("view");
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newLinkName.trim()) return;

    await createLink({
      name: newLinkName.trim(),
      permissions: newLinkPermissions,
    });

    setNewLinkName("");
    setIsCreating(false);
  };

  const handleCopy = async (token: string) => {
    const url = `${window.location.origin}/shared/${token}`;
    await navigator.clipboard.writeText(url);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const activeLinks = shareLinks?.filter((link) => link.active) ?? [];
  const inactiveLinks = shareLinks?.filter((link) => !link.active) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Share Access</h2>
        <p className="text-sm text-muted-foreground">
          Create links to share dashboard access with family and caregivers
        </p>
      </div>

      {/* Create new link */}
      {!isCreating ? (
        <button
          onClick={() => setIsCreating(true)}
          className="flex items-center gap-2 px-4 py-3 w-full rounded-lg border border-dashed hover:border-muted-foreground/50 hover:bg-muted/50 transition-colors text-muted-foreground"
        >
          <Plus className="h-4 w-4" />
          Create share link
        </button>
      ) : (
        <Card>
          <CardContent className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">
                Link Name
              </label>
              <input
                type="text"
                value={newLinkName}
                onChange={(e) => setNewLinkName(e.target.value)}
                placeholder="e.g., Grandma's link"
                className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">
                Permissions
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setNewLinkPermissions("view")}
                  className={`flex-1 px-3 py-2 rounded-md text-sm transition-colors ${
                    newLinkPermissions === "view"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  View only
                </button>
                <button
                  onClick={() => setNewLinkPermissions("view+pause")}
                  className={`flex-1 px-3 py-2 rounded-md text-sm transition-colors ${
                    newLinkPermissions === "view+pause"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  View + Pause
                </button>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setIsCreating(false)}
                className="flex-1 px-3 py-2 rounded-md border hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!newLinkName.trim()}
                className="flex-1 px-3 py-2 rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active links */}
      {activeLinks.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">
            Active Links
          </h3>
          {activeLinks.map((link) => (
            <Card key={link.token}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="p-2 rounded-full bg-success/20 text-success">
                      <LinkIcon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium truncate">{link.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {link.permissions === "view+pause"
                          ? "Can view and pause"
                          : "View only"}{" "}
                        · Created {formatDate(link.createdAt)}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleCopy(link.token)}
                      className="p-2 rounded-md hover:bg-muted transition-colors"
                      title="Copy link"
                    >
                      {copiedToken === link.token ? (
                        <Check className="h-4 w-4 text-success" />
                      ) : (
                        <Copy className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                    <button
                      onClick={() => revokeLink({ token: link.token })}
                      className="p-2 rounded-md hover:bg-danger/20 transition-colors"
                      title="Revoke link"
                    >
                      <Trash2 className="h-4 w-4 text-danger" />
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Inactive/revoked links */}
      {inactiveLinks.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">
            Revoked Links
          </h3>
          {inactiveLinks.map((link) => (
            <Card key={link.token} className="opacity-60">
              <CardContent className="p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-muted text-muted-foreground">
                      <LinkIcon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="font-medium">{link.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Revoked · Created {formatDate(link.createdAt)}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => removeLink({ token: link.token })}
                    className="p-2 rounded-md hover:bg-muted transition-colors"
                    title="Delete permanently"
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty state */}
      {shareLinks?.length === 0 && !isCreating && (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="p-3 rounded-full bg-muted inline-block mb-3">
              <LinkIcon className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="font-medium mb-1">No share links yet</h3>
            <p className="text-sm text-muted-foreground">
              Create a link to share dashboard access with family members
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
