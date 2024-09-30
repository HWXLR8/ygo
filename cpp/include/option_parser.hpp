#ifndef OPTION_PARSER_H
#define OPTION_PARSER_H

#include <optional>
#include <vector>
#include <map>
#include <string>

class OptionParser {
public:
  OptionParser(int argc, char** argv,
	       std::optional<std::vector<std::string>> required_opts,
	       std::optional<std::vector<std::string>> optional_opts,
	       std::optional<std::vector<std::string>> opts_with_value);
  void printOpts();
  bool optExists(std::string opt);
  std::string getOptValue(std::string);

private:
  int argc_;
  char** argv_;
  std::string program_name_;
  std::vector<std::string> all_opts_ = {};
  std::vector<std::string> required_opts_ = {};
  std::vector<std::string> optional_opts_ = {};
  std::vector<std::string> opts_with_value_ = {};
  std::map<std::string, std::string> options_;

  void parse();
  bool isValidOpt(std::string opt);
  bool optRequiresValue(std::string opt);
};

#endif
