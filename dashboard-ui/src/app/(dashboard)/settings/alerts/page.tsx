"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, Plus, ChevronDown, ChevronUp, Trash2 } from "lucide-react";

interface AlertRule {
  name: string;
  enabled: boolean;
  detector: string;
  field: string;
  operator: string;
  value: number;
  durationSeconds: number;
  severity: string;
  message: string;
  cooldownSeconds: number;
}

export default function AlertSettingsPage() {
  const rules = useQuery(api.alertRules.list);
  const seedDefaults = useMutation(api.alertRules.seedDefaults);
  const upsertRule = useMutation(api.alertRules.upsert);
  const toggleRule = useMutation(api.alertRules.toggle);
  const removeRule = useMutation(api.alertRules.remove);

  const [expandedRule, setExpandedRule] = useState<string | null>(null);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  // Seed defaults if no rules exist
  useEffect(() => {
    if (rules !== undefined && rules.length === 0) {
      seedDefaults({});
    }
  }, [rules, seedDefaults]);

  const handleToggle = async (name: string) => {
    await toggleRule({ name });
  };

  const handleEdit = (rule: AlertRule) => {
    setEditingRule({ ...rule });
    setExpandedRule(rule.name);
  };

  const handleSave = async () => {
    if (!editingRule) return;
    await upsertRule(editingRule);
    setEditingRule(null);
  };

  const handleDelete = async (name: string) => {
    if (confirm(`Delete rule "${name}"?`)) {
      await removeRule({ name });
    }
  };

  const severityColors: Record<string, string> = {
    critical: "bg-danger/20 text-danger border-danger/50",
    warning: "bg-warning/20 text-warning border-warning/50",
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Alert Rules</h2>
        <p className="text-sm text-muted-foreground">
          Configure when alerts are triggered based on vital signs
        </p>
      </div>

      {/* Rules list */}
      <div className="space-y-3">
        {rules?.map((rule) => {
          const isExpanded = expandedRule === rule.name;
          const isEditing = editingRule?.name === rule.name;

          return (
            <Card key={rule.name}>
              <CardContent className="p-0">
                {/* Rule header */}
                <div
                  className="p-4 flex items-center justify-between cursor-pointer"
                  onClick={() =>
                    setExpandedRule(isExpanded ? null : rule.name)
                  }
                >
                  <div className="flex items-center gap-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggle(rule.name);
                      }}
                      className={`relative w-10 h-5 rounded-full transition-colors ${
                        rule.enabled ? "bg-primary" : "bg-muted"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                          rule.enabled ? "translate-x-5" : ""
                        }`}
                      />
                    </button>
                    <div>
                      <p className="font-medium">{rule.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {rule.detector} · {rule.field.split(".").pop()} {rule.operator}{" "}
                        {rule.value}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium border ${
                        severityColors[rule.severity] || "bg-muted"
                      }`}
                    >
                      {rule.severity}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </div>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="border-t p-4 space-y-4">
                    {isEditing ? (
                      <>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Threshold Value
                            </label>
                            <input
                              type="number"
                              value={editingRule.value}
                              onChange={(e) =>
                                setEditingRule((prev) =>
                                  prev
                                    ? { ...prev, value: Number(e.target.value) }
                                    : null
                                )
                              }
                              className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Duration (seconds)
                            </label>
                            <input
                              type="number"
                              value={editingRule.durationSeconds}
                              onChange={(e) =>
                                setEditingRule((prev) =>
                                  prev
                                    ? {
                                        ...prev,
                                        durationSeconds: Number(e.target.value),
                                      }
                                    : null
                                )
                              }
                              className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Severity
                            </label>
                            <select
                              value={editingRule.severity}
                              onChange={(e) =>
                                setEditingRule((prev) =>
                                  prev
                                    ? { ...prev, severity: e.target.value }
                                    : null
                                )
                              }
                              className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                            >
                              <option value="warning">Warning</option>
                              <option value="critical">Critical</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Cooldown (seconds)
                            </label>
                            <input
                              type="number"
                              value={editingRule.cooldownSeconds}
                              onChange={(e) =>
                                setEditingRule((prev) =>
                                  prev
                                    ? {
                                        ...prev,
                                        cooldownSeconds: Number(e.target.value),
                                      }
                                    : null
                                )
                              }
                              className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            Message
                          </label>
                          <input
                            type="text"
                            value={editingRule.message}
                            onChange={(e) =>
                              setEditingRule((prev) =>
                                prev
                                  ? { ...prev, message: e.target.value }
                                  : null
                              )
                            }
                            className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                          />
                        </div>

                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingRule(null)}
                            className="flex-1 px-3 py-2 rounded-md border hover:bg-muted transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={handleSave}
                            className="flex-1 px-3 py-2 rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
                          >
                            Save
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-muted-foreground">Threshold</p>
                            <p className="font-medium">
                              {rule.field.split(".").pop()} {rule.operator} {rule.value}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Duration</p>
                            <p className="font-medium">{rule.durationSeconds}s</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Cooldown</p>
                            <p className="font-medium">{rule.cooldownSeconds}s</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Detector</p>
                            <p className="font-medium capitalize">{rule.detector}</p>
                          </div>
                        </div>

                        <div className="text-sm">
                          <p className="text-muted-foreground">Message</p>
                          <p className="font-medium">{rule.message}</p>
                        </div>

                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEdit(rule)}
                            className="flex-1 px-3 py-2 rounded-md border hover:bg-muted transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(rule.name)}
                            className="px-3 py-2 rounded-md border border-danger/50 text-danger hover:bg-danger/10 transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Empty state */}
      {rules?.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="p-3 rounded-full bg-muted inline-block mb-3">
              <AlertTriangle className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="font-medium mb-1">No alert rules</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Default rules will be created automatically
            </p>
            <button
              onClick={() => seedDefaults({})}
              className="px-4 py-2 rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
            >
              Create Default Rules
            </button>
          </CardContent>
        </Card>
      )}

      {/* Info text */}
      <p className="text-xs text-muted-foreground text-center">
        Changes to alert rules will be synced to the backend on next restart
      </p>
    </div>
  );
}
