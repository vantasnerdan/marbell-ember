// Marbell Ember · glass pass
// The film's rule: coral gets a faint phosphor glow, nothing else glows.
// The accent is read from palette slot 5, so the glow follows the theme.
// One pass does everything (halo, beacons, banked embers, focus sweep, cursor), so
// the screen is filtered once per frame. The lens falloff is baked into plate.png.

const int   TAPS        = 16;    // halo samples per pixel; the cost of the pass scales with this
const float GLOW_RADIUS = 9.0;   // px
const float GLOW_GAIN   = 0.13;
const float SWEEP_TIME  = 0.55;  // s, ignition line when the window takes focus

// Banked embers: a window that is not focused cools (less colour, a little less light)
// and warms back up as the ignition line runs. 0.0 turns it off.
const float BANK      = 0.30;
const float BANK_TIME = 0.45;    // s

// Beacons: two signal colours that the herdr sidebar uses only for agent state.
// Anything drawn in them breathes (working) or beats (blocked), with a halo.
// They live in palette slots 200 (working, #FFB52E) and 201 (blocked, #FF2E7E), read
// through iPalette so they are in the same colour space as the rendered text.
const float BEACON_GAIN  = 0.40;
const float WORK_PERIOD  = 4.6;  // s, one slow breath
const float BLOCK_PERIOD = 2.6;  // s, between double beats

// Cursor: a thread from where it was to where it is (a tapered comet, as wide as the
// cursor, that catches up in ~160 ms) and a halo that breathes in place of a blink.
const float DURATION      = 0.16;  // s
const float TRAIL_ALPHA   = 0.60;
const float BLOOM         = 0.05;
const float CURSOR_HALO   = 0.14;
const float CURSOR_PERIOD = 4.2;   // s

const float TAU = 6.2831853;

// Ghostty hands the shader the palette in sRGB but, with linear alpha blending, the
// screen texture in linear light. Compare against both encodings of the key colour.
vec3 toLinear(vec3 c) {
    return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c));
}

float near(vec3 c, vec3 k, vec3 kLin) {
    return min(distance(c, k), distance(c, kLin));
}

float signal(vec3 c, vec3 k, vec3 kLin) {
    return 1.0 - smoothstep(0.05, 0.13, near(c, k, kLin));
}

float accentness(vec3 c, vec3 a, vec3 aLin, vec3 hi, vec3 hiLin) {
    return 1.0 - smoothstep(0.07, 0.20, min(near(c, a, aLin), near(c, hi, hiLin)));
}

