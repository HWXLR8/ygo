#include <iostream>
#include <cstring>
#include <cmath>
#include <thread>

#include <mixer.hpp>

ALuint Mixer::Sources_[256];
std::map<std::string, ALuint> Mixer::Sounds_;
std::queue<std::string> Mixer::SoundQueue_ = {};

void Mixer::init() {
  ALCdevice *device;
  ALCcontext *context;
  ALboolean enumeration;

  enumeration = alcIsExtensionPresent(NULL, "ALC_ENUMERATION_EXT");
  if (enumeration == AL_FALSE) {
    throw std::runtime_error("device enumeration is not supported");
  }

  // init ALUT
  alutInitWithoutContext(NULL, NULL);

  // list audio devices
  listDevices(alcGetString(NULL, ALC_DEVICE_SPECIFIER));

  // open default device
  device = alcOpenDevice(NULL);
  if (!device) {
    throw std::runtime_error("could not open audio device");
  }
  std::cout << "USING AUDIO DEVICE: " <<
    alcGetString(device, ALC_DEVICE_SPECIFIER) << std::endl;

  // reset the error stack
  alGetError();

  // create context
  context = alcCreateContext(device, NULL);
  if (!alcMakeContextCurrent(context)) {
    throw std::runtime_error("failed to make context current");
  }

  // configure the listener
  // check for errors after each one
  alListener3f(AL_POSITION, 0, 0, 1.0f);
  alListener3f(AL_VELOCITY, 0, 0, 0);
  ALfloat listenerOri[] = { 0.0f, 0.0f, 1.0f, 0.0f, 1.0f, 0.0f };
  alListenerfv(AL_ORIENTATION, listenerOri);

  generateSources();
}

void Mixer::generateSources() {
  ALCenum err;
  alGenSources((ALuint)256, Sources_);
  if ((err = alGetError()) != AL_NO_ERROR) {
    throw std::runtime_error(openALErrorToString(err));
  }
}

void Mixer::listDevices(const ALCchar* devices) {
  const ALCchar *device = devices;
  const ALCchar *next = devices + 1;
  unsigned int len = 0;

  std::cout << "Audio device list:" << std::endl;
  std::cout << "------------------" << std::endl;
  while (device && *device != '\0' && next && *next != '\0') {
    std::cout << device << std::endl;
    len = strlen(device);
    device += (len + 1);
    next += (len + 2);
  }
  std::cout << "------------------" << std::endl;
}

void Mixer::render(std::string sound_name) {
  // configure the source (origin of the sound)
  // check for errors after each one

  // alSourcef(Sources_[0], AL_PITCH, 1);
  // alSourcef(Sources_[0], AL_GAIN, 1);
  // alSource3f(Sources_[0], AL_POSITION, 0, 0, 0);
  // alSource3f(Sources_[0], AL_VELOCITY, 0, 0, 0);
  // alSourcei(Sources_[0], AL_LOOPING, AL_FALSE);

  // create buffer
  ALuint buffer = getSound(sound_name);

  // binding source to buffer
  std::optional<ALuint> op_source = getFreeSource();
  if (!op_source.has_value()) {
    throw std::runtime_error("Exhausted the list of free audio sources, this is either a bug, or you have more than 256 sources.");
  }
  ALuint source = op_source.value();
  alSourcei(source, AL_BUFFER, buffer);

  // play the sound
  alSourcePlay(source);

  // alDeleteSources(source, &source);
  // device = alcGetContextsDevice(context);
  // alcMakeContextCurrent(NULL);
  // alcDestroyContext(context);
  // alcCloseDevice(device);
  // alutExit();
}

void Mixer::loadSoundFromFile(std::string path, std::string name) {
  ALuint buffer = alutCreateBufferFromFile(path.c_str());
  if (buffer == AL_NONE) {
    throw std::runtime_error("failed to load sound file: " + path);
    return;
  }
  Sounds_[name] = buffer;
}

ALuint Mixer::getSound(std::string sound_name) {
  if (Sounds_.find(sound_name) == Sounds_.end()) {
    throw std::runtime_error("no such sound named: " + sound_name + ". Has it been loaded yet?");
  }
  return Sounds_[sound_name];
}

void Mixer::pushToQueue(std::string sound_name) {
  if (Sounds_.find(sound_name) == Sounds_.end()) {
    throw std::runtime_error("invalid sound added to queue named: " + sound_name + ". Has it been loaded yet?");
  }
  std::mutex mtx;
  mtx.lock();
  SoundQueue_.push(sound_name);
  mtx.unlock();
}

std::string Mixer::popFromQueue() {
  std::mutex mtx;
  mtx.lock();
  std::string sound_name = SoundQueue_.front();
  SoundQueue_.pop();
  mtx.unlock();
  return sound_name;
}

void Mixer::startMixer() {
  while (true) {
    if (!SoundQueue_.empty()) {
      std::string sound = popFromQueue();
      render(sound);
    }
  }
}

void Mixer::playSound(std::string sound_name) {
  pushToQueue(sound_name);
}

bool Mixer::isSourcePlaying(ALuint source) {
    ALenum state;
    alGetSourcei(source, AL_SOURCE_STATE, &state);
    return (state == AL_PLAYING);
}

std::string Mixer::openALErrorToString(int err) {
  switch (err) {
  case AL_NO_ERROR: return "AL_NO_ERROR";
  case AL_INVALID_ENUM: return "AL_INVALID_ENUM";
  case AL_INVALID_VALUE: return "AL_INVALID_VALUE";
  case AL_OUT_OF_MEMORY: return "AL_OUT_OF_MEMORY";
  case AL_INVALID_NAME: return "AL_INVALID_NAME";
  case AL_INVALID_OPERATION: return "AL_INVALID_OPERATION";
  default:
    return "Unknown error code";
  }
}

std::optional<ALuint> Mixer::getFreeSource() {
  for (ALuint source : Sources_) {
    if(!isSourcePlaying(source)) {
      return source;
    }
  }
  return std::nullopt;
}
