#include <stdexcept>
#include <iostream>
#include <algorithm>

#include <option_parser.hpp>

OptionParser::OptionParser(int argc, char** argv,
			   std::optional<std::vector<std::string>> required_opts,
			   std::optional<std::vector<std::string>> optional_opts,
			   std::optional<std::vector<std::string>> opts_with_value) {
  argc_ = argc;
  argv_ = argv;
  program_name_ = argv_[0];

  if (required_opts.has_value()) {
    required_opts_ = required_opts.value();
  }
  if (optional_opts.has_value()) {
    optional_opts_ = optional_opts.value();
  }
  if (opts_with_value.has_value()) {
    opts_with_value_ = opts_with_value.value();
  }

  // merge required and optional opts
  all_opts_.insert(all_opts_.end(), required_opts_.begin(), required_opts_.end());
  all_opts_.insert(all_opts_.end(), optional_opts_.begin(), optional_opts_.end());

  parse();
  printOpts();
}

void OptionParser::parse() {
  std::pair<std::string, std::string> option;
  for (int i = 1; i < argc_; i++) {
    std::string opt = argv_[i];

    if (!isValidOpt(opt) && option.first[0] != '-') {
      throw std::runtime_error("invalid option: " + opt);
    }

    // option or value?
    if (opt[0] == '-') {
      // was the previous opt expecting a value?
      if (optRequiresValue(option.first)) {
	throw std::runtime_error("option '" + option.first +  "' expects value");
      }

      // have we reached the end with an opt expecting a value?
      if (optRequiresValue(opt) && i == argc_ - 1) {
	throw std::runtime_error("option '" + opt +  "' expects value");
      }

      option.first = opt;
      if (optRequiresValue(opt)) {
	// value is expected in next loop iteration
	continue;
      } else {
	// no value expected, just insert the opt
	options_.insert(option);
	option = {};
      }
    } else {
      // was the previous an option?
      if (option.first[0] == '-') {
	option.second = opt;
	options_.insert(option);
	option = {};
      } else {
	throw std::runtime_error("invalid option: " + opt);
      }
    }
  }
}

void OptionParser::printOpts() {
  std::cout << "RUNNING WITH THE FOLLOWING FLAGS:" << std::endl;
  for (auto opt : options_) {
    std::cout << opt.first << " : " << opt.second << std::endl;
  }
  std::cout << std::endl;
}

bool OptionParser::isValidOpt(std::string opt) {
  return (std::find(all_opts_.begin(), all_opts_.end(), opt) != all_opts_.end());
}

bool OptionParser::optRequiresValue(std::string opt) {
  return (std::find(opts_with_value_.begin(), opts_with_value_.end(), opt) != opts_with_value_.end());
}

std::string OptionParser::getOptValue(std::string opt) {
  if (!isValidOpt(opt)) {
    throw std::runtime_error("invalid opt: " + opt);
  }
  if (!optExists(opt)) {
    return "";
  }
  return options_[opt];
}

bool OptionParser::optExists(std::string opt) {
  return !(options_.find(opt) == options_.end());
}
