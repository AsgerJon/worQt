//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen
//
//  A carom ball: hands the fragment shader the way each point lies from
//  the ball's middle, in the ball's own frame, so the dots turn with it.

VARYING vec3 ballDirection;

void MAIN()
{
    ballDirection = VERTEX;
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(VERTEX, 1.0);
}
