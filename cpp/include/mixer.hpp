#ifndef MIXER_H
#define MIXER_H

#include <AL/al.h>
#include <AL/alc.h>
#include <AL/alut.h>

#include <string>
#include <queue>
#include <map>
#include <mutex>
#include <optional>

class Mixer {
public:
  static void init();
  static void loadSoundFromFile(std::string path, std::string name);
  static std::string popFromQueue();
  static void startMixer();
  // playSound() queues up the sound
  static void playSound(std::string sound_name);

private:
  static ALuint Sources_[256];
  static std::map<std::string, ALuint> Sounds_;
  static std::queue<std::string> SoundQueue_;
  // render() actually plays the sound
  static void render(std::string sound);
  static void pushToQueue(std::string sound_name);
  static void generateSources();
  static void listDevices(const ALCchar* devices);
  static ALuint getSound(std::string sound_name);
  static std::optional<ALuint> getFreeSource();
  static bool isSourcePlaying(ALuint source);
  static std::string openALErrorToString(int err);
};

#endif
