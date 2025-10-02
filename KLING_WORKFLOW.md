# Kling 2.1 Pro First+Last Frame Workflow

## Overview

Kling 2.1 Pro offers a unique **first frame + last frame** feature that provides superior control over video generation. Instead of using a single image or text prompt, you can provide two separate images:
- **First Frame**: The starting state of your video
- **Last Frame**: The ending state of your video

Kling then generates the transition between these two frames, giving you precise control over the beginning and end of your video.

## When to Use First+Last Frame

The AI Video system **intelligently recommends** when to use this approach based on:

### ✅ **Always Recommended:**
- **Scenes ≥ 4 seconds**: Longer scenes always benefit from the additional control

### ✅ **Recommended with Movement:**
- **Scenes 2-4 seconds** with significant movement:
  - Walking, running, approaching, exiting
  - Turning, leaning, riding, driving
  - Any transformation or transition
  - Camera tracking, dolly, crane, orbiting movements

### ❌ **Not Recommended:**
- **Scenes < 2 seconds**: Too short to benefit from dual-frame approach
- **Static scenes without movement**: Standard image-to-video works fine

## System Behavior

When you generate prompts, the system will automatically:

1. **Analyze each scene** for duration and movement
2. **Flag suitable scenes** with `use_first_last_frame: true`
3. **Generate two separate T2I prompts**:
   - `first_frame_prompt`: For the starting state
   - `last_frame_prompt`: For the ending state
4. **Provide reasoning** explaining why it's recommended
5. **Include workflow instructions** in the markdown output

## Example Output

### Scene Marked for First+Last Frame:

```markdown
## Scene 2

**⏱ Time:** 2.7s - 5.9s (3.2s)
**📍 Location:** City street during daytime

### 🤖 AI Generation Prompts (Kling 2.1 Pro Compatible)

**💡 Recommendation: Use First+Last Frame Approach**

This scene (3.2s with significant movement/transformation) will benefit from 
Kling 2.1 Pro's first+last frame feature.

#### First Frame Prompt (Text-to-Image)
```
Young couple on motorcycle at starting position. Male driver, female passenger 
behind with arms around driver's waist. City street backdrop, daytime. 
Lighting: Natural sunlight, side-lighting. Film: Cinestill 800T characteristics. 
Style: 1990s Hong Kong New Wave cinema. Beginning of action.
```

#### Last Frame Prompt (Text-to-Image)
```
Young couple on motorcycle having completed movement. Male driver, female passenger 
behind with arms around driver's waist. City street backdrop, daytime.
Lighting: Natural sunlight, side-lighting. Film: Cinestill 800T characteristics.
Style: 1990s Hong Kong New Wave cinema. End of action.
```

**Workflow:** Generate both frames with text-to-image model (e.g., SeaArt, 
Midjourney, DALL-E), then use both as input to Kling 2.1 Pro for video generation.

#### Video Generation (Kling 2.1 Pro)
Use first+last frame mode with the two generated images above.
```

## Workflow Steps

### 1. **Analyze Your Video**
```bash
ai-video analyze your_video.mp4
ai-video make-prompts assets/reports/your_video_report.json
```

### 2. **Open the Generated Markdown**
```bash
cat assets/prompts/your_video_id/prompts_detailed.md
```

### 3. **For Each Scene Marked with 💡 Recommendation:**

#### Step A: Generate First Frame
- Copy the **First Frame Prompt**
- Use your preferred T2I model:
  - **SeaArt**: Free, high quality
  - **Midjourney**: Professional results
  - **DALL-E 3**: Easy to use
  - **Stable Diffusion**: Local control
- Save the generated image (e.g., `scene_02_first.png`)

#### Step B: Generate Last Frame
- Copy the **Last Frame Prompt**
- Use the same T2I model for consistency
- Save the generated image (e.g., `scene_02_last.png`)

