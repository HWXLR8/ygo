#ifndef RENDERER_H
#define RENDERER_H

#include <glm/glm.hpp>

#include <texture.hpp>
#include <shader.hpp>

class Renderer {
 public:
  Renderer(Shader& shader);
  ~Renderer();
  void setShader(Shader& shader);
  void blit(Texture2D &texture, glm::vec2 position, glm::vec2 size, glm::vec3 rotation, glm::vec4 color);

 private:
  Shader shader_;
  unsigned int quadVAO_;
  void initRenderData();
};

#endif
