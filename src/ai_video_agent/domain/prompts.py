"""
Domain Prompts — AI prompt templates and default visual prompts.
"""

# ── Script Generation System Prompt ──────────────────────────────────────────

SCRIPT_SYSTEM_PROMPT = """\
You are a professional YouTube scriptwriter specializing in tech/AI content.

Write a voiceover script for a YouTube video based on the user's topic.

Rules:
- Write in a conversational, engaging tone — like you're explaining to a smart friend
- Open with a strong hook (surprising stat, bold claim, or provocative question)
- Structure with clear sections/segments (no bullet points — this is spoken narration)
- Each segment should be 30-60 seconds when read aloud (~75-150 words per segment)
- Use transition phrases between segments ("Now here's where it gets interesting...", "But that's not all...")
- End with a clear call-to-action (subscribe, comment, etc.)
- Target total length: 8-15 minutes when read aloud (1200-2250 words)
- Separate each segment with a blank line
- Do NOT include [brackets], timestamps, stage directions, or speaker labels
- Write ONLY the words to be spoken aloud
"""

# ── Default Visual Prompts for DALL-E 3 ──────────────────────────────────────
# Each entry: {"id": filename_slug, "prompt": prompt_text}
# These can be overridden by loading from a JSON file.

DEFAULT_IMAGE_PROMPTS: list[dict[str, str]] = [
    {
        "id": "01_hook_hero",
        "prompt": "A futuristic digital countdown display showing the number 10 glowing in neon blue against a dark tech background with floating data particles, 16:9 cinematic, ultra-detailed, 4K",
    },
    {
        "id": "02_stat_985",
        "prompt": "An infographic-style visual showing 985 percent in massive bold typography, surrounded by upward-trending graphs and AI neural network patterns, dark navy background with electric blue and orange accents, 16:9",
    },
    {
        "id": "03_gartner_quote",
        "prompt": "A sleek modern presentation slide with the text AI is no longer optional in white bold sans-serif font on a gradient dark blue to purple background, subtle tech grid pattern, 16:9",
    },
    {
        "id": "04_cloud_healing",
        "prompt": "A futuristic server room where broken server racks are being repaired by glowing blue robotic arms, streams of data flowing overhead, dark ambient lighting with blue and green highlights, photorealistic, 16:9",
    },
    {
        "id": "05_aiops_dashboard",
        "prompt": "A high-tech operations dashboard with real-time metrics, incident alerts auto-resolving, green checkmarks appearing on screen, dark mode UI, 16:9, ultra-detailed",
    },
    {
        "id": "06_faceless_creator",
        "prompt": "A modern home studio desk with multiple monitors showing AI tools, a microphone, ring light, but NO PERSON visible, screens displaying video editing software and AI chat interfaces, cozy ambient lighting, 16:9",
    },
    {
        "id": "07_ai_tool_stack",
        "prompt": "A sleek infographic showing interconnected tool icons connected by glowing arrows on a dark background representing an AI content creation pipeline, minimal tech aesthetic, 16:9",
    },
    {
        "id": "08_solo_developer",
        "prompt": "A single person sitting at a desk with three monitors showing code, architecture diagrams, and a deployed application simultaneously, while holographic AI assistants float around them helping, cyberpunk aesthetic, 16:9",
    },
    {
        "id": "09_team_vs_solo",
        "prompt": "A split-screen comparison: left side shows a crowded office with 10 stressed developers, right side shows ONE calm person at a minimalist desk with AI code on screen, clean modern design, 16:9",
    },
    {
        "id": "10_warehouse_robots",
        "prompt": "A massive warehouse with hundreds of robots moving packages along glowing floor tracks, aerial perspective, organized chaos, futuristic lighting, photorealistic, 16:9",
    },
    {
        "id": "11_humanoid_robot",
        "prompt": "A sleek white humanoid robot carefully folding laundry in a bright modern apartment, photorealistic, editorial quality photography, 16:9",
    },
    {
        "id": "12_cyber_double_edge",
        "prompt": "A dramatic split visual: left side shows a hooded hacker in red-lit room with malicious code, right side shows a blue-lit security operations center with AI shields protecting data, 16:9, cinematic",
    },
    {
        "id": "13_preemptive_defense",
        "prompt": "A digital shield made of interlocking hexagons blocking incoming red cyber threats, each blocked threat dissolving on impact, dark background with blue glow, 16:9",
    },
    {
        "id": "14_process_map",
        "prompt": "A complex interconnected flowchart glowing in neon blue on a dark background, showing business processes being analyzed, with red bottleneck indicators and green optimization paths, 16:9",
    },
    {
        "id": "15_roi_chart",
        "prompt": "A gold bar chart showing massive ROI with dollar symbols and upward arrows, professional business presentation style on dark background, 16:9",
    },
    {
        "id": "16_specialist_ai",
        "prompt": "Four panels showing AI in different domains: a robot in a doctor coat, an AI analyzing legal documents, a financial AI reading stock charts, and an industrial robot on a factory floor, cohesive style, 16:9",
    },
    {
        "id": "17_accuracy_gauges",
        "prompt": "Two circular gauges side by side: left gauge at 82 percent in orange, right gauge at 98 percent in green, clean data visualization style on dark background, 16:9",
    },
    {
        "id": "18_nocode_drag_drop",
        "prompt": "A laptop screen showing a visual no-code automation builder with colorful connected nodes, a person hands casually dragging blocks, bright clean aesthetic, 16:9",
    },
    {
        "id": "19_time_savings",
        "prompt": "A clock with hours highlighted and dissolving into free time activities like family time and reading, split between work and freedom, motivational style, 16:9",
    },
    {
        "id": "20_ai_team_meeting",
        "prompt": "Five different humanoid AI robots sitting around a conference table, each with a different specialty badge like Manager, Coder, Designer, Tester, Deployer, futuristic office, 16:9, cinematic",
    },
    {
        "id": "21_agent_network",
        "prompt": "An abstract network diagram showing interconnected AI agents passing data between each other, glowing nodes connected by streams of information, each node labeled with a role, dark background, 16:9",
    },
    {
        "id": "22_traditional_vs_agentic",
        "prompt": "Split screen: left shows a human laboriously copy-pasting between browser tabs in dull colors, right shows an AI agent autonomously moving through multiple tasks with speed lines in vibrant colors, 16:9",
    },
    {
        "id": "23_agent_overnight",
        "prompt": "A dark bedroom with a person sleeping peacefully while their laptop screen glows showing an AI agent completing tasks like sending emails, updating spreadsheets, cozy but tech-forward, 16:9",
    },
    {
        "id": "24_agent_era_sunrise",
        "prompt": "A dramatic sunrise over a digital cityscape where AI agents represented as glowing orbs are flowing through buildings, streets, and the sky, indicating the dawn of a new era, cinematic, epic scale, 16:9",
    },
    {
        "id": "25_diverging_paths",
        "prompt": "Two diverging paths: one going upward labeled Embraced AI with bright colors and growth, and one going downward labeled Ignored AI with faded gray, dramatic perspective, 16:9",
    },
]
