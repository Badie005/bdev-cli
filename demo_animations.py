"""
Demo script showcasing Claude Code-inspired animations.

Run this to see all the animation features in action.
"""

from cli.utils.ui import console
from cli.utils.animation import animations, AnimationSpeed
from cli.utils.theme import theme
import time


def demo_basic_animations():
    """Demonstrate basic animation types."""
    p = theme.palette

    console.banner("Animation Demo", animate=True)
    time.sleep(0.3)

    console.header("Basic Messages", animate=True)

    console.success("Success message with fade-in", animate=True)
    time.sleep(0.2)

    console.error("Error message with shake", animate=True)
    time.sleep(0.2)

    console.warning("Warning message", animate=True)
    time.sleep(0.2)

    console.info("Info message", animate=True)
    time.sleep(0.2)

    console.empty_line()


def demo_typewriter():
    """Demonstrate typewriter effect."""
    console.header("Typewriter Effect", animate=True)
    time.sleep(0.2)

    console.type("This text is being typed out character by character...", speed=0.02)
    time.sleep(0.3)

    console.empty_line()


def demo_pulse():
    """Demonstrate pulse animation."""
    console.header("Pulse Animation", animate=True)
    time.sleep(0.2)

    console.pulse("Pulsing attention grabber!", times=3)
    time.sleep(0.3)

    console.empty_line()


def demo_count_up():
    """Demonstrate count-up animation."""
    console.header("Count Up Animation", animate=True)
    time.sleep(0.2)

    console.type("Counting up to 100: ")
    console.count_up(0, 100, duration=0.8)
    time.sleep(0.3)

    console.empty_line()


def demo_progress():
    """Demonstrate progress bar."""
    console.header("Progress Bar", animate=True)
    time.sleep(0.2)

    for i in range(0, 101, 10):
        console.progress_bar(i, 100, width=40)
        time.sleep(0.08)

    console.empty_line()
    time.sleep(0.2)


def demo_thinking():
    """Demonstrate thinking animation."""
    console.header("Thinking Animation", animate=True)
    time.sleep(0.2)

    console.thinking("Processing your request...")
    time.sleep(0.1)

    console.empty_line()


def demo_loading():
    """Demonstrate loading spinner."""
    console.header("Loading Spinner", animate=True)
    time.sleep(0.2)

    with console.loading("Loading resources..."):
        time.sleep(1.5)

    console.success("Loading complete!")
    time.sleep(0.2)

    console.empty_line()


def demo_progress_bar_context():
    """Demonstrate progress bar context."""
    console.header("Progress Context", animate=True)
    time.sleep(0.2)

    progress = console.progress("Processing files", total=50)
    with progress:
        import random

        for i in range(50):
            progress.update(advance=1)
            time.sleep(0.03)

    console.success("All files processed!")
    time.sleep(0.2)

    console.empty_line()


def demo_cards():
    """Demonstrate rich card components."""
    console.header("Cards & Panels", animate=True)
    time.sleep(0.2)

    console.card(
        "Quick Tip",
        "Use animations sparingly for maximum impact. "
        "Over-animated interfaces can feel distracting.",
        icon="💡",
        action_text="Got it!",
    )
    time.sleep(0.3)

    console.empty_line()

    console.status_card(
        "success",
        "System Status",
        details=["All services operational", "CPU usage: 23%", "Memory usage: 45%"],
    )
    time.sleep(0.3)

    console.empty_line()


def demo_notifications():
    """Demonstrate notifications."""
    console.header("Notifications", animate=True)
    time.sleep(0.2)

    console.notification(
        "Update Available", "A new version is ready to install.", type="info"
    )
    time.sleep(0.3)

    console.empty_line()

    console.toast(
        "Toast notification appearing for 2 seconds...", duration=2, type="success"
    )
    time.sleep(2.2)

    console.empty_line()


def demo_config():
    """Demonstrate animation configuration."""
    console.header("Animation Configuration", animate=True)
    time.sleep(0.2)

    # Show current config
    config = animations.config
    console.muted(f"Animations enabled: {config.enabled}")
    console.muted(f"Speed setting: {config.speed.name}")
    console.muted(f"Minimal mode: {config.minimal_mode}")

    console.empty_line()

    # Test speed settings
    console.type("Testing different animation speeds:\n")

    console.muted("  - FAST speed:")
    old_speed = animations.config.speed
    animations.config.speed = AnimationSpeed.FAST
    console.success("Fast message", animate=True)

    console.muted("  - SLOW speed:")
    animations.config.speed = AnimationSpeed.SLOW
    console.success("Slow message", animate=True)

    # Restore
    animations.config.speed = old_speed

    console.empty_line()
    time.sleep(0.3)


def main():
    """Run all animation demos."""
    p = theme.palette

    console.banner("Claude Code Animation Demo", animate=True)
    time.sleep(0.2)

    console.muted("This demo showcases all animation features.")
    console.muted("Press Ctrl+C to exit early.\n")
    time.sleep(0.3)

    try:
        demo_basic_animations()
        demo_typewriter()
        demo_pulse()
        demo_count_up()
        demo_progress()
        demo_thinking()
        demo_loading()
        demo_progress_bar_context()
        demo_cards()
        demo_notifications()
        demo_config()

        console.header("Demo Complete", animate=True)
        console.success("All animations demonstrated!")
        console.muted("\nTry them out in your own code! 🎨")

    except KeyboardInterrupt:
        console.print()
        console.muted("\nDemo interrupted by user.")
        console.info("Goodbye!")


if __name__ == "__main__":
    main()
