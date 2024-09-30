#version 330
#define PI 3.1415926538

uniform sampler2D Texture;

in vec3 v_color;
in vec2 v_text;

out vec4 f_color;

uniform float time;
uniform float r;
uniform float g;
uniform float b;
uniform float a;

void main() {
  float t = time / 15;
  vec4 col = vec4 (0.08*sin(t+2*PI)+1.1, 0.08*sin(t+2*PI/3)+1.1, 0.08*sin(t+4*PI/3) + 1.1, 1.0) * vec4 (r, g, b, a);
  f_color = texture(Texture, v_text) * col;
}
