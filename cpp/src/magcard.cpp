#include <magcard.hpp>
#include <config.hpp>

MagCard::MagCard() {
  card_ = new Graphic("../netplay/assets/ducc.png", COORD.mag_card, MAG_CARD_SIZE, false);
}

void MagCard::update(std::optional<Card*> active_card) {
  // are we hovering over a card?
  if (active_card.has_value()) {
    Texture2D active_card_tex = active_card.value()->getTexture();
    Texture2D card_tex = card_->getTexture();
    // is that card different than the current mag card?
    if (card_tex != active_card_tex) {
      card_->setTexture(active_card_tex);
    }
    card_->setVisible();
  } else {
    card_->setInvisible();
  }
}

void MagCard::render(Renderer* renderer) {
  card_->render(renderer);
}
