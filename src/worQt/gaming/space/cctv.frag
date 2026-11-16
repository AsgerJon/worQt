// cctv.frag: the closed circuit monitor's picture as an old camera tube
// gave it (Qt Quick 3D's own post effect: no QML loaded while running,
// unlike Qt's MultiEffect, which deadlocked against worQt's 'App.notify'
// on the QML loader's thread). Black and white, a cold tint, the blacks
// lifted and the whites crushed a little; alpha kept (the near layer is
// see-through over the far).
//
// Apache-2.0 license
// Copyright (c) 2026 Asger Jon Vistisen

void MAIN()
{
    vec4 colour = texture(INPUT, INPUT_UV);
    float light = dot(colour.rgb, vec3(0.299, 0.587, 0.114));
    float shaped = clamp((light - 0.04 * colour.a) * 1.25, 0.0, 1.0);
    FRAGCOLOR = vec4(shaped * vec3(0.86, 0.93, 1.0), colour.a);
}
