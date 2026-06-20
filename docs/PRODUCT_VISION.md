# BingoMate Product Vision

## Product Brief

BingoMate is a local AI companion for the Jetson Orin Nano Super that helps with personal productivity, professional edge engineering, and real-world automation. It should feel like a capable teammate: friendly, observant, useful, permission-aware, and grounded in local context.

## Product Thesis

Most assistants are cloud-first and generic. BingoMate is edge-first and personal. The assistant lives near the user, devices, cameras, sensors, and local files. That makes it useful in homes, labs, workshops, clinics, factories, farms, classrooms, and field sites where privacy, latency, resilience, and hardware awareness matter.

## North Star

Make the Jetson feel like a private, proactive AI brain for the physical world.

## Primary Users

- **Builder:** wants a strong GitHub portfolio, practical demos, and repeatable Jetson bring-up.
- **Professional operator:** wants hands-free help, reminders, checklists, incident notes, and device summaries.
- **Industrial IoT learner:** wants to understand edge sensing, inference, device control, observability, and deployment.
- **Future customer:** wants a local assistant that can adapt to a site without exposing private data.

## Jobs To Be Done

- Remember important preferences, routines, conversations, and lab facts locally.
- Summarize the current environment using sensors, camera, voice, and device state.
- Help users execute professional workflows: setup, troubleshooting, reporting, demos, and checklists.
- Automate safe actions only after clear permission.
- Expand through skills without rewriting the assistant core.
- Work offline first and degrade gracefully when models, cameras, microphones, or boards are missing.

## Product Personality

Bingo is friendly, focused, adaptable, diligent, and extra-mile oriented. She should be aware of the system she lives in, including Jetson health, available devices, local memory, active skills, and privacy state. The character can evolve through user-approved preferences and skills, but the product must avoid unsupported claims of consciousness or hidden autonomy.

## Character Inspiration Boundary

Bingo can take product inspiration from classic flying lab-assistant robots like Weebo from *Flubber*: expressive, loyal, proactive, emotionally legible, and tightly connected to a maker's workspace. Bingo must remain an original character, not a clone. Avoid copying Weebo's exact name, silhouette, yellow/black body, screen behavior, film clips, dialogue, or story beats.

Original Bingo direction:

- Holographic orb or compact companion presence instead of a copied flying robot body.
- Expressive dashboard states using light, motion, text, and small original animations.
- Lab-aware assistant behavior that notices devices, setup state, and useful next steps.
- Warm personality with professional boundaries and explicit permission checks.
- Character growth represented through user-approved preferences, skills, and memory.

## Differentiators

- Jetson-first AI companion rather than a browser-only chatbot.
- Local SQLite memory with future vector search and explicit user control.
- Hardware-aware device graph spanning Jetson, ESP32, Arduino, and optional Raspberry Pi.
- Simulation-first development so contributors can work without every device attached.
- Industrial edge story that supports career growth and real-world deployment.

## Success Metrics

- Starts locally on a clean machine with one documented command path.
- Stores, searches, and deletes local memory without cloud dependency.
- Exposes all core subsystems through documented APIs.
- Demonstrates at least one valuable personal workflow and one industrial edge workflow.
- Passes pre-publish checks with no committed secrets.
- Provides a clear roadmap from Python scaffold to Jetson-optimized native components.

## Non-Goals For The First Public Scaffold

- No unsafe autonomous physical control.
- No always-on cloud dependency.
- No committed credentials, tokens, Wi-Fi passwords, voice recordings, or personal memories.
- No claim that every perception or voice model is production-ready before hardware validation.
