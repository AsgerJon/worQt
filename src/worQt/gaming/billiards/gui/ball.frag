//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen
//
//  A carom ball, as Super Aramith's Pro-Cup set: six dots where the
//  axes of the ball's own frame meet its surface, as the faces of a
//  cube; 'dotSize' is a dot's radius over the ball's. Colours come in
//  linear. Polished resin under a clear coat. The lit cloth's blue
//  bounces up into the ball's underside, 'bounceColor' as strong as
//  'bounceStrength': a light for the balls alone, so it lives here.

VARYING vec3 ballDirection;

void MAIN()
{
    vec3 along = abs(normalize(ballDirection));
    float nearest = max(along.x, max(along.y, along.z));
    float edge = sqrt(1.0 - dotSize * dotSize);
    float blur = max(fwidth(nearest), 1e-5);
    float inDot = smoothstep(edge - blur, edge + blur, nearest);
    vec3 colour = mix(bodyColor, dotColor, inDot);
    BASE_COLOR = vec4(colour, 1.0);
    float below = clamp(-normalize(VAR_WORLD_NORMAL).y, 0.0, 1.0);
    EMISSIVE_COLOR = colour * bounceColor * (bounceStrength * below);
    METALNESS = 0.0;
    ROUGHNESS = mix(0.1, 0.45, inDot);
    //  The lamps' and room's light on the clear coat washed the dots out
    //  (the user): the dots reflect little, so they read black.
    SPECULAR_AMOUNT = mix(0.4, 0.05, inDot);
    CLEARCOAT_AMOUNT = mix(0.6, 0.1, inDot);
    CLEARCOAT_ROUGHNESS = 0.03;
}
