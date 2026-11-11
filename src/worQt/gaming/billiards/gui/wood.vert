//  Apache-2.0 license
//  Copyright (c) 2026 Asger Jon Vistisen
//
//  Walnut: hands the fragment shader each point in the piece's own
//  frame, in mm, moved by 'grainShift' so no two pieces are cut from
//  the same place in the log.

VARYING vec3 woodPoint;

void MAIN()
{
    woodPoint = VERTEX + grainShift;
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(VERTEX, 1.0);
}
