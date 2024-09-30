#ifndef GRAPHIC_H
#define GRAPHIC_H

#include <optional>

#include <renderer.hpp>

class Graphic {
public:
  Graphic(std::string texturePath, glm::vec2 position, glm::vec2 size, bool transparent);
  void update(double dt);
  void render(Renderer *renderer);
  void move(glm::vec2 dest, std::optional<double> a_time, double dt);
  void changeSize(glm::vec2 new_size, glm::vec2 speed, double dt);
  bool isActive(glm::vec2 mouse_);
  bool isMoving();
  void stopMoving();
  glm::vec2 getPosition();
  void illuminate();
  void fade();
  void setColor(glm::vec4 color);
  bool isVisible();
  void setVisible();
  void setInvisible();
  void setTexture(Texture2D new_tex);
  Texture2D getTexture();
  void steerMovement(glm::vec2 new_dest);

protected:
  glm::vec2 size_;
  glm::vec2 position_;
  glm::vec3 rotation_ = {0.0f, 0.0f, 0.0f};
  glm::vec4 color_ = {1.0f, 1.0f, 1.0f, 1.0f};

  // move
  bool move_in_progress_ = false;
  glm::vec2 move_speed_;
  glm::vec2 move_chunk_ = {0, 0};
  glm::vec2 move_dest_;
  double move_remaining_time_;

  // change size
  bool change_size_in_progress_ = false;
  glm::vec2 new_size_;
  glm::vec2 growth_speed_;
  glm::vec2 growth_chunk_;
  glm::vec2 remaining_growth_;

  bool visible_ = true;
  bool illuminated_ = true;
  Texture2D texture_;

private:
  glm::vec2 calculateUnitVector(glm::vec2 p1, glm::vec2 p2);
  double calculateVectorMagnitude(glm::vec2 p1, glm::vec2 p2);
};

#endif
