#version 330
#define PI 3.1415926538

uniform sampler2D Texture;

in vec3 v_color;
in vec2 v_text;

out vec4 f_color;

uniform float r;
uniform float g;
uniform float b;
uniform float a;

void main() {
  vec4 col = vec4 (r, g, b, a);
  f_color = texture(Texture, v_text) * col;
}
