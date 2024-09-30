#version 330 core

in vec2 TexCoords;
out vec4 color;

uniform sampler2D image;
uniform vec4 spriteColor;
uniform float time;

void main() {
  color = vec4(spriteColor) * texture(image, vec2(TexCoords.x*8 - time/10, TexCoords.y*5 + time/10));
}
