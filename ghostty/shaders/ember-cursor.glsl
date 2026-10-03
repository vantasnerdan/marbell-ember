// Marbell Ember · cursor thread
// The cursor leaves a coral thread from where it was to where it is: a tapered
// comet, as wide as the cursor, that catches up in ~160 ms.

const float DURATION = 0.16;   // s
const float TRAIL_ALPHA = 0.60;
const float BLOOM = 0.05;

float sdTaper(vec2 p, vec2 a, vec2 b, float ra, float rb) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-4), 0.0, 1.0);
    return length(pa - ba * h) - mix(ra, rb, h);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 base = texture(iChannel0, fragCoord / iResolution.xy);
    fragColor = base;

    vec2 cur  = iCurrentCursor.xy  + vec2(iCurrentCursor.z,  -iCurrentCursor.w)  * 0.5;
    vec2 prev = iPreviousCursor.xy + vec2(iPreviousCursor.z, -iPreviousCursor.w) * 0.5;
    float h = iCurrentCursor.w;
    float travel = distance(cur, prev);
    float t = clamp((iTime - iTimeCursorChange) / DURATION, 0.0, 1.0);
    if (t >= 1.0 || travel < 1.0 || h < 1.0) return;

    float e = 1.0 - pow(1.0 - t, 3.0);
    vec2 tail = mix(prev, cur, e);
    float d = sdTaper(fragCoord, tail, cur, 0.0, iCurrentCursor.z * 0.5);
    float body = smoothstep(1.2, -1.2, d);
    float halo = exp(-max(d, 0.0) / (h * 0.18)) * 0.18;

    // long jumps (screen redraws) get a quieter thread than typing
    float calm = mix(1.0, 0.45, smoothstep(h * 12.0, h * 40.0, travel));
    float a = (body * TRAIL_ALPHA + halo) * (1.0 - t) * calm;

    float bloom = exp(-distance(fragCoord, cur) / (h * 0.5)) * BLOOM * (1.0 - t);
    vec3 c = iCurrentCursorColor.rgb;
    fragColor = vec4(mix(base.rgb, c, clamp(a, 0.0, 1.0)) + c * bloom, base.a);
}
