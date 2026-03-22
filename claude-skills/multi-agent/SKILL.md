---
name: multi-agent
description: Orchestrate parallel sub-agent work with automatic context survival. Use when the user mentions "multi-agent project" or wants multiple tasks handled concurrently by spawned agents. Parses bullet points, dashes, or numbered items as separate sub-agent tasks, creates a monitor agent to track token usage, and handles context handoff at 90% capacity to prevent compaction loss.
---

# Multi-Agent Project Orchestration

Coordinate parallel sub-agents with built-in monitoring and context survival.

## Trigger

Activate when user says "multi-agent project" followed by a list of tasks.

## Workflow

### 1. Parse Tasks

Extract individual tasks from the user's request:
- Bullet points (`•`, `*`)
- Dashes (`-`)
- Numbered lists (`1.`, `2.`)
- Newline-separated items

Each parsed item becomes a sub-agent task.

### 2. Create Task Tracking File

Before spawning agents, create a tracking file:

```bash
# Create tracking file
cat > memory/multi-agent-$(date +%Y%m%d-%H%M%S).json << 'EOF'
{
  "project_id": "<timestamp>",
  "started": "<ISO timestamp>",
  "status": "running",
  "tasks": [
    {"id": 1, "task": "<task text>", "session_key": null, "status": "pending", "tokens_pct": 0}
  ],
  "monitor_session": null
}
EOF
```

### 3. Spawn Monitor Agent First

Create the monitor agent with this task:

```
sessions_spawn:
  label: "monitor-<project_id>"
  task: |
    You are a sub-agent monitor. Your job:
    
    1. Every 2 minutes, check on sibling sessions using sessions_list
    2. For each tracked session, note token usage percentage
    3. When any session reaches 90% token capacity:
       - Use sessions_history to get their recent context
       - Create a summary of: current task state, progress, blockers, next steps
       - Spawn a continuation agent with that summary
       - Update the tracking file with the new session key
    4. Report to main session when all tasks complete or if critical issues arise
    
    Tracking file: memory/multi-agent-<project_id>.json
    
    Check sessions now, then continue monitoring until all tasks complete.
```

### 4. Spawn Task Agents

For each parsed task, spawn a sub-agent:

```
sessions_spawn:
  label: "task-<n>-<project_id>"
  task: |
    <original task text>
    
    CONTEXT RULES:
    - You are part of multi-agent project <project_id>
    - A monitor agent is watching your token usage
    - If you approach 90% capacity, the monitor will create a continuation agent
    - Document your progress in memory/task-<n>-<project_id>.md as you work
    - When complete, update your status in memory/multi-agent-<project_id>.json
```

Update the tracking file with each session key after spawning.

### 5. Report to User

After spawning all agents:

```
✅ Multi-agent project started

📋 Project ID: <id>
🔍 Monitor: <monitor session key>

Tasks spawned:
1. <task 1> → <session key>
2. <task 2> → <session key>
...

Tracking: memory/multi-agent-<id>.json

The monitor agent will handle context handoffs automatically.
I'll receive updates when tasks complete.
```

## Monitor Agent: Context Handoff Protocol

When a task agent reaches 90% tokens:

1. **Capture context** via `sessions_history(sessionKey, limit=50, includeTools=true)`

2. **Generate summary**:
   ```
   ## Task Continuation Context
   
   **Original Task:** <task>
   **Progress:** <what's been done>
   **Current State:** <where we are>
   **Blockers:** <any issues>
   **Next Steps:** <what remains>
   **Key Files:** <relevant paths>
   ```

3. **Spawn continuation**:
   ```
   sessions_spawn:
     label: "task-<n>-cont-<project_id>"
     task: |
       CONTINUATION of task <n> from multi-agent project <project_id>
       
       <summary from step 2>
       
       Continue from where the previous agent left off.
       Update memory/task-<n>-<project_id>.md with your progress.
   ```

4. **Update tracking file** with new session key

## Checking Project Status

User can ask "status of multi-agent project" to get:
- Read the tracking JSON
- Check sessions_list for current token usage
- Report completed/running/pending tasks

## Example

User: "multi-agent project:
- Research competitor X pricing
- Draft email to customer Y about renewal
- Find all Apex classes that reference Lead conversion"

Response:
1. Parse 3 tasks
2. Create tracking file
3. Spawn monitor agent
4. Spawn 3 task agents
5. Report session keys and tracking location
