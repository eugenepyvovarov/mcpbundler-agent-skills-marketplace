# mcpbundler-agent-skills-marketplace

Marketplace for Agent skills curated for the MCPBundler app(https://mcpbundler.com)

Owner: eugenepyvovarov

## Categories

- [AI/Machine Learning](#aimachine-learning)
- [Development](#development)
- [Productivity](#productivity)
- [Swift Development](#swift-development)

### AI/Machine Learning

| Skill | Description |
| --- | --- |
| `hf-cli` | Execute Hugging Face Hub operations using the `hf` CLI. Use when the user needs to download models/datasets/spaces, upload files to Hub repositories, create repos, manage local cache, or run compute jobs on HF infrastructure. Covers authentication, file transfers, repository creation, cache operations, and cloud compute.<br><br>Origin: https://github.com/huggingface/skills |
| `hf-tool-builder` | Use this skill when the user wants to build tool/scripts or achieve a task where using data from the Hugging Face API would help. This is especially useful when chaining or combining API calls or the task will be repeated/automated. This Skill creates a reusable script to fetch, enrich or process data.<br><br>Origin: https://github.com/huggingface/skills |
| `hugging-face-evaluation-manager` | Add and manage evaluation results in Hugging Face model cards. Supports extracting eval tables from README content, importing scores from Artificial Analysis API, and running custom model evaluations with vLLM/lighteval. Works with the model-index metadata format.<br><br>Origin: https://github.com/huggingface/skills |
| `hugging-face-paper-publisher` | Publish and manage research papers on Hugging Face Hub. Supports creating paper pages, linking papers to models/datasets, claiming authorship, and generating professional markdown-based research articles.<br><br>Origin: https://github.com/huggingface/skills |
| `model-trainer` | This skill should be used when users want to train or fine-tune language models using TRL (Transformer Reinforcement Learning) on Hugging Face Jobs infrastructure. Covers SFT, DPO, GRPO and reward modeling training methods, plus GGUF conversion for local deployment. Includes guidance on the TRL Jobs package, UV scripts with PEP 723 format, dataset preparation and validation, hardware selection, cost estimation, Trackio monitoring, Hub authentication, and model persistence. Should be invoked for tasks involving cloud GPU training, GGUF conversion, or when users mention training on Hugging Face Jobs without local GPU setup.<br><br>Origin: https://github.com/huggingface/skills |

### Development

| Skill | Description |
| --- | --- |
| `enterprise-readiness-skill` | Assess and enhance software projects for enterprise-grade security, quality, and automation. Use when evaluating projects for production readiness, implementing supply chain security (SLSA, signing, SBOMs), hardening CI/CD pipelines, or establishing quality gates. Aligned with OpenSSF Scorecard, Best Practices Badge (all levels), SLSA, and S2C2F. By Netresearch.<br><br>Origin: https://github.com/netresearch/enterprise-readiness-skill |
| `git-workflow-skill` | Agent Skill: Git workflow best practices for teams and CI/CD. Use when establishing branching strategies, implementing Conventional Commits, configuring PRs, or integrating Git with CI/CD. By Netresearch.<br><br>Origin: https://github.com/netresearch/git-workflow-skill |

### Productivity

| Skill | Description |
| --- | --- |
| `brainstorming` | You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.<br><br>Origin: https://github.com/obra/superpowers |
| `spec-to-plan` | Transform project descriptions and feature requests into comprehensive specifications and actionable task lists. Use when the user wants to: (1) Create a specification from a project/feature description, (2) Generate a detailed plan with task breakdown, (3) Clarify requirements before implementation, (4) Convert ideas into structured development plans with progress tracking. Works with or without existing codebase files.<br><br>Origin: https://mcpbundler.com |

### Swift Development

| Skill | Description |
| --- | --- |
| `swift-concurrency-expert` | Swift Concurrency review and remediation for Swift 6.2+. Use when asked to review Swift Concurrency usage, improve concurrency compliance, or fix Swift concurrency compiler errors in a feature or file.<br><br>Origin: https://github.com/Dimillian/Skills |
| `swiftui-liquid-glass` | Implement, review, or improve SwiftUI features using the iOS 26+ Liquid Glass API. Use when asked to adopt Liquid Glass in new SwiftUI UI, refactor an existing feature to Liquid Glass, or review Liquid Glass usage for correctness, performance, and design alignment.<br><br>Origin: https://github.com/Dimillian/Skills |
| `swiftui-ui-patterns` | Best practices and example-driven guidance for building SwiftUI views and components. Use when creating or refactoring SwiftUI UI, designing tab architecture with TabView, composing screens, or needing component-specific patterns and examples.<br><br>Origin: https://github.com/Dimillian/Skills |
| `swiftui-view-refactor` | Refactor and review SwiftUI view files for consistent structure, dependency injection, and Observation usage. Use when asked to clean up a SwiftUI view's layout/ordering, handle view models safely (non-optional when possible), or standardize how dependencies and @Observable state are initialized and passed.<br><br>Origin: https://github.com/Dimillian/Skills |
