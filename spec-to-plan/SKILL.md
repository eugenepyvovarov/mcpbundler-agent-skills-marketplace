---
name: spec-to-plan
description: "Transform project descriptions and feature requests into comprehensive specifications and actionable task lists. Use when the user wants to: (1) Create a specification from a project/feature description, (2) Generate a detailed plan with task breakdown, (3) Clarify requirements before implementation, (4) Convert ideas into structured development plans with progress tracking. Works with or without existing codebase files."
---

# Spec-to-Plan Skill

This skill guides the process of transforming project descriptions into clear specifications and actionable task lists for developers.

## Process Overview

The skill follows a five-phase workflow:

1. **Create Initial Specification** - Analyze the feature/project description
2. **Clarify Questions** - Identify and resolve all ambiguities
3. **Generate Markdown Spec** - Produce detailed specification document (presented as `spec.md` in chat)
4. **Create Comprehensive Todo** - Break down into implementable tasks
5. **Output Plan Markdown** - Generate final `plan.md` with progress tracking (presented in chat)

**Final deliverables:** Both specification and plan content are provided as markdown in the conversation.

## Phase 1: Initial Specification

Load the prompt template from `references/phase1_spec_prompt.md` and fill in the feature description provided by the user.

**Key principles:**
- If files are provided, analyze the codebase thoroughly
- If no files, work from the task description or ask for detailed project description
- Identify dependencies, structure, and integration points
- Note edge cases (within reason - ask about scope depth)
- List ALL unclear or ambiguous points

**Do NOT implement yet** - only analyze and prepare questions.

## Phase 2: Clarify Questions

Ask all clarification questions at once. After receiving answers:
- If more questions persist, ask them
- Continue until no ambiguities remain
- Do NOT assume any requirements beyond explicitly described details

**Scope control:**
- Ask the user about desired depth and scope when uncertain
- Avoid going overboard with edge cases unless specifically requested
- Focus on what's explicitly needed

## Phase 3: Generate Markdown Spec

After all questions are answered, create a comprehensive specification document and present it in the chat:

**Content requirements:**
- No specific template required (flexible format)
- Should be clear, detailed, and implementation-ready
- Include all decisions and clarifications from the Q&A phase
- Document the full feature/project specification

**Output:**
- Present the complete `spec.md` content directly in the chat
- Use a clear header to indicate this is the specification document

## Phase 4: Create Comprehensive Todo

Load the prompt template from `references/phase2_plan_prompt.md`.

Generate a detailed task breakdown that includes:
- Status tracking with emojis (🟩 Done, 🟨 In Progress, 🟥 To Do)
- Overall progress percentage at the top
- Confirmed decisions section
- Modular, minimal steps
- Important implementation details
- File-level changes (Add/Modify/Keep sections)
- Progress calculations

**Critical:** Do NOT add extra scope or unnecessary complexity beyond what was explicitly clarified.

## Phase 5: Output Plan Markdown

Create the final `plan.md` content and present it in the chat:

**Content requirements:**
- Clear structure following the template in `phase2_plan_prompt.md`
- Checkbox tasks with status emojis
- Dynamic progress tracking
- Implementation details section
- File changes section listing specific files and modifications needed

**Output:**
- Present the complete `plan.md` content directly in the chat
- Use a clear header to indicate this is the implementation plan

Both the specification and plan are provided as markdown content in the conversation.

## Workflow Tips

**When to analyze codebase:**
- If user provides files → analyze them thoroughly
- If no files → work from description or ask for project details

**Question iteration:**
- Ask comprehensive questions in each round
- Wait for all answers before proceeding
- Continue asking until complete clarity is achieved

**Scope management:**
- Always ask about desired depth when uncertain
- Keep steps elegant and minimal
- Ensure seamless integration with existing codebase

**Output quality:**
- Plans should lead to simple, elegant, minimal code
- No extra complexity beyond discussed requirements
- All steps should be modular and implementable

## Reference Files

- `references/phase1_spec_prompt.md` - Initial specification prompt template
- `references/phase2_plan_prompt.md` - Plan generation prompt with examples
