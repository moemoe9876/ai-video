# Creative Reimagination Mode Guide

## Overview

The **Reimagination Agent** now supports two distinct modes of operation:

1. **Standard Mode** (default) - Preserves the original scene's core elements while exploring new creative directions
2. **Creative Reimagination Mode** - Enables complete creative independence, allowing you to create entirely new content inspired by (but not bound by) the original

## When to Use Each Mode

### Standard Mode
Use this when you want:
- Variations on the original scene with different aesthetics
- New styling, mood, and atmosphere while keeping the same subject and action
- Branded elements and specific locations preserved
- Creative exploration within the bounds of the original content

**Example use case:** "Create 3 different mood variations of this commercial that all feature the same characters and location, but with different lighting, era, and cinematic styles."

### Creative Reimagination Mode
Use this when you want:
- Completely new content inspired by the original video
- Freedom to reimagine subjects, locations, and compositions
- Creative freedom to build something entirely different
- The original prompts to serve only as inspiration or a "blueprint"

**Example use case:** "I love the energy and vibe of this commercial, but I want you to reimagine it as a Spike Lee film with completely different characters, settings, and narrative—use the original only as creative inspiration."

## How to Activate Creative Mode

Simply provide a `--user-prompt` when calling the reimagination agent:

```bash
# Standard Mode (no user-prompt)
ai-video reimagine \
  --input assets/prompts/VIDEO_ID/prompts_detailed.md \
  --style "neon cyberpunk"

# Creative Reimagination Mode (with user-prompt)
ai-video reimagine \
  --input assets/prompts/VIDEO_ID/prompts_detailed.md \
  --user-prompt "Reimagine this as a dreamy, surreal Japanese anime with pastel colors and floating elements. Be completely creative—change everything to match this vision."
```

## Understanding the Priority Hierarchy

When the agent generates prompts, it follows this priority order:

### In Standard Mode
1. Global style (cinematography, mood, palette direction)
2. Original scene details (subjects, actions, locations, brands)
3. Variant diversity (each variant explores different aesthetic choices)

### In Creative Reimagination Mode
1. **User directive** (your custom prompt takes absolute precedence)
2. Global style (cinematography preferences, if specified)
3. Original content (used only as inspiration or creative blueprint)

**Key point:** In Creative Mode, the user's directive is final. If your vision requires dropping brands, changing locations, or reimagining subjects, the agent will do so.

## System Prompt Changes

The system prompt now includes explicit guidance for both modes:

### Standard Mode Behavior
- "Treat the provided `prompts_detailed.md` as the authoritative source of truth"
- "Preserve the core subject, action, and spatial intent"
- "Carry forward every concrete detail (brands, signage, lettering, vehicle makes/models)"

### Creative Reimagination Mode Behavior
- "User directive takes absolute precedence"
- "You are not bound by the original scene's subject, action, location, or any details"
- "Original prompts serve only as inspiration or a creative blueprint"
- "You have full creative freedom to build something entirely different"
- "Create prompts that are entirely NEW and INDEPENDENT from the original source material"

## Agent Logic Changes

The `reimagination_agent.py` now:

1. **Detects the mode** by checking if `user_prompt` is provided
2. **Passes mode information** to Gemini via the payload:
   ```python
   {
     "mode": "creative_reimagination" if is_creative_mode else "standard",
     "creative_mode_enabled": is_creative_mode,
     "preserve_subject_action": not is_creative_mode  # False in creative mode
   }
   ```
3. **Generates different instructions** based on mode:
   - **Standard:** "Create clear, production-ready generation prompts that keep the original subject and action..."
   - **Creative:** "CREATIVE REIMAGINATION MODE: This directive takes ABSOLUTE PRECEDENCE. You are not bound by the original scene's subject, action, location... Generate brand new subject matter, locations, actions, and compositions..."

## Example Workflows

### Workflow 1: Spike Lee Reimagination (Creative Mode)

```bash
ai-video reimagine \
  --input assets/prompts/absurd_truth_in_passion/prompts_detailed.md \
  --style "90s Brooklyn street realism with Afrofuturist color" \
  --user-prompt "You are Spike Lee. Reimagine this video as if you were directing it. Channel hip-hop culture, streetwear fashion, sports, and the visual language of your most iconic films. Build something completely new that celebrates urban life and cultural pride."
```

**Result:** Completely fresh content channeling Spike Lee's aesthetic and values, not just variations on the original.

### Workflow 2: Style Variants (Standard Mode)

```bash
ai-video reimagine \
  --input assets/prompts/commercial/prompts_detailed.md \
  --style "cyberpunk tokyo"
```

**Result:** Same commercial with the same characters and locations, but reimagined with cyberpunk aesthetics, neon lighting, and futuristic mood.

### Workflow 3: Multiple Creative Directions

