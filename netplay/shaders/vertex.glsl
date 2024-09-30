#version 330

in vec3 in_vert;
in vec3 in_color;
in vec2 in_text;

out vec3 v_color;
out vec2 v_text;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main() {
  gl_Position = projection * view * model * vec4(in_vert, 1.0);
  v_color = in_color;
  v_text = in_text;
}
