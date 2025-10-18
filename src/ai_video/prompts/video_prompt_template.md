# Video Prompt Templates

## Text-to-Video Prompt Structure

**Prompt = Subject + Action + Scene + Camera Framing + Lighting + Style**

### Components

1. **Subject**: Detailed description of the main focus (appearance, clothing, features)
2. **Action**: What motion or activity is occurring (use realistic, physically plausible actions)
3. **Scene**: The environment and setting
4. **Camera Framing**: Shot type, angle, and camera motion (e.g., "medium close-up," "low-angle tracking move")
5. **Lighting**: Lighting conditions and quality
6. **Style**: Visual style and mood

### Camera Language Tips

- Describe framing with cinematic vocabulary rather than physical measurements. Use terms like "extreme close-up," "medium shot," "full-body shot," "wide shot," or "long shot."
- Specify camera perspective with phrases such as "eye-level," "low-angle," "high-angle," "bird's-eye view," or "worm's-eye view" to shape emotional tone.
- Reference lens intent symbolically — "wide-angle lens" for expansive perspective, "telephoto lens" for compressed depth, "anamorphic lens" for cinematic stretch.
- Layer depth cues ("foreground foliage in crisp focus, subject mid-frame, skyline softly blurred") to help models infer foreground, midground, and background relationships.
- Align framing with mood: low angles suggest power, high angles add vulnerability, close-ups feel intimate, and wide shots provide context.

### Example Text-to-Video Prompts

```
A cheerful corgi wearing sunglasses lounges on a bright orange flotation device, gently bobbing up and down with the wave movement in a sparkling blue ocean under a sunny sky with fluffy white clouds. Camera slowly zooms in on the corgi. Natural daylight, bright and clear. Vibrant, playful style.
```

```
A serene landscape featuring a large, lush tree with drooping branches, situated on a small island in a calm lake. The leaves gradually change from vibrant green to withered yellow. Static wide shot. Soft diffused daylight. Cinematic, naturalistic style.
```

## Image-to-Video Prompt Structure

### Single-Action Structure
**Prompt = Subject + Action + Background + Background Movement + Camera Movement**

### Multi-Action Structure
**Prompt = Subject 1 + Action 1 + Subject 2 + Action 2**

### Components for Image-to-Video

1. **Subject**: Describe the main element from the image
2. **Action**: The motion you want to create (subtle or pronounced)
3. **Background**: The surrounding environment
4. **Background Movement**: How the background should move (clouds, water, etc.)
5. **Camera Movement**: How the camera should move through the scene

> Tip: For both text-to-video and image-to-video prompts, steer composition with cinematic shot names ("medium close-up," "wide shot") and angle descriptors ("low-angle," "bird's-eye view") rather than physical distances.

### Example Image-to-Video Prompts

```
The cute fluffy kitten wearing a navy blue captain's hat steers the wooden boat, gently rocking with the water. The sparkling blue ocean has small ripples and waves moving around the boat. Camera slowly zooms in on the kitten.
```

```
The woman in the white t-shirt turns her head and smiles at the camera, her blonde hair moves gently in the breeze. Soft kitchen background slightly out of focus. Camera remains static at medium shot.
```

```
The motorcyclist leans into the turn, accelerating along the winding autumn road. Trees with orange and red leaves sway slightly in the wind, some leaves falling. Camera tracks alongside the motorcycle.
```

## Advanced Features

### Transitions Between Shots
Use explicit transition markers:
```
[Scene 1] Woman walks through doorway into kitchen, camera follows. [Switch to close-up] Her hand reaches for coffee mug on counter, fingers wrap around handle. [Switch to wide shot] She turns toward window, morning light illuminates her face.
```

### Multi-Subject Interactions
```
Woman in white shirt enters from left, carrying a cup. Man in blue sweater looks up from newspaper and smiles at her. They meet at the table, she sets down the cup. Background shows sunny kitchen window. Camera slowly pushes in on the couple.
```

### Reference Consistency
When generating multiple clips with same characters:
```
The same woman with long blonde hair (as in previous frame) now sits at the counter, both hands wrapped around a white coffee mug. Steam rises from the cup. She closes her eyes and takes a sip. Soft morning light from the left. Camera holds on medium close-up.
```

## Best Practices

### DO:
- Use simple, clear language
- Describe realistic, physically plausible motion
- Include camera movement for dynamism
- Match the prompt to the actual image content (for I2V)
- Specify background movement for immersion
- Use cultural/stylistic keywords when relevant
- Emphasize intensity with adverbs (quickly, slowly, gently, intensely)

### DON'T:
- Specify exact numbers or measurements (e.g., "20 meters away")
- Describe overly complex or physically impossible actions
- Use abstract or vague descriptions
- Mismatch prompt to image (e.g., "man" when image shows woman)
- Skip transition markers when switching shots
- Overload with too many simultaneous actions

## Prompt Length Guidelines

- **Text-to-Video**: 1-3 sentences, 50-150 words
- **Image-to-Video**: 1-2 sentences, 30-100 words
- Focus on the most important elements
- Prioritize motion and camera movement

## Style Keywords

### Mood
- Energetic, calm, peaceful, dramatic, playful, mysterious, serene

### Visual Style
- Cinematic, realistic, documentary, commercial, artistic, vintage, modern

### Technical
- Slow motion, time-lapse, smooth, fluid, natural motion

### Cultural/Aesthetic
- Oriental mood, Chinese, Mediterranean, Scandinavian, tropical

## Camera Movement Combinations

Effective combinations:
- "Zoom in while moving forward"
- "Pan left while tilting up"
- "Aerial shot descending slowly"
- "Handheld tracking shot with subtle shake"
- "Static shot with rack focus"
- "Orbit around subject while zooming out"

Remember: The key to effective video prompts is clarity, physical plausibility, and matching the visual style to your source material.
