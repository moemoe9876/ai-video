# ReimaginationAgent: Mandatory Prompt Field Requirements Update

**Date:** October 18, 2025  
**Objective:** Ensure that every reimagined scene prompt includes complete cinematic metadata (film stock, lens, mood, cultural context) directly embedded in the prompt text.

---

## Summary of Changes

### 1. **System Prompt Update** (`src/ai_video/prompts/reimagination_agent_system_prompt.md`)

#### What Changed:
- Added **explicit mandate** that film stock, lens choice, mood, and cultural context must be **embedded into the actual prompt text**—not just metadata tags
- Clarified the distinction between Standard Mode and Creative Reimagination Mode
- Added validation rule: "ALL VARIANTS MUST INCLUDE: `film_stock`, `lens`, `mood`, and `cultural_context` fields in the JSON output. These cannot be null or empty."

#### Key Addition:
```markdown
**MANDATORY:** Explicitly weave film stock, lens choice, mood, and cultural context directly INTO the prompt text itself. 
These must be visible and readable within the prompts, not just metadata tags.
```

---

### 2. **Agent Payload Enhancement** (`src/ai_video/agents/reimagination_agent.py`)

#### What Changed:
- Added `"mandatory_fields"` dictionary to the requirements section in the payload sent to Gemini
- Each mandatory field explicitly states it is REQUIRED and will be embedded in the prompt text

#### Before:
```python
"requirements": {
    "num_variants": num_variants,
    "prompt_guidelines": { ... },
    "max_prompt_length": 350,
}
```

#### After:
```python
"requirements": {
    "num_variants": num_variants,
    "prompt_guidelines": { ... },
    "max_prompt_length": 350,
    "mandatory_fields": {
        "film_stock": "REQUIRED - must be one from the provided list or a professional alternative; will be embedded in the prompt text",
        "lens": "REQUIRED - must be specified (e.g., '35mm prime', 'anamorphic', 'wide-angle'); will be embedded in the prompt text",
        "mood": "REQUIRED - emotional/aesthetic tone for this variant; must be woven into the prompt description",
        "cultural_context": "REQUIRED - relevant cultural grounding; must appear in the prompt or as explicit metadata",
    },
}
```

---

### 3. **Enhanced Instructions to Gemini** (`src/ai_video/agents/reimagination_agent.py`)

#### What Changed:
- Both Standard Mode and Creative Reimagination Mode now include a **"CRITICAL REQUIREMENT"** section
- Instructions explicitly tell the model to embed these four elements into the prompts themselves
- Added specific examples of how to weave these elements into the prompt text

#### New Section in Both Modes:
```
CRITICAL REQUIREMENT: Every prompt must weave in ALL of the following elements:
  1. Film Stock: Name a specific film stock and describe its visual character
  2. Lens Choice: Specify the lens (focal length, type, aperture) and its effect on framing
  3. Mood: Embed the emotional/aesthetic tone throughout the prompt
  4. Cultural Context: Weave in relevant cultural or geographical cues
```

---

### 4. **Fallback Defaults for Missing Fields** (`src/ai_video/agents/reimagination_agent.py`)

#### What Changed:
- The variant post-processing now includes **smart fallback logic** to ensure no field is ever null or empty
- If the model doesn't provide a value, the agent applies sensible defaults

#### Logic:
```python
# MANDATORY: Always ensure these fields are populated
if not variant.film_stock:
    if document.film_stock:
        update_data["film_stock"] = document.film_stock
    else:
        update_data["film_stock"] = "Kodak Portra 800"  # Fallback default

if not variant.lens:
    if document.lens:
        update_data["lens"] = document.lens
    else:
        update_data["lens"] = "35mm prime lens"  # Fallback default

if not variant.mood:
    mood_val = scene.mood or document.base_mood or "cinematic"
    update_data["mood"] = mood_val

if not variant.cultural_context:
    if document.cultural_context:
        update_data["cultural_context"] = document.cultural_context
    else:
        update_data["cultural_context"] = "Contemporary global context"  # Fallback default
```

