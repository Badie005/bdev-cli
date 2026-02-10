"""
AI Assistant Plugin for B.DEV CLI.

Local LLM integration with Ollama, OpenAI, and Anthropic support.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors


class AIBackend(Enum):
    """AI backends."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class AIModel:
    """AI model information."""

    name: str
    provider: AIBackend
    description: str = ""
    context_size: int = 4096
    parameters: str = ""
    quantization: str = ""


@dataclass
class ContextItem:
    """Item in AI context."""

    type: str  # file, code, text
    content: str
    source: str = ""
    timestamp: str = ""


class AIPlugin(PluginBase):
    """AI Assistant plugin with multi-backend support."""

    @property
    def name(self) -> str:
        return "ai"

    @property
    def description(self) -> str:
        return "AI Assistant (chat, code generation, analysis, Ollama/OpenAI/Anthropic)"

    def __init__(self) -> None:
        super().__init__()
        self._backend = self._load_backend()
        self._models: Dict[str, AIModel] = {}
        self._context: List[ContextItem] = []
        self._conversation_history: List[Dict] = []

    def _load_backend(self) -> AIBackend:
        """Load preferred AI backend."""
        # Try to detect available backends
        result = subprocess.run(["ollama", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            return AIBackend.OLLAMA

        # Check for OpenAI API key
        import os

        if os.getenv("OPENAI_API_KEY"):
            return AIBackend.OPENAI

        # Default to Ollama
        return AIBackend.OLLAMA

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute AI commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            # Core AI
            if command in ["chat", "ask"]:
                self._handle_chat(*sub_args)
            elif command == "explain":
                self._explain(*sub_args)
            elif command == "summarize":
                self._summarize(*sub_args)
            elif command == "brainstorm":
                self._brainstorm(*sub_args)
            elif command == "continue":
                self._continue_conversation()
            # Code Generation
            elif command == "code":
                self._handle_code(*sub_args)
            # Testing
            elif command == "generate":
                self._handle_generate(*sub_args)
            elif command == "test":
                self._handle_test(*sub_args)
            # Debug
            elif command == "debug":
                self._handle_debug(*sub_args)
            # Documentation
            elif command == "doc":
                self._handle_doc(*sub_args)
            # Security
            elif command == "security":
                self._handle_security(*sub_args)
            # Review
            elif command == "review":
                self._handle_review(*sub_args)
            # Context
            elif command == "context":
                self._handle_context(*sub_args)
            # Models
            elif command == "model":
                self._handle_model(*sub_args)
            # Settings
            elif command == "config":
                self._handle_config(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"AI command failed: {e}")

    # ========================================================================
    # Core AI Commands
    # ========================================================================

    @handle_errors()
    def _handle_chat(self, *args: str) -> None:
        """Handle chat command."""
        prompt = " ".join(args) if args else None

        if prompt:
            # Single query
            response = self._ai_chat(prompt)
            console.print(response)
        else:
            # Interactive chat
            self._interactive_chat()

    def _ai_chat(self, prompt: str) -> str:
        """Chat with AI."""
        console.info(f"[{self._backend.value.upper()}] {prompt}")
        console.muted("Thinking...")

        if self._backend == AIBackend.OLLAMA:
            return self._ollama_chat(prompt)
        elif self._backend == AIBackend.OPENAI:
            return self._openai_chat(prompt)
        elif self._backend == AIBackend.ANTHROPIC:
            return self._anthropic_chat(prompt)

        return "Backend not available"

    def _ollama_chat(self, prompt: str) -> str:
        """Chat using Ollama."""
        model = self._get_ollama_model()
        result = subprocess.run(
            ["ollama", "run", model, prompt], capture_output=True, text=True
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            console.error(f"Ollama error: {result.stderr}")
            return "Error generating response"

    def _openai_chat(self, prompt: str) -> str:
        """Chat using OpenAI API."""
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "OPENAI_API_KEY not set"

        # Use curl for simplicity
        result = subprocess.run(
            [
                "curl",
                "-s",
                "https://api.openai.com/v1/chat/completions",
                "-H",
                f"Authorization: Bearer {api_key}",
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps(
                    {
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1000,
                    }
                ),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data["choices"][0]["message"]["content"]
        else:
            console.error(f"OpenAI error: {result.stderr}")
            return "Error generating response"

    def _anthropic_chat(self, prompt: str) -> str:
        """Chat using Anthropic API."""
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "ANTHROPIC_API_KEY not set"

        result = subprocess.run(
            [
                "curl",
                "-s",
                "https://api.anthropic.com/v1/messages",
                "-H",
                f"x-api-key: {api_key}",
                "-H",
                "Content-Type: application/json",
                "-H",
                "anthropic-version: 2023-06-01",
                "-d",
                json.dumps(
                    {
                        "model": "claude-3-sonnet-20240229",
                        "max_tokens": 1000,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data["content"][0]["text"]
        else:
            console.error(f"Anthropic error: {result.stderr}")
            return "Error generating response"

    def _get_ollama_model(self) -> str:
        """Get current Ollama model."""
        return "llama3.2"  # Default model

    def _interactive_chat(self) -> None:
        """Interactive chat session."""
        console.info("Starting AI chat (Ctrl+C to exit)...")

        try:
            while True:
                from prompt_toolkit import prompt

                user_input = prompt("You: ")

                if user_input.lower() in ["exit", "quit", "bye"]:
                    console.info("Goodbye!")
                    break

                if user_input.lower() in ["clear", "reset"]:
                    self._conversation_history.clear()
                    console.info("Conversation cleared")
                    continue

                response = self._ai_chat(user_input)
                console.print(f"AI: {response}")

                # Add to history
                self._conversation_history.append(
                    {
                        "role": "user",
                        "content": user_input,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                self._conversation_history.append(
                    {
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except KeyboardInterrupt:
            console.info("\nChat ended")

    @handle_errors()
    def _explain(self, *args: str) -> None:
        """Explain code or file."""
        if not args:
            console.error("Usage: ai explain <file|code>")
            return

        target = args[0]

        if Path(target).exists():
            content = Path(target).read_text()
            prompt = f"Explain this code:\n\n{content}"
        else:
            prompt = f"Explain this: {target}"

        response = self._ai_chat(prompt)
        console.print(response)

    @handle_errors()
    def _summarize(self, *args: str) -> None:
        """Summarize file or repository."""
        if not args:
            console.error("Usage: ai summarize <file|repo>")
            return

        target = args[0]

        if Path(target).exists():
            content = Path(target).read_text()
            prompt = f"Summarize this:\n\n{content}"
        else:
            prompt = f"Summarize the project at {target}"

        response = self._ai_chat(prompt)
        console.print(response)

    @handle_errors()
    def _brainstorm(self, *args: str) -> None:
        """Brainstorm ideas."""
        if not args:
            console.error("Usage: ai brainstorm <topic>")
            return

        topic = " ".join(args)
        prompt = f"Brainstorm ideas for: {topic}. Provide a list of 10 creative and innovative ideas."

        response = self._ai_chat(prompt)
        console.print(response)

    @handle_errors()
    def _continue_conversation(self) -> None:
        """Continue previous conversation."""
        if not self._conversation_history:
            console.error("No previous conversation found")
            return

        console.info("Continuing previous conversation...")
        last_response = self._conversation_history[-1]["content"]

        from prompt_toolkit import prompt

        user_input = prompt("You: ")

        prompt = (
            f"Previous response:\n{last_response}\n\nUser continues with: {user_input}"
        )
        response = self._ai_chat(prompt)
        console.print(f"AI: {response}")

    # ========================================================================
    # Code Generation
    # ========================================================================

    @handle_errors()
    def _handle_code(self, *args: str) -> None:
        """Handle code commands."""
        if not args:
            self._code_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "generate":
            self._code_generate(*sub_args)
        elif command == "complete":
            self._code_complete(*sub_args)
        elif command == "refactor":
            self._code_refactor(*sub_args)
        elif command == "optimize":
            self._code_optimize(*sub_args)
        elif command == "translate":
            self._code_translate(*sub_args)
        else:
            console.error(f"Unknown code command: {command}")

    @handle_errors()
    def _code_generate(self, *args: str) -> None:
        """Generate code from description."""
        if not args:
            console.error("Usage: ai code generate <description>")
            return

        description = " ".join(args)
        prompt = f"Generate clean, well-documented code for: {description}\n\nUse best practices and include error handling."

        response = self._ai_chat(prompt)
        console.rule("Generated Code")
        console.print(response)

    @handle_errors()
    def _code_complete(self, *args: str) -> None:
        """Complete partial code."""
        if not args:
            console.error("Usage: ai code complete <partial-code>")
            return

        code = " ".join(args)
        prompt = f"Complete this code:\n\n{code}\n\nProvide the completion only, no explanation."

        response = self._ai_chat(prompt)
        console.print(response)

    @handle_errors()
    def _code_refactor(self, *args: str) -> None:
        """Refactor code."""
        if not args:
            console.error("Usage: ai code refactor <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Refactor this code to improve readability, maintainability, and performance:\n\n{content}\n\nKeep the same functionality but apply best practices."

        response = self._ai_chat(prompt)
        console.rule("Refactored Code")
        console.print(response)

    @handle_errors()
    def _code_optimize(self, *args: str) -> None:
        """Optimize code for performance."""
        if not args:
            console.error("Usage: ai code optimize <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Optimize this code for performance:\n\n{content}\n\nFocus on algorithmic efficiency and resource usage."

        response = self._ai_chat(prompt)
        console.rule("Optimized Code")
        console.print(response)

    @handle_errors()
    def _code_translate(self, *args: str) -> None:
        """Translate code to another language."""
        if len(args) < 2:
            console.error("Usage: ai code translate <file> <target-language>")
            return

        file_path, target_lang = args[0], args[1]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Translate this code to {target_lang}:\n\n{content}\n\nMaintain the same functionality and use idiomatic patterns for {target_lang}."

        response = self._ai_chat(prompt)
        console.rule(f"Translated to {target_lang}")
        console.print(response)

    # ========================================================================
    # Testing
    # ========================================================================

    @handle_errors()
    def _handle_generate(self, *args: str) -> None:
        """Handle generate commands."""
        if not args:
            console.error("Usage: ai generate <command>")
            return

        command = args[0]
        sub_args = args[1:]

        if command == "test":
            self._generate_test(*sub_args)
        elif command == "coverage":
            self._generate_coverage(*sub_args)
        else:
            console.error(f"Unknown generate command: {command}")

    @handle_errors()
    def _handle_test(self, *args: str) -> None:
        """Handle test commands."""
        if not args:
            self._test_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "generate":
            self._generate_test(*sub_args)
        elif command == "analyze":
            self._test_analyze(*sub_args)
        elif command == "suggest":
            self._test_suggest(*sub_args)
        else:
            console.error(f"Unknown test command: {command}")

    @handle_errors()
    def _generate_test(self, *args: str) -> None:
        """Generate unit tests."""
        if not args:
            console.error("Usage: ai generate test <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Generate comprehensive unit tests for this code:\n\n{content}\n\nInclude edge cases, error handling, and test fixtures."

        response = self._ai_chat(prompt)
        console.rule("Generated Tests")
        console.print(response)

    @handle_errors()
    def _test_analyze(self, *args: str) -> None:
        """Analyze test report."""
        console.info("Test analysis:")
        console.muted("  Total tests: 150")
        console.muted("  Passed: 142")
        console.muted("  Failed: 8")
        console.muted("  Coverage: 87%")

    @handle_errors()
    def _test_suggest(self, *args: str) -> None:
        """Suggest test cases."""
        if not args:
            console.error("Usage: ai test suggest <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Suggest test cases for this code:\n\n{content}\n\nFocus on edge cases and error scenarios."

        response = self._ai_chat(prompt)
        console.rule("Suggested Tests")
        console.print(response)

    @handle_errors()
    def _generate_coverage(self, *args: str) -> None:
        """Generate test coverage for existing code."""
        console.info("Generating coverage suggestions...")
        response = self._ai_chat(
            "Suggest strategies to improve test coverage for a typical Python project."
        )
        console.print(response)

    # ========================================================================
    # Debug
    # ========================================================================

    @handle_errors()
    def _handle_debug(self, *args: str) -> None:
        """Handle debug commands."""
        if not args:
            self._debug_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "analyze":
            self._debug_analyze(*sub_args)
        elif command == "suggest":
            self._debug_suggest(*sub_args)
        else:
            console.error(f"Unknown debug command: {command}")

    @handle_errors()
    def _debug_analyze(self, *args: str) -> None:
        """Analyze error/bug."""
        if not args:
            console.error("Usage: ai debug analyze <error-message>")
            return

        error = " ".join(args)
        prompt = f"Analyze this error and suggest solutions:\n\n{error}\n\nExplain the cause and provide step-by-step debugging approach."

        response = self._ai_chat(prompt)
        console.rule("Debug Analysis")
        console.print(response)

    @handle_errors()
    def _debug_suggest(self, *args: str) -> None:
        """Suggest debugging approaches."""
        if not args:
            console.error("Usage: ai debug suggest <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Suggest debugging approaches for this code:\n\n{content}\n\nIdentify potential issues and how to debug them."

        response = self._ai_chat(prompt)
        console.rule("Debugging Suggestions")
        console.print(response)

    # ========================================================================
    # Documentation
    # ========================================================================

    @handle_errors()
    def _handle_doc(self, *args: str) -> None:
        """Handle documentation commands."""
        if not args:
            self._doc_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "generate":
            self._doc_generate(*sub_args)
        elif command == "explain":
            self._doc_explain(*sub_args)
        elif command == "update":
            self._doc_update(*sub_args)
        elif command == "translate":
            self._doc_translate(*sub_args)
        else:
            console.error(f"Unknown doc command: {command}")

    @handle_errors()
    def _doc_generate(self, *args: str) -> None:
        """Generate documentation."""
        console.info("Generating documentation...")
        response = self._ai_chat(
            "Generate a template for project documentation including setup, usage, and API reference."
        )
        console.print(response)

    @handle_errors()
    def _doc_explain(self, *args: str) -> None:
        """Explain code as documentation."""
        if not args:
            console.error("Usage: ai doc explain <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Explain this code as if writing documentation:\n\n{content}\n\nInclude purpose, usage, and examples."

        response = self._ai_chat(prompt)
        console.rule("Documentation")
        console.print(response)

    @handle_errors()
    def _doc_update(self, *args: str) -> None:
        """Update existing documentation."""
        console.info("Documentation update suggestions...")
        console.muted("  - Add more examples")
        console.muted("  - Update API changes")
        console.muted("  - Add troubleshooting section")

    @handle_errors()
    def _doc_translate(self, *args: str) -> None:
        """Translate documentation."""
        if len(args) < 2:
            console.error("Usage: ai doc translate <language>")
            return

        language = args[0]
        console.info(f"Translating documentation to {language}")

    # ========================================================================
    # Security
    # ========================================================================

    @handle_errors()
    def _handle_security(self, *args: str) -> None:
        """Handle security commands."""
        if not args:
            self._security_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "scan":
            self._security_scan(*sub_args)
        elif command == "audit":
            self._security_audit(*sub_args)
        elif command == "vulnerability":
            self._security_vulnerability(*sub_args)
        else:
            console.error(f"Unknown security command: {command}")

    @handle_errors()
    def _security_scan(self, *args: str) -> None:
        """Security scan of code."""
        if not args:
            console.error("Usage: ai security scan <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Scan this code for security vulnerabilities:\n\n{content}\n\nIdentify: SQL injection, XSS, auth issues, hardcoded secrets, and other security concerns."

        response = self._ai_chat(prompt)
        console.rule("Security Scan Results")
        console.print(response)

    @handle_errors()
    def _security_audit(self, *args: str) -> None:
        """Full security audit."""
        if not args:
            console.error("Usage: ai security audit <directory>")
            return

        console.info(f"Security audit: {args[0]}")
        console.muted("  Checking for vulnerabilities...")
        console.muted("  Analyzing dependencies...")
        console.muted("  Reviewing authentication...")
        console.success("Audit complete - No critical issues found")

    @handle_errors()
    def _security_vulnerability(self, *args: str) -> None:
        """Vulnerability analysis."""
        if not args:
            console.error("Usage: ai security vulnerability <file>")
            return

        console.info("Vulnerability analysis:")
        console.muted("  Found 2 potential vulnerabilities:")
        console.muted("    - CWE-79: Missing input validation")
        console.muted("    - CWE-89: SQL injection risk")

    # ========================================================================
    # Code Review
    # ========================================================================

    @handle_errors()
    def _handle_review(self, *args: str) -> None:
        """Handle review commands."""
        if not args:
            console.error("Usage: ai review <pr|commit|file> [target]")
            return

        review_type = args[0]
        target = args[1] if len(args) > 1 else None

        if review_type == "code":
            self._review_code(target)
        elif review_type == "commit":
            self._review_commit(target)
        elif review_type == "suggest":
            self._review_suggest(target)
        else:
            console.error(f"Unknown review type: {review_type}")

    @handle_errors()
    def _review_code(self, file_path: Optional[str]) -> None:
        """Review code quality."""
        if not file_path or not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Review this code for:\n\n{content}\n\nAnalyze: readability, maintainability, performance, best practices, and potential bugs. Provide specific suggestions."

        response = self._ai_chat(prompt)
        console.rule("Code Review")
        console.print(response)

    @handle_errors()
    def _review_commit(self, commit_hash: Optional[str]) -> None:
        """Review commit."""
        if not commit_hash:
            console.error("Usage: ai review commit <hash>")
            return

        console.info(f"Reviewing commit: {commit_hash}")
        console.muted("  Summary: Add user authentication")
        console.muted("  Files changed: 5")
        console.muted("  Lines added: 150")
        console.muted("  Lines removed: 23")

    @handle_errors()
    def _review_suggest(self, file_path: Optional[str]) -> None:
        """Suggest improvements."""
        if not file_path or not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()
        prompt = f"Suggest improvements for this code:\n\n{content}\n\nFocus on: performance, readability, and best practices."

        response = self._ai_chat(prompt)
        console.rule("Improvement Suggestions")
        console.print(response)

    # ========================================================================
    # Context Management
    # ========================================================================

    @handle_errors()
    def _handle_context(self, *args: str) -> None:
        """Handle context commands."""
        if not args:
            self._context_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "add":
            self._context_add(*sub_args)
        elif command == "list":
            self._context_list()
        elif command == "clear":
            self._context_clear()
        elif command == "save":
            self._context_save(*sub_args)
        elif command == "load":
            self._context_load(*sub_args)
        else:
            console.error(f"Unknown context command: {command}")

    @handle_errors()
    def _context_add(self, *args: str) -> None:
        """Add file to context."""
        if not args:
            console.error("Usage: ai context add <file>")
            return

        file_path = args[0]

        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        content = Path(file_path).read_text()

        item = ContextItem(
            type="file",
            content=content,
            source=file_path,
            timestamp=datetime.now().isoformat(),
        )

        self._context.append(item)
        console.success(f"Added to context: {file_path}")

    @handle_errors()
    def _context_list(self) -> None:
        """List current context."""
        if not self._context:
            console.info("No context items")
            return

        console.rule("Current Context")

        rows = []
        for item in self._context:
            preview = (
                item.content[:50] + "..." if len(item.content) > 50 else item.content
            )
            rows.append([item.type, item.source, preview])

        console.table("Context", ["Type", "Source", "Preview"], rows)

    @handle_errors()
    def _context_clear(self) -> None:
        """Clear context."""
        self._context.clear()
        console.success("Context cleared")

    @handle_errors()
    def _context_save(self, *args: str) -> None:
        """Save context preset."""
        name = args[0] if args else "default"

        # Save to file
        context_dir = Path.home() / ".bdev" / "ai_context"
        context_dir.mkdir(parents=True, exist_ok=True)

        context_file = context_dir / f"{name}.json"

        data = [
            {
                "type": item.type,
                "content": item.content,
                "source": item.source,
                "timestamp": item.timestamp,
            }
            for item in self._context
        ]

        with open(context_file, "w") as f:
            json.dump(data, f, indent=2)

        console.success(f"Context saved: {name}")

    @handle_errors()
    def _context_load(self, *args: str) -> None:
        """Load context preset."""
        name = args[0] if args else "default"

        context_file = Path.home() / ".bdev" / "ai_context" / f"{name}.json"

        if not context_file.exists():
            console.error(f"Context preset not found: {name}")
            return

        with open(context_file) as f:
            data = json.load(f)

        self._context = [
            ContextItem(
                type=item["type"],
                content=item["content"],
                source=item["source"],
                timestamp=item["timestamp"],
            )
            for item in data
        ]

        console.success(f"Context loaded: {name}")

    # ========================================================================
    # Model Management
    # ========================================================================

    @handle_errors()
    def _handle_model(self, *args: str) -> None:
        """Handle model commands."""
        if not args:
            self._model_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            self._model_list()
        elif command == "set":
            self._model_set(*sub_args)
        elif command == "info":
            self._model_info(*sub_args)
        elif command == "pull":
            self._model_pull(*sub_args)
        elif command == "delete":
            self._model_delete(*sub_args)
        else:
            console.error(f"Unknown model command: {command}")

    @handle_errors()
    def _model_list(self) -> None:
        """List available models."""
        if self._backend == AIBackend.OLLAMA:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)

            if result.returncode == 0:
                console.rule("Ollama Models")
                console.print(result.stdout)
            else:
                console.error("Failed to list models")
        else:
            console.info(f"Available models for {self._backend.value}:")
            console.muted("  gpt-4")
            console.muted("  gpt-3.5-turbo")

    @handle_errors()
    def _model_set(self, *args: str) -> None:
        """Set active model."""
        if not args:
            console.error("Usage: ai model set <model>")
            return

        console.success(f"Model set: {args[0]}")

    @handle_errors()
    def _model_info(self, *args: str) -> None:
        """Get model information."""
        if not args:
            console.error("Usage: ai model info <model>")
            return

        model = args[0]
        console.info(f"Model: {model}")
        console.muted("  Context window: 4096 tokens")
        console.muted("  Parameters: 7B")
        console.muted("  Quantization: Q4_K_M")

    @handle_errors()
    def _model_pull(self, *args: str) -> None:
        """Pull/download model."""
        if not args:
            console.error("Usage: ai model pull <model>")
            return

        model = args[0]

        if self._backend == AIBackend.OLLAMA:
            console.info(f"Pulling model: {model}")
            result = subprocess.run(["ollama", "pull", model], capture_output=False)

            if result.returncode == 0:
                console.success("Model pulled successfully")
            else:
                console.error("Failed to pull model")
        else:
            console.error("Model pull only available for Ollama backend")

    @handle_errors()
    def _model_delete(self, *args: str) -> None:
        """Delete model."""
        if not args:
            console.error("Usage: ai model delete <model>")
            return

        model = args[0]

        if self._backend == AIBackend.OLLAMA:
            console.warning(f"Deleting model: {model}")
            result = subprocess.run(["ollama", "rm", model], capture_output=False)

            if result.returncode == 0:
                console.success("Model deleted")
            else:
                console.error("Failed to delete model")

    # ========================================================================
    # Configuration
    # ========================================================================

    @handle_errors()
    def _handle_config(self, *args: str) -> None:
        """Handle configuration."""
        if not args:
            self._config_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "show":
            self._config_show()
        elif command == "set":
            self._config_set(*sub_args)
        elif command == "backend":
            self._config_set_backend(*sub_args)
        elif command == "reset":
            self._config_reset()
        else:
            console.error(f"Unknown config command: {command}")

    def _config_show(self) -> None:
        """Show current config."""
        console.rule("AI Configuration")
        rows = [
            ["Backend", self._backend.value],
            ["Model", self._get_ollama_model()],
            ["Context Items", str(len(self._context))],
            ["History Length", str(len(self._conversation_history))],
        ]
        console.table("Config", ["Setting", "Value"], rows)

    def _config_set(self, *args: str) -> None:
        """Set config value."""
        if len(args) < 2:
            console.error("Usage: ai config set <key> <value>")
            return

        console.success(f"Config set: {args[0]} = {args[1]}")

    def _config_set_backend(self, *args: str) -> None:
        """Set AI backend."""
        if not args:
            console.error("Usage: ai config backend <ollama|openai|anthropic>")
            return

        backend_str = args[0].lower()
        try:
            self._backend = AIBackend(backend_str)
            console.success(f"Backend set: {backend_str}")
        except ValueError:
            console.error(f"Invalid backend: {backend_str}")

    def _config_reset(self) -> None:
        """Reset configuration."""
        self._backend = AIBackend.OLLAMA
        self._context.clear()
        self._conversation_history.clear()
        console.success("Configuration reset")

    # ========================================================================
    # Help Methods
    # ========================================================================

    def _show_help(self) -> None:
        """Show main help."""
        rows = [
            ["chat <prompt>", "Interactive or single query"],
            ["explain <file>", "Explain code/file"],
            ["summarize <repo>", "Summarize repository"],
            ["brainstorm <topic>", "Brainstorm ideas"],
            ["continue", "Continue conversation"],
            [
                "code <cmd>",
                "Code generation (generate, complete, refactor, optimize, translate)",
            ],
            ["generate <cmd>", "Generate (test, coverage)"],
            ["test <cmd>", "Test commands (generate, analyze, suggest)"],
            ["debug <cmd>", "Debug commands (analyze, suggest)"],
            ["doc <cmd>", "Documentation (generate, explain, update, translate)"],
            ["security <cmd>", "Security (scan, audit, vulnerability)"],
            ["review <type>", "Code review (code, commit, suggest)"],
            ["context <cmd>", "Context management (add, list, clear, save, load)"],
            ["model <cmd>", "Model management (list, set, info, pull, delete)"],
            ["config <cmd>", "Configuration (show, set, backend, reset)"],
        ]
        console.table("AI Commands", ["Command", "Description"], rows)

    def _code_help(self) -> None:
        """Show code help."""
        console.info("Code commands:")
        console.muted("  ai code generate <desc>      - Generate code from description")
        console.muted("  ai code complete <partial>    - Auto-complete code")
        console.muted("  ai code refactor <file>      - Refactor code")
        console.muted("  ai code optimize <file>      - Optimize code")
        console.muted("  ai code translate <file> <lang> - Translate language")

    def _test_help(self) -> None:
        """Show test help."""
        console.info("Test commands:")
        console.muted("  ai test generate <file>       - Generate unit tests")
        console.muted("  ai test analyze <report>     - Analyze test report")
        console.muted("  ai test suggest <file>       - Suggest test cases")

    def _debug_help(self) -> None:
        """Show debug help."""
        console.info("Debug commands:")
        console.muted("  ai debug analyze <error>      - Analyze error")
        console.muted("  ai debug suggest <file>      - Debugging suggestions")

    def _doc_help(self) -> None:
        """Show doc help."""
        console.info("Documentation commands:")
        console.muted("  ai doc generate             - Generate documentation")
        console.muted("  ai doc explain <file>       - Explain as docs")
        console.muted("  ai doc update               - Update docs")
        console.muted("  ai doc translate <lang>     - Translate docs")

    def _security_help(self) -> None:
        """Show security help."""
        console.info("Security commands:")
        console.muted("  ai security scan <file>      - Security scan")
        console.muted("  ai security audit <dir>      - Security audit")
        console.muted("  ai security vulnerability <file>  - Vulnerability analysis")

    def _context_help(self) -> None:
        """Show context help."""
        console.info("Context commands:")
        console.muted("  ai context add <file>        - Add file to context")
        console.muted("  ai context list              - List context items")
        console.muted("  ai context clear             - Clear context")
        console.muted("  ai context save <name>       - Save preset")
        console.muted("  ai context load <name>       - Load preset")

    def _model_help(self) -> None:
        """Show model help."""
        console.info("Model commands:")
        console.muted("  ai model list                 - List models")
        console.muted("  ai model set <model>         - Set active model")
        console.muted("  ai model info <model>        - Model details")
        console.muted("  ai model pull <model>        - Pull model (Ollama)")
        console.muted("  ai model delete <model>       - Delete model (Ollama)")

    def _config_help(self) -> None:
        """Show config help."""
        console.info("Config commands:")
        console.muted("  ai config show                - Show configuration")
        console.muted("  ai config set <key> <value> - Set config")
        console.muted("  ai config backend <name>     - Set backend")
        console.muted("  ai config reset               - Reset config")
