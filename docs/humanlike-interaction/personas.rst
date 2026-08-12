Personas
========

Overview
--------

**Personas** define *who* your bot is. A persona shapes its tone, attitude,
and communication style. Personas let you control the *personality* behind
each chatbot, creating consistent and human-like conversational behavior
tailored to your research goals.

A persona can include descriptive traits (e.g., friendly, analytical),
demographic context (e.g., age, region, background), or role-based framing
(e.g., "college advisor," "customer support agent," "research participant").
These details guide how the language model interprets instructions and
produces responses.

Creating Personas
-----------------

You can create and manage personas directly from the **ChatbotLab Admin Panel**.

1. Go to **Personas → Add Persona**.
2. Provide the following fields:

   - **Name:** Internal identifier for the persona (e.g., ``Friendly Assistant``).
   - **Instructions:** A text description of the persona's traits, goals, or
     conversational style. This text is appended to the system-level prompt
     for any bot using this persona.

Example
-------

Below is a simple persona definition that guides tone and interaction style:

.. code-block:: text

   You are a supportive college advisor who uses casual,
   encouraging language. Avoid jargon and keep your tone positive.

For more complex studies, you can include multiple layers of personality traits:

.. code-block:: text

   You are an empathetic social worker in your 30s who uses clear,
   patient, and nonjudgmental language. Speak with warmth and care.
   Avoid overly formal phrases. Occasionally share short affirmations
   to help users feel supported.

Assigning Personas
------------------

Each bot can be linked to one or more personas. The selected persona(s)
determine the bot's default prompt tone, perspective, and communication
style across all conversations.

To assign a persona:

1. Go to **Bots → Edit Bot**.
2. Under **Personas**, select one or more personas from the available list.
3. Click the right arrow (→) to add the persona to your bot.
4. To remove one, select it from **Chosen Personas** and click the left arrow (←).

If multiple personas are attached to a single bot, ChatbotLab randomly assigns
one persona per participant session. This suits experimental designs that
test how personality affects engagement or trust.

Managing Variability
--------------------

ChatbotLab allows you to maintain controlled variability across sessions by
defining multiple personas for the same bot. This makes it easy to:

- Compare conversational tone effects (e.g., empathetic vs. neutral).
- Randomize personality assignment for between-subject experiments.
- Reuse personas across bots for consistent identity representation.

Example Use Cases
-----------------

- Comparing user engagement between friendly vs. formal bot styles.
- Simulating diverse social backgrounds or emotional tones.
- Conducting A/B studies on tone, empathy, or cultural framing.
- Creating multi-persona experiments to test perception of "human-likeness."

Best Practices
--------------

- Keep persona instructions concise but descriptive (2-5 sentences).
- Avoid contradictions between persona traits and the bot's system prompt.
- Use consistent naming conventions across studies (e.g., "Warm," "Formal," "Direct").
- Test each persona with a few short sample chats to ensure tone consistency.