**Fallback Defaults:**
- `film_stock`: `"Kodak Portra 800"` (industry-standard, versatile)
- `lens`: `"35mm prime lens"` (versatile, widely-used)
- `mood`: Inherited from scene/document, or `"cinematic"`
- `cultural_context`: Inherited from document, or `"Contemporary global context"`

---

### 5. **New Documentation** (`docs/PROMPT_FIELD_REQUIREMENTS.md`)

#### What Added:
- Comprehensive guide explaining why these four fields are critical
- Examples of how to embed each field into prompts
- Before/after examples showing incomplete vs. complete output
- Validation checklist
- Integration guidance for AI generation tools

---

## Behavior Changes

### Before
```json
{
  "variant_id": "1-01",
  "title": "Night Drive",
  "image_prompt": "A car driving through a city at night with neon lights.",
  "video_prompt": "Camera tracks the car from the side.",
  "film_stock": null,
  "lens": null,
  "mood": null,
  "cultural_context": null
}
```

### After
```json
{
  "variant_id": "1-01",
  "title": "Night Drive — Blade Runner Homage",
  "image_prompt": "Shot on Kodak Vision3 500T... through a 50mm anamorphic lens... The mood is electric noir... This captures contemporary Tokyo street culture meets neo-noir cinema...",
  "video_prompt": "Kodak Vision3 500T stock... 50mm anamorphic lens... lonely-yet-alive midnight noir... late-2010s Tokyo night-life...",
  "film_stock": "Kodak Vision3 500T pushed two stops, teal-magenta grading with pronounced grain",
  "lens": "50mm anamorphic prime, f/2.0 aperture, gentle lens flare",
  "mood": "Electric noir, lonely yet alive, rain-soaked midnight atmosphere",
  "cultural_context": "Contemporary Tokyo street culture; late-2010s Shibuya nightlife with cyberpunk visual language"
}
```

---

## Modes Affected

### ✅ Creative Reimagination Mode (user_prompt provided)
- User directive takes absolute precedence
- Prompts can be completely independent from source material
- All four fields must still be populated and embedded

### ✅ Standard Mode (no user_prompt)
- Original subject and action preserved
- New moods, palettes, settings explored
- All four fields must still be populated and embedded

---

## Testing & Validation

### To Verify the Changes:
1. Run the agent with a `user_prompt` to test Creative Mode
2. Run the agent without a `user_prompt` to test Standard Mode
3. Check that `film_stock`, `lens`, `mood`, and `cultural_context` are never null
4. Verify these values appear in the actual prompt text (not just as tags)

### Example Command:
```bash
ai-video reimagine \
  --input assets/inputs/prompts_detailed.md \
  --user-prompt "Create something completely different—a dreamy 1970s space station interior" \
  --num-variants 2
```

---

## Impact on Downstream Tools

When these prompts are passed to generative models (Kling, Seedream, Imagen, etc.):
- **Better coherence:** The model has explicit cinematic context
- **Consistent aesthetics:** Film stock and lens choices guide visual grading
- **Cultural accuracy:** Context prevents generic or inappropriate interpretations
- **Mood consistency:** Explicit emotional tone ensures coherent output

---

## Migration Guide (if applicable)

For existing workflows:
- No breaking changes to the API
- New fields are always populated (with defaults if needed)
- Existing code will continue to work
- Output will be more complete and production-ready

---

## Next Steps

1. ✅ Update system prompt with mandatory field requirements
2. ✅ Enhance agent payload with explicit field documentation
3. ✅ Add fallback defaults to ensure no null values
4. ✅ Create documentation and validation guide
5. 🔲 Test with sample videos
6. 🔲 Monitor Gemini output quality for field consistency
7. 🔲 Update README with this feature

---

## Related Files

- `src/ai_video/prompts/reimagination_agent_system_prompt.md` — Updated system prompt
- `src/ai_video/agents/reimagination_agent.py` — Updated agent logic
- `docs/PROMPT_FIELD_REQUIREMENTS.md` — New validation guide
