#!/usr/bin/env ruby
require "erb"
require 'securerandom'

## Fetch submodule
system "echo", "-n", "Initializing cookbook submodule ...    "
`git submodule update --init --recursive`
sleep(1)
system "echo", "-e", "\rInitializing cookbook submodule ...     [DONE]\033[K"

def random_string(length=10)
  chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
  str = ''
  length.times { str << chars[rand(chars.size)] }
  str
end

class ERBContext
  def initialize(hash)
    hash.each_pair do |key, value|
      instance_variable_set('@' + key.to_s, value)
    end
  end

  def get_binding
    binding
  end
end

class String
  def eruby(assigns={})
    ERB.new(self).result(ERBContext.new(assigns).get_binding)
  end
end

## Create fresh local.py with default database connection info
if !File.exists? "lfucg-ckan/config.ini"
    config_data = {
        :config => {
            "DATABASE_NAME" => "lfucg",
            "DATABASE_USER" => "postgres",
            "DATABASE_PASSWORD" => "password",
            "DATABASE_HOST" => "127.0.0.1",
            "DATABASE_PORT" => "5432",
            "SESSION_SECRET" => random_string(length=25),
            "APP_INSTANCE_UUID" => SecureRandom.uuid,
            "USER" => "vagrant",
            "SITE_URL" => "http://localhost:8000"
        }
    }
    system "echo", "-n", "Initializing config.ini with defaults ..."
    template = File.read("lfucg-ckan/config.ini.erb")
    File.write("lfucg-ckan/config.ini", template.eruby(config_data))
    sleep(1)
    system "echo", "-e", "\rInitializing config.ini with defaults ... [DONE]\033[K"
end

puts "Starting vm ..."
Dir.chdir("chef-lfucg") do
    system "vagrant up"
end