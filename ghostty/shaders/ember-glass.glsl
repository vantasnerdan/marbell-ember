// Marbell Ember · glass pass
// The film's rule: coral gets a faint phosphor glow, nothing else glows.
// The accent is read from palette slot 5, so the glow follows the theme.
// Static apart from the focus sweep, so it stays clean under video compression.

const float GLOW_RADIUS = 9.0;   // px
const float GLOW_GAIN   = 0.13;
const float VIGNETTE    = 0.22;
const float SWEEP_TIME  = 0.55;  // s, ignition line when the window takes focus

// Beacons: two signal colours that the herdr sidebar uses only for agent state.
// Anything drawn in them breathes (working) or blinks (blocked), with a halo.
// They live in palette slots 200 (working, #FFB52E) and 201 (blocked, #FF2E7E), read
// through iPalette so they are in the same colour space as the rendered text.
const float BEACON_GAIN = 0.40;

// Ghostty hands the shader the palette in sRGB but, with linear alpha blending, the
// screen texture in linear light. Compare against both encodings of the key colour.
vec3 toLinear(vec3 c) {
    return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c));
}

float signal(vec3 c, vec3 k) {
    float d = min(distance(c, k), distance(c, toLinear(k)));
    return 1.0 - smoothstep(0.05, 0.13, d);
}

float accentness(vec3 c, vec3 accent, vec3 accentHi) {
    float d = min(min(distance(c, accent), distance(c, accentHi)),
                  min(distance(c, toLinear(accent)), distance(c, toLinear(accentHi))));
    return 1.0 - smoothstep(0.07, 0.20, d);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 base = texture(iChannel0, uv);
    vec3 accent = iPalette[5];
    vec3 accentHi = iPalette[13];
    vec3 SIG_WORK = iPalette[200];
    vec3 SIG_BLOCK = iPalette[201];

    // golden-angle spiral blur of accent-coloured pixels only
    float glow = 0.0;
    float work = 0.0;
    float block = 0.0;
    float wsum = 0.0;
    for (int i = 1; i <= 28; i++) {
        float f = float(i);
        float r = GLOW_RADIUS * sqrt(f / 28.0);
        float a = f * 2.39996323;
        vec2 o = vec2(cos(a), sin(a)) * r / iResolution.xy;
        float w = exp(-2.2 * f / 28.0);
        vec3 s = texture(iChannel0, uv + o).rgb;
        glow += accentness(s, accent, accentHi) * w;
        work += signal(s, SIG_WORK) * w;
        block += signal(s, SIG_BLOCK) * w;
        wsum += w;
    }
    glow /= wsum;
    work /= wsum;
    block /= wsum;

    // halo only: coral shapes light the space around them, never themselves
    vec3 col = base.rgb + accent * glow * GLOW_GAIN * (1.0 - accentness(base.rgb, accent, accentHi));

    // working breathes on a ~2 s cycle; blocked blinks about once a second
    float breathe = 0.5 + 0.5 * sin(iTime * 3.1);
    float blink = pow(0.5 + 0.5 * sin(iTime * 6.3), 3.0);
    col *= mix(1.0, 0.60 + 0.40 * breathe, signal(base.rgb, SIG_WORK));
    col *= mix(1.0, 0.50 + 0.50 * blink, signal(base.rgb, SIG_BLOCK));
    col += SIG_WORK * work * (0.15 + 0.85 * breathe) * BEACON_GAIN * (1.0 - signal(base.rgb, SIG_WORK));
    col += SIG_BLOCK * block * (0.10 + 0.90 * blink) * BEACON_GAIN * (1.0 - signal(base.rgb, SIG_BLOCK));

    // lens falloff toward the corners
    vec2 q = uv - 0.5;
    col *= 1.0 - VIGNETTE * dot(q, q) * 2.0;

    // ignition: one thin line of coral light runs top to bottom on focus
    float t = (iTime - iTimeFocus) / SWEEP_TIME;
    if (iFocus > 0 && t >= 0.0 && t < 1.0) {
        float e = 1.0 - pow(1.0 - t, 3.0);
        float y = 1.0 - e;
        float d = abs(uv.y - y) * iResolution.y;
        float line = exp(-d * d / 6.0) + 0.35 * exp(-d / 28.0) * step(y, uv.y);
        col += accent * line * 0.55 * (1.0 - t);
    }

    fragColor = vec4(col, base.a);
}