```bash
ai-video reimagine \
  --input assets/prompts/short_film/prompts_detailed.md \
  --num-variants 4 \
  --user-prompt "Create 4 completely independent interpretations: 1) A surreal dream sequence, 2) A high-octane action thriller, 3) A intimate indie drama, 4) A whimsical animated fantasy."
```

**Result:** Four entirely different takes on the creative vision, each a unique genre or style interpretation.

## Output Structure

Both modes produce the same JSON and Markdown formats:

- **`variant_prompts.json`** - Structured variant data with image and video prompts
- **`variant_report.md`** - Human-readable report with all variants, mood, style notes, and metadata

The only difference is the **content** of the prompts:
- **Standard Mode:** Variations that preserve the original
- **Creative Mode:** Independent creations inspired by user directive

## Tips for Best Results

### In Creative Reimagination Mode

1. **Be specific about your vision:**
   - ✅ Good: "Reimagine as a Wes Anderson film with pastel colors, symmetrical framing, and whimsical characters"
   - ❌ Vague: "Make it different"

2. **Reference filmmakers, genres, or moods:**
   - "Channel the surrealist energy of David Lynch"
   - "Make it look like a 1970s blaxploitation film"
   - "Create the emotional intensity of a Lars von Trier drama"

3. **Describe the emotional or cultural vibe:**
   - "Capture the playful irreverence of early 2000s internet culture"
   - "Build the spiritual mystique of East Asian martial arts cinema"
   - "Channel the raw energy of underground hip-hop"

4. **Allow multiple variants to explore different interpretations:**
   - Use `--num-variants 4` or `--num-variants 5`
   - Each variant should offer a unique take on your creative direction

### In Standard Mode

1. **Provide a cohesive style:**
   - "cyberpunk tokyo" or "film noir 1940s" or "ethereal dream sequence"

2. **The agent will maintain:**
   - Original characters and subjects
   - Original locations and spatial relationships
   - Branded elements and specific details
   - Original narrative intent

3. **The agent will vary:**
   - Lighting and mood
   - Era and aesthetic period
   - Cinematography style and film stock
   - Palette and color grading
   - Camera movement and framing

## Technical Implementation

### Modified Files

1. **`src/ai_video/prompts/reimagination_agent_system_prompt.md`**
   - Added "Scene fidelity & creative freedom" section with two explicit modes
   - Updated "Variant expectations" with mode-specific guidance
   - Clarified priority hierarchy with user directive at top in Creative Mode
   - Updated "Validation" section with conditional logic

2. **`src/ai_video/agents/reimagination_agent.py`**
   - Added mode detection: `is_creative_mode = bool(user_prompt)`
   - Updated payload to include `mode`, `creative_mode_enabled`, and `preserve_subject_action` flags
   - Generated different instructions for each mode
   - Creative Mode instructions explicitly state "creative freedom," "not bound by original," and "entirely new"

### Backward Compatibility

✅ **Fully backward compatible** - Existing calls without `--user-prompt` work exactly as before (Standard Mode).

### API Integration

The Gemini API receives explicit instructions for each mode:

**Standard Mode:**
```
"Keep the original subject and action but explore new moods, palettes, and settings..."
```

**Creative Mode:**
```
"CREATIVE REIMAGINATION MODE: This directive takes ABSOLUTE PRECEDENCE. You are not bound 
by the original scene's subject, action, location, or any details. Use the original prompts 
ONLY as inspiration or a creative blueprint... Generate brand new subject matter, locations, 
actions, and compositions that fulfill the user's vision."
```

## FAQ

**Q: Will Standard Mode variants still preserve the brands and locations?**
A: Yes, absolutely. Standard Mode treats the original as authoritative and carries forward all branded details unless you explicitly ask for them to be removed.

**Q: Can I use Creative Mode but still preserve some original elements?**
A: Yes. Mention specific elements in your user prompt that you want to keep (e.g., "...but keep the same characters and setting"). The user prompt is flexible and can include preservation instructions.

**Q: What if my user prompt conflicts with the global style?**
A: In Creative Mode, your user prompt takes priority. The global style is applied as a secondary aesthetic direction.

**Q: How many variants should I request?**
A: For Standard Mode: 2-3 variants explore most creative directions. For Creative Mode: 3-5 variants let the agent explore multiple interpretations of your vision.

**Q: Will the agent create something completely unrelated to the original?**
A: Yes, in Creative Mode. The original serves only as inspiration. If your user prompt describes a completely different scene, tone, or medium, the agent will create that.

## Summary

With Creative Reimagination Mode, you now have **complete creative freedom** to:

✨ Reimagine videos as if directed by your favorite filmmaker  
✨ Explore entirely new genres and mediums  
✨ Build narratives inspired by (but independent from) the original  
✨ Unlock true creative possibilities with AI video generation  

The key is to provide a rich `--user-prompt` that captures your creative vision. The agent will honor that vision absolutely and generate content that is independently creative, not just variations on a theme.
