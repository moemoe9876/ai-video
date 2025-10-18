# Text-to-Image Prompt Template

Generate prompts following this structure:

**Prompt = Subject + Action + Scene + Camera + Lighting + Style**

Focus on a single, continuous moment. Never combine multiple scenes, locations, or time periods into one prompt.

## Components

### Subject
- Who or what is the main focus?
- Detailed physical appearance
- Clothing, accessories, expressions
- Body posture and positioning
- Keep the subject count tight (one hero subject or a clearly defined small group)

### Action
- What is the subject doing?
- Present tense, active voice
- Be specific and clear

### Scene
- Where is this taking place?
- Foreground and background elements
- Environmental details
- Spatial relationships
- All elements must plausibly coexist in the same moment

### Camera
- Shot type (wide, medium, close-up)
- Camera angle (eye-level, low angle, high angle)
- Framing and composition
- Distance from subject
- Avoid referencing multiple shots or cuts; describe one camera setup
- Use cinematography-friendly language (e.g., "medium close-up," "bird's-eye view") instead of physical measurements

### Lighting
- Type of light (natural, artificial)
- Quality (soft, hard, diffused)
- Direction (front, back, side)
- Time of day implications
- Specific techniques (golden hour, studio light)

### Style
- Visual style (cinematic, realistic, artistic)
- Color palette and grading
- Film stock or look (if applicable)
- Mood and atmosphere
- Reference styles if helpful
- If no scene-specific style is provided, default to cinematic realism

## Camera Angle Reference

| Camera Angle | Description | Emotional Effect |
| --- | --- | --- |
| Eye-level | Camera and subject share the same height. | Natural, calm, relatable. |
| High-angle | Camera looks down on the subject. | Conveys vulnerability, diminishes scale. |
| Low-angle | Camera looks up toward the subject. | Emphasizes power, confidence, grandeur. |
| Bird's-eye view | Elevated overhead view of the entire scene. | Highlights scale, geography, choreography. |
| Worm's-eye view | Extreme low vantage close to the ground. | Exaggerates height, adds drama and awe. |
| Dutch angle | Camera is intentionally tilted. | Signals tension, disorientation, kinetic energy. |

## Framing Vocabulary

- **Extreme close-up**: Focuses on micro details (eyes, hands, textures).
- **Close-up**: Frames the face or a key object for intimacy.
- **Medium shot**: Waist-up composition balancing subject and surroundings.
- **Medium close-up**: Chest-up framing ideal for dialogue.
- **Full body shot**: Shows the subject head-to-toe within the scene.
- **Wide / Long shot**: Embraces the environment and spatial context.
- **Point-of-view shot**: Places the camera where the character is looking.

Pair these shot types with lens cues:

- **Wide-angle lens** for expansive perspective and foreground drama.
- **Standard lens** for a natural field of view.
- **Telephoto lens** for compressed depth and selective focus.
- **Fisheye / anamorphic** lenses for stylized curvature or cinematic stretch.

## Prompting Tips for Camera Language

1. Lead with the desired angle: *"High-angle close-up of..."*
2. Layer foreground, midground, and background cues for depth: *"Foreground wildflowers in sharp focus, subject mid-frame, mountains softly blurred."*
3. Match framing to mood—low angles for power, high angles for fragility, close-ups for intimacy, wide shots for scope.
4. Avoid physical measurements like “20 meters away”; rely on cinematic naming instead.
5. Combine angle + lens + action for clarity: *"Bird's-eye view wide shot with a slow orbit."*

## Example Prompts

### Example 1: Kitchen Scene
```
A woman with long blonde hair wearing a white t-shirt and blue jeans, pouring coffee into a ceramic mug in a modern kitchen with white marble counters and stainless steel appliances. Medium shot, camera at eye level. Soft morning light streams through large windows, creating warm highlights and gentle shadows. Cinematic style with warm color grading, natural film look, peaceful morning atmosphere.
```

### Example 2: Product Shot
```
A sleek silver coffee machine centered on a dark wooden counter, steam rising from the spout into a white ceramic cup. Close-up shot with shallow depth of field, background softly blurred. Dramatic side lighting with spotlight, highlighting the metallic surface. High contrast cinematic style, modern commercial aesthetic, rich blacks and bright highlights.
```

### Example 3: Outdoor Scene
```
Athletic man in sports gear running along a coastal path, ocean visible in background with waves crashing on rocks. Wide tracking shot following the subject from the side, capturing full body motion. Golden hour lighting, warm backlight creating rim light around the subject. Vibrant cinematic style shot on Kodak Portra 800, saturated blues and oranges, dynamic and energetic mood.
```

## Guidelines

1. **Be Specific**: Use concrete details rather than vague descriptions
2. **Natural Language**: Write in clear, readable sentences
3. **Avoid Numbers**: Don't specify exact measurements or counts
4. **Single Shot**: Never describe montages, jump cuts, or multiple locations
5. **Mood Over Technical**: Prioritize atmosphere and feeling
6. **Consistency**: Maintain consistent style across related prompts
7. **Length**: Aim for 1-3 sentences, 50-150 words
8. **Negative Prompts**: Optionally specify what to avoid (blur, distortion, etc.)

## Negative Prompt Template

Common elements to exclude:
```
blur, blurry, out of focus, distorted, low quality, pixelated, grainy, noisy, artifacts, watermark, text, logo, signature, amateur, ugly, deformed
```

Customize based on specific needs for each scene.
