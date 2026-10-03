// Marbell Ember · glass pass
// The film's rule: coral gets a faint phosphor glow, nothing else glows.
// The accent is read from palette slot 5, so the glow follows the theme.
// Static apart from the focus sweep, so it stays clean under video compression.

const float GLOW_RADIUS = 9.0;   // px
const float GLOW_GAIN   = 0.42;
const float VIGNETTE    = 0.22;
const float SWEEP_TIME  = 0.55;  // s, ignition line when the window takes focus

float accentness(vec3 c, vec3 accent, vec3 accentHi) {
    float d = min(distance(c, accent), distance(c, accentHi));
    return 1.0 - smoothstep(0.07, 0.20, d);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 base = texture(iChannel0, uv);
    vec3 accent = iPalette[5];
    vec3 accentHi = iPalette[13];

    // golden-angle spiral blur of accent-coloured pixels only
    float glow = 0.0;
    float wsum = 0.0;
    for (int i = 1; i <= 28; i++) {
        float f = float(i);
        float r = GLOW_RADIUS * sqrt(f / 28.0);
        float a = f * 2.39996323;
        vec2 o = vec2(cos(a), sin(a)) * r / iResolution.xy;
        float w = exp(-2.2 * f / 28.0);
        glow += accentness(texture(iChannel0, uv + o).rgb, accent, accentHi) * w;
        wsum += w;
    }
    glow /= wsum;

    vec3 col = base.rgb + accent * glow * GLOW_GAIN;

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