#### Step C: Generate Video with Kling 2.1 Pro
1. Go to [Kling AI](https://klingai.com)
2. Select **Image-to-Video** mode
3. Choose **First+Last Frame** option
4. Upload your first frame image
5. Upload your last frame image
6. Set duration (use the scene duration from analysis)
7. Optional: Add movement hints if desired
8. Generate video

### 4. **For Scenes Without 💡 Recommendation:**
Use standard workflow:
- Generate single image from T2I prompt
- Use standard Image-to-Video in Kling
- Or use Text-to-Video directly

## Benefits of First+Last Frame

### 🎯 **Superior Control**
- Exact control over starting and ending positions
- Consistent subject appearance throughout
- Predictable transitions

### 🎨 **Better Quality**
- Kling knows exactly where to start and end
- Reduces hallucinations and drift
- More accurate recreation of original video

### ⏱️ **Longer Videos**
- Works better for scenes >4 seconds
- Maintains coherence across longer durations

### 🎭 **Complex Movements**
- Better handling of walking, turning, approaching
- Accurate camera movements (tracking, dolly, etc.)
- Transformation and transition scenes

## Tips for Best Results

### 🖼️ **First Frame Prompt**
- Focus on **starting position**
- Include "at beginning", "starting position", "before movement"
- Describe initial state clearly

### 🖼️ **Last Frame Prompt**
- Focus on **ending position**
- Include "having completed", "at end of", "after movement"
- Describe final state clearly
- Keep lighting, style, and environment consistent with first frame

### 🎬 **Both Frames Should:**
- Use identical lighting conditions
- Match film stock and style
- Maintain same camera angle/position
- Keep environment consistent
- Only vary subject position/pose

### ⚙️ **Kling Settings**
- Use **scene duration** from analysis for video length
- Set **camera movement** to match analysis (static, tracking, etc.)
- Add **motion strength** hints if movement is subtle

## Example Scenarios

### ✅ **Perfect for First+Last Frame:**
- Person walking toward camera (start: far away, end: close up)
- Motorcycle riding past (start: left side, end: right side)
- Character turning around (start: facing away, end: facing camera)
- Door opening (start: closed, end: open)
- Sunrise/sunset (start: dark, end: bright)

### ❌ **Use Standard I2V Instead:**
- Static shot of person standing (< 2s)
- Close-up of face with subtle expression change
- Product shot with minimal movement
- Quick cuts between scenes

## Troubleshooting

### Issue: Generated frames don't match
**Solution**: Use same T2I model, same settings, same seed if possible

### Issue: Video transition looks unnatural
**Solution**: Ensure both frames have consistent lighting/environment, only subject position should change

### Issue: Subject appears/disappears mid-video
**Solution**: Both frames must include the subject, just in different positions

### Issue: Recommended for short scene
**Solution**: System uses 2s threshold - you can still use standard I2V if you prefer

## API/Programmatic Access

The prompt generation stores first+last frame data in JSON:

```json
{
  "use_first_last_frame": true,
  "first_frame_prompt": "...",
  "last_frame_prompt": "...",
  "first_last_frame_reasoning": "Scene duration is 3.2s, Scene has significant movement/transformation. First+last frame approach provides better control..."
}
```

Access programmatically:

```python
from ai_video.models import VideoReport
from ai_video.storage import load_model

report = load_model("assets/reports/video_report.json", VideoReport)

for scene in report.scenes:
    if scene.shots:
        for shot in scene.shots:
            # Check video prompts for first+last frame recommendation
            # (stored in prompt bundle)
            pass
```

## Summary

The **intelligent first+last frame system** automatically:
1. ✅ Detects scenes that benefit from dual-frame approach
2. ✅ Generates optimized first and last frame prompts
3. ✅ Provides clear reasoning and workflow instructions
4. ✅ Falls back to standard I2V for unsuitable scenes

This gives you the **best of both worlds**: automated intelligence with manual control when you need it.