float sdTaper(vec2 p, vec2 a, vec2 b, float ra, float rb) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-4), 0.0, 1.0);
    return length(pa - ba * h) - mix(ra, rb, h);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 base = texture(iChannel0, uv);

    // key colours, converted once per pixel rather than once per tap
    vec3 accent = iPalette[5];
    vec3 accentHi = iPalette[13];
    vec3 sigWork = iPalette[200];
    vec3 sigBlock = iPalette[201];
    vec3 accentLin = toLinear(accent);
    vec3 accentHiLin = toLinear(accentHi);
    vec3 sigWorkLin = toLinear(sigWork);
    vec3 sigBlockLin = toLinear(sigBlock);

    // golden-angle spiral blur of accent- and signal-coloured pixels only
    float n = float(TAPS);
    float glow = 0.0;
    float work = 0.0;
    float block = 0.0;
    float wsum = 0.0;
    for (int i = 1; i <= TAPS; i++) {
        float f = float(i) / n;
        float a = float(i) * 2.39996323;
        vec2 o = vec2(cos(a), sin(a)) * GLOW_RADIUS * sqrt(f) / iResolution.xy;
        float w = exp(-2.2 * f);
        vec3 s = texture(iChannel0, uv + o).rgb;
        glow += accentness(s, accent, accentLin, accentHi, accentHiLin) * w;
        work += signal(s, sigWork, sigWorkLin) * w;
        block += signal(s, sigBlock, sigBlockLin) * w;
        wsum += w;
    }
    glow /= wsum;
    work /= wsum;
    block /= wsum;

    float isAccent = accentness(base.rgb, accent, accentLin, accentHi, accentHiLin);
    float isWork = signal(base.rgb, sigWork, sigWorkLin);
    float isBlock = signal(base.rgb, sigBlock, sigBlockLin);

    // halo only: coral shapes light the space around them, never themselves
    vec3 col = base.rgb + accent * glow * GLOW_GAIN * (1.0 - isAccent);

    // working breathes slowly; blocked gives two soft beats and rests. A window that is
    // not focused is not animated, so there the beacons hold steady at full strength.
    float live = iFocus > 0 ? 1.0 : 0.0;
    float breathe = 0.5 + 0.5 * sin(iTime * TAU / WORK_PERIOD);
    float p = fract(iTime / BLOCK_PERIOD);
    float b1 = (p - 0.10) / 0.055;
    float b2 = (p - 0.30) / 0.070;
    float beat = min(1.0, exp(-b1 * b1) + 0.65 * exp(-b2 * b2));
    breathe = mix(1.0, breathe, live);
    beat = mix(1.0, beat, live);
    col *= mix(1.0, 0.60 + 0.40 * breathe, isWork);
    col *= mix(1.0, 0.55 + 0.45 * beat, isBlock);
    col += sigWork * work * (0.15 + 0.85 * breathe) * BEACON_GAIN * (1.0 - isWork);
    col += sigBlock * block * (0.15 + 0.85 * beat) * BEACON_GAIN * (1.0 - isBlock);

    // banked embers: cool while unfocused, warm back up when focus returns
    float sinceFocus = iTime - iTimeFocus;
    float bank = BANK * (1.0 - live * smoothstep(0.0, BANK_TIME, sinceFocus));
    col = mix(col, vec3(dot(col, vec3(0.2126, 0.7152, 0.0722))), bank) * (1.0 - 0.35 * bank);

    // ignition: one thin line of coral light runs top to bottom on focus
    float t = sinceFocus / SWEEP_TIME;
    if (iFocus > 0 && t >= 0.0 && t < 1.0) {
        float e = 1.0 - pow(1.0 - t, 3.0);
        float y = 1.0 - e;
        float d = abs(uv.y - y) * iResolution.y;
        float line = exp(-d * d / 6.0) + 0.35 * exp(-d / 28.0) * step(y, uv.y);
        col += accent * line * 0.55 * (1.0 - t);
    }

    // cursor
    vec2 size = iCurrentCursor.zw;
    float h = size.y;
    if (h >= 1.0) {
        vec2 cur  = iCurrentCursor.xy  + vec2(size.x, -size.y) * 0.5;
        vec2 prev = iPreviousCursor.xy + vec2(iPreviousCursor.z, -iPreviousCursor.w) * 0.5;
        vec3 c = iCurrentCursorColor.rgb;

        // the thread
        float travel = distance(cur, prev);
        float ct = clamp((iTime - iTimeCursorChange) / DURATION, 0.0, 1.0);
        if (ct < 1.0 && travel >= 1.0) {
            float e = 1.0 - pow(1.0 - ct, 3.0);
            vec2 tail = mix(prev, cur, e);
            float d = sdTaper(fragCoord, tail, cur, 0.0, size.x * 0.5);
            float body = smoothstep(1.2, -1.2, d);
            float halo = exp(-max(d, 0.0) / (h * 0.18)) * 0.18;

            // long jumps (screen redraws) get a quieter thread than typing
            float calm = mix(1.0, 0.45, smoothstep(h * 12.0, h * 40.0, travel));
            float a = (body * TRAIL_ALPHA + halo) * (1.0 - ct) * calm;

            float bloom = exp(-distance(fragCoord, cur) / (h * 0.5)) * BLOOM * (1.0 - ct);
            col = mix(col, c, clamp(a, 0.0, 1.0)) + c * bloom;
        }

        // the breath: light around a cursor that is shown, in the focused window only
        if (iCursorVisible > 0 && iFocus > 0) {
            vec2 q = abs(fragCoord - cur) - size * 0.5;
            float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0);
            float breath = 0.5 + 0.5 * sin(iTime * TAU / CURSOR_PERIOD);
            col += c * exp(-max(sd, 0.0) / (h * 0.30)) * step(0.0, sd) * CURSOR_HALO * (0.30 + 0.70 * breath);
        }
    }

    fragColor = vec4(col, base.a);
}
