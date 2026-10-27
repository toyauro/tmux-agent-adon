// Optional static glow for the four bright tmux-agent-adon indicator colours.
// Ghostty invokes mainImage with iChannel0 and iResolution provided.
// Other pixels of the same colour may also glow: the shader does not know
// about tmux panes, agents, or the provenance of an individual pixel.

vec3 adonLight(vec3 pixel) {
    const vec3 green = vec3(56.0, 255.0, 105.0) / 255.0;
    const vec3 yellow = vec3(255.0, 227.0, 71.0) / 255.0;
    const vec3 red = vec3(255.0, 107.0, 120.0) / 255.0;
    const vec3 idle = vec3(223.0, 245.0, 255.0) / 255.0;

    // Recognise nearly solid centres. A narrow tolerance avoids treating
    // ordinary background text and antialiased transition colours as lights.
    vec3 light = vec3(0.0);
    light += green * (1.0 - smoothstep(0.010, 0.045, distance(pixel, green)));
    light += yellow * (1.0 - smoothstep(0.010, 0.045, distance(pixel, yellow)));
    light += red * (1.0 - smoothstep(0.010, 0.045, distance(pixel, red)));
    light += idle * (1.0 - smoothstep(0.010, 0.045, distance(pixel, idle)));
    return light;
}

vec3 adonSample(vec2 uv, vec2 pixels) {
    vec2 sampleUv = clamp(uv + pixels / iResolution.xy, 0.0, 1.0);
    return adonLight(texture(iChannel0, sampleUv).rgb);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 original = texture(iChannel0, uv);

    // Preserve bright foreground glyphs, including each light's core. Draw
    // only into dark surroundings. No time uniform means the effect is steady.
    if (max(max(original.r, original.g), original.b) > 0.45) {
        fragColor = original;
        return;
    }

    vec3 glow = vec3(0.0);
    glow += adonSample(uv, vec2(-3.0, 0.0));
    glow += adonSample(uv, vec2( 3.0, 0.0));
    glow += adonSample(uv, vec2(0.0, -3.0));
    glow += adonSample(uv, vec2(0.0,  3.0));
    glow += adonSample(uv, vec2(-3.0, -3.0));
    glow += adonSample(uv, vec2(-3.0,  3.0));
    glow += adonSample(uv, vec2( 3.0, -3.0));
    glow += adonSample(uv, vec2( 3.0,  3.0));
    glow *= 0.055;
    glow += adonSample(uv, vec2(-7.0, 0.0)) * 0.025;
    glow += adonSample(uv, vec2( 7.0, 0.0)) * 0.025;
    glow += adonSample(uv, vec2(0.0, -7.0)) * 0.025;
    glow += adonSample(uv, vec2(0.0,  7.0)) * 0.025;

    fragColor = vec4(min(original.rgb + glow, vec3(1.0)), original.a);
}
