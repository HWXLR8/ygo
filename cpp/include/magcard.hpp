#ifndef MAGCARD_H
#define MAGCARD_H

#include <renderer.hpp>
#include <graphic.hpp>
#include <card.hpp>

class MagCard {
public:
  MagCard();
  void update(std::optional<Card*> active_card);
  void render(Renderer* renderer);
private:
  Graphic* card_;
};

#endif
