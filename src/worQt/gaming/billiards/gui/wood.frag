//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen
//
//  Wood, lacquered, ebony in the tones the scene gives: growth rings
//  about an axis along the piece's own z, a little below and beside it
//  and wandering, so a flat face shows long wavy lines along the piece;
//  broad colour swells along it. The rings fade where they would be
//  finer than a pixel. 'woodLight' and 'woodDark' come in linear.

VARYING vec3 woodPoint;

void MAIN()
{
    vec3 p = woodPoint;
    float bend = 9.0 * sin(p.z * 0.0041) + 15.0 * sin(p.z * 0.0013 + 1.7);
    float radius = length(vec2(0.8 * p.x + 41.0, p.y + 230.0 + bend));
    float rings = radius / 6.5;
    float ring = fract(rings);
    float line = smoothstep(0.55, 0.85, ring)
               * (1.0 - smoothstep(0.85, 1.0, ring));
    float fade = clamp(1.0 - 2.0 * fwidth(rings), 0.0, 1.0);
    float swell = 0.5 + 0.5 * sin(p.z * 0.0023 + 0.011 * p.x
                                  + 0.7 * sin(p.z * 0.0009));
    float shade = 0.72 + 0.28 * swell - 0.45 * line * fade;
    BASE_COLOR = vec4(mix(woodDark, woodLight, clamp(shade, 0.0, 1.0)),
                      1.0);
    //  A satin lacquer: the lamp straight above shows as a soft sheen,
    //  not a mirror that turns the dark wood white seen from overhead.
    METALNESS = 0.0;
    ROUGHNESS = 0.45;
    SPECULAR_AMOUNT = 0.35;
    CLEARCOAT_AMOUNT = 0.6;
    CLEARCOAT_ROUGHNESS = 0.35;
}
